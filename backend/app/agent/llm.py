"""Provider-neutral LLM client: OpenAI-compatible, retries, quota-aware cooldowns, per-role fallback chain.
Handles Gemini 3 'thought signatures' (required when echoing tool calls back)."""
import os, re, json, time, random, uuid, logging
from openai import OpenAI, RateLimitError, APITimeoutError, APIConnectionError, APIStatusError
from .config import PROVIDERS, ROLES, ROLE_TEMP

log = logging.getLogger("basrar.llm")
RETRYABLE = {408, 409, 429, 500, 502, 503, 504}
SENTINEL = {"google": {"thought_signature": "skip_thought_signature_validator"}}   # Google's documented last-resort bypass

class LLMError(Exception): pass

def extract_json(text: str):
    """Robustly pull the first JSON object out of a model reply (fences, prose, <think> blocks)."""
    t = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    t = re.sub(r"```(?:json)?", "", t)
    a, b = t.find("{"), t.rfind("}")
    if a < 0 or b <= a: return None
    try: return json.loads(t[a:b + 1])
    except Exception: return None

def assistant_message(m: dict) -> dict:
    """Normalized reply -> OpenAI-format history entry. Provider extras (Gemini thought signatures) are preserved."""
    msg = {"role": "assistant", "content": m["content"] or ""}
    if m["tool_calls"]:
        calls = []
        for c in m["tool_calls"]:
            tc = {"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": c["arguments"]}}
            if c.get("extra_content"): tc["extra_content"] = c["extra_content"]
            calls.append(tc)
        msg["tool_calls"] = calls
    return msg

def _prepare(messages, provider):
    """Adapt provider-neutral history for the target provider."""
    out = []
    for m in messages:
        if m.get("role") == "assistant" and m.get("tool_calls"):
            calls = [dict(c) for c in m["tool_calls"]]
            if provider == "gemini":
                if "extra_content" not in calls[0]: calls[0]["extra_content"] = SENTINEL   # history from another model/provider
            else:
                for c in calls: c.pop("extra_content", None)
            m = {**m, "tool_calls": calls}
        out.append(m)
    return out

def _detail(e):
    return str(getattr(e, "message", None) or e)[:300]

def _retry_after(e):
    try: return float(e.response.headers.get("retry-after"))
    except Exception: return None

class LLM:
    def __init__(self): self._clients = {}; self._cool = {}      # (provider, model) -> time until which we skip it

    def _client(self, provider):
        if provider not in self._clients:
            p = PROVIDERS.get(provider)
            if not p: raise LLMError(f"unknown provider {provider}")
            key = os.getenv(p["key_env"])
            if not key: raise LLMError(f"{p['key_env']} is not set")
            self._clients[provider] = OpenAI(base_url=p["base_url"], api_key=key, timeout=60, max_retries=0)
        return self._clients[provider]

    def chat(self, role, messages, tools=None, max_tokens=4096, retries=3):
        errors = []
        for provider, model in ROLES[role]:
            key = (provider, model)
            if self._cool.get(key, 0) > time.time():
                errors.append(f"{provider}/{model}: skipped (quota/rate-limit cooldown)"); continue
            try: client = self._client(provider)
            except LLMError as e: errors.append(str(e)); continue
            msgs = _prepare(messages, provider)
            err = None
            for attempt in range(retries):
                try:
                    kw = dict(model=model, messages=msgs, max_tokens=max_tokens, temperature=ROLE_TEMP[role])
                    if tools: kw.update(tools=tools, tool_choice="auto")
                    r = client.chat.completions.create(**kw)
                    msg = r.choices[0].message
                    calls = [{"id": tc.id or "call_" + uuid.uuid4().hex[:8], "name": tc.function.name,
                              "arguments": tc.function.arguments or "{}",
                              "extra_content": (getattr(tc, "model_extra", None) or {}).get("extra_content")}
                             for tc in (msg.tool_calls or [])]
                    text = re.sub(r"<think>.*?</think>", "", msg.content or "", flags=re.S).strip()
                    if not text and not calls: raise LLMError("empty response")
                    return {"content": text, "tool_calls": calls, "provider": provider, "model": model}
                except RateLimitError as e:
                    err = e; d = _detail(e).lower(); ra = _retry_after(e)
                    if any(h in d for h in ("per-day", "per_day", "perday", "daily")):          # daily quota: retrying is pointless
                        self._cool[key] = time.time() + 3600
                        errors.append(f"{provider}/{model}: daily quota exhausted"); break
                    if ra and ra > 30:
                        self._cool[key] = time.time() + ra; errors.append(f"{provider}/{model}: rate limited for {ra:.0f}s"); break
                except (APITimeoutError, APIConnectionError, LLMError) as e: err = e
                except APIStatusError as e:
                    err = e
                    if e.status_code not in RETRYABLE:                    # 400/401/404...: this model/history won't work, try next
                        errors.append(f"{provider}/{model}: HTTP {e.status_code}: {_detail(e)}"); break
                log.warning("%s/%s attempt %d failed: %s", provider, model, attempt + 1, _detail(err) if err else "")
                if attempt < retries - 1: time.sleep(min(3 * 2 ** attempt + random.random(), 25))
            else:
                errors.append(f"{provider}/{model}: {type(err).__name__} {_detail(err)[:120] if err else ''}")
        raise LLMError("all providers failed for role '%s': %s" % (role, "; ".join(errors)))

llm = LLM()