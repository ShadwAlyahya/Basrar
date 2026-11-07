"""The autonomous loop: understand -> decide -> call tools -> verify -> independent review -> communicate."""
import json
from .state import Session
from .tools import DISPATCH, OPENAI_TOOLS, apply_decisions
from .llm import llm, assistant_message
from .config import MAX_CRITIC_ROUNDS
from .guard import unverified, fact_pool
from . import critic
 
SYSTEM = """You are Basrar, an autonomous senior data analyst working through tools on the user's dataset.
The original file is immutable; you work on a copy and every change is audited.
 
PROCESS (enforced by code: submit_findings is rejected if you skip a step):
1. UNDERSTAND: profile_dataset, then detect_issues. Infer what each column means and what the goal needs.
2. DECIDE: for each issue pick an action and justify it. INVESTIGATE with inspect_rows BEFORE touching suspicious data
   (negative profit may be real losses; huge values may be typos or real big orders). Safe ops (strip_whitespace, parse_dates,
   cast_numeric) run automatically. Sensitive ops (drop_duplicates, impute, drop_missing_rows, cap_outliers) can only be QUEUED
   with propose_cleaning for user approval; never say they happened until approved. Do not impute columns with massive missingness.
3. After proposing sensitive ops, stop calling tools and tell the user briefly what you found and what you recommend. The system pauses for approval.
4. EXECUTE only the analyses the goal needs (kpi, aggregate, correlations, distribution, forecast, what_if, calc).
   Any data change invalidates earlier analytic results and charts: recompute them.
5. VERIFY: call verify_cleaning after any data change and explain drift.
6. COMMUNICATE: create 2-5 charts from evidence, then submit_findings. Every KPI/insight cites evidence_ids; every number you write must
   exist in that evidence (use calc for changes, ratios, shares). If rejected, fix and resubmit. An independent reviewer then checks the result.
STANDARDS: never invent numbers; state uncertainty (forecast reliability, weak R^2, correlation is not causation, partial data);
do not generalize beyond the data (top_n is a subset). If the goal is empty, choose 3 sharp questions yourself and say which.
LANGUAGE: answer in the user's language (Arabic or English). Use Western digits 0-9. Keep column names exactly as in the data."""
 
CHAT = """\nMODE: chat follow-up. The analysis already exists. Answer the user's question; call tools whenever you need a number
(kpi, aggregate, forecast, what_if, calc...). Every number must come from a tool result in this session. Be concise.
If the user asks to change data, use propose_cleaning (approval required). Create a chart only if asked or clearly useful."""
 
def _sys(s, mode):
    note = f"\n\nDATASET: {s.filename}; {len(s.work)} rows now ({len(s.original)} original); data_version={s.data_version}. GOAL: {s.goal or '(none - propose questions)'}."
    return {"role": "system", "content": SYSTEM + (CHAT if mode == "chat" else "") + note}
 
def _shrink(o, n=40):
    if isinstance(o, list): return [_shrink(x, n) for x in o[:n]] + ([f"...{len(o) - n} more"] if len(o) > n else [])
    if isinstance(o, dict): return {k: _shrink(v, n) for k, v in o.items()}
    return o
 
def _exec_tool(s, tc):
    s.metrics["tool_calls"] += 1; args = {}
    try:
        args = json.loads(tc["arguments"] or "{}")
        if not isinstance(args, dict): raise ValueError("arguments must be a JSON object")
        fn = DISPATCH.get(tc["name"])
        if not fn: raise ValueError(f"unknown tool {tc['name']}")
        out = fn(s, **args)
    except Exception as e:                                           # the agent sees the error and self-corrects
        out = {"error": f"{type(e).__name__}: {e}"}; s.metrics["tool_errors"] += 1
    if out.get("status") == "rejected": s.metrics["rejections"] += 1
    s.metrics["tool_log"].append({"name": tc["name"], "args": args, "status": out.get("status") or ("error" if "error" in out else "ok")})
    return json.dumps(_shrink(out), default=str, ensure_ascii=False)[:9000]
 
def _review(s):
    """Independent critic. Returns high-severity issues to fix, or None when done."""
    s.reviewed_version = s.findings_version; s.metrics["critic_rounds"] += 1
    rv = critic.review(s); s.findings["review"] = rv
    high = [i for i in rv["issues"] if i.get("severity") == "high"]
    if rv["verdict"] == "revise" and high and s.metrics["critic_rounds"] <= MAX_CRITIC_ROUNDS: return high
    s.findings["caveats"] = s.findings.get("caveats", []) + [i["problem"] for i in rv["issues"]]
    return None
 
def run(s: Session, user_msg: str | None = None, mode: str = "analysis", max_steps: int = 22) -> dict:
    if user_msg: s.messages.append({"role": "user", "content": user_msg})
    for _ in range(max_steps):
        s.metrics["steps"] += 1
        m = llm.chat("analyst", [_sys(s, mode)] + s.messages, tools=OPENAI_TOOLS)
        s.metrics["llm_calls"] += 1
        k = f"{m['provider']}/{m['model']}"; s.metrics["models_used"][k] = s.metrics["models_used"].get(k, 0) + 1
        s.messages.append(assistant_message(m))
        if not m["tool_calls"]:
            if mode == "analysis" and not s.findings and not s.pending and s.metrics["nudges"] < 2:
                s.metrics["nudges"] += 1
                s.messages.append({"role": "user", "content": "You have not completed the workflow. Continue with the tools "
                                   "(profile, detect issues, investigate, verify, analyse, charts) and finish with submit_findings."})
                continue
            res = {"status": "done", "message": m["content"], "findings_ready": bool(s.findings)}
            if mode == "chat":
                bad = unverified(m["content"], fact_pool(s)); res["verification"] = {"ok": not bad, "unverified_numbers": bad}
            return res
        for tc in m["tool_calls"]:
            s.messages.append({"role": "tool", "tool_call_id": tc["id"], "content": _exec_tool(s, tc)})
        if s.pending:
            return {"status": "needs_approval", "message": m["content"], "pending": list(s.pending.values())}
        if s.findings and s.findings_version != s.reviewed_version:
            high = _review(s)
            if high:
                s.messages.append({"role": "user", "content": "INDEPENDENT REVIEWER FEEDBACK. Fix every high-severity issue (rewrite the wording, "
                                   "add evidence, or remove the claim), then resubmit with submit_findings:\n" + json.dumps(high, ensure_ascii=False)})
    return {"status": "max_steps", "message": "Stopped after the step limit.", "findings_ready": bool(s.findings)}
 
def resume_after_decisions(s: Session, decisions: dict) -> dict:
    done = apply_decisions(s, decisions)
    note = ("USER DECISIONS: " + json.dumps(done, default=str, ensure_ascii=False) +
            "\nIf data changed, earlier analytic results, charts and findings were invalidated. Continue: call verify_cleaning, "
            "recompute what you need, then create charts and submit_findings.")
    return run(s, note)
 