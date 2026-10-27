# Current handoff

_Update this file at each checkpoint._

## Status: Assignment 3 (Steady) — branch assignment3, folder assignment3/

- [x] 4 skills (breathing 63 s, grounding ~54 s, STOP ~42 s, reframe ~65 s), one instruction per screen, one-tap Stop
- [x] Crisis support in every header, static, works with model failure + backend down
- [x] Check-in (retrieval + model, validated, 6 s timeout, fallback), reframe alternatives (opt-in)
- [x] SQLite: sessions, exercise_runs, messages, model_calls, app_state, skill_cards; History + Clear history; "Your usual"
- [x] pytest 50/50, API scenarios 17/17 (mock), browser checks 15/15
- [ ] Live-model repeats (`python3 -m eval.scenarios --live`) -- needs an API key in assignment3/backend/.env
- [ ] Record demo + process screencast (script: assignment3/docs/recording-script.md); paste links in report-3.3.md
- [ ] Fill "What I checked myself" in assignment3/AI-USE.md


## Status: Assignment 2, Part 2 in-class (local hotel storage) — branch assignment2_part2_in_class

- [x] saved_hotels, saved_hotel_zips, demo_hotel_nights (additive migration on startup; A1 tables untouched)
- [x] /api/local: GET hotels?zip=, GET saved-ids, POST hotels, DELETE hotels/{id}
- [x] Add to Local / Remove from Local; "Saved locally" vs "API results"; local failure = error, not empty
- [x] Automated: `python -m pytest -q` -> 26 passed (8 new, temp DBs); `npm run build` OK
- [ ] Manual DB Browser + browser benchmarks (student)
- DB file: backend/expedia_lite.db. Demo nights: 2026-10-10..14, defaults 10000 cents / 20 rooms (simulated).

## Status: Assignment 2, Part 1 (live hotel search + map)

## What works

- [x] `GET /api/live/hotels?zip=` resolves a U.S. ZIP via Geoapify and returns
      hotel-category places within 5 km, nearest first, de-duplicated
- [x] Wrong/non-U.S. geocoding results are rejected (no search elsewhere)
- [x] Vue list + Leaflet map with shared selection (list -> map, map -> list)
- [x] Separate UI states: loading, results, invalid input, ZIP not found,
      no results, rate limited, failed request
- [x] Keyboard: ZIP form, list items, and map pins (Tab + Enter)
- [x] Assignment 1 search and booking CRUD unchanged

## What was checked

- [x] `python -m pytest -q` in backend/ -> 18 passed (fake Geoapify)
- [x] Headless browser against a mock backend: all states + both selection directions
- [x] Live searches with a real key (16801, 02134, 00000, 1234, backend stopped) -- recorded in docs/a2-part1/report.md

## Known limitations

- OSM/Geoapify coverage is incomplete; max 50 places per search
- Distance is straight-line from the ZIP center point
- OSM public tiles: light use only

## Next task

Part 2 (due Oct 6): SQLite shortlist table keyed by (provider, provider_place_id),
save/list/remove endpoints, duplicate prevention, labeled fixed JSON sample,
restart + persistence evidence.
