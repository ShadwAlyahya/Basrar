"""End-to-end test of the loop, approval gate, guards, critic, narrator and LLM fallback using a scripted fake LLM.
Run from project root:  python -m tests.test_flow_mock   (no API keys needed)"""
import sys, types, json, time
try: import openai
except ImportError:
    m = types.ModuleType("openai")
    class _E(Exception): pass
    class APIStatusError(_E): status_code = 500
    class RateLimitError(APIStatusError): status_code = 429
    class APITimeoutError(_E): pass
    class APIConnectionError(_E): pass
    m.OpenAI = lambda **k: None; m.APIStatusError = APIStatusError; m.RateLimitError = RateLimitError
    m.APITimeoutError = APITimeoutError; m.APIConnectionError = APIConnectionError; sys.modules["openai"] = m
import numpy as np, pandas as pd
from app.agent import agent, narrator, tools, llm as llm_mod
from app.agent.state import new_session
from app.agent.tools import SENSITIVE_OPS

def reply(text="", calls=()):
    return {"content": text, "tool_calls": [{"id": f"c{time.time_ns()}{i}", "name": n, "arguments": json.dumps(a)} for i, (n, a) in enumerate(calls)],
            "provider": "fake", "model": "fake"}

def make_df():
    rng = np.random.default_rng(0); n = 300
    df = pd.DataFrame({"Order Date": pd.date_range("2024-01-01", periods=n).astype(str), "Region": rng.choice(list("ABC"), n),
                       "Sales": rng.gamma(3, 100, n).round(2), "Profit": rng.normal(30, 40, n).round(2)})
    df.loc[3:8, "Profit"] = np.nan
    return pd.concat([df, df.head(12)], ignore_index=True)

def test_agent_flow():
    df = make_df(); s = new_session(df, "mock.csv"); orig = df.copy(); st = {"a": 0, "c": 0}
    def good_findings():
        top = s.evidence["E3"]["result"]["rows"][0]; kp = s.evidence["E4"]["result"]["value"]
        return ("submit_findings", {"summary": f"Region {top['name']} leads.", "kpis": [{"title": "Total Sales", "value": f"{kp:,.0f}", "evidence_id": "E4", "icon": "dollar"}],
                "insights": [{"text": f"Region {top['name']} has the highest sales at {top['value']}.", "evidence_ids": ["E3"], "claimed_numbers": [top["value"]]}],
                "recommendations": [{"title": "Focus", "reasoning": "Invest where sales are strongest."}]})
    def chat(role, messages, tools=None, **kw):
        if role == "critic":
            st["c"] += 1
            return reply(json.dumps({"verdict": "revise", "issues": [{"insight": 0, "severity": "high", "problem": "wording implies causality", "fix": "say associated"}]}) if st["c"] == 1
                         else json.dumps({"verdict": "approve", "issues": [{"insight": None, "severity": "low", "problem": "small sample"}]}))
        if role == "narrator":
            st["n"] = st.get("n", 0) + 1
            sec = {k: "text" for k in narrator.SECTIONS}
            if st["n"] == 1: sec["eda_analysis"] = "Sales reached 98765.43 in total."      # invented number -> must be caught
            return reply(json.dumps(sec))
        if messages[-1]["role"] == "user" and messages[-1]["content"].startswith("Total"): return reply("Total sales are 999999.")
        a = st["a"]; st["a"] += 1
        script = [lambda: reply("", [("profile_dataset", {}), ("detect_issues", {})]),
                  lambda: reply("", [("propose_cleaning", {"operation": "parse_dates", "params": {"column": "Order Date"}, "reason": "dates as text"}),
                                     ("propose_cleaning", {"operation": "drop_duplicates", "params": {}, "reason": "12 exact duplicates"})]),
                  lambda: reply("", [("verify_cleaning", {})]),
                  lambda: reply("", [("aggregate", {"group_by": "Region", "metric": "Sales", "agg": "sum"}), ("kpi", {"metric": "Sales", "agg": "sum"})]),
                  lambda: reply("", [("create_chart", {"evidence_id": "E3", "chart_type": "bar", "title": "Sales by region", "description": "d"})]),
                  lambda: reply("", [("submit_findings", {"summary": "x", "kpis": [], "insights": [{"text": "Sales are 123456789", "evidence_ids": ["E3"], "claimed_numbers": [123456789]}], "recommendations": []})]),
                  lambda: reply("", [good_findings()]),      # accepted -> critic says revise
                  lambda: reply("", [good_findings()]),      # accepted -> critic approves
                  lambda: reply("Analysis complete.")]
        return script[a]()
    llm_mod.llm.chat = chat

    r = agent.run(s, "Analyze. Goal: sales by region")
    assert r["status"] == "needs_approval" and len(r["pending"]) == 1, r
    assert r["pending"][0]["preview"]["rows_after"] == len(df) - 12
    assert len(s.work) == len(df), "sensitive op must NOT run before approval"
    pid = r["pending"][0]["id"]
    r = agent.resume_after_decisions(s, {pid: True})
    assert r["status"] == "done" and r["findings_ready"], r
    assert s.metrics["rejections"] == 1, "bad number must have been rejected once"
    assert s.metrics["critic_rounds"] == 2 and s.findings["review"]["verdict"] == "approve"
    assert any("small sample" in c for c in s.findings["caveats"])
    assert s.original.equals(orig) and len(s.work) == len(df) - 12
    assert all(a["approved_by"] in ("user", "user(modified)") for a in s.audit if a.get("op") in SENSITIVE_OPS)
    r = agent.run(s, "Total?", mode="chat"); assert r["verification"]["ok"] is False
    rep = narrator.build_report(s, "EN"); assert st["n"] == 2 and not rep["warnings"], rep
    print("flow/guards/critic/narrator OK")

def test_guards():
    s = new_session(make_df(), "g.csv")
    tools.profile_dataset(s); tools.detect_issues(s)
    s.work.loc[:, "Profit"] = np.nan; s.work.loc[:60, "Profit"] = 1.0
    try: tools.propose_cleaning(s, "impute", {"column": "Profit"}, "x"); raise AssertionError("must refuse >60% missing")
    except ValueError as e: assert "Refused" in str(e)
    e = tools.aggregate(s, "Region", "Sales", "sum"); eid = e["evidence_id"]
    tools.propose_cleaning(s, "strip_whitespace", {}, "safe")
    try: tools.create_chart(s, eid, "bar", "t", "d"); raise AssertionError("stale evidence must be refused")
    except ValueError: pass
    r = tools.submit_findings(s, "x", [], [], []); assert r["status"] == "rejected" and any("verify_cleaning" in x for x in r["errors"])
    e = tools.aggregate(s, "Region", "Sales", "sum"); eid = e["evidence_id"]
    a, b = e["rows"][0]["value"], e["rows"][1]["value"]
    c = tools.calc(s, "diff", a, b, eid, eid); assert abs(c["result"] - (a - b)) < 1e-2
    try: tools.calc(s, "diff", 123.456, b, eid, eid); raise AssertionError("invented input must be refused")
    except ValueError as ex: assert "not a value" in str(ex)
    print("guards OK")

def test_llm_fallback():
    import openai
    from agent import config
    calls = []
    class Msg:
        def __init__(s, c): s.content = c; s.tool_calls = None
    class Resp:
        def __init__(s, c): s.choices = [types.SimpleNamespace(message=Msg(c))]
    class C:
        def __init__(s, name, fail): s.name = name; s.chat = types.SimpleNamespace(completions=s); s.fail = fail
        def create(s, **kw):
            calls.append(s.name)
            if s.fail: raise openai.RateLimitError.__new__(openai.RateLimitError)
            return Resp("hello")
    l = llm_mod.LLM(); l._clients = {"p1": C("p1", True), "p2": C("p2", False)}
    config.ROLES["analyst"] = [("p1", "m1"), ("p2", "m2")]
    llm_mod.time.sleep = lambda *_: None
    out = l.chat("analyst", [{"role": "user", "content": "hi"}], retries=2)
    assert out["content"] == "hello" and calls == ["p1", "p1", "p2"], calls
    print("retry + fallback OK")

def test_quota_and_signatures():
    import openai
    from agent import config
    calls = []
    class Msg:
        def __init__(s, c): s.content = c; s.tool_calls = None
    class Resp:
        def __init__(s, c): s.choices = [types.SimpleNamespace(message=Msg(c))]
    class Quota(openai.RateLimitError):
        message = "Rate limit exceeded: free-models-per-day"
    class C:
        def __init__(s, name, fail): s.name = name; s.chat = types.SimpleNamespace(completions=s); s.fail = fail; s.seen = None
        def create(s, **kw):
            calls.append(s.name); s.seen = kw["messages"]
            if s.fail: raise Quota.__new__(Quota)
            return Resp("ok")
    l = llm_mod.LLM(); g = C("gemini", False); l._clients = {"p1": C("p1", True), "gemini": g}
    config.ROLES["analyst"] = [("p1", "m1"), ("gemini", "m2")]
    llm_mod.time.sleep = lambda *_: None
    hist = [{"role": "user", "content": "x"}, {"role": "assistant", "content": "", "tool_calls": [{"id": "1", "type": "function", "function": {"name": "kpi", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "1", "content": "{}"}]
    assert l.chat("analyst", hist)["content"] == "ok"
    assert calls == ["p1", "gemini"], f"daily quota must not be retried: {calls}"
    assert g.seen[1]["tool_calls"][0]["extra_content"]["google"]["thought_signature"], "gemini needs a signature on echoed tool calls"
    calls.clear(); l.chat("analyst", hist); assert calls == ["gemini"], "exhausted model must be skipped during cooldown"
    print("quota cooldown + gemini signatures OK")

if __name__ == "__main__":
    test_guards(); test_llm_fallback(); test_quota_and_signatures(); test_agent_flow(); print("ALL PASSED")