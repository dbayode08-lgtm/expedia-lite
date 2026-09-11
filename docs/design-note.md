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
