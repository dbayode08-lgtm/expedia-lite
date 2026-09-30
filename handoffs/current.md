# Current handoff

_Update this file at each checkpoint._

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
