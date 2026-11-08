import io
from typing import Union
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from .state import SESSIONS, new_session
from .llm import LLMError
from .guard import trim
from .tools import _j
from . import agent, narrator

router = APIRouter(prefix="/agent", tags=["agent"])

def _get(sid):
    if sid not in SESSIONS: raise HTTPException(404, "session not found")
    return SESSIONS[sid]

def _guarded(s, fn, *a, **k):
    if not s.lock.acquire(blocking=False): raise HTTPException(409, "the agent is still working on this session")
    try: return fn(*a, **k)
    except LLMError as e: raise HTTPException(503, f"LLM unavailable: {e}")
    finally: s.lock.release()

class Goal(BaseModel): goal: str = ""
class Decisions(BaseModel): decisions: dict[str, Union[bool, dict]]
class Msg(BaseModel): message: str

@router.post("/sessions")
async def create(file: UploadFile = File(...)):
    raw = await file.read()
    if len(raw) > 50 * 1024 * 1024: raise HTTPException(413, "max 50MB")
    name = (file.filename or "").lower()
    try:
        df = pd.read_csv(io.BytesIO(raw)) if name.endswith(".csv") else pd.read_excel(io.BytesIO(raw)) if name.endswith((".xlsx", ".xls")) else None
    except Exception as e: raise HTTPException(400, f"cannot parse file: {e}")
    if df is None: raise HTTPException(400, "only CSV/XLSX supported")
    df = df.dropna(how="all").dropna(axis=1, how="all"); df.columns = [str(c).strip() for c in df.columns]
    if df.empty or df.shape[1] < 2 or df.columns.duplicated().any(): raise HTTPException(400, "empty file or duplicate column names")
    s = new_session(df, file.filename)
    return _j({"session_id": s.id, "rows": len(df), "columns": list(df.columns), "preview": df.head(20).astype(str).to_dict("records")})

@router.post("/sessions/{sid}/suggest")
def suggest(sid: str, g: Goal):
    s = _get(sid); s.goal = g.goal or s.goal
    return _j({"questions": _guarded(s, narrator.suggest_questions, s)})

@router.post("/sessions/{sid}/run")
def run(sid: str, g: Goal):
    s = _get(sid); s.goal = g.goal
    res = _guarded(s, agent.run, s, f"Analyze this dataset. Business goal: {g.goal or 'not provided - propose questions yourself'}")
    return _j(res)

@router.get("/sessions/{sid}/pending")
def pending(sid: str): return _j(list(_get(sid).pending.values()))

@router.post("/sessions/{sid}/approvals")
def approve(sid: str, d: Decisions):
    s = _get(sid); return _j(_guarded(s, agent.resume_after_decisions, s, d.decisions))

@router.post("/sessions/{sid}/chat")
def chat(sid: str, m: Msg):
    s = _get(sid); return _j(_guarded(s, agent.run, s, m.message, "chat"))

@router.get("/sessions/{sid}/report")
def report(sid: str, lang: str = Query("EN", pattern="^(EN|AR)$")):
    s = _get(sid)
    try: return _j(_guarded(s, narrator.build_report, s, lang))
    except ValueError as e: raise HTTPException(409, str(e))

@router.get("/sessions/{sid}/audit")
def audit(sid: str): return _j(_get(sid).audit)

@router.get("/sessions/{sid}/metrics")
def metrics(sid: str):
    import time; m = dict(_get(sid).metrics); m["elapsed_s"] = round(time.time() - m.pop("started"), 1)
    m["recent_tools"] = [{"name": t["name"], "status": t["status"]} for t in m.pop("tool_log")[-8:]]; return _j(m)

@router.get("/sessions/{sid}/evidence/{eid}")
def evidence(sid: str, eid: str):
    e = _get(sid).evidence.get(eid)
    if not e: raise HTTPException(404, "evidence not found")
    return _j({"id": eid, "tool": e["tool"], "args": e["args"], "result": trim(e["result"], 40)})

@router.get("/sessions/{sid}/cleaned.csv")
def cleaned(sid: str):
    buf = io.StringIO(); _get(sid).work.to_csv(buf, index=False)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=cleaned.csv"})

@router.get("/sessions/{sid}/dashboard")
def dashboard(sid: str):
    s = _get(sid); f = s.findings
    iss = next((e["result"]["issues"] for e in reversed(list(s.evidence.values())) if e["tool"] == "detect_issues"), [])
    pick = lambda t: "; ".join(f"{i.get('column', 'all')}: {i['count']}" for i in iss if i["type"] == t) or "none"
    return _j({
        "kpis": f.get("kpis", []), "charts": s.charts, "ai_insights": f.get("summary", ""), 
        "insights": f.get("insights", []), "recommendations": f.get("recommendations", []), 
        "caveats": f.get("caveats", []), "review": f.get("review"),
        "cleaning_report": {"missing_values": pick("missing"), "duplicates": pick("duplicates"), "outliers": pick("outliers_iqr")},
        "audit": s.audit, "pending": list(s.pending.values()), "rows_original": len(s.original), "rows_now": len(s.work)
    })