"""
Expedia Lite — Part 2 database seeding.

Seeds hotels, trips, users, bookings tables from the CSVs into a SQLite
database file. Safe to run multiple times: if the database already has
a `hotels` table, seeding is skipped entirely, so restarting the app
never duplicates or reloads the starter records.

Column names are read directly from each CSV's header row, so this
works whether the real data pack's columns are named exactly like this
starter data or not — it just mirrors whatever is there.
"""
import csv
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent
DB_PATH = DATA_DIR / "expedia_lite.db"

TABLES = [
    ("hotels", "hotels.csv", "hotel_id"),
    ("trips", "trips.csv", "trip_id"),
    ("users", "users.csv", "user_id"),
    ("bookings", "bookings.csv", "booking_id"),
]


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def _load_csv_table(conn: sqlite3.Connection, table: str, csv_name: str, pk: str) -> None:
    csv_path = DATA_DIR / csv_name
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        cols_sql = ", ".join(f'"{h}" TEXT' for h in headers)
        conn.execute(f'CREATE TABLE "{table}" ({cols_sql}, PRIMARY KEY ("{pk}"))')
        col_list = ", ".join(f'"{h}"' for h in headers)
        placeholders = ", ".join("?" for _ in headers)
        rows = [[row[h] for h in headers] for row in reader]
        conn.executemany(
            f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders})', rows
        )


def seed() -> bool:
    """Seed the database if empty. Returns True if seeding ran, False if skipped."""
    conn = get_conn()
    try:
        if _table_exists(conn, "hotels"):
            return False  # already seeded — never re-seed
        for table, csv_name, pk in TABLES:
            _load_csv_table(conn, table, csv_name, pk)
        conn.commit()
        return True
    finally:
        conn.close()


if __name__ == "__main__":
    ran = seed()
    print("Seeded database." if ran else "Database already seeded — skipped.")