# AGENTS.md — Expedia Lite

Instructions for any coding agent (Codex, Claude Code) working in this
repository.

## Project

Expedia Lite is a two-part local travel application for IST 402 Assignment
1. Part 1 is read-only CSV search. Part 2 adds SQLite-backed booking CRUD.
Stack: FastAPI backend, Vue 3 + Vite frontend, SQLite for persistence
(Part 2 onward).

## Structure

- `backend/` — Python/FastAPI. `main.py` is the entry point. In Part 1 it
  reads `hotels.csv` and `trips.csv` directly. In Part 2 it should read and
  write a SQLite database instead, seeded once from the CSVs.
- `frontend/` — Vue 3 + Vite. `src/App.vue` is currently the whole UI;
  split into components as booking/history features are added in Part 2.
- `docs/` — one short design note explaining frontend/FastAPI/backend
  responsibilities.
- `prompts/` — save the prompts actually used to build each feature, for
  AI-use disclosure.
- `handoffs/current.md` — keep this current: what works, what was checked,
  known limitations, next task.

## Conventions

- Keep frontend and backend fully separate folders; communicate only over
  HTTP through FastAPI endpoints prefixed `/api/`.
- Preserve existing hotel/trip/user/booking IDs when seeding or editing
  data; assign new unique IDs to new records.
- Do not hand-write browser test selectors. Describe the behavior to test
  in plain English and drive the agent to exercise the running app in a
  real browser, then save the resulting script.
- Before committing: run the backend and frontend locally, verify the
  targeted behavior manually, and record expected vs. observed results.
- Follow CHECK → TAKE ACTION → VERIFY before adding any new dependency.

## Out of scope for Part 1

No database, no booking creation, no authentication. Search only.
