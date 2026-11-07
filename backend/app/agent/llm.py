"""Provider-neutral LLM client: OpenAI-compatible, retries with backoff, per-role fallback chain."""
import os, re, json, time, random, uuid, logging
from openai import OpenAI, RateLimitError, APITimeoutError, APIConnectionError, APIStatusError
from .config import PROVIDERS, ROLES, ROLE_TEMP

log = logging.getLogger("basrar.llm")
RETRYABLE = {408, 409, 429, 500, 502, 503, 504}

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
    """Normalized reply -> OpenAI-format history entry (reasoning blocks are intentionally dropped)."""
    msg = {"role": "assistant", "content": m["content"] or ""}
    if m["tool_calls"]:
        msg["tool_calls"] = [{"id": c["id"], "type": "function",
                              "function": {"name": c["name"], "arguments": c["arguments"]}} for c in m["tool_calls"]]
    return msg

class LLM:
    def __init__(self): self._clients = {}

    def _client(self, provider):
        if provider not in self._clients:
            p = PROVIDERS.get(provider)
            if not p: raise LLMError(f"unknown provider {provider}")
            key = os.getenv(p["key_env"])
            if not key: raise LLMError(f"{p['key_env']} is not set")
            self._clients[provider] = OpenAI(base_url=p["base_url"], api_key=key, timeout=90, max_retries=0)
        return self._clients[provider]

    def chat(self, role, messages, tools=None, max_tokens=4096, retries=3):
        errors = []
        for provider, model in ROLES[role]:
            try: client = self._client(provider)
            except LLMError as e: errors.append(str(e)); continue
            for attempt in range(retries):
                try:
                    kw = dict(model=model, messages=messages, max_tokens=max_tokens, temperature=ROLE_TEMP[role])
                    if tools: kw.update(tools=tools, tool_choice="auto")
                    r = client.chat.completions.create(**kw)
                    msg = r.choices[0].message
                    calls = [{"id": tc.id or "call_" + uuid.uuid4().hex[:8], "name": tc.function.name,
                              "arguments": tc.function.arguments or "{}"} for tc in (msg.tool_calls or [])]
                    text = re.sub(r"<think>.*?</think>", "", msg.content or "", flags=re.S).strip()
                    if not text and not calls: raise LLMError("empty response")
                    return {"content": text, "tool_calls": calls, "provider": provider, "model": model}
                except RateLimitError as e: err = e
                except (APITimeoutError, APIConnectionError, LLMError) as e: err = e
                except APIStatusError as e:
                    err = e
                    if e.status_code not in RETRYABLE:           # e.g. 400/401/404: this model won't work, try next
                        errors.append(f"{provider}/{model}: HTTP {e.status_code}"); break
                log.warning("%s/%s attempt %d failed: %s", provider, model, attempt + 1, err)
                if attempt < retries - 1: time.sleep(min(2 ** attempt + random.random(), 20))
            else:
                errors.append(f"{provider}/{model}: {type(err).__name__}")
        raise LLMError("all providers failed for role '%s': %s" % (role, "; ".join(errors)))

llm = LLM()