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

## Assignment 2 — Hotel Discovery with Public APIs

### MVC responsibilities

- **Model** — `backend/live_search/models.py` (response shapes: search
  center, place result; no price/rating/availability fields) and
  `backend/live_search/geoapify_client.py` (all Geoapify calls and
  normalization). SQLite tables live in `backend/seed.py`.
- **Controller** — `backend/live_search/controller.py` validates the ZIP,
  calls the model, and maps each outcome to a status code:
  200 results/empty, 400 `invalid_zip`, 404 `zip_not_found`,
  429 `rate_limited`, 502 `provider_error`, 503 `not_configured`.
- **View** — `frontend/src/components/HotelSearchPage.vue` (states),
  `ZipSearchForm.vue`, `HotelList.vue`, `HotelMap.vue`; shared selection
  state in `frontend/src/composables/useHotelSearch.js`; HTTP in
  `frontend/src/services/hotelSearchApi.js`. The view never calls Geoapify.

### Rules

- `GEOAPIFY_API_KEY` goes in `backend/.env` only. Never put it in frontend
  code, reports, screenshots, or commits. Map tiles use OpenStreetMap (no key).
- A geocoding result counts only if it is a U.S. postcode equal to the typed
  ZIP; otherwise report "ZIP not found" and do not search anywhere else.
- Never invent names, prices, ratings, availability, or bookings for live
  places. Missing fields are labeled or omitted.
- A failed or rate-limited request must never be shown as an empty search.

### Verification loop

1. `cd backend && python -m pytest -q` — offline checks with a fake
   Geoapify (no quota used, no dependence on live result counts).
2. Run both servers and check the changed behavior in a browser.
3. Record expected vs. observed (with the ZIP and date for live searches)
   in the part's report, and update `handoffs/current.md`.

### Dependencies (CHECK → TAKE ACTION → VERIFY)

- CHECK what is already installed / listed in `requirements.txt` and
  `package.json`.
- TAKE ACTION only after telling the student the exact install command and
  getting approval.
- VERIFY by running the tests and `npm run build`.
- Approved 2026-09-29: `httpx`, `python-dotenv`, `pytest` (backend);
  `leaflet@^1.9.4` (frontend).

## Out of scope for Part 1

No database, no booking creation, no authentication. Search only.
