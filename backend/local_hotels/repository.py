"""MODEL (data access): save / list / remove saved API hotels in SQLite.

Rates and room counts in demo_hotel_nights are simulated classroom values,
not hotel API prices or inventory.
"""
import sqlite3
from typing import Optional

DEMO_STAY_DATES = ["2026-10-10", "2026-10-11", "2026-10-12", "2026-10-13", "2026-10-14"]


def save_hotel(conn: sqlite3.Connection, hotel: dict, center: dict) -> bool:
    """Save one API hotel + its searched-ZIP link + demo nights, in one transaction.

    Returns True if the hotel was newly saved, False if it already existed.
    Repeated saves never duplicate rows and never overwrite existing nightly
    rates/availability (INSERT OR IGNORE everywhere; demo nights insert only
    hotel_id + stay_date so the column DEFAULTs supply 10000 cents / 20 rooms).
    """
    with conn:  # BEGIN ... COMMIT, or ROLLBACK on any error
        cur = conn.execute(
            "INSERT OR IGNORE INTO saved_hotels (hotel_id, name, address, latitude, longitude) "
            "VALUES (?, ?, ?, ?, ?)",
            (hotel["provider_place_id"], hotel.get("name"), hotel.get("address"),
             hotel["lat"], hotel["lon"]),
        )
        created = cur.rowcount == 1
        conn.execute(
            "INSERT OR IGNORE INTO saved_hotel_zips "
            "(hotel_id, zip, center_lat, center_lon, center_label, distance_m) VALUES (?, ?, ?, ?, ?, ?)",
            (hotel["provider_place_id"], center["zip"], center["lat"], center["lon"],
             center.get("label"), hotel.get("distance_m")),
        )
        conn.executemany(
            "INSERT OR IGNORE INTO demo_hotel_nights (hotel_id, stay_date) VALUES (?, ?)",
            [(hotel["provider_place_id"], d) for d in DEMO_STAY_DATES],
        )
    return created


def saved_ids(conn: sqlite3.Connection) -> list[str]:
    return [r[0] for r in conn.execute("SELECT hotel_id FROM saved_hotels ORDER BY hotel_id")]


def hotels_for_zip(conn: sqlite3.Connection, zip_code: str) -> tuple[Optional[dict], list[dict]]:
    """Saved hotels linked to this ZIP, each with its dated demo nights.

    Values are read fresh from the database on every call, so edits committed
    in DB Browser ("Write Changes") show up on the next search.
    """
    rows = conn.execute(
        """SELECT h.hotel_id, h.name, h.address, h.latitude, h.longitude,
                  z.zip, z.center_lat, z.center_lon, z.center_label, z.distance_m
           FROM saved_hotel_zips z
           JOIN saved_hotels h ON h.hotel_id = z.hotel_id
           WHERE z.zip = ?
           ORDER BY z.distance_m IS NULL, z.distance_m, h.hotel_id""",
        (zip_code,),
    ).fetchall()
    if not rows:
        return None, []

    first = rows[0]
    center = {"zip": first["zip"], "lat": first["center_lat"], "lon": first["center_lon"],
              "label": first["center_label"]}

    hotels = []
    for r in rows:
        nights = conn.execute(
            "SELECT stay_date, nightly_rate_cents, rooms_available FROM demo_hotel_nights "
            "WHERE hotel_id = ? ORDER BY stay_date",
            (r["hotel_id"],),
        ).fetchall()
        hotels.append({
            "provider": "geoapify",
            "provider_place_id": r["hotel_id"],
            "name": r["name"],
            "address": r["address"],
            "lat": r["latitude"],
            "lon": r["longitude"],
            "distance_m": r["distance_m"],
            "nights": [dict(n) for n in nights],
        })
    return center, hotels


def remove_hotel(conn: sqlite3.Connection, hotel_id: str) -> bool:
    """Delete a saved hotel, its ZIP links and its demo nights together.

    Explicit deletes inside one transaction (plus ON DELETE CASCADE as a
    backstop). Returns False if the hotel wasn't saved. Other hotels' rows
    and the Assignment 1 tables are untouched.
    """
    with conn:
        exists = conn.execute("SELECT 1 FROM saved_hotels WHERE hotel_id = ?", (hotel_id,)).fetchone()
        if not exists:
            return False
        conn.execute("DELETE FROM demo_hotel_nights WHERE hotel_id = ?", (hotel_id,))
        conn.execute("DELETE FROM saved_hotel_zips WHERE hotel_id = ?", (hotel_id,))
        conn.execute("DELETE FROM saved_hotels WHERE hotel_id = ?", (hotel_id,))
    return True
