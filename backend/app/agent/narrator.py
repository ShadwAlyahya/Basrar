"""Report writer + light helper tasks. The narrator may only use numbers present in the facts; output is verified."""
import json
from .llm import llm, extract_json
from .guard import brief, fact_pool, unverified

SECTIONS = ["title", "introduction", "data_understanding", "data_cleaning", "eda_analysis", "recommendations_section", "limitations"]

def _system(lang):
    L = "Arabic (professional Modern Standard Arabic, Western digits 0-9, keep column names and technical terms as in the data)" if lang == "AR" else "English"
    return f"""You write executive analytics reports. Language: {L}.
Use ONLY the facts in FACTS. Never compute or estimate new numbers; every number must appear in FACTS (rounding allowed).
Never claim a cleaning step happened unless it is in cleaning_audit; mention pending/rejected ones as not applied.
Be specific, concise, business-oriented; state limitations honestly (caveats, forecast reliability, missing data).
Return ONLY JSON with string keys: {", ".join(SECTIONS)}."""

def build_report(s, lang="EN"):
    key = (lang, s.findings_version, s.data_version)
    if key in s.report_cache: return s.report_cache[key]
    if not s.findings: raise ValueError("no findings yet - run the analysis first")
    facts = json.dumps(brief(s), default=str, ensure_ascii=False)[:20000]
    msgs = [{"role": "system", "content": _system(lang)}, {"role": "user", "content": "FACTS:\n" + facts}]
    pool = fact_pool(s); rep, bad = {}, []
    for attempt in range(2):
        m = llm.chat("narrator", msgs, max_tokens=3500)
        rep = extract_json(m["content"]) or {}
        bad = [(k, unverified(str(rep.get(k, "")), pool)) for k in SECTIONS]; bad = [(k, b) for k, b in bad if b]
        if not bad and all(k in rep for k in SECTIONS[:-1]): break
        msgs += [{"role": "assistant", "content": m["content"]},
                 {"role": "user", "content": "Fix this: " + (f"these numbers are not in FACTS: {bad}. " if bad else "") +
                  "Return the complete JSON again using only numbers from FACTS, with all sections."}]
    out = {**{k: str(rep.get(k, "")) for k in SECTIONS}, "lang": lang,
           "warnings": [f"unverified numbers in '{k}': {b}" for k, b in bad]}
    s.report_cache[key] = out
    return out

def suggest_questions(s, n=4):
    from .tools import profile_dataset
    prof = profile_dataset(s)
    msgs = [{"role": "system", "content": "You are a senior data analyst. Given a dataset schema, propose sharp business questions "
             'answerable from it. Return ONLY JSON: {"questions":["..."]}. Same language as the goal if given, else English.'},
            {"role": "user", "content": json.dumps({"goal": s.goal, "n": n, "schema": prof["schema"], "rows": prof["rows"]}, ensure_ascii=False)}]
    m = llm.chat("helper", msgs, max_tokens=700)
    return (extract_json(m["content"]) or {}).get("questions", [])[:n]