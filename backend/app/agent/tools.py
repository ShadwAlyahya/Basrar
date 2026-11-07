"""Deterministic analysis tools. Every analytic result is stored as Evidence (E1, E2, ...).
Process rules are enforced HERE (in code), not only in the prompt."""
import json, os, re, uuid, warnings
import numpy as np, pandas as pd
from .state import Session, log
from .guard import numbers_in, supported, unverified, evidence_pool, fact_pool, _AR

warnings.filterwarnings("ignore")
SAFE_OPS = {"strip_whitespace", "parse_dates", "cast_numeric"}                       # auto-applied + logged
SENSITIVE_OPS = {"drop_duplicates", "impute", "drop_missing_rows", "cap_outliers"}   # need user approval
ANALYTIC = {"aggregate", "correlations", "distribution", "forecast", "what_if", "kpi", "calc"}
REQUIRED = {"parse_dates": ["column"], "cast_numeric": ["column"], "drop_missing_rows": ["column"],
            "impute": ["column"], "cap_outliers": ["column"]}
REDACT = os.getenv("REDACT_SAMPLES") == "1"      # set to 1 to never send raw cell values to the LLM

def _j(o):
    if isinstance(o, (np.bool_, bool)): return bool(o)
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, (float, np.floating)): return None if np.isnan(o) else round(float(o), 4)
    if isinstance(o, (pd.Timestamp, pd.Period)): return str(o)
    if isinstance(o, dict): return {str(k): _j(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [_j(x) for x in o]
    return o

def _ev(s: Session, tool, args, result):
    eid = f"E{len(s.evidence) + 1}"
    s.evidence[eid] = {"tool": tool, "args": _j(args), "result": _j(result), "data_version": s.data_version}
    return {"evidence_id": eid, **_j(result)}

def _col(s, c):
    if c not in s.work.columns:
        raise ValueError(f"Unknown column '{c}'. Available: {list(map(str, s.work.columns))}")
    return s.work[c]

# ------------------------------------------------------------------ understanding
def profile_dataset(s, **_):
    df = s.work; cols = []
    for c in df.columns:
        x = df[c]
        if pd.api.types.is_numeric_dtype(x): kind = "numeric"
        elif pd.api.types.is_datetime64_any_dtype(x): kind = "datetime"
        else:
            kind = "text/categorical"; xs = x.dropna().astype(str).head(200)
            if len(xs):
                if pd.to_numeric(xs.str.replace(r"[,$%\s]", "", regex=True), errors="coerce").notna().mean() > .9: kind = "numeric_stored_as_text"
                elif pd.to_datetime(xs, errors="coerce").notna().mean() > .8: kind = "date_stored_as_text"
                elif x.nunique() == len(x.dropna()) and len(x) > 20: kind = "identifier"
        cols.append({"name": str(c), "dtype": str(x.dtype), "semantic": kind, "missing": int(x.isna().sum()),
                     "missing_pct": round(x.isna().mean() * 100, 2), "unique": int(x.nunique()),
                     "sample": [] if REDACT else x.dropna().head(3).astype(str).tolist()})
    return _ev(s, "profile_dataset", {}, {"rows": len(df), "columns": len(df.columns), "schema": cols})

def detect_issues(s, **_):
    df = s.work; issues = []
    d = int(df.duplicated().sum())
    if d: issues.append({"type": "duplicates", "count": d, "pct": round(d / len(df) * 100, 2)})
    for c in df.columns:
        m = int(df[c].isna().sum())
        if m: issues.append({"type": "missing", "column": str(c), "count": m, "pct": round(m / len(df) * 100, 2)})
    for c in df.select_dtypes("number").columns:
        x = df[c].dropna()
        if x.empty: continue
        q1, q3 = x.quantile([.25, .75]); iqr = q3 - q1
        o = int(((x < q1 - 1.5 * iqr) | (x > q3 + 1.5 * iqr)).sum()) if iqr else 0
        if o: issues.append({"type": "outliers_iqr", "column": str(c), "count": o, "max": float(x.max()), "median": float(x.median())})
        n = int((x < 0).sum())
        if n: issues.append({"type": "negative_values", "column": str(c), "count": n})
    for c in df.select_dtypes("object").columns:
        x = df[c].dropna().astype(str)
        if not len(x): continue
        if pd.to_numeric(x.str.replace(r"[,$%\s]", "", regex=True), errors="coerce").notna().mean() > .9:
            issues.append({"type": "numeric_stored_as_text", "column": str(c)})
        elif pd.to_datetime(x.head(200), errors="coerce").notna().mean() > .8:
            issues.append({"type": "date_stored_as_text", "column": str(c)})
        if (x != x.str.strip()).any(): issues.append({"type": "whitespace", "column": str(c)})
    return _ev(s, "detect_issues", {}, {"rows": len(df), "issues": issues})

def inspect_rows(s, condition, column=None, limit=8, **_):
    df = s.work
    if condition == "duplicate": mask = df.duplicated(keep=False)
    else:
        if not column: raise ValueError("column is required for this condition")
        x = _col(s, column)
        if condition == "missing": mask = x.isna()
        elif condition == "negative": mask = x < 0
        elif condition == "outlier":
            q1, q3 = x.quantile([.25, .75]); iqr = q3 - q1; mask = (x < q1 - 1.5 * iqr) | (x > q3 + 1.5 * iqr)
        else: raise ValueError("condition must be missing|negative|duplicate|outlier")
    sub, rest = df[mask], df[~mask]; num = list(df.select_dtypes("number").columns)[:6]
    res = {"count": int(mask.sum()), "pct_of_rows": round(mask.mean() * 100, 2),
           "sample": [] if REDACT else sub.head(int(limit)).astype(str).to_dict("records"),
           "numeric_means_flagged_vs_rest": {str(c): {"flagged": sub[c].mean(), "rest": rest[c].mean()} for c in num}}
    if column and condition in ("outlier", "negative") and pd.api.types.is_numeric_dtype(df[column]):
        res["flagged_value_range"] = {"min": sub[column].min(), "max": sub[column].max(), "median": sub[column].median(),
                                      "rest_median": rest[column].median()}
        res["share_of_column_total_pct"] = round(float(sub[column].sum() / df[column].sum() * 100), 2) if df[column].sum() else None
    return _ev(s, "inspect_rows", {"column": column, "condition": condition}, res)

# ------------------------------------------------------------------ cleaning
def _apply(df, op, p):
    df = df.copy(); affected = 0; extra = {}
    if op == "strip_whitespace":
        for c in df.select_dtypes("object").columns: df[c] = df[c].str.strip()
    elif op == "parse_dates":
        c = p["column"]; na0 = int(df[c].isna().sum())
        df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=bool(p.get("dayfirst", False)))
        affected = int(df[c].notna().sum()); extra["failed_to_parse"] = int(df[c].isna().sum()) - na0
    elif op == "cast_numeric":
        c = p["column"]; na0 = int(df[c].isna().sum())
        t = df[c].astype(str).str.replace(r"^\((.*)\)$", r"-\1", regex=True).str.replace(r"[,$%\s]", "", regex=True)
        df[c] = pd.to_numeric(t, errors="coerce")
        affected = int(df[c].notna().sum()); extra["failed_to_parse"] = int(df[c].isna().sum()) - na0
    elif op == "drop_duplicates":
        n = len(df); df = df.drop_duplicates(subset=p.get("subset") or None); affected = n - len(df)
    elif op == "drop_missing_rows":
        n = len(df); df = df.dropna(subset=[p["column"]]); affected = n - len(df)
    elif op == "impute":
        c, m = p["column"], p.get("method", "median"); affected = int(df[c].isna().sum())
        if m == "constant":
            v = p.get("value"); v = float(v) if pd.api.types.is_numeric_dtype(df[c]) else v
        elif m == "mean": v = df[c].mean()
        elif m == "mode": v = df[c].mode().iloc[0]
        else: v = df[c].median()
        df[c] = df[c].fillna(v); extra["fill_value"] = _j(v)
    elif op == "cap_outliers":
        c = p["column"]; q1, q3 = df[c].quantile([.25, .75]); iqr = q3 - q1; lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        affected = int(((df[c] < lo) | (df[c] > hi)).sum()); df[c] = df[c].clip(lo, hi); extra["bounds"] = [_j(lo), _j(hi)]
    else: raise ValueError(f"unknown operation {op}")
    return df, affected, extra

def _preview(s, op, p):
    new, affected, extra = _apply(s.work, op, p); drift = {}
    for c in s.work.select_dtypes("number").columns:
        a, b = float(s.work[c].sum()), float(new[c].sum()) if c in new.columns else 0.0
        if a and abs((b - a) / abs(a)) > 1e-4: drift[str(c)] = round((b - a) / abs(a) * 100, 2)
    return _j({"rows_before": len(s.work), "rows_after": len(new), "affected": affected,
               "column_sum_drift_pct": drift, **extra})

def _invalidate(s):
    s.data_version += 1; s.dirty = True; s.charts = []; s.findings = {}

def _execute(s, op, p, approved_by):
    before = len(s.work)
    new, affected, extra = _apply(s.work, op, p)
    s.work = new; _invalidate(s)
    log(s, op=op, params=p, rows_before=before, rows_after=len(new), affected=affected, approved_by=approved_by,
        data_version=s.data_version, **extra)
    return _j({"rows_before": before, "rows_after": len(new), "affected": affected, **extra,
               "note": "Data changed: earlier analytic results and charts are invalidated; recompute what you need."})

def propose_cleaning(s, operation, params=None, reason="", **_):
    p = params or {}
    if operation not in SAFE_OPS | SENSITIVE_OPS: raise ValueError(f"unknown operation {operation}")
    for k in REQUIRED.get(operation, []):
        if k not in p: raise ValueError(f"params.{k} is required for {operation}")
    if "column" in p: _col(s, p["column"])
    if operation == "impute":
        mp = float(_col(s, p["column"]).isna().mean() * 100)
        if mp > 60: raise ValueError(f"Refused: {p['column']} is {mp:.0f}% missing; imputing would fabricate most values. "
                                     "Exclude the column from analysis and state this as a limitation.")
    if operation in SAFE_OPS:
        return {"status": "applied_automatically", **_execute(s, operation, p, "auto(safe)")}
    for a in s.pending.values():
        if a["operation"] == operation and a["params"] == p: return {"status": "already_pending", "approval_id": a["id"]}
    pid = "A" + uuid.uuid4().hex[:5]
    prev = _preview(s, operation, p)
    s.pending[pid] = {"id": pid, "operation": operation, "params": p, "reason": reason, "preview": prev}
    return {"status": "awaiting_user_approval", "approval_id": pid, "preview": prev,
            "note": "NOT executed. Do not assume it happened. Finish your turn by explaining to the user what you found and recommend."}

def apply_decisions(s, decisions: dict):
    """decision: True = approve, False = reject, dict = approve with parameter overrides (user edited it)."""
    out = []
    for pid, dec in decisions.items():
        a = s.pending.pop(pid, None)
        if not a: continue
        if dec is False or dec is None:
            log(s, op=a["operation"], params=a["params"], decision="rejected", approved_by="user"); out.append({**a, "decision": "rejected"}); continue
        params = {**a["params"], **dec} if isinstance(dec, dict) else a["params"]
        try:
            out.append({"id": pid, "operation": a["operation"], "params": params, "decision": "approved",
                        **_execute(s, a["operation"], params, "user(modified)" if isinstance(dec, dict) else "user")})
        except Exception as e:
            out.append({"id": pid, "operation": a["operation"], "decision": "failed", "error": str(e)})
    return out

def verify_cleaning(s, **_):
    checks = []
    for c, base in s.baseline.items():
        if c in s.work.columns and pd.api.types.is_numeric_dtype(s.work[c]):
            now = float(s.work[c].sum()); drift = (now - base) / abs(base) * 100 if base else 0
            checks.append({"column": c, "sum_before": base, "sum_after": now, "drift_pct": round(drift, 2), "flag": abs(drift) > 1})
    expected_removed = sum(a["rows_before"] - a["rows_after"] for a in s.audit if "rows_after" in a)
    actual_removed = len(s.original) - len(s.work)
    s.dirty = False
    return _j({"rows_original": len(s.original), "rows_now": len(s.work), "row_accounting_consistent": expected_removed == actual_removed,
               "totals": checks, "columns_with_drift": [x["column"] for x in checks if x["flag"]],
               "audit_ops_applied": [a["op"] for a in s.audit if a.get("decision") != "rejected"],
               "tip": "Drift is acceptable only if explained by an approved operation in the audit log; mention it in the findings."})

# ------------------------------------------------------------------ analysis
def kpi(s, metric=None, agg="sum", **_):
    df = s.work
    if agg == "count" or not metric: return _ev(s, "kpi", {"metric": metric, "agg": "count"}, {"value": len(df), "metric": "rows"})
    x = _col(s, metric)
    return _ev(s, "kpi", {"metric": metric, "agg": agg}, {"metric": metric, "agg": agg, "value": x.agg(agg), "non_null": int(x.notna().sum())})

def aggregate(s, group_by, metric=None, agg="sum", top_n=10, freq=None, **_):
    df = s.work; g = _col(s, group_by)
    if freq: g = pd.to_datetime(g, errors="coerce").dt.to_period(freq)
    r = df.groupby(g).size() if (agg == "count" or not metric) else df.groupby(g)[_col(s, metric).name].agg(agg)
    total_groups = len(r)
    r = r.sort_index() if freq else r.sort_values(ascending=False).head(int(top_n))
    return _ev(s, "aggregate", {"group_by": group_by, "metric": metric, "agg": agg, "freq": freq, "top_n": top_n},
               {"rows": [{"name": str(k), "value": v} for k, v in r.items()], "groups_total": total_groups,
                "total_shown": float(r.sum()), "note": "top_n subset" if (not freq and total_groups > len(r)) else None})

def correlations(s, min_abs=0.3, **_):
    n = s.work.select_dtypes("number"); n = n.loc[:, n.nunique() > 2].iloc[:, :15]
    if n.shape[1] < 2: return _ev(s, "correlations", {}, {"pairs": [], "note": "fewer than 2 usable numeric columns"})
    m = n.corr()
    pairs = [{"a": str(a), "b": str(b), "r": m.loc[a, b]} for i, a in enumerate(m.columns) for b in m.columns[i + 1:]
             if abs(m.loc[a, b]) >= min_abs]
    return _ev(s, "correlations", {"min_abs": min_abs}, {"pairs": sorted(pairs, key=lambda x: -abs(x["r"]))[:10], "n_rows": len(n),
                                                          "note": "Pearson; correlation is not causation"})

def distribution(s, column, **_):
    x = _col(s, column)
    if pd.api.types.is_numeric_dtype(x):
        h, e = np.histogram(x.dropna(), bins=10)
        return _ev(s, "distribution", {"column": column}, {"stats": x.describe().to_dict(), "skew": x.skew(),
                   "rows": [{"name": f"{e[i]:.0f}-{e[i + 1]:.0f}", "value": int(h[i])} for i in range(10)]})
    vc = x.value_counts().head(10)
    return _ev(s, "distribution", {"column": column}, {"rows": [{"name": str(k), "value": int(v)} for k, v in vc.items()]})

def forecast(s, date_col, metric, periods=6, freq="M", **_):
    d = s.work.assign(_d=pd.to_datetime(_col(s, date_col), errors="coerce")).dropna(subset=["_d"])
    y = d.groupby(d["_d"].dt.to_period(freq))[_col(s, metric).name].sum().sort_index()
    if len(y) < 8: raise ValueError(f"Only {len(y)} periods - too few for a reliable forecast")
    full = pd.period_range(y.index.min(), y.index.max(), freq=freq); gaps = len(full) - len(y); y = y.reindex(full, fill_value=0)
    def fit(series, h):
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            sp = 12 if freq == "M" and len(series) >= 24 else None
            return np.asarray(ExponentialSmoothing(series.values, trend="add", seasonal="add" if sp else None,
                              seasonal_periods=sp).fit().forecast(h)), "holt-winters"
        except Exception:
            k = np.polyfit(range(len(series)), series.values, 1); return k[0] * np.arange(len(series), len(series) + h) + k[1], "linear-trend"
    hold = max(2, len(y) // 5); pred, method = fit(y.iloc[:-hold], hold); act = y.iloc[-hold:].values
    mape = float(np.mean(np.abs((act - pred) / np.where(act == 0, 1, act))) * 100)
    fc, _m = fit(y, int(periods)); idx = pd.period_range(y.index[-1] + 1, periods=int(periods), freq=freq)
    rows = [{"name": str(i), "value": v} for i, v in y.items()] + [{"name": str(i) + " (fc)", "value": v} for i, v in zip(idx, fc)]
    return _ev(s, "forecast", {"date_col": date_col, "metric": metric, "periods": periods, "freq": freq},
               {"method": method, "backtest_mape_pct": mape, "history_periods": len(y), "filled_gap_periods": gaps, "rows": rows,
                "forecast_only": [r for r in rows if "(fc)" in r["name"]],
                "reliability": "low" if mape > 25 else "medium" if mape > 10 else "good"})

def what_if(s, target, driver, pct_change, **_):
    d = s.work[[_col(s, target).name, _col(s, driver).name]].dropna()
    if len(d) < 10: raise ValueError("not enough rows for a what-if estimate")
    k = np.polyfit(d[driver], d[target], 1); r2 = float(np.corrcoef(d[driver], d[target])[0, 1] ** 2)
    base = float(d[target].sum()); delta = float(k[0] * d[driver].sum() * pct_change / 100)
    return _ev(s, "what_if", {"target": target, "driver": driver, "pct_change": pct_change},
               {"baseline_total": base, "estimated_change": delta, "new_total": base + delta, "r_squared": r2,
                "warning": "weak relationship - indicative only" if r2 < .3 else None,
                "assumption": "linear relationship, other factors constant"})

def calc(s, op, a, b, a_evidence, b_evidence, label="", **_):
    """Derived numbers (change, ratio, share) with provenance: both inputs must exist in cited evidence."""
    for v, e in ((a, a_evidence), (b, b_evidence)):
        if e not in s.evidence: raise ValueError(f"unknown evidence {e}")
        if not supported(float(v), 4, evidence_pool(s, [e])): raise ValueError(f"{v} is not a value in {e}")
    res = {"diff": a - b, "sum": a + b, "pct_change": (a - b) / b * 100 if b else None,
           "ratio": a / b if b else None, "share_pct": a / b * 100 if b else None}.get(op)
    if res is None: raise ValueError("op must be diff|sum|pct_change|ratio|share_pct and b must be non-zero")
    return _ev(s, "calc", {"op": op, "a_evidence": a_evidence, "b_evidence": b_evidence}, {"op": op, "a": a, "b": b, "result": res, "label": label})

# ------------------------------------------------------------------ visualization + validated findings
def create_chart(s, evidence_id, chart_type, title, description, **_):
    ev = s.evidence.get(evidence_id)
    if not ev or "rows" not in ev["result"]: raise ValueError("evidence_id must reference a result containing 'rows'")
    if ev["data_version"] != s.data_version: raise ValueError("that evidence is stale (data changed since); recompute it first")
    rows = ev["result"]["rows"]
    if len(rows) > 60: raise ValueError("too many points for a chart; aggregate further")
    s.charts.append({"type": chart_type, "title": title, "description": description, "dataKey": "value", "data": rows, "evidence_id": evidence_id})
    return {"status": "chart_created", "total_charts": len(s.charts)}

def _dec(n):
    t = repr(float(n)); return 6 if "e" in t else (0 if t.endswith(".0") else len(t.split(".")[1]))

def _kpi_ok(v, pool):
    """KPI display strings like '$128,430', '14.2%', '1.2M' must match the cited evidence (rounding allowed)."""
    m = re.search(r"(-?\d[\d,]*\.?\d*)\s*([kKmMbB])?(?![A-Za-z])", str(v).translate(_AR))
    if not m: return True
    raw = m.group(1).replace(",", ""); x = float(raw); dec = len(raw.split(".")[1]) if "." in raw else 0
    mult = {"k": 1e3, "m": 1e6, "b": 1e9}.get((m.group(2) or "").lower(), 1); xv = x * mult
    tol = 0.5 * 10 ** (-dec) * mult + 1e-9
    return any(abs(xv - p) <= max(tol, abs(p) * 1e-4) or abs(xv - p * 100) <= max(tol, abs(p) * 1e-4)
               or abs(xv * 100 - p) <= max(tol, abs(p) * 1e-4) for p in pool)

def submit_findings(s, summary, kpis, insights, recommendations, **_):
    errors = []; used = {e["tool"] for e in s.evidence.values()}
    for t in ("profile_dataset", "detect_issues"):
        if t not in used: errors.append(f"call {t} before submitting")
    if s.dirty: errors.append("data changed since the last check: call verify_cleaning first")
    if not insights: errors.append("at least one insight is required")
    for i, k in enumerate(kpis):
        e = k.get("evidence_id")
        if e not in s.evidence: errors.append(f"kpi[{i}] needs a valid evidence_id"); continue
        if s.evidence[e]["tool"] in ANALYTIC and s.evidence[e]["data_version"] != s.data_version: errors.append(f"kpi[{i}]: {e} is stale, recompute"); continue
        if not _kpi_ok(k.get("value"), evidence_pool(s, [e])): errors.append(f"kpi[{i}] value {k.get('value')} not found in {e}")
    cited_all = set()
    for i, ins in enumerate(insights):
        ids = ins.get("evidence_ids") or []
        if not ids or any(e not in s.evidence for e in ids): errors.append(f"insight[{i}]: missing/invalid evidence_ids"); continue
        cited_all |= set(ids)
        for e in ids:
            if s.evidence[e]["tool"] in ANALYTIC and s.evidence[e]["data_version"] != s.data_version:
                errors.append(f"insight[{i}]: {e} was computed before the data changed; recompute it")
        pool = evidence_pool(s, ids)
        for n in ins.get("claimed_numbers", []):
            if not supported(float(n), _dec(n), pool): errors.append(f"insight[{i}]: claimed number {n} not found in cited evidence")
        bad = unverified(ins.get("text", ""), pool)
        if bad: errors.append(f"insight[{i}]: text contains numbers not in cited evidence: {bad} (use calc for derived numbers)")
    bad = unverified(summary, fact_pool(s))
    if bad: errors.append(f"summary contains unsupported numbers: {bad}")
    if errors: return {"status": "rejected", "errors": errors, "action": "fix the issues and resubmit"}
    caveats = []
    if s.pending: caveats.append(f"{len(s.pending)} proposed cleaning operation(s) were not applied; results use the data as it stands.")
    for e in cited_all:
        r = s.evidence[e]["result"]
        if s.evidence[e]["tool"] == "forecast" and r.get("reliability") == "low": caveats.append(f"Forecast ({e}) has low reliability (backtest MAPE {r.get('backtest_mape_pct')}%).")
        if s.evidence[e]["tool"] == "what_if" and r.get("warning"): caveats.append(f"What-if ({e}): {r['warning']}.")
    soft = [f"recommendation[{i}] mentions numbers not found in evidence: {b}" for i, r in enumerate(recommendations)
            if (b := unverified(r.get("reasoning", "") + " " + r.get("title", ""), fact_pool(s)))]
    s.findings_version += 1
    s.findings = {"summary": summary, "kpis": kpis, "insights": insights, "recommendations": recommendations,
                  "caveats": caveats, "soft_warnings": soft}
    return {"status": "accepted", "note": "An independent reviewer will check the findings."}

DISPATCH = {f.__name__: f for f in [profile_dataset, detect_issues, inspect_rows, propose_cleaning, verify_cleaning, kpi, aggregate,
            correlations, distribution, forecast, what_if, calc, create_chart, submit_findings]}

# ------------------------------------------------------------------ OpenAI-format tool schemas
S, N, B = {"type": "string"}, {"type": "number"}, {"type": "boolean"}
E = lambda *v: {"type": "string", "enum": list(v)}
def _t(name, desc, props, req=()):
    return {"type": "function", "function": {"name": name, "description": desc,
            "parameters": {"type": "object", "properties": props, "required": list(req)}}}
OPENAI_TOOLS = [
 _t("profile_dataset", "Columns, dtypes, semantic types, missing %, sample values. Call FIRST.", {}),
 _t("detect_issues", "Find duplicates, missing, outliers, negatives, wrong formats. Detection only; changes nothing.", {}),
 _t("inspect_rows", "Investigate flagged rows BEFORE deciding (why is Profit negative? are big values typos or real?).",
    {"condition": E("missing", "negative", "duplicate", "outlier"), "column": S, "limit": N}, ["condition"]),
 _t("propose_cleaning", "Propose a cleaning operation. Safe ops (strip_whitespace, parse_dates, cast_numeric) run automatically. "
    "Sensitive ops (drop_duplicates, impute, drop_missing_rows, cap_outliers) are QUEUED for user approval with a dry-run preview.",
    {"operation": E(*sorted(SAFE_OPS | SENSITIVE_OPS)),
     "params": {"type": "object", "properties": {"column": S, "subset": {"type": "array", "items": S},
                "method": E("median", "mean", "mode", "constant"), "value": S, "dayfirst": B}},
     "reason": S}, ["operation", "reason"]),
 _t("verify_cleaning", "Compare row counts and numeric totals vs the original. Required after any data change.", {}),
 _t("kpi", "Single headline number (sum/mean/median/min/max/count/nunique) of a column.",
    {"metric": S, "agg": E("sum", "mean", "median", "min", "max", "count", "nunique")}),
 _t("aggregate", "Group-by analysis. Use freq (D/W/M/Q/Y) on a date column for trends over time.",
    {"group_by": S, "metric": S, "agg": E("sum", "mean", "median", "count"), "top_n": N, "freq": S}, ["group_by"]),
 _t("correlations", "Top correlated numeric pairs.", {"min_abs": N}),
 _t("distribution", "Distribution of one column.", {"column": S}, ["column"]),
 _t("forecast", "Forecast a metric over time, with backtest error and reliability.",
    {"date_col": S, "metric": S, "periods": N, "freq": S}, ["date_col", "metric"]),
 _t("what_if", "Scenario: change a driver by pct_change% and estimate the effect on a target.",
    {"target": S, "driver": S, "pct_change": N}, ["target", "driver", "pct_change"]),
 _t("calc", "Derived number (diff, sum, pct_change, ratio, share_pct) from two values taken from evidence. a and b must come from a_evidence/b_evidence.",
    {"op": E("diff", "sum", "pct_change", "ratio", "share_pct"), "a": N, "b": N, "a_evidence": S, "b_evidence": S, "label": S},
    ["op", "a", "b", "a_evidence", "b_evidence"]),
 _t("create_chart", "Create a chart from an existing evidence_id (never from invented numbers).",
    {"evidence_id": S, "chart_type": E("bar", "line", "area", "pie"), "title": S, "description": S},
    ["evidence_id", "chart_type", "title", "description"]),
 _t("submit_findings", "Submit final KPIs/insights/recommendations. Rejected unless every KPI/insight cites valid, fresh evidence and every number matches it.",
    {"summary": S,
     "kpis": {"type": "array", "items": {"type": "object", "properties": {"title": S, "value": S, "change": S, "icon": E("dollar", "activity", "database"), "evidence_id": S}, "required": ["title", "value", "evidence_id"]}},
     "insights": {"type": "array", "items": {"type": "object", "properties": {"text": S, "evidence_ids": {"type": "array", "items": S}, "claimed_numbers": {"type": "array", "items": N}}, "required": ["text", "evidence_ids"]}},
     "recommendations": {"type": "array", "items": {"type": "object", "properties": {"title": S, "reasoning": S}, "required": ["title", "reasoning"]}}},
    ["summary", "kpis", "insights", "recommendations"]),
]