# Steady: IST 402 Assignment 3 (mental health skills prototype)

> **Coursework prototype only.** Steady is a class project, evaluated only with fictional scenarios. It is not therapy, not a support service, and no one monitors it. Do not offer, link or recommend it to anyone as something to use during a difficult moment.

Steady offers four brief skills, one at a time: paced breathing (4-6), 5-4-3-2-1 grounding, STOP, and a one-minute reframe. A **Crisis support** button stays on every screen and works without the backend or the model. Design reasoning: [`docs/design.md`](docs/design.md).

Stack: Vue 3 + Vite (frontend, port **5174**), FastAPI (backend, port **8001**), SQLite (`backend/steady.db`). These ports are different from Expedia Lite's (5173/8000), so both can run at once.

## Run it (clean checkout)

Prerequisites: Python 3.10+, Node.js 18+.

```bash
# from the repo root
cd assignment3/backend
cp .env.example .env              # default LLM_PROVIDER=mock: no key, no paid calls
python3 -m pip install -r requirements.txt     # add --break-system-packages or use a venv if pip refuses
python3 -m uvicorn main:app --reload --port 8001
```

New terminal:

```bash
cd assignment3/frontend
npm install
npm run dev                        # http://127.0.0.1:5174
```

On a Mac you can instead double-click `assignment3/start-steady.command` (it runs both).

### Optional: live model

Edit `backend/.env`: set `LLM_PROVIDER=openai` (plus `OPENAI_API_KEY`) or `LLM_PROVIDER=anthropic` (plus `ANTHROPIC_API_KEY`). Restart the backend. Live calls are capped at `LIVE_CALL_LIMIT` (default 50); after that the app switches to mock responses. Keys live only in `backend/.env`, which is git-ignored.

### Demo switches

- `http://127.0.0.1:5174/?simulateFailure=1` makes every model request fail (needs `ALLOW_FAILURE_SIMULATION=1`, the default).
- `LLM_PROVIDER=fail` in `.env` does the same server-side.

## Tests

```bash
cd assignment3/backend
python3 -m pytest -q              # 50 tests, temp DB, mock model, no network
python3 -m eval.scenarios         # 17 API scenarios -> docs/evaluation/mock-results.md
python3 -m eval.scenarios --live  # 4 scenarios x 3 repeats with the live model (needs a key; max 12 calls)
```

Browser walkthrough (both servers running, mock model; needs Playwright installed: `npm i -g playwright && npx playwright install chromium`):

```bash
cd assignment3 && node e2e/browser-check.cjs     # screenshots -> docs/evidence/
```

Inspect the database with DB Browser for SQLite: open `assignment3/backend/steady.db` (tables `sessions`, `exercise_runs`, `messages`, `model_calls`).

## Layout

```
assignment3/
├── shared/            skills.json (steps + timing) and crisis.json (resources + patterns), read by BOTH apps
├── backend/
│   ├── main.py        FastAPI app
│   ├── app/           db.py (schema) · routes.py (controller) · llm.py (model layer) · safety.py · personalization.py · skills.py
│   ├── eval/          scenarios.py (evaluation runner, mock + live)
│   └── tests/         pytest (temp DB)
├── frontend/src/      App.vue (journey) · components/ (one per screen/skill) · services/api.js · safety.js · composables/useRunTimer.js
├── e2e/               browser-check.cjs (Playwright walkthrough)
├── docs/              design.md · flow.png · timing.md · evaluation/ · evidence/ · evidence-log.md · code-walkthrough.md · recording-script.md
├── reports/           report-3.1.md · report-3.2.md · report-3.3.md (upload each as report.md)
├── AGENTS.md          instructions for the coding agent
└── AI-USE.md          AI tools and models used
```

## Reused from Assignments 1–2 and the RAG activity

| Reused | From | Where now |
|---|---|---|
| FastAPI + Vue + SQLite split; `/api/` prefix; CORS setup | Expedia Lite A1 | `backend/main.py` |
| `get_conn()` + additive `migrate()` with `CREATE TABLE IF NOT EXISTS` | A1 Part 2 `seed.py`, A2 `local_hotels/schema.py` | `backend/app/db.py` |
| Controller/model separation; failures never shown as "empty" | A2 `live_search` / `local_hotels` | `routes.py` / `llm.py`, fallback lines |
| `call()` fetch wrapper that throws on failure | A2 `localHotelsApi.js` | `frontend/src/services/api.js` |
| pytest with a temporary database per test | A2 `tests/test_local_hotels.py` | `backend/tests/conftest.py` |
| Secrets only in `backend/.env`, `.env.example` committed | A2 | `backend/.env.example` |
| Double-click start script | `start-app.command` | `start-steady.command` |
| AGENTS.md, handoff, prompts, report conventions | A1/A2 | here |
| Retrieve stored info → put in prompt → save conversation | RAG activity (hotel chatbot) | `llm.retrieve_cards` + `messages` table |
