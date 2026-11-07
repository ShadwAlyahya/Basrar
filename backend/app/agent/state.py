"""Session state. The ORIGINAL dataframe is never mutated."""
from dataclasses import dataclass, field
import pandas as pd, uuid, time, threading

def _metrics():
    return {"steps": 0, "tool_calls": 0, "tool_errors": 0, "rejections": 0, "critic_rounds": 0,
            "nudges": 0, "llm_calls": 0, "models_used": {}, "tool_log": [], "started": time.time()}

@dataclass
class Session:
    id: str
    original: pd.DataFrame
    work: pd.DataFrame
    filename: str = ""
    goal: str = ""
    audit: list = field(default_factory=list)       # every change + who approved it
    pending: dict = field(default_factory=dict)     # approval_id -> proposed sensitive action (+ dry-run preview)
    evidence: dict = field(default_factory=dict)    # E1.. -> tool outputs (the only source of truth for numbers)
    charts: list = field(default_factory=list)
    findings: dict = field(default_factory=dict)
    messages: list = field(default_factory=list)    # OpenAI-format history (provider-neutral)
    baseline: dict = field(default_factory=dict)
    data_version: int = 0                           # bumps on every data change -> stale evidence is rejected
    dirty: bool = False                             # data changed since last verify_cleaning
    findings_version: int = 0
    reviewed_version: int = 0
    metrics: dict = field(default_factory=_metrics)
    report_cache: dict = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)

SESSIONS: dict[str, Session] = {}   # swap for Redis/DB later

def new_session(df: pd.DataFrame, filename: str) -> Session:
    s = Session(id=uuid.uuid4().hex[:12], original=df.copy(), work=df.copy(), filename=filename)
    s.baseline = {c: float(df[c].sum()) for c in df.select_dtypes("number").columns}
    SESSIONS[s.id] = s
    return s

def log(s: Session, **entry):
    entry["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    s.audit.append(entry)