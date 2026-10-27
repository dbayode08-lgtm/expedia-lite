"""Deterministic API checks (mock model, temp DB)."""
import json

import httpx
import pytest

from app import llm
from app.safety import is_crisis_text
from app.skills import SKILLS, MAX_EXERCISE_SECONDS


def count(table):
    from app.db import get_conn
    c = get_conn()
    try:
        return c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        c.close()


def test_health_and_static(client):
    assert client.get("/api/health").json() == {"ok": True}
    assert len(client.get("/api/skills").json()["skills"]) == 4
    assert client.get("/api/crisis").json()["resources"][0]["href"] == "tel:988"


def test_chat_saves_both_messages(client, sid):
    r = client.post("/api/chat", json={"session_id": sid, "message": "my chest is tight"}).json()
    assert r["suggested_skill"] == "breathing" and r["source"] == "mock"
    assert count("messages") == 2 and count("model_calls") == 1


def test_chat_unknown_session_404(client):
    assert client.post("/api/chat", json={"session_id": 999, "message": "hi"}).status_code == 404


def test_crisis_text_skips_model(client, sid):
    r = client.post("/api/chat", json={"session_id": sid, "message": "I want to end it all"}).json()
    assert r["crisis"] and r["source"] == "crisis_rule"
    assert count("model_calls") == 0


@pytest.mark.parametrize("text,expected", [
    ("I want to kill myself", True), ("thinking about suicide", True), ("I've been hurting myself", True),
    ("I don’t want to live", True), ("everyone is better off without me", True),
    ("this exam is killing me", False), ("my feet are killing me", False), ("I'm stressed", False),
    ("I'm dying to see that movie", False),
])
def test_crisis_patterns(text, expected):
    assert is_crisis_text(text) is expected


def test_simulated_failure_falls_back(client, sid):
    r = client.post("/api/chat", json={"session_id": sid, "message": "hi"}, headers={"X-Simulate-Model-Failure": "1"}).json()
    assert r["source"] == "fallback" and "isn't available" in r["reply"]
    assert count("messages") == 2      # failure is still recorded in the conversation


def test_failure_simulation_can_be_disabled(client, sid, monkeypatch):
    monkeypatch.setenv("ALLOW_FAILURE_SIMULATION", "0")
    r = client.post("/api/chat", json={"session_id": sid, "message": "hi"}, headers={"X-Simulate-Model-Failure": "1"}).json()
    assert r["source"] == "mock"


@pytest.mark.parametrize("raw", [
    "not json at all",
    json.dumps({"reply": "Great job! You should breathe.", "suggested_skill": "breathing"}),
    json.dumps({"reply": "It sounds like a symptom of a disorder.", "suggested_skill": None}),
    json.dumps({"reply": "x" * 400, "suggested_skill": None}),
    json.dumps({"reply": "One. Two. Three.", "suggested_skill": None}),
    json.dumps({"reply": "", "suggested_skill": None}),
])
def test_invalid_model_output_rejected(raw):
    with pytest.raises(llm.ModelError):
        llm.validate_checkin(raw)


def test_unknown_skill_from_model_dropped():
    out = llm.validate_checkin(json.dumps({"reply": "Okay.", "suggested_skill": "yoga"}))
    assert out["suggested_skill"] is None


def test_timeout_falls_back(client, sid, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    def boom(*a, **k): raise httpx.ReadTimeout("t")
    monkeypatch.setattr(llm, "call_openai", boom)
    r = client.post("/api/chat", json={"session_id": sid, "message": "rough day"}).json()
    assert r["source"] == "fallback" and r["model_error"] == "timeout"


def test_live_cap_switches_to_mock(client, sid, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LIVE_CALL_LIMIT", "2")
    calls = []
    monkeypatch.setattr(llm, "call_openai", lambda s, u: calls.append(1) or json.dumps({"reply": "Okay.", "suggested_skill": None}))
    sources = [client.post("/api/chat", json={"session_id": sid, "message": "hi"}).json()["source"] for _ in range(4)]
    assert sources == ["live_model", "live_model", "mock", "mock"] and len(calls) == 2
    assert client.get("/api/model/status").json()["live_calls_used"] == 2


def test_missing_key_is_a_fallback_not_a_crash(client, sid, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = client.post("/api/chat", json={"session_id": sid, "message": "hi"}).json()
    assert r["source"] == "fallback" and r["model_error"].startswith("not_configured")


def test_retrieval_puts_relevant_card_first():
    assert llm.retrieve_cards("I feel numb and far away")[0]["skill"] == "grounding"
    system, user = llm.build_checkin_messages("my heart is racing")
    assert "breathing" in user.split("PERSON WROTE")[0] and "not a therapist" in system


def test_reframe_alternatives_and_failure(client, sid):
    ok = client.post("/api/reframe/alternatives", json={"session_id": sid, "thought": "I messed up"}).json()
    assert len(ok["alternatives"]) == 2 and ok["source"] == "mock"
    bad = client.post("/api/reframe/alternatives", json={"session_id": sid, "thought": "I messed up"},
                      headers={"X-Simulate-Model-Failure": "1"}).json()
    assert bad["alternatives"] == [] and bad["source"] == "fallback"
    crisis = client.post("/api/reframe/alternatives", json={"session_id": sid, "thought": "I should just kill myself"}).json()
    assert crisis["crisis"] and crisis["alternatives"] == []


def test_run_lifecycle_and_feedback(client, sid):
    rid = client.post("/api/runs", json={"session_id": sid, "skill": "breathing", "chosen_via": "usual"}).json()["run_id"]
    assert client.post(f"/api/runs/{rid}/end", json={"status": "completed", "steps_done": 6, "setup_ms": 3, "duration_ms": 63000, "paused_ms": 4000}).status_code == 200
    assert client.post(f"/api/runs/{rid}/feedback", json={"feedback": "helped"}).status_code == 200
    run = client.get("/api/history").json()["sessions"][0]["runs"][0]
    assert (run["status"], run["duration_ms"], run["paused_ms"], run["feedback"]) == ("completed", 63000, 4000, "helped")


def test_bad_run_input(client, sid):
    assert client.post("/api/runs", json={"session_id": sid, "skill": "yoga"}).status_code == 400
    assert client.post("/api/runs/999/end", json={"status": "completed", "steps_done": 1}).status_code == 404
    assert client.post("/api/runs/999/feedback", json={"feedback": "helped"}).status_code == 404


def _finish(client, sid, skill, status="completed", feedback=None):
    rid = client.post("/api/runs", json={"session_id": sid, "skill": skill}).json()["run_id"]
    client.post(f"/api/runs/{rid}/end", json={"status": status, "steps_done": 1})
    if feedback:
        client.post(f"/api/runs/{rid}/feedback", json={"feedback": feedback})


def test_personalization_rules(client, sid):
    assert client.get("/api/personalization").json()["usual_skill"] is None
    _finish(client, sid, "stop")
    assert client.get("/api/personalization").json()["usual_skill"] is None          # 1 completion is not enough
    _finish(client, sid, "stop")
    assert client.get("/api/personalization").json()["usual_skill"] == "stop"
    for _ in range(4):
        _finish(client, sid, "stop", status="stopped")                                 # stopping never lowers it
    assert client.get("/api/personalization").json()["usual_skill"] == "stop"
    _finish(client, sid, "grounding", feedback="helped")
    _finish(client, sid, "grounding", feedback="helped")
    assert client.get("/api/personalization").json()["usual_skill"] == "grounding"     # higher score wins
    _finish(client, sid, "grounding", status="stopped", feedback="not_this_time")
    _finish(client, sid, "grounding", status="stopped", feedback="not_this_time")
    # two "not this time" taps cancel grounding's score -> the earlier usual (stop) returns
    assert client.get("/api/personalization").json()["usual_skill"] == "stop"


def test_abandoned_run_becomes_stopped_on_next_visit(client, sid):
    rid = client.post("/api/runs", json={"session_id": sid, "skill": "breathing"}).json()["run_id"]
    client.post("/api/sessions", json={})
    runs = [r for s in client.get("/api/history").json()["sessions"] for r in s["runs"]]
    assert [r["status"] for r in runs if r["id"] == rid] == ["stopped"]


def test_clear_history(client, sid):
    _finish(client, sid, "stop"); _finish(client, sid, "stop")
    client.post("/api/chat", json={"session_id": sid, "message": "hi"})
    assert client.delete("/api/history").status_code == 200
    assert client.get("/api/history").json()["sessions"] == []
    assert client.get("/api/personalization").json()["usual_skill"] is None
    assert count("model_calls") == 0


def test_every_skill_planned_within_90_seconds():
    for s in SKILLS.values():
        step_total = sum(st.get("seconds", 0) for st in s["steps"])
        assert step_total == s["planned_seconds"], s["id"]
        assert s["planned_seconds"] <= MAX_EXERCISE_SECONDS, s["id"]
    b = SKILLS["breathing"]["steps"][1]
    assert b["cycles"] * (b["inhale"] + b["exhale"]) == b["seconds"]
    # reframe worst case: planned time + full model timeout still under the cap
    assert SKILLS["reframe"]["planned_seconds"] + 6 <= MAX_EXERCISE_SECONDS
