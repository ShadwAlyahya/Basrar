"""Independent reviewer (different model family than the analyst). Catches what number-matching cannot."""
import json
from .llm import llm, LLMError, extract_json
from .guard import brief

SYSTEM = """You are an independent, skeptical senior data reviewer. You receive an analyst's findings with the evidence behind them.
Find real problems only. Check:
- causal claims drawn from correlation or from a single time pattern
- forecasts/what-ifs stated as facts although reliability is low or R^2 is weak
- claims that contradict the evidence (wrong direction, wrong ranking, wrong period)
- generalizing from a top_n subset or a small sample
- ignoring missing data, rejected/pending cleaning, or approved cleaning that changes the number
- recommendations not supported by the insights; overconfident wording
Return ONLY JSON: {"verdict":"approve"|"revise","issues":[{"insight":<index or null>,"severity":"high"|"medium"|"low","problem":"...","fix":"..."}]}
Use severity "high" only when the finding would mislead a decision. If everything is sound return approve with an empty list."""

def review(s):
    payload = json.dumps(brief(s), default=str, ensure_ascii=False)[:14000]
    try:
        m = llm.chat("critic", [{"role": "system", "content": SYSTEM}, {"role": "user", "content": payload}], max_tokens=1500)
    except LLMError as e:
        return {"verdict": "skipped", "issues": [], "error": str(e)}
    j = extract_json(m["content"])
    if not isinstance(j, dict): return {"verdict": "skipped", "issues": [], "error": "unparseable reviewer output"}
    issues = [i for i in j.get("issues", []) if isinstance(i, dict) and i.get("problem")]
    return {"verdict": j.get("verdict", "approve"), "issues": issues, "reviewer": f"{m['provider']}/{m['model']}"}