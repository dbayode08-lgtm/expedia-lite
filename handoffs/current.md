# Current handoff

_Update this file at each checkpoint._

## What works

- [ ] Backend `/api/search` reads hotels.csv/trips.csv and joins on hotel_id
- [ ] Frontend search box + button call the backend and render a table
- [ ] No-results message displays correctly
- [ ] Replaced placeholder CSVs with the instructor's real sample data

## What was checked

- [ ] Search for a hotel name known to exist in the real sample data
- [ ] Search for a name with no matches
- [ ] Confirmed both servers start cleanly following the README

## Known limitations

- No persistence — every request re-reads the CSV files from disk
- No booking, history, or CRUD yet (Part 2)

## Next task

Move to Part 2: seed SQLite from the CSVs, add booking create/read/
update(cancel)/delete through the frontend.
