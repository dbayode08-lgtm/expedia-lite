# Expedia Lite

A small local travel application for IST 402 Assignment 1: search hotels and
their offered stays from CSV data (Part 1), then move to a full
SQLite-backed booking CRUD flow (Part 2).

## Project structure

```
expedia-lite/
├── backend/          FastAPI app + the instructor's sample CSVs
├── frontend/          Vue 3 + Vite app
├── docs/               design note and the data pack's own README
├── prompts/            selected prompts used with the coding agent
├── handoffs/           current.md — status handoff
├── AGENTS.md           instructions for the coding agent working in this repo
└── report.md           submission report (added at each checkpoint)
```

## Prerequisites

- Python 3.10+
- Node.js 18+ and npm

## Setup

The instructor's sample data pack (`hotels.csv`, `trips.csv`, `users.csv`,
`bookings.csv`) is already in `backend/`. `users.csv` and `bookings.csv`
aren't used until Part 2.

### Backend

```bash
cd backend
pip install -r requirements.txt --break-system-packages   # or use a venv
uvicorn main:app --reload --port 8000
```

Running at http://127.0.0.1:8000. Health check: `/api/health`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Running at http://127.0.0.1:5173. Run both servers at the same time and
open that URL.

## Part 1 behavior

- Type a hotel name or city into the search box and click Search (or press
  Enter). Matching is case-insensitive substring on both fields.
- Matching hotels and their offered trips are shown in a table, including
  nights and a derived stay price (`nights × nightly_rate_usd`).
- A message is shown when no hotel matches the query.
- An empty query returns every hotel and trip.

## A note on the search field

The assignment brief describes searching by hotel name. The instructor's
data pack (`docs/data-readme.md`) provides worked test cases that search by
**city** instead (e.g. "Boston" → trips T001, T002, T009, T010). The
backend matches a query against both `hotel_name` and `city`, so either
kind of search works and the data pack's documented test table passes
exactly — verified against all six worked examples (Boston, New York,
Philadelphia, Washington, State College, Miami/no-match).

## Data

`backend/main.py` reads `hotels.csv` and `trips.csv` from disk on every
request (`utf-8-sig` encoding, since the files carry a BOM), filters
hotels by hotel name or city, and joins each matching hotel to its trips
via `hotel_id`. Stay price is computed, not stored. No database yet —
Part 2 replaces this with SQLite, seeded from these same files.
