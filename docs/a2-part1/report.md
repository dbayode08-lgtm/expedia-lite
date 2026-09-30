# Assignment 2 — Part 1: Live Hotel Search and Map

## 1. Project access

- **Repository:** https://github.com/dbayode08-lgtm/expedia-lite
- **Assessed commit:** `8fd9e6b06432055dd7402bb7118a2a5ba6a4f9dd` (https://github.com/dbayode08-lgtm/expedia-lite/commit/8fd9e6b06432055dd7402bb7118a2a5ba6a4f9dd)
- **Where the new code lives:**
  - `backend/live_search/` — MVC split for the live search (`models.py`, `geoapify_client.py`, `controller.py`)
  - `backend/tests/test_live_search.py` — offline checks (no API calls)
  - `frontend/src/components/HotelSearchPage.vue`, `ZipSearchForm.vue`, `HotelList.vue`, `HotelMap.vue`
  - `frontend/src/composables/useHotelSearch.js`, `frontend/src/services/hotelSearchApi.js`

### Startup and configuration

1. Get a free API key at <https://myprojects.geoapify.com> (no paid plan needed).
2. Create the key file (it is git-ignored and never committed):
   ```bash
   cd backend
   cp .env.example .env        # then paste your key after GEOAPIFY_API_KEY=
   ```
3. Backend:
   ```bash
   cd backend
   pip install -r requirements.txt     # fastapi, uvicorn, httpx, python-dotenv, pytest
   uvicorn main:app --reload --port 8000
   ```
4. Frontend (new terminal):
   ```bash
   cd frontend
   npm install                         # includes leaflet
   npm run dev
   ```
5. Open <http://127.0.0.1:5173>. The live ZIP search is at the top; the Assignment 1 sample-data search and bookings are below it and unchanged.

Endpoint: `GET /api/live/hotels?zip=16801`. The browser only ever calls our FastAPI server; the Geoapify key exists only in `backend/.env`.

## 2. Research notes

| Source | Useful | Problematic / missing | Decision for this app |
|---|---|---|---|
| Google Hotels / Google Maps hotel search — <https://www.google.com/travel/hotels> | List and map side by side; clicking a pin highlights the matching card and vice versa | Mixes sponsored results and prices into the list; hard to tell what's data vs. ads | List + map side by side with one shared selection; no prices or ratings anywhere |
| Booking.com map view — <https://www.booking.com> | Selected pin gets a stronger visual style; the popup repeats the name | Map opens as an overlay that hides the list, so you can't see both at once | Keep both visible on desktop; stack them on narrow screens |
| Airbnb search map — <https://www.airbnb.com> | Hovering/selecting a card highlights its pin; "no results" suggests changing the search | Empty map with no explanation when a request fails | Every state (loading, invalid, ZIP not found, zero results, rate limit, failure) gets its own message; failures never look like "0 results" |
| Geoapify Forward Geocoding docs — <https://apidocs.geoapify.com/docs/geocoding/forward-geocoding/> | Structured `postcode=` search with `type=postcode` and `filter=countrycode:us` | Returns a "best match" even when it isn't the exact ZIP you asked for | Backend accepts a result only if it is a U.S. postcode **equal to** the typed ZIP; otherwise it reports "ZIP not found" and runs no hotel search |
| Geoapify Places API docs — <https://apidocs.geoapify.com/docs/places/> | `categories=accommodation.hotel`, `filter=circle:lon,lat,5000`, `bias=proximity` for nearest-first, `limit` | Data comes from OpenStreetMap: many places have no name/address, and coverage is incomplete | Show "Unnamed place (no name in data)" / "Address not provided" instead of inventing; say results are not a complete inventory; cap at 50 per search |
| Geoapify pricing / usage terms — <https://www.geoapify.com/pricing/> | Free tier is enough for class use | Daily credit limit; 429 when exceeded | Search only on submit (no search-as-you-type); 429 shown as its own "rate limited" state; offline tests use mocks, not the live API |
| Leaflet docs — <https://leafletjs.com/reference.html> | `L.marker` with `keyboard: true` is focusable and fires `click` on Enter; `fitBounds`, popups, tooltips | `circleMarker` (SVG) is not keyboard-focusable | Use `divIcon` markers so pins work with Tab + Enter |
| OSM tile usage policy — <https://operations.osmfoundation.org/policies/tiles/> | Free tiles, no key needed, so no credential is in the browser | Attribution is mandatory; not meant for heavy traffic | Keep the attribution control visible (it also credits Geoapify); low-volume class use only |

## 3. Early mockup

![Early mockup](https://github.com/dbayode08-lgtm/expedia-lite/blob/8fd9e6b06432055dd7402bb7118a2a5ba6a4f9dd/docs/a2-part1/mockup.jpg?raw=true)

Mockup file: https://github.com/dbayode08-lgtm/expedia-lite/blob/8fd9e6b06432055dd7402bb7118a2a5ba6a4f9dd/docs/a2-part1/mockup.jpg

Hand sketch: ZIP form on top, one status banner for every state, list on the left, map on the right, with card ↔ pin selection and no prices or ratings.

**Timing and changes:** I started Part 1 late, so the layout and states were planned in chat right before the build, and this paper sketch was drawn from that plan after the first working version was running. The finished app matches the sketch. Details added or changed during implementation:
- Each card also shows the full address, or "Address not provided" when the data has none.
- Before any search, the map shows a U.S. overview. After an invalid or not-found ZIP it does not move anywhere new.
- Map pins became focusable markers instead of plain circles so they work with Tab + Enter.

## 4. Demo video

<https://drive.google.com/file/d/1aTZaDTs0brs4dL8J-tAdzKAnLXzIP2qk/view?usp=sharing>

Show in order: search `16801` → results in the list and on the map → click a list item (pin highlights) → click a pin (list item highlights) → Tab + Enter selection → `02134` (leading zero) → `1234` (invalid) → `00000` (ZIP not found) → stop the backend and search (failure message, not "0 results").

## 5. Verification record

### Offline checks (repeatable, no API quota used)

Run from `backend/`: `python -m pytest -q` — Geoapify is replaced by a fake transport, so these never depend on live result counts.

| Input / action | Expected | Observed (2026-09-29) |
|---|---|---|
| Normal response with a duplicate place id, one place missing an id, one missing a name | Duplicate dropped, id-less skipped, nearest first, `name: null` kept, no price/rating fields | Pass |
| ZIP `02134` | Sent to Geoapify as the string `02134` with `filter=countrycode:us`; center zip `02134` | Pass |
| `1680`, `168011`, `16a01`, empty, spaces, `16801-1234` | 400 `invalid_zip`, **no** Geoapify call made | Pass |
| Geocoder returns nothing | 404 `zip_not_found` | Pass |
| Geocoder returns a different ZIP (`16803` for `16801`) | 404, and **no** hotel search at the wrong location | Pass |
| Geocoder returns a non-U.S. result | 404 | Pass |
| Places returns zero features | 200 with `hotels: []` (true empty search) | Pass |
| Places returns 429 | 429 `rate_limited` (not an empty search) | Pass |
| Geoapify 401 / 500 / 503 | 502 `provider_error`; the key never appears in the response | Pass |
| Network timeout | 502 `provider_error` | Pass |
| Server has no key | 503 `not_configured` | Pass |

Result: **18 passed**.

### Browser checks against a mock backend (all six UI states)

| Input / action | Expected | Observed (2026-09-29) |
|---|---|---|
| `16a` | Invalid-input warning, no request | "Enter exactly five digits…" |
| ZIP not found (mock 404) | "Couldn't find U.S. ZIP code… No search was run." | Matched |
| Rate limit (mock 429) | Error banner that says it is not an empty search | Matched |
| Provider failure (mock 502) | "Search failed…" error banner | Matched |
| Zero results (mock 200, empty) | "No hotel-category places found within 5 km…" | Matched |
| 3 results | 3 list items and 3 pins; unnamed place labeled honestly | Matched |
| Click 3rd list item | That pin becomes the selected style and its popup opens | Matched |
| Click a pin | Matching list item becomes `aria-pressed=true` and scrolls into view | Matched |
| Tab to a list item, press Enter | Item selected, map follows | Matched |
| Map attribution | "© OpenStreetMap contributors \| Places: Geoapify" visible | Matched |

### Live checks (real Geoapify key, observed 2026-09-29)

| Input / action | Expected | Observed |
|---|---|---|
| ZIP `16801` | Center label mentions State College, PA 16801; hotels listed nearest first; each list name matches its map popup | 2026-09-29: 15 hotel-category places; center "State College, PA 16801, United States of America"; list starts Scholar Hotel State College (1.0 km), Ramada State College (1.0 km), Residence Inn by Marriott (1.1 km), Courtyard by Marriott (1.1 km), Hyatt Place (1.2 km); pins shown for each result; popup names match the list |
| ZIP `02134` (leading zero) | Center label mentions 02134 (Boston area); zero is kept | 2026-09-29: zero kept; center "Allston, Boston, MA 02134, United States of America"; 50 places returned, which is the per-search cap, so this is a partial list, not every hotel. Nearest first: Farrington Inn (0.3 km), Studio Allston Hotel (0.9 km), The Atlas Hotel (1.1 km). Studio Allston's address is in 02135: correct, because the search is 5 km around the ZIP's center point, not limited to addresses inside the ZIP |
| Click a hotel card in the list (live results) | Its pin turns solid blue and its popup opens with the same name | 2026-09-29: matched |
| Click a pin on the map (live results) | The matching card highlights in the list | 2026-09-29: matched |
| Keyboard only: Tab from the ZIP box to a hotel card, press Enter (ZIP 16801) | Card is selected; its pin highlights and popup opens | 2026-09-29: matched (Ramada State College selected, popup opened on the map) |
| ZIP `00000` | "Couldn't find U.S. ZIP code 00000" — no hotel list | 2026-09-29: yellow warning "Couldn't find U.S. ZIP code 00000. Check the digits and try again. No search was run."; no list, map stays on the U.S. overview (no search at some other location) |
| ZIP `1234` | Invalid-input message, no network request (DevTools → Network) | 2026-09-29: yellow warning "Enter exactly five digits, e.g. 16801 or 02134."; previous hotel list and pins cleared. (Network tab not checked live; the offline test confirms the backend also rejects it without calling Geoapify) |
| Backend stopped, search `16801` | "Couldn't reach the hotel search server" error, not "0 results" | 2026-09-29: red banner "Search failed: Couldn't reach the hotel search server. Is the backend running?"; no list, no "0 results" message |
| `git ls-files backend/.env` | Prints nothing (the key file is not tracked) | 2026-09-29: prints nothing; `git check-ignore` shows it is ignored by `.gitignore` (`.env` rule) |

### Remaining limitations

- Results come from OpenStreetMap via Geoapify: some hotels are missing, some entries have no name or address. The app says this and does not claim a complete inventory.
- At most 50 places per search.
- Distance is straight-line from the ZIP's center point returned by Geoapify, not driving distance, and not from the traveler's location.
- No saving yet (Part 2 adds the SQLite shortlist).
- OSM's public tiles are for light use only; heavy use would need a keyed tile provider.

## 6. AI disclosure and evidence log

**Tool:** Claude (Anthropic), model **Claude Opus 5.5**, used in the Claude app with access to this project folder.
**Used for:** planning, writing the backend search module and Vue components, writing the offline tests, headless-browser checks against a mock backend, and drafting this report. I reviewed the code, ran it with my own key, and recorded the live observations myself.

| Prompt excerpt (mine) | What it led to |
|---|---|
| "haven't started at all so from the beginning would be great" | First pass: a standalone FastAPI `app/` package + new Vite app with the Geoapify client, controller, and Vue list/map |
| "you should have them from project 1" | **Revised approach:** the standalone scaffold was dropped. The code was moved into the existing `expedia-lite` repo as `backend/live_search/` (matching the flat `main.py` layout) and one `<HotelSearchPage />` section in `App.vue`, leaving Assignment 1 search and bookings untouched |
| "approved" (reply to the agent's CHECK step, which listed the exact `pip install httpx python-dotenv pytest` and `npm install leaflet@^1.9.4` commands) | Dependencies added to `requirements.txt` / `package.json`; VERIFY = 18 tests pass and `npm run build` succeeds |

**Failed / revised approaches:**
1. **Standalone project → existing repo.** The first build assumed no existing code. After I pointed to my Assignment 1 project, it was ported into `expedia-lite` so Part 2 can reuse the SQLite database.
2. **Map pins were not keyboard-accessible.** Leaflet `circleMarker` pins can't receive focus, which would fail the keyboard requirement. They were replaced with `divIcon` markers (`keyboard: true`), and the browser check confirms Tab + Enter selection.
3. **First browser check failed.** The mock backend didn't serve `/api/users` and `/api/bookings`, so the existing Assignment 1 section crashed and the page was blank. Those two mock endpoints were added and the check passed. (Worth noting for later: the existing `App.vue` assumes `bookings` is always present in the response.)
