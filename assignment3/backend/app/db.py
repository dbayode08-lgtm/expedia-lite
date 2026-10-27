"""MODEL (storage): SQLite connection + schema for the Steady skills prototype.

One local database file (steady.db, git-ignored). The path can be overridden with
STEADY_DB_PATH so tests always run against a temporary database.

Pattern reused from Expedia Lite (A1/A2): get_conn() + an additive, repeatable
migrate() using CREATE TABLE IF NOT EXISTS, safe to call on every startup.
"""
import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "steady.db"


def db_path() -> Path:
    return Path(os.environ.get("STEADY_DB_PATH", DEFAULT_DB_PATH))


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    ended_at      TEXT,
    fewer_options INTEGER NOT NULL DEFAULT 0      -- user-chosen "less on screen" (D1)
);

-- Every message in the optional check-in conversation (user + app/model side).
CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role        TEXT NOT NULL CHECK (role IN ('user','assistant')),
    content     TEXT NOT NULL,
    source      TEXT,            -- live_model | mock | fallback | crisis_rule  (assistant rows)
    crisis_flag INTEGER NOT NULL DEFAULT 0,
    suggested_skill TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- One row per started exercise. status: started -> completed | stopped
CREATE TABLE IF NOT EXISTS exercise_runs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    skill        TEXT NOT NULL,
    chosen_via   TEXT NOT NULL DEFAULT 'menu',  -- menu | usual | suggested
    status       TEXT NOT NULL DEFAULT 'started' CHECK (status IN ('started','completed','stopped')),
    steps_done   INTEGER NOT NULL DEFAULT 0,
    setup_ms     INTEGER,      -- choosing the skill -> first instruction (reported separately)
    duration_ms  INTEGER,      -- first instruction -> final planned step, minus user pauses
    paused_ms    INTEGER NOT NULL DEFAULT 0,
    feedback     TEXT CHECK (feedback IN ('helped','not_this_time','skipped') OR feedback IS NULL),
    started_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    ended_at     TEXT
);

-- Every attempted model request (live or mock), for verification evidence.
CREATE TABLE IF NOT EXISTS model_calls (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER,
    purpose     TEXT NOT NULL,      -- checkin | reframe
    provider    TEXT NOT NULL,      -- openai | anthropic | mock | fail
    ok          INTEGER NOT NULL,
    latency_ms  INTEGER,
    error       TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- Small key/value store: live_calls_used (cap of 50 live model calls).
CREATE TABLE IF NOT EXISTS app_state (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Retrieval context for the model: short, fixed skill cards (seeded from skills.py).
CREATE TABLE IF NOT EXISTS skill_cards (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    skill    TEXT NOT NULL,
    title    TEXT NOT NULL,
    body     TEXT NOT NULL,
    keywords TEXT NOT NULL,
    UNIQUE (skill, title)
);
"""


def migrate(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    from .skills import SKILL_CARDS  # local import avoids a cycle

    with conn:
        conn.executemany(
            "INSERT OR IGNORE INTO skill_cards (skill, title, body, keywords) VALUES (?,?,?,?)",
            [(c["skill"], c["title"], c["body"], c["keywords"]) for c in SKILL_CARDS],
        )


def init_db() -> None:
    conn = get_conn()
    try:
        migrate(conn)
    finally:
        conn.close()
