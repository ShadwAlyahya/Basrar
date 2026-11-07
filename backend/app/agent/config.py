"""Providers + role routing. Override any role with env, e.g.
ROLE_ANALYST="openrouter:nvidia/nemotron-3-ultra-550b-a55b:free,gemini:gemini-flash-latest"
First entry = primary, the rest = fallbacks (history is provider-neutral, so fallback works mid-session)."""
import os
 
PROVIDERS = {
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "key_env": "OPENROUTER_API_KEY"},
    "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/", "key_env": "GEMINI_API_KEY"},
}
NEMOTRON = os.getenv("MODEL_NEMOTRON", "nvidia/nemotron-3-ultra-550b-a55b:free")
XING = os.getenv("MODEL_XING", "xingchen-agi/xing4.0-29b-a4b:free")
GEMINI = os.getenv("MODEL_GEMINI", "gemini-flash-latest")   # check the exact id in Google AI Studio
 
def _roles(env, default):
    v = os.getenv(env)
    if not v: return default
    return [tuple(x.strip().split(":", 1)) for x in v.split(",") if x.strip()]
 
ROLES = {
    "analyst":  _roles("ROLE_ANALYST",  [("openrouter", NEMOTRON), ("gemini", GEMINI)]),   # tool loop + chat
    "critic":   _roles("ROLE_CRITIC",   [("gemini", GEMINI), ("openrouter", NEMOTRON)]),   # different family on purpose
    "narrator": _roles("ROLE_NARRATOR", [("gemini", GEMINI), ("openrouter", NEMOTRON)]),   # reports AR/EN
    "helper":   _roles("ROLE_HELPER",   [("openrouter", XING), ("gemini", GEMINI)]),       # light tasks
}
ROLE_TEMP = {"analyst": 0.1, "critic": 0.0, "narrator": 0.3, "helper": 0.4}
MAX_CRITIC_ROUNDS = int(os.getenv("MAX_CRITIC_ROUNDS", "2"))
 