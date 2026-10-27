# Assignment 3.2: Working Application and Safety (Steady)

- **Repository:** https://github.com/dbayode08-lgtm/expedia-lite (branch `assignment3`, folder `assignment3/`)
- **Commit:** `ae04d6a`
- **Submitted:** Oct 26, 2026
- **Run:** [https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/README.md](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/README.md). Mock model by default, no key needed.

## What works (all four skills, through the running interface)
| Required | Where / evidence |
|---|---|
| Complete a skill in the UI | Breathing, grounding, STOP and reframe all complete. Screenshots [03](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence/03-breathing-inhale.png), [05](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence/05-breathing-done.png), [06](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence/06-stop-observe.png), [07](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence/07-grounding-step1.png), [09](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence/09-reframe-alternatives.png) |
| Model's contribution | Check-in reply + suggested skill ([02](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence/02-checkin-suggestion.png)); reframe alternatives ([09](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence/09-reframe-alternatives.png)). Code: `backend/app/llm.py` |
| Conversation + session persistence in SQLite | `sessions`, `messages`, `exercise_runs`, `model_calls` in `backend/steady.db`. History view ([13](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence/13-history.png)) |
| Measured exercise duration | Breathing **63.0 s** measured (planned 63), STOP **43.1 s** (planned 42); crisis-panel time excluded (`paused_ms` 4 084). [timing in evaluation §3](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evaluation/evaluation.md) |
| Independent crisis-support route | Header button on every screen, static content ([04](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence/04-crisis-panel-during-breathing.png)); works with a failed model ([14](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence/14-model-failure-checkin.png)) and backend down ([16](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence/16-backend-down-crisis.png)) |
| Request fails | `?simulateFailure=1` → fallback line, `model_calls.ok=0`, skills and Crisis support keep working ([14](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence/14-model-failure-checkin.png), [15](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence/15-model-failure-reframe.png)) |
| User leaves an exercise | One-tap Stop → "Stopped. That's fine." ([08](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence/08-stopped.png)); run saved as `stopped` |

## Safety decision on crisis-related input
Crisis-like text (regex in `shared/crisis.json`, checked in the browser and on the server) is **not sent to the model**. The app shows a fixed message and opens Crisis support over whatever is on screen, pausing it. The person can still continue or leave (R3/R4). Limits: keyword matching misses indirect language and over-triggers on negations. That's why the button never depends on it.

## How the evidence was gathered
- `pytest`: 50 tests, temp DB, mock model ([tests](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/backend/tests/))
- Playwright walkthrough of the running app: 15/15 checks ([e2e/browser-check.cjs](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/e2e/browser-check.cjs), screenshots in [docs/evidence](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence/))
- DB inspection: run rows read back through `/api/history` and in DB Browser for SQLite

## Not finished at this milestone
Live-model checks (no API key yet). Personalization and history were built here but refined in 3.3.
