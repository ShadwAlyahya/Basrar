"""Numeric grounding: every number the system shows must be traceable to tool evidence."""
import re, json

_AR = str.maketrans("٠١٢٣٤٥٦٧٨٩٫٬", "0123456789.,")
_NUM = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?")

def numbers_in(text):
    out = []
    for m in _NUM.findall(str(text).translate(_AR)):
        raw = m.replace(",", "")
        try: v = float(raw)
        except ValueError: continue
        out.append((v, len(raw.split(".")[1]) if "." in raw else 0))
    return out

def supported(v, dec, pool):
    """Match with rounding tolerance (half a unit of the last written digit); also fraction<->percent."""
    tol = 0.5 * 10 ** (-dec) + 1e-9
    for p in pool:
        t = max(tol, abs(p) * 1e-4)
        if abs(v - p) <= t or abs(v - p * 100) <= t or abs(v * 100 - p) <= t: return True
    return False

def unverified(text, pool):
    bad = []
    for v, dec in numbers_in(text):
        if dec == 0 and (abs(v) < 10 or 1900 <= v <= 2100): continue      # list numbers / years
        if not supported(v, dec, pool): bad.append(v)
    return bad

def evidence_pool(s, ids):
    nums = set()
    for e in ids:
        if e in s.evidence: nums.update(v for v, _ in numbers_in(json.dumps(s.evidence[e]["result"])))
    return nums

def fact_pool(s):
    nums = evidence_pool(s, list(s.evidence))
    nums.update([len(s.original), len(s.work), s.original.shape[1], s.work.shape[1]])
    for a in s.audit: nums.update(v for v, _ in numbers_in(json.dumps(a, default=str)))
    return nums

def trim(o, n=25):
    if isinstance(o, list): return [trim(x, n) for x in o[:n]] + ([f"...{len(o) - n} more"] if len(o) > n else [])
    if isinstance(o, dict): return {k: trim(v, n) for k, v in o.items()}
    return o

def cited_ids(s):
    f = s.findings or {}
    ids = {e for i in f.get("insights", []) for e in i.get("evidence_ids", [])}
    ids |= {k.get("evidence_id") for k in f.get("kpis", []) if k.get("evidence_id")}
    ids |= {c["evidence_id"] for c in s.charts}
    return ids

def brief(s):
    """Compact fact sheet used by the critic and the narrator."""
    f = s.findings or {}
    ev = {k: {"tool": s.evidence[k]["tool"], "args": s.evidence[k]["args"], "result": trim(s.evidence[k]["result"])}
          for k in sorted(cited_ids(s)) if k in s.evidence}
    issues = next((e["result"].get("issues") for e in reversed(list(s.evidence.values())) if e["tool"] == "detect_issues"), [])
    return {"goal": s.goal, "dataset": {"file": s.filename, "rows_original": len(s.original), "rows_now": len(s.work),
                                         "columns": list(map(str, s.work.columns))},
            "data_quality_issues_found": issues,
            "cleaning_audit": [{k: v for k, v in a.items() if k != "ts"} for a in s.audit],
            "pending_not_applied": list(s.pending.values()),
            "summary": f.get("summary"), "kpis": f.get("kpis"), "insights": f.get("insights"),
            "recommendations": f.get("recommendations"), "caveats": f.get("caveats", []), "evidence": ev}