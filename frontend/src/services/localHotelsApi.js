// Saved (local) hotels -- talks ONLY to our FastAPI backend (/api/local/...).
// Nightly rates and room counts are simulated classroom data from SQLite.
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

async function call(path, options = {}) {
  let resp
  try {
    resp = await fetch(`${API_BASE}${path}`, options)
  } catch (err) {
    if (err.name === 'AbortError') throw err
    throw new Error("Couldn't reach the local hotel storage server. Is the backend running?")
  }
  let body = null
  try { body = await resp.json() } catch { /* handled below */ }
  if (!resp.ok || body === null) {
    throw new Error(body?.message ?? `Local storage request failed (HTTP ${resp.status}).`)
  }
  return body
}

/** Saved hotels for a ZIP. Resolves { count, center, hotels } or THROWS on failure (never "empty"). */
export function getLocalHotels(zip, { signal } = {}) {
  return call(`/api/local/hotels?zip=${encodeURIComponent(zip)}`, { signal })
}

/** Provider IDs of every saved hotel (source of truth for saved status, survives refresh). */
export async function getSavedIds() {
  const body = await call('/api/local/saved-ids')
  return body.ids ?? []
}

export function saveHotel(hotel, center) {
  return call('/api/local/hotels', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      hotel: {
        provider_place_id: hotel.provider_place_id,
        name: hotel.name ?? null,
        address: hotel.address ?? null,
        lat: hotel.lat,
        lon: hotel.lon,
        distance_m: hotel.distance_m ?? null,
      },
      center: { zip: center.zip, lat: center.lat, lon: center.lon, label: center.label ?? null },
    }),
  })
}

export function removeHotel(hotelId) {
  return call(`/api/local/hotels/${encodeURIComponent(hotelId)}`, { method: 'DELETE' })
}
