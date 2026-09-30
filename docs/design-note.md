# Design note — Expedia Lite (Part 1)

## Frontend (Vue)

A single `App.vue` component holds a search input, a Search button, and a
results table. It calls `GET /api/search?query=...` on the backend and
renders the returned hotels/trips, or a "no results" message when the
result list is empty. The frontend holds no business logic — nights and
stay price are computed by the backend and just displayed here.

## FastAPI

`backend/main.py` exposes `GET /api/search`. It is the only contract
between frontend and backend: given a `query` parameter, it returns
matching hotels joined with their trips, each trip annotated with derived
`nights` and `stay_price_usd`. CORS is enabled for the local Vite dev
server origin so the browser can call the API from a different port.

## Backend / data

For Part 1, "backend" and "data access" are the same layer: `main.py`
reads `hotels.csv` and `trips.csv` from disk on every request using
Python's `csv` module (`utf-8-sig` encoding, since the data pack's files
carry a byte-order mark), filters hotels by a case-insensitive substring
match against **either** `hotel_name` or `city`, and joins each matching
hotel to its trips via `hotel_id`. There is no persistence layer yet —
Part 2 replaces this with SQLite, seeded once from these CSVs.

## Design decision: searching by name and city

The assignment brief asks for a hotel-name search. The instructor's data
pack documents worked test cases that search by city instead. Rather than
pick one and fail the other, the search matches a query against both
fields — a hotel-name search still works, and the data pack's documented
city-search test table (Boston, New York, Philadelphia, Washington, State
College, Miami) passes exactly as specified.

## Assignment 2 Part 1 — live hotel search

The browser sends `GET /api/live/hotels?zip=16801` to FastAPI. The
controller (`backend/live_search/controller.py`) validates the ZIP, asks the
Geoapify client (`geoapify_client.py`) to resolve it to a U.S. postcode point,
then asks for `accommodation.hotel` places within 5 km. The client keeps only
a postcode result that exactly matches the typed ZIP, normalizes places into
`PlaceResult` (provider id, name or null, address or null, coordinates,
distance), and raises distinct errors for "ZIP not found", rate limits, and
provider failures, which the controller turns into distinct status codes.
The Vue view shows the list and the Leaflet map from the same data and one
shared `selectedId`, so selecting in either place highlights the same hotel.
The Geoapify key never leaves `backend/.env`.
