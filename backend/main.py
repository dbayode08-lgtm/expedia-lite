"""
Expedia Lite — Part 1 backend.

Reads hotels.csv and trips.csv from disk, joins them on hotel_id, and
exposes a single search endpoint the Vue frontend calls.

Schema (instructor sample data pack):
  hotels.csv: hotel_id, hotel_name, city, state, nightly_rate_usd
  trips.csv:  trip_id, hotel_id, trip_name, check_in, check_out

A trip's stay price is derived, not stored: nights * nightly_rate_usd,
where nights = check_out - check_in (see docs/data-readme.md).
"""
import csv
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

DATA_DIR = Path(__file__).parent
HOTELS_CSV = DATA_DIR / "hotels.csv"
TRIPS_CSV = DATA_DIR / "trips.csv"

app = FastAPI(title="Expedia Lite API")

# Allow the local Vue dev server (default Vite port) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_csv(path: Path) -> list[dict]:
    # utf-8-sig strips the byte-order mark the data pack's CSVs are saved with,
    # so it doesn't end up glued to the first column name.
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def nights_between(check_in: str, check_out: str) -> int:
    d1 = date.fromisoformat(check_in)
    d2 = date.fromisoformat(check_out)
    return (d2 - d1).days


@app.get("/api/search")
def search_hotels(query: str = Query("", description="Hotel name or city to search for")):
    """
    Case-insensitive substring match against hotel name OR city.
    Returns each matching hotel joined with all of its offered trips,
    including a derived nights count and stay price per trip.
    An empty query returns every hotel and trip.
    """
    hotels = load_csv(HOTELS_CSV)
    trips = load_csv(TRIPS_CSV)

    needle = query.strip().lower()
    if needle:
        matched_hotels = [
            h for h in hotels
            if needle in h["hotel_name"].lower() or needle in h["city"].lower()
        ]
    else:
        matched_hotels = hotels

    results = []
    for hotel in matched_hotels:
        rate = float(hotel["nightly_rate_usd"])
        hotel_trips = []
        for t in trips:
            if t["hotel_id"] != hotel["hotel_id"]:
                continue
            nights = nights_between(t["check_in"], t["check_out"])
            hotel_trips.append({
                **t,
                "nights": nights,
                "stay_price_usd": round(nights * rate, 2),
            })
        results.append({**hotel, "trips": hotel_trips})

    return {"query": query, "count": len(results), "results": results}


@app.get("/api/health")
def health():
    return {"status": "ok"}
