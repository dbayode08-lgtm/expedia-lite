// Talks ONLY to our FastAPI backend. No Geoapify key or URL lives in the frontend.
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'   // same backend as App.vue

export const ZIP_PATTERN = /^\d{5}$/

/**
 * Returns one of:
 *   { kind: 'results', data }      -- 200 with >= 1 hotel
 *   { kind: 'empty', data }        -- 200 with 0 hotels (real, successful search)
 *   { kind: 'invalid', message }   -- 400
 *   { kind: 'not_found', message } -- 404, ZIP not established
 *   { kind: 'rate_limited', message } -- 429
 *   { kind: 'error', message }     -- anything else (network, 5xx, bad JSON)
 */
export async function searchHotels(zip, { signal } = {}) {
  let resp
  try {
    resp = await fetch(`${API_BASE}/api/live/hotels?zip=${encodeURIComponent(zip)}`, { signal })
  } catch (err) {
    if (err.name === 'AbortError') throw err
    return { kind: 'error', message: "Couldn't reach the hotel search server. Is the backend running?" }
  }

  let body = null
  try {
    body = await resp.json()
  } catch {
    return { kind: 'error', message: `The server sent an unreadable response (HTTP ${resp.status}).` }
  }

  if (resp.ok) {
    if (!Array.isArray(body?.hotels)) {
      return { kind: 'error', message: 'The server response was missing the hotel list.' }
    }
    return { kind: body.hotels.length ? 'results' : 'empty', data: body }
  }

  const message = body?.message ?? `Search failed (HTTP ${resp.status}).`
  switch (resp.status) {
    case 400: return { kind: 'invalid', message }
    case 404: return { kind: 'not_found', message }
    case 429: return { kind: 'rate_limited', message }
    default:  return { kind: 'error', message }
  }
}
