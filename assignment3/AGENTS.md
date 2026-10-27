# AGENTS.md: Steady (Assignment 3)

Instructions for any coding agent working in `assignment3/`.

## What this is
A coursework prototype of brief coping-skill exercises, grounded in the R1–R4 / D1–D6 study findings (see `docs/design.md`). Fictional scenarios only. Never describe it as therapy, never imply monitoring, never diagnose.

## Hard rules (do not weaken without updating docs/design.md and the tests)
1. **Crisis support stays in the header of every view** and renders from `shared/crisis.json` bundled at build time. It must never call the backend or the model.
2. **Crisis detection runs before any model call** (backend `app/safety.py` and browser `src/safety.js`, same `shared/crisis.json` patterns). Crisis-like text is never sent to a model.
3. **Skill steps and timing come only from `shared/skills.json`.** The model never adds, removes or rewrites steps. Every `planned_seconds` ≤ 90 (enforced by `test_every_skill_planned_within_90_seconds`).
4. **Stop is one tap with no confirmation**, and stopped runs never lower personalization.
5. **Model output is validated** (`llm.validate_*`). Any failure becomes a fixed fallback line; nothing user-facing depends on a model call succeeding.
6. Keys only in `backend/.env`. Default `LLM_PROVIDER=mock`. Live calls are capped by `LIVE_CALL_LIMIT` (≤ 50).
7. Language (D6): plain and neutral. No exclamation marks, praise, streaks, scores, or clinical terms.

## Structure (MVC)
- Model: `backend/app/db.py` (schema), `llm.py` (provider calls + validation), `personalization.py`, `skills.py`, `safety.py`
- Controller: `backend/app/routes.py`
- View: `frontend/src/App.vue` (journey state), `components/*` (one per screen / skill)

## Verification loop
1. `cd backend && python3 -m pytest -q` (all must pass, mock only)
2. `python3 -m eval.scenarios` (writes `docs/evaluation/mock-results.md`)
3. Both servers running → `node e2e/browser-check.cjs` → check screenshots in `docs/evidence/`
4. `cd frontend && npm run build`
5. Record expected vs observed in `docs/evaluation/evaluation.md`, and add decisions to `docs/evidence-log.md`.

## Dependencies (CHECK → TAKE ACTION → VERIFY)
No new dependencies beyond Expedia Lite's approved set (fastapi, uvicorn, httpx, python-dotenv, pytest; vue, vite). Playwright is used only for the optional browser check and is not a project dependency. Ask before adding anything.
