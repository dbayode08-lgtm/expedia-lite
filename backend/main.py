"""
Expedia Lite — Part 2 backend.

All reads and writes go through SQLite (expedia_lite.db). The database
is seeded once from the CSVs on first run (see seed.py) and never
re-seeded on restart, so bookings persist across server restarts.
"""
import sqlite3
from datetime import date, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from seed import get_conn, seed

DB_PATH = Path(__file__).parent / "expedia_lite.db"

app = FastAPI(title="Expedia Lite API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Seeds only if the database doesn't already have data — safe to
    # call on every startup, including restarts.
    seed()


def nights_between(check_in: str, check_out: str) -> int:
    d1 = date.fromisoformat(check_in)
    d2 = date.fromisoformat(check_out)
    return (d2 - d1).days


def next_id(conn: sqlite3.Connection, table: str, pk: str, prefix: str) -> str:
    """Generate the next sequential ID like B003 given existing B001, B002."""
    rows = conn.execute(f'SELECT "{pk}" FROM "{table}"').fetchall()
    max_n = 0
    for r in rows:
        val = r[pk]
        if val and val.startswith(prefix) and val[len(prefix):].isdigit():
            max_n = max(max_n, int(val[len(prefix):]))
    return f"{prefix}{max_n + 1:03d}"


# ---------- Search (Part 1 behavior, now backed by SQLite) ----------

@app.get("/api/search")
def search_hotels(query: str = Query("", description="Hotel name or city to search for")):
    conn = get_conn()
    try:
        hotels = [dict(r) for r in conn.execute("SELECT * FROM hotels").fetchall()]
        trips = [dict(r) for r in conn.execute("SELECT * FROM trips").fetchall()]
    finally:
        conn.close()

    needle = query.strip().lower()
    if needle:
        matched = [
            h for h in hotels
            if needle in h["hotel_name"].lower() or needle in h["city"].lower()
        ]
    else:
        matched = hotels

    results = []
    for hotel in matched:
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


# ---------- Bookings CRUD ----------

class BookingCreate(BaseModel):
    user_id: str
    trip_id: str


@app.get("/api/bookings")
def list_bookings():
    """All bookings, joined with trip/hotel/user details for display."""
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT b.booking_id, b.user_id, b.trip_id, b.booked_on, b.status,
                   u.display_name AS user_name,
                   t.trip_name, t.check_in, t.check_out,
                   h.hotel_name, h.city, h.state
            FROM bookings b
            JOIN users u ON u.user_id = b.user_id
            JOIN trips t ON t.trip_id = b.trip_id
            JOIN hotels h ON h.hotel_id = t.hotel_id
            ORDER BY b.booking_id
        """).fetchall()
        return {"count": len(rows), "bookings": [dict(r) for r in rows]}
    finally:
        conn.close()


@app.post("/api/bookings")
def create_booking(booking: BookingCreate):
    conn = get_conn()
    try:
        user = conn.execute(
            "SELECT 1 FROM users WHERE user_id = ?", (booking.user_id,)
        ).fetchone()
        if not user:
            raise HTTPException(404, f"User {booking.user_id} not found")
        trip = conn.execute(
            "SELECT 1 FROM trips WHERE trip_id = ?", (booking.trip_id,)
        ).fetchone()
        if not trip:
            raise HTTPException(404, f"Trip {booking.trip_id} not found")

        new_id = next_id(conn, "bookings", "booking_id", "B")
        today = datetime.now().strftime("%Y-%m-%d")
        conn.execute(
            "INSERT INTO bookings (booking_id, user_id, trip_id, booked_on, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (new_id, booking.user_id, booking.trip_id, today, "confirmed"),
        )
        conn.commit()
        return {"booking_id": new_id, "status": "confirmed"}
    finally:
        conn.close()


@app.patch("/api/bookings/{booking_id}/cancel")
def cancel_booking(booking_id: str):
    conn = get_conn()
    try:
        existing = conn.execute(
            "SELECT 1 FROM bookings WHERE booking_id = ?", (booking_id,)
        ).fetchone()
        if not existing:
            raise HTTPException(404, f"Booking {booking_id} not found")
        conn.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE booking_id = ?",
            (booking_id,),
        )
        conn.commit()
        return {"booking_id": booking_id, "status": "cancelled"}
    finally:
        conn.close()


@app.delete("/api/bookings/{booking_id}")
def delete_booking(booking_id: str):
    conn = get_conn()
    try:
        existing = conn.execute(
            "SELECT 1 FROM bookings WHERE booking_id = ?", (booking_id,)
        ).fetchone()
        if not existing:
            raise HTTPException(404, f"Booking {booking_id} not found")
        conn.execute("DELETE FROM bookings WHERE booking_id = ?", (booking_id,))
        conn.commit()
        return {"booking_id": booking_id, "deleted": True}
    finally:
        conn.close()


@app.get("/api/users")
def list_users():
    """Demo travelers, for a simple picker in the frontend booking form."""
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM users").fetchall()
        return {"users": [dict(r) for r in rows]}
    finally:
        conn.close()


@app.get("/api/health")
def health():
    return {"status": "ok"}