"""Model layer: prompt building, provider calls, output validation, call budget.

What the MODEL may do (and nothing else):
  * check-in: write <= 2 short, neutral sentences and name ONE of the four fixed
    skills (or none). The app shows the reply plus the skill as a button; the
    user still chooses (R4).
  * reframe (opt-in): offer up to two short, neutral alternative readings of the
    thought the user typed. The user picks one, writes their own, or skips.

What the APP controls (never the model): skill steps and timing, saving,
the Stop control, crisis detection and the Crisis support route.

Providers (LLM_PROVIDER in backend/.env):
  mock       deterministic saved-style responses, no network (default; tests, peer testing)
  openai     OpenAI Chat Completions (OPENAI_API_KEY, OPENAI_MODEL)
  anthropic  Anthropic Messages API (ANTHROPIC_API_KEY, ANTHROPIC_MODEL)
  fail       every call fails -- used to demonstrate failure handling

Live calls are capped at LIVE_CALL_LIMIT (default 50, stored in SQLite).
After the cap the app switches to mock responses automatically.
"""
import json
import os
import re
import time
from typing import Optional

import httpx

from .db import get_conn
from .skills import SKILL_CARDS, SKILL_IDS

LIVE_PROVIDERS = {"openai", "anthropic"}

CHECKIN_SYSTEM = """You are the text layer of a coursework prototype that offers four brief coping-skill exercises.
You are not a therapist, counselor or crisis service, and no one is monitoring the conversation.

Write a reply of at most two short sentences, then name at most one skill.
Rules:
- Plain, calm, neutral words. No exclamation marks, no cheerleading, no praise.
- Do not diagnose, label feelings as symptoms, or use clinical terms.
- Do not give advice, instructions or new techniques. Only the four skills listed in CONTEXT exist.
- Do not ask follow-up questions that require the person to explain more.
- Do not say you understand exactly how they feel.
- If nothing fits, set suggested_skill to null and say they can pick any option or stop.
Respond with JSON only: {"reply": "...", "suggested_skill": "breathing" | "grounding" | "stop" | "reframe" | null}"""

REFRAME_SYSTEM = """You are the text layer of a coursework prototype running a one-minute cognitive reframe exercise.
The person has named one distressing thought. Offer at most two alternative ways to read the same situation.
Rules:
- Each alternative is one sentence, under 20 words, first person ("Maybe I...", "It could be that...").
- Neutral and plausible. Not cheerful, not dismissive, no exclamation marks.
- Do not give advice or instructions, do not diagnose, do not mention therapy.
- Do not argue that the thought is wrong; just offer another reading.
Respond with JSON only: {"alternatives": ["...", "..."]}"""

BANNED = [
    r"diagnos", r"\bdisorder", r"\btherap", r"\bsymptom", r"\bmonitor", r"\bmedicat",
    r"!", r"\bgreat job\b", r"\bproud of you\b", r"\bamazing\b", r"\byou should\b",
    r"\byou need to\b", r"\byou have (a|an)\b", r"\bBPD\b", r"\bborderline\b",
]
_BANNED_RE = [re.compile(p, re.IGNORECASE) for p in BANNED]


class ModelError(Exception):
    pass


# ---------------------------------------------------------------- retrieval
def retrieve_cards(text: str, k: int = 2) -> list[dict]:
    """Keyword-overlap retrieval over the fixed skill cards (same idea as the RAG activity,
    scaled down: four short cards, no embeddings). Always returns at least the top-k."""
    words = set(re.findall(r"[a-z']+", (text or "").lower()))
    scored = []
    for card in SKILL_CARDS:
        kws = set(card["keywords"].split())
        scored.append((len(words & kws), card))
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored[:k]]


def build_checkin_messages(user_text: str) -> tuple[str, str]:
    cards = retrieve_cards(user_text)
    context = "\n".join(f"- {c['skill']}: {c['title']}. {c['body']}" for c in cards)
    others = ", ".join(SKILL_IDS)
    user = f"CONTEXT (most relevant skills first; all available: {others}):\n{context}\n\nPERSON WROTE:\n{user_text.strip()[:500]}"
    return CHECKIN_SYSTEM, user


def build_reframe_messages(thought: str, evidence: str = "") -> tuple[str, str]:
    user = f"THOUGHT: {thought.strip()[:300]}"
    if evidence.strip():
        user += f"\nWHAT MAKES IT FEEL TRUE: {evidence.strip()[:200]}"
    return REFRAME_SYSTEM, user


# ---------------------------------------------------------------- validation
def _check_text(text: str, max_chars: int) -> None:
    if not isinstance(text, str) or not text.strip():
        raise ModelError("validation: empty text")
    if len(text) > max_chars:
        raise ModelError(f"validation: too long ({len(text)} chars)")
    for rx in _BANNED_RE:
        if rx.search(text):
            raise ModelError(f"validation: banned pattern {rx.pattern!r}")


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        raise ModelError("validation: no JSON object in model output")
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError as e:
        raise ModelError(f"validation: bad JSON ({e.msg})")


def validate_checkin(raw: str) -> dict:
    data = _parse_json(raw)
    reply = data.get("reply")
    _check_text(reply, 280)
    if len(re.findall(r"[.?]+(\s|$)", reply.strip())) > 2:
        raise ModelError("validation: more than two sentences")
    skill = data.get("suggested_skill")
    if skill not in SKILL_IDS:
        skill = None
    return {"reply": reply.strip(), "suggested_skill": skill}


def validate_reframe(raw: str) -> dict:
    data = _parse_json(raw)
    alts = data.get("alternatives")
    if not isinstance(alts, list) or not alts:
        raise ModelError("validation: no alternatives list")
    clean = []
    for a in alts[:2]:
        _check_text(a, 140)
        clean.append(a.strip())
    return {"alternatives": clean}


# ---------------------------------------------------------------- mock provider
MOCK_RULES = [
    ("breathing", r"breath|chest|heart|racing|panic|shaky|tight|can'?t calm"),
    ("grounding", r"spacey|unreal|numb|foggy|zoned|far away|disconnected|floating|not here"),
    ("stop", r"angry|furious|urge|snap|yell|react|text (him|her|them)|send|about to"),
    ("reframe", r"\bthink|thought|always|never|stupid|my fault|failure|messed|hate me|upset with me|ruined"),
]
MOCK_REPLIES = {
    "breathing": "That sounds like a lot in your body right now. Paced breathing is one option if you want it.",
    "grounding": "Feeling far away can be unsettling. Grounding is one option if you want it.",
    "stop": "That sounds like a strong pull to act. STOP is one option if you want it.",
    "reframe": "That thought sounds heavy. The one-minute reframe is one option if you want it.",
    None: "Thanks for saying that. You can pick any option below, or stop here.",
}


def mock_checkin(user_text: str) -> str:
    t = (user_text or "").lower()
    for skill, rx in MOCK_RULES:
        if re.search(rx, t):
            return json.dumps({"reply": MOCK_REPLIES[skill], "suggested_skill": skill})
    return json.dumps({"reply": MOCK_REPLIES[None], "suggested_skill": None})


def mock_reframe(thought: str) -> str:
    return json.dumps({"alternatives": [
        "Maybe this is one hard moment, not the whole story.",
        "It could be that I don't have all the information yet.",
    ]})


# ---------------------------------------------------------------- live providers
def _timeout() -> float:
    return float(os.environ.get("MODEL_TIMEOUT_SECONDS", "6"))


def call_openai(system: str, user: str) -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ModelError("not_configured: OPENAI_API_KEY missing")
    r = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            "temperature": 0.4,
            "max_tokens": 200,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        },
        timeout=_timeout(),
    )
    if r.status_code != 200:
        raise ModelError(f"provider_error: HTTP {r.status_code}")
    return r.json()["choices"][0]["message"]["content"]


def call_anthropic(system: str, user: str) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ModelError("not_configured: ANTHROPIC_API_KEY missing")
    r = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
        json={
            "model": os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5"),
            "max_tokens": 200,
            "temperature": 0.4,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        },
        timeout=_timeout(),
    )
    if r.status_code != 200:
        raise ModelError(f"provider_error: HTTP {r.status_code}")
    return "".join(b.get("text", "") for b in r.json().get("content", []))


# ---------------------------------------------------------------- budget
def live_call_limit() -> int:
    return int(os.environ.get("LIVE_CALL_LIMIT", "50"))


def live_calls_used(conn) -> int:
    row = conn.execute("SELECT value FROM app_state WHERE key='live_calls_used'").fetchone()
    return int(row["value"]) if row else 0


def _bump_live_calls(conn) -> None:
    with conn:
        conn.execute(
            "INSERT INTO app_state(key, value) VALUES('live_calls_used','1') "
            "ON CONFLICT(key) DO UPDATE SET value = CAST(value AS INTEGER) + 1"
        )


def configured_provider() -> str:
    return os.environ.get("LLM_PROVIDER", "mock").strip().lower() or "mock"


def effective_provider(conn) -> str:
    p = configured_provider()
    if p in LIVE_PROVIDERS and live_calls_used(conn) >= live_call_limit():
        return "mock"  # cap reached -> fall back to mocked responses
    return p


# ---------------------------------------------------------------- entry point
def run_model(purpose: str, system: str, user: str, mock_raw: str, validator,
              session_id: Optional[int] = None, simulate_failure: bool = False) -> tuple[dict, str, Optional[str]]:
    """Returns (validated_data, source, error). Never raises: on any failure returns ({}, 'fallback', error)."""
    conn = get_conn()
    try:
        provider = "fail" if simulate_failure else effective_provider(conn)
        start = time.perf_counter()
        error = None
        data: dict = {}
        try:
            if provider == "fail":
                raise ModelError("simulated_failure: model request failed (test mode)")
            if provider == "openai":
                _bump_live_calls(conn)
                raw = call_openai(system, user)
            elif provider == "anthropic":
                _bump_live_calls(conn)
                raw = call_anthropic(system, user)
            else:
                raw = mock_raw
            data = validator(raw)
        except httpx.TimeoutException:
            error = "timeout"
        except httpx.HTTPError as e:
            error = f"network: {type(e).__name__}"
        except ModelError as e:
            error = str(e)
        except Exception as e:  # unexpected shape from a provider, etc.
            error = f"unexpected: {type(e).__name__}"
        latency = int((time.perf_counter() - start) * 1000)
        with conn:
            conn.execute(
                "INSERT INTO model_calls(session_id, purpose, provider, ok, latency_ms, error) VALUES (?,?,?,?,?,?)",
                (session_id, purpose, provider, 0 if error else 1, latency, error),
            )
        if error:
            return {}, "fallback", error
        return data, ("live_model" if provider in LIVE_PROVIDERS else "mock"), None
    finally:
        conn.close()
