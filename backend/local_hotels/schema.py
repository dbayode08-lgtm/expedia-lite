"""MODEL (schema): additive, repeatable migration for saved API hotels.

Safe on the existing expedia_lite.db and on a fresh one: every statement is
CREATE ... IF NOT EXISTS, and nothing touches the Assignment 1 tables
(hotels, trips, users, bookings) or their records.

Tables
  saved_hotels       one row per API hotel, keyed by the provider's ID
  saved_hotel_zips   which searched ZIP(s) a saved hotel belongs to, plus the
                     ZIP's center point so local results can redraw the map
  demo_hotel_nights  one row per hotel per night: simulated classroom rate
                     (cents) and rooms available. NOT data from the hotel API.
"""
import sqlite3

DEFAULT_RATE_CENTS = 10000   # $100.00 / night -- fictional classroom default
DEFAULT_ROOMS = 20           # fictional classroom default

SCHEMA_SQL = f"""
CREATE TABLE IF NOT EXISTS saved_hotels (
    hotel_id   TEXT PRIMARY KEY NOT NULL CHECK (length(hotel_id) > 0),  -- Geoapify place_id, stored exactly
    name       TEXT,                                                    -- NULL when the API has no name
    address    TEXT,                                                    -- NULL when the API has no address
    latitude   REAL NOT NULL CHECK (latitude  BETWEEN -90  AND 90),
    longitude  REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180)
);

CREATE TABLE IF NOT EXISTS saved_hotel_zips (
    hotel_id     TEXT NOT NULL REFERENCES saved_hotels(hotel_id) ON DELETE CASCADE,
    zip          TEXT NOT NULL CHECK (length(zip) = 5 AND zip NOT GLOB '*[^0-9]*'),
    center_lat   REAL NOT NULL CHECK (center_lat BETWEEN -90  AND 90),
    center_lon   REAL NOT NULL CHECK (center_lon BETWEEN -180 AND 180),
    center_label TEXT,
    distance_m   INTEGER,
    PRIMARY KEY (hotel_id, zip)
);

CREATE TABLE IF NOT EXISTS demo_hotel_nights (
    hotel_id           TEXT NOT NULL REFERENCES saved_hotels(hotel_id) ON DELETE CASCADE,
    stay_date          TEXT NOT NULL CHECK (stay_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
                                            AND date(stay_date) = stay_date),
    nightly_rate_cents INTEGER NOT NULL DEFAULT {DEFAULT_RATE_CENTS} CHECK (nightly_rate_cents >= 0),
    rooms_available    INTEGER NOT NULL DEFAULT {DEFAULT_ROOMS} CHECK (rooms_available >= 0),
    PRIMARY KEY (hotel_id, stay_date)
);

CREATE INDEX IF NOT EXISTS idx_saved_hotel_zips_zip ON saved_hotel_zips(zip);
"""


def migrate(conn: sqlite3.Connection) -> None:
    """Create the Part 2 tables if they don't exist yet. Repeatable."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()
