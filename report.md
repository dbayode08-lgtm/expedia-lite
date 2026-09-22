# Expedia Lite — Part 2

## Repository and commit

Repository: https://github.com/dbayode08-lgtm/expedia-lite
Commit: 38f0be3ff8f9029db8ab265113b37d63ac328777

## Implementation

All reads and writes now go through SQLite (`backend/expedia_lite.db`) instead of the CSV files used in Part 1. `backend/seed.py` seeds the database once from `hotels.csv`, `trips.csv`, `users.csv`, and `bookings.csv` on first run; it checks whether a `hotels` table already exists and skips seeding entirely if so, so restarting the app never re-seeds or duplicates the starter records.

`backend/main.py` adds four booking endpoints on top of the existing search: `POST /api/bookings` (create), `GET /api/bookings` (read, joined with trip/hotel/user details for display), `PATCH /api/bookings/{id}/cancel` (update — sets status to "cancelled" but keeps the record), and `DELETE /api/bookings/{id}` (delete). New booking IDs are generated sequentially (e.g. B007) based on the highest existing ID, so seeded IDs are preserved and new ones never collide.

The frontend (`frontend/src/App.vue`) adds a "Booking as:" traveler picker, a Book button on each search result trip, and a Booking History table below search results with Cancel and Delete buttons per row (Cancel only shows for non-cancelled bookings).

## Verification

| Action | Expected | Observed |
|---|---|---|
| Create a booking (search → Book) | New row appears in Booking History with status "confirmed" | Matched — see screenshot below (B007 created and confirmed) |
| Read booking history | All bookings display with correct hotel/trip/traveler details, joined from 3 tables | Matched — see screenshot below |
| Cancel a booking | Status changes to "cancelled"; Cancel button disappears, only Delete remains | Matched — screenshot below shows B002 and B006 already in "cancelled" status with only the Delete button visible for those rows, confirming the UI correctly reflects cancelled state |
| Delete a booking | Row disappears from the table entirely | Matched (tested via UI: booking removed from table immediately) |
| Browser refresh | Newly created booking persists after reload | Matched |
| Full restart (both backend and frontend servers stopped and restarted) | All bookings — seeded and newly added — persist with correct status; no duplication; no re-seeding | Matched — see screenshot below (7 bookings shown after a full restart, including B007 created earlier in the session) |

Screenshot: `docs/screenshots/part2-persistence.png`

I also verified all four CRUD operations directly against the backend via curl before testing through the UI, confirming correct JSON responses and proper 404 handling for a nonexistent booking ID.

## Project context and next steps

- [README](https://github.com/dbayode08-lgtm/expedia-lite/blob/main/README.md)
- [AGENTS.md](https://github.com/dbayode08-lgtm/expedia-lite/blob/main/AGENTS.md)
- [Design note](https://github.com/dbayode08-lgtm/expedia-lite/blob/main/docs/design-note.md)
- [Selected prompts](https://github.com/dbayode08-lgtm/expedia-lite/tree/main/prompts)
- [Current handoff](https://github.com/dbayode08-lgtm/expedia-lite/blob/main/handoffs/current.md)

**Changes since Part 1:** Replaced direct CSV reads with a seeded SQLite database. Added full booking CRUD (create, read, update/cancel, delete) through the frontend. Verified persistence across both browser refresh and full server restart.

**Limitations:** No authentication — the traveler picker is a simple dropdown of demo users rather than real login. No editing of an existing booking's dates or trip, only cancel/delete.

**Next task:** None remaining for this assignment — Parts 1 and 2 are both complete.