"""CONTROLLER: HTTP endpoints under /api/. Validates input, calls the model layer
and the database, maps outcomes to responses.
"""
import os
from typing import Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from . import llm
from .db import get_conn
from .personalization import usual_skill
from .safety import CRISIS, CRISIS_REPLY, is_crisis_text
from .skills import SKILLS_DOC, SKILL_IDS

router = APIRouter(prefix="/api")

FALLBACK_CHECKIN = "The text helper isn't available right now. You can pick any option below, or stop here."


def _simulate(header_value: Optional[str]) -> bool:
    return header_value == "1" and os.environ.get("ALLOW_FAILURE_SIMULATION", "1") == "1"


def _session_exists(conn, session_id: int) -> None:
    if not conn.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone():
        raise HTTPException(404, detail="session_not_found")


# ------------------------------------------------------------------ static
@router.get("/health")
def health():
    return {"ok": True}


@router.get("/skills")
def skills():
    return SKILLS_DOC


@router.get("/crisis")
def crisis():
    return CRISIS


@router.get("/model/status")
def model_status():
    conn = get_conn()
    try:
        return {
            "configured_provider": llm.configured_provider(),
            "effective_provider": llm.effective_provider(conn),
            "live_calls_used": llm.live_calls_used(conn),
            "live_call_limit": llm.live_call_limit(),
        }
    finally:
        conn.close()


# ------------------------------------------------------------------ sessions
class SessionIn(BaseModel):
    fewer_options: bool = False


@router.post("/sessions", status_code=201)
def create_session(body: SessionIn):
    conn = get_conn()
    try:
        with conn:
            # A run left 'started' (tab closed, browser quit) is recorded as stopped -- leaving
            # without pressing Stop is still leaving, and it never counts against a skill (R3).
            conn.execute(
                "UPDATE exercise_runs SET status='stopped', ended_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') "
                "WHERE status='started'"
            )
            cur = conn.execute("INSERT INTO sessions(fewer_options) VALUES (?)", (int(body.fewer_options),))
        return {"session_id": cur.lastrowid}
    finally:
        conn.close()


@router.post("/sessions/{session_id}/end")
def end_session(session_id: int):
    conn = get_conn()
    try:
        _session_exists(conn, session_id)
        with conn:
            conn.execute(
                "UPDATE sessions SET ended_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=? AND ended_at IS NULL",
                (session_id,),
            )
        return {"ok": True}
    finally:
        conn.close()


# ------------------------------------------------------------------ check-in chat
class ChatIn(BaseModel):
    session_id: int
    message: str = Field(min_length=1, max_length=1000)


def _save_msg(conn, session_id, role, content, source=None, crisis=False, skill=None):
    conn.execute(
        "INSERT INTO messages(session_id, role, content, source, crisis_flag, suggested_skill) VALUES (?,?,?,?,?,?)",
        (session_id, role, content, source, int(crisis), skill),
    )


@router.post("/chat")
def chat(body: ChatIn, x_simulate_model_failure: Optional[str] = Header(default=None)):
    conn = get_conn()
    try:
        _session_exists(conn, body.session_id)
        crisis = is_crisis_text(body.message)
        with conn:
            _save_msg(conn, body.session_id, "user", body.message, crisis=crisis)
    finally:
        conn.close()

    if crisis:
        # Documented decision: crisis-like text is NOT sent to the model.
        reply, source, skill, error = CRISIS_REPLY, "crisis_rule", None, None
    else:
        system, user = llm.build_checkin_messages(body.message)
        data, source, error = llm.run_model(
            "checkin", system, user, llm.mock_checkin(body.message), llm.validate_checkin,
            session_id=body.session_id, simulate_failure=_simulate(x_simulate_model_failure),
        )
        reply = data.get("reply", FALLBACK_CHECKIN)
        skill = data.get("suggested_skill")

    conn = get_conn()
    try:
        with conn:
            _save_msg(conn, body.session_id, "assistant", reply, source=source, crisis=crisis, skill=skill)
    finally:
        conn.close()
    return {
        "reply": reply,
        "suggested_skill": skill,
        "source": source,
        "crisis": crisis,
        "model_error": error,
    }


# ------------------------------------------------------------------ reframe assist (opt-in)
class ReframeIn(BaseModel):
    session_id: int
    thought: str = Field(min_length=1, max_length=500)
    evidence: str = Field(default="", max_length=500)


@router.post("/reframe/alternatives")
def reframe_alternatives(body: ReframeIn, x_simulate_model_failure: Optional[str] = Header(default=None)):
    if is_crisis_text(body.thought) or is_crisis_text(body.evidence):
        return {"alternatives": [], "source": "crisis_rule", "crisis": True, "model_error": None}
    conn = get_conn()
    try:
        _session_exists(conn, body.session_id)
    finally:
        conn.close()
    system, user = llm.build_reframe_messages(body.thought, body.evidence)
    data, source, error = llm.run_model(
        "reframe", system, user, llm.mock_reframe(body.thought), llm.validate_reframe,
        session_id=body.session_id, simulate_failure=_simulate(x_simulate_model_failure),
    )
    return {"alternatives": data.get("alternatives", []), "source": source, "crisis": False, "model_error": error}


# ------------------------------------------------------------------ exercise runs
class RunIn(BaseModel):
    session_id: int
    skill: str
    chosen_via: Literal["menu", "usual", "suggested"] = "menu"


@router.post("/runs", status_code=201)
def start_run(body: RunIn):
    if body.skill not in SKILL_IDS:
        raise HTTPException(400, detail="unknown_skill")
    conn = get_conn()
    try:
        _session_exists(conn, body.session_id)
        with conn:
            cur = conn.execute(
                "INSERT INTO exercise_runs(session_id, skill, chosen_via) VALUES (?,?,?)",
                (body.session_id, body.skill, body.chosen_via),
            )
        return {"run_id": cur.lastrowid}
    finally:
        conn.close()


class RunEnd(BaseModel):
    status: Literal["completed", "stopped"]
    steps_done: int = Field(ge=0, le=20)
    setup_ms: Optional[int] = Field(default=None, ge=0)
    duration_ms: Optional[int] = Field(default=None, ge=0)
    paused_ms: int = Field(default=0, ge=0)


@router.post("/runs/{run_id}/end")
def end_run(run_id: int, body: RunEnd):
    conn = get_conn()
    try:
        row = conn.execute("SELECT status FROM exercise_runs WHERE id=?", (run_id,)).fetchone()
        if not row:
            raise HTTPException(404, detail="run_not_found")
        with conn:
            conn.execute(
                "UPDATE exercise_runs SET status=?, steps_done=?, setup_ms=?, duration_ms=?, paused_ms=?, "
                "ended_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?",
                (body.status, body.steps_done, body.setup_ms, body.duration_ms, body.paused_ms, run_id),
            )
        return {"ok": True}
    finally:
        conn.close()


class FeedbackIn(BaseModel):
    feedback: Literal["helped", "not_this_time", "skipped"]


@router.post("/runs/{run_id}/feedback")
def run_feedback(run_id: int, body: FeedbackIn):
    conn = get_conn()
    try:
        with conn:
            cur = conn.execute("UPDATE exercise_runs SET feedback=? WHERE id=?", (body.feedback, run_id))
        if cur.rowcount == 0:
            raise HTTPException(404, detail="run_not_found")
        return {"ok": True}
    finally:
        conn.close()


# ------------------------------------------------------------------ personalization + history
@router.get("/personalization")
def personalization():
    conn = get_conn()
    try:
        return usual_skill(conn)
    finally:
        conn.close()


@router.get("/history")
def history(limit: int = 30):
    conn = get_conn()
    try:
        sessions = [dict(r) for r in conn.execute(
            "SELECT * FROM sessions WHERE id IN (SELECT session_id FROM exercise_runs UNION SELECT session_id FROM messages) "
            "ORDER BY id DESC LIMIT ?", (limit,))]
        for s in sessions:
            s["runs"] = [dict(r) for r in conn.execute(
                "SELECT id, skill, chosen_via, status, steps_done, setup_ms, duration_ms, paused_ms, feedback, started_at, ended_at "
                "FROM exercise_runs WHERE session_id=? ORDER BY id", (s["id"],))]
            s["messages"] = [dict(r) for r in conn.execute(
                "SELECT role, content, source, crisis_flag, suggested_skill, created_at FROM messages WHERE session_id=? ORDER BY id",
                (s["id"],))]
        return {"sessions": sessions}
    finally:
        conn.close()


@router.delete("/history")
def clear_history():
    """User control: remove every saved session, run, message and model-call log."""
    conn = get_conn()
    try:
        with conn:
            conn.execute("DELETE FROM messages")
            conn.execute("DELETE FROM exercise_runs")
            conn.execute("DELETE FROM sessions")
            conn.execute("DELETE FROM model_calls")
        return {"ok": True}
    finally:
        conn.close()
