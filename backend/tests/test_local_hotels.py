"""Offline checks for saved local hotels -- every test uses a TEMPORARY database.

Run from backend/:  python -m pytest -q
Never touches backend/expedia_lite.db.
"""
import shutil
import sqlite3

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import seed
from local_hotels.controller import router
from local_hotels.repository import DEMO_STAY_DATES
from local_hotels.schema import migrate

app = FastAPI()
app.include_router(router)

CENTER = {"zip": "16801", "lat": 40.7934, "lon": -77.86, "label": "State College, PA 16801"}
HOTEL_A = {"provider_place_id": "abc123", "name": "Hotel A", "address": "1 Main St",
           "lat": 40.79, "lon": -77.86, "distance_m": 300}
HOTEL_B = {"provider_place_id": "def456", "name": None, "address": None,
           "lat": 40.80, "lon": -77.85, "distance_m": 900}


@pytest.fixture
def client(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setattr(seed, "DB_PATH", db)
    seed.seed()                     # Assignment 1 tables from the real CSVs
    conn = seed.get_conn()
    migrate(conn)
    conn.close()
    return TestClient(app)


def rows(sql, *args):
    conn = seed.get_conn()
    try:
        return [tuple(r) for r in conn.execute(sql, args).fetchall()]
    finally:
        conn.close()


def save(client, hotel, center=CENTER):
    return client.post("/api/local/hotels", json={"hotel": hotel, "center": center})


def test_migration_is_repeatable_and_keeps_assignment1_records(client):
    before = {t: rows(f"SELECT * FROM {t}") for t in ("hotels", "trips", "users", "bookings")}
    conn = seed.get_conn()
    migrate(conn); migrate(conn)
    conn.close()
    after = {t: rows(f"SELECT * FROM {t}") for t in ("hotels", "trips", "users", "bookings")}
    assert before == after and all(before.values())


def test_schema_defaults_keys_and_foreign_key(client):
    conn = seed.get_conn()
    try:
        cols = {r["name"]: r for r in conn.execute("PRAGMA table_info(demo_hotel_nights)")}
        assert cols["nightly_rate_cents"]["dflt_value"] == "10000"
        assert cols["rooms_available"]["dflt_value"] == "20"
        assert cols["hotel_id"]["pk"] == 1 and cols["stay_date"]["pk"] == 2
        fks = conn.execute("PRAGMA foreign_key_list(demo_hotel_nights)").fetchall()
        assert fks[0]["table"] == "saved_hotels"
        with pytest.raises(sqlite3.IntegrityError):   # orphan night rejected
            conn.execute("INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES ('nope', '2026-10-10')")
        with pytest.raises(sqlite3.IntegrityError):   # bad latitude rejected
            conn.execute("INSERT INTO saved_hotels VALUES ('x', 'n', 'a', 95, 0)")
    finally:
        conn.close()


def test_empty_zip_is_a_successful_empty_lookup(client):
    r = client.get("/api/local/hotels", params={"zip": "16801"})
    assert r.status_code == 200 and r.json()["count"] == 0


def test_invalid_zip(client):
    assert client.get("/api/local/hotels", params={"zip": "123"}).status_code == 400


def test_save_creates_hotel_zip_and_five_default_nights(client):
    r = save(client, HOTEL_A)
    assert r.status_code == 201 and r.json()["created"] is True
    assert rows("SELECT * FROM saved_hotels") == [("abc123", "Hotel A", "1 Main St", 40.79, -77.86)]
    assert rows("SELECT hotel_id, zip FROM saved_hotel_zips") == [("abc123", "16801")]
    assert rows("SELECT stay_date, nightly_rate_cents, rooms_available FROM demo_hotel_nights ORDER BY stay_date") == \
        [(d, 10000, 20) for d in DEMO_STAY_DATES]

    body = client.get("/api/local/hotels", params={"zip": "16801"}).json()
    assert body["count"] == 1 and body["center"]["zip"] == "16801"
    assert [n["stay_date"] for n in body["hotels"][0]["nights"]] == DEMO_STAY_DATES
    assert client.get("/api/local/saved-ids").json() == {"ids": ["abc123"]}


def test_repeat_save_does_not_duplicate_or_overwrite(client):
    save(client, HOTEL_A)
    conn = seed.get_conn()
    conn.execute("UPDATE demo_hotel_nights SET nightly_rate_cents=500, rooms_available=10 "
                 "WHERE hotel_id='abc123' AND stay_date='2026-10-10'")
    conn.commit(); conn.close()

    r = save(client, {**HOTEL_A, "name": "Renamed"})
    assert r.status_code == 201 and r.json()["created"] is False
    assert rows("SELECT COUNT(*) FROM saved_hotels") == [(1,)]
    assert rows("SELECT COUNT(*) FROM demo_hotel_nights") == [(5,)]
    assert rows("SELECT nightly_rate_cents, rooms_available FROM demo_hotel_nights "
                "WHERE stay_date='2026-10-10'") == [(500, 10)]
    # and the edited value is what the lookup returns
    night = client.get("/api/local/hotels", params={"zip": "16801"}).json()["hotels"][0]["nights"][0]
    assert night == {"stay_date": "2026-10-10", "nightly_rate_cents": 500, "rooms_available": 10}


def test_remove_deletes_only_that_hotels_rows(client):
    save(client, HOTEL_A); save(client, HOTEL_B)
    a1_before = rows("SELECT * FROM bookings")
    r = client.delete("/api/local/hotels/def456")
    assert r.status_code == 200
    assert rows("SELECT hotel_id FROM saved_hotels") == [("abc123",)]
    assert rows("SELECT COUNT(*) FROM demo_hotel_nights WHERE hotel_id='def456'") == [(0,)]
    assert rows("SELECT COUNT(*) FROM saved_hotel_zips WHERE hotel_id='def456'") == [(0,)]
    assert rows("SELECT COUNT(*) FROM demo_hotel_nights WHERE hotel_id='abc123'") == [(5,)]
    assert rows("SELECT * FROM bookings") == a1_before
    assert client.delete("/api/local/hotels/def456").status_code == 404


def test_storage_failure_is_an_error_not_empty(client, monkeypatch, tmp_path):
    monkeypatch.setattr(seed, "DB_PATH", tmp_path / "missing_dir" / "x.db")
    r = client.get("/api/local/hotels", params={"zip": "16801"})
    assert r.status_code == 500 and r.json()["error"] == "local_storage_error"
