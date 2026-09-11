# Expedia Lite — Part 1

## Repository and commit

Repository: https://github.com/dbayode08-lgtm/expedia-lite
Commit: 52de663f67b6c6bd39bc3d1f9a3fb3289bc5efb8

## Implementation

The frontend is a single Vue 3 component (`frontend/src/App.vue`) with a search input, a Search button, and a results table. It calls `GET /api/search` on the backend and renders the returned hotels and trips, or a "no results" message when nothing matches.

FastAPI (`backend/main.py`) is the only contract between frontend and backend. It reads `hotels.csv` and `trips.csv` directly from disk on every request, joins matching hotels to their trips via `hotel_id`, and returns derived fields (nights stayed, computed stay price) since the data pack doesn't store price directly.

One design decision worth noting: the assignment brief describes searching by hotel name, but the instructor's own sample-data README documents worked test cases that search by city instead (e.g. searching "Boston" returns trips T001, T002, T009, T010). Rather than satisfy only one reading, the search matches a query against both `hotel_name` and `city`, so both interpretations work correctly.

## Verification

| Action | Expected | Observed |
|---|---|---|
| Search "Boston" | Returns 2 hotels (Harbor Lantern Hotel, Maple Square Inn) and trips T001, T002, T009, T010, matching the instructor's documented test case | Matched exactly — see screenshot below |
| Search "Miami" | No hotels match; a "no hotels matched" message displays | Matched exactly — see screenshot below |

Screenshots: `docs/screenshots/search-boston.png`, `docs/screenshots/search-miami.png`

I also manually verified the backend endpoint directly (via browser and curl) against every worked example in the data pack's README (Boston, New York, Philadelphia, Washington, State College, Miami/no-match) before testing through the UI, and confirmed the derived stay-price calculation (e.g. trip T001: 2 nights × $150/night = $300).

## Project context and next steps

- [README](https://github.com/dbayode08-lgtm/expedia-lite/blob/main/README.md)
- [AGENTS.md](https://github.com/dbayode08-lgtm/expedia-lite/blob/main/AGENTS.md)
- [Design note](https://github.com/dbayode08-lgtm/expedia-lite/blob/main/docs/design-note.md)
- [Selected prompts](https://github.com/dbayode08-lgtm/expedia-lite/tree/main/prompts)
- [Current handoff](https://github.com/dbayode08-lgtm/expedia-lite/blob/main/handoffs/current.md)

**Limitations:** No persistence yet — every search re-reads the CSVs from disk. No booking, history, or CRUD.

**Next task:** Part 2 — seed a SQLite database from the CSVs and add booking create/read/update(cancel)/delete through the frontend.