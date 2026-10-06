// View-side controller: owns search state + which hotel is selected.
// Both the list and the map read `selectedId` from here, which is what keeps them in sync.
//
// Assignment 2 Part 2 -- local-first lookup:
//   entered ZIP -> our local saved-hotel lookup
//     -> saved hotels found:        show them ("Saved locally"), NO hotel-provider call
//     -> lookup OK but zero saved:  fall back to the Part 1 API search ("API results")
//     -> lookup FAILED:             show an error (a failure is never treated as empty)
import { computed, reactive, ref } from 'vue'
import { searchHotels, ZIP_PATTERN } from '../services/hotelSearchApi'
import { getLocalHotels, getSavedIds, saveHotel, removeHotel } from '../services/localHotelsApi'

export function useHotelSearch() {
  const status = ref('idle')   // idle | loading | results | empty | invalid | not_found | rate_limited | error | local_cleared
  const message = ref('')
  const result = ref(null)     // { center, radius_m, result_limit, count, hotels }
  const source = ref(null)     // 'local' | 'api'
  const selectedId = ref(null)
  const lastZip = ref('')
  const savedIds = ref(new Set())
  const pending = reactive({})        // provider_place_id -> 'add' | 'remove'
  const feedback = ref(null)          // { kind: 'ok' | 'error', text }
  let controller = null

  const hotels = computed(() => result.value?.hotels ?? [])
  const selectedHotel = computed(() => hotels.value.find(h => h.provider_place_id === selectedId.value) ?? null)

  async function refreshSavedIds() {
    try {
      savedIds.value = new Set(await getSavedIds())
    } catch (err) {
      feedback.value = { kind: 'error', text: `Couldn't load saved status: ${err.message}` }
    }
  }

  async function search(rawZip) {
    const zip = (rawZip ?? '').trim()
    lastZip.value = zip
    selectedId.value = null
    feedback.value = null

    if (!ZIP_PATTERN.test(zip)) {       // instant feedback; backend validates again
      controller?.abort()
      result.value = null
      source.value = null
      status.value = 'invalid'
      message.value = 'Enter exactly five digits, e.g. 16801 or 02134.'
      return
    }

    controller?.abort()                 // a newer search wins over a slower older one
    controller = new AbortController()
    const { signal } = controller
    status.value = 'loading'
    message.value = ''
    result.value = null
    source.value = null

    // 1) Local saved hotels first.
    let local
    try {
      local = await getLocalHotels(zip, { signal })
    } catch (err) {
      if (err.name === 'AbortError') return
      status.value = 'error'
      message.value = `Local saved-hotel lookup failed: ${err.message} (No API search was run.)`
      return
    }

    if (local.count > 0) {
      source.value = 'local'
      result.value = { center: local.center, radius_m: local.radius_m, result_limit: null,
                       count: local.count, hotels: local.hotels }
      status.value = 'results'
      for (const h of local.hotels) savedIds.value.add(h.provider_place_id)
      return
    }

    // 2) Successful empty local lookup -> existing Part 1 API search.
    try {
      const out = await searchHotels(zip, { signal })
      source.value = 'api'
      status.value = out.kind
      message.value = out.message ?? ''
      result.value = out.data ?? null
      if (out.kind === 'results') await refreshSavedIds()
    } catch (err) {
      if (err.name !== 'AbortError') {
        status.value = 'error'
        message.value = 'Something went wrong while searching.'
      }
    }
  }

  async function add(hotel) {
    if (pending[hotel.provider_place_id] || savedIds.value.has(hotel.provider_place_id)) return
    const center = result.value?.center
    if (!center) return
    pending[hotel.provider_place_id] = 'add'
    feedback.value = null
    try {
      await saveHotel(hotel, center)
      savedIds.value = new Set([...savedIds.value, hotel.provider_place_id])   // only after success
      feedback.value = { kind: 'ok', text: `Saved "${hotel.name ?? 'Unnamed place'}" locally with Oct 10–14 demo nights.` }
    } catch (err) {
      feedback.value = { kind: 'error', text: `Couldn't save "${hotel.name ?? 'Unnamed place'}": ${err.message}` }
    } finally {
      delete pending[hotel.provider_place_id]
    }
  }

  async function remove(hotel) {
    const id = hotel.provider_place_id
    if (pending[id] || !savedIds.value.has(id)) return
    pending[id] = 'remove'
    feedback.value = null
    try {
      await removeHotel(id)
      // Update the interface only after the backend confirms removal.
      const next = new Set(savedIds.value); next.delete(id); savedIds.value = next
      if (source.value === 'local' && result.value) {
        const remaining = result.value.hotels.filter(h => h.provider_place_id !== id)
        result.value = { ...result.value, hotels: remaining, count: remaining.length }
        if (selectedId.value === id) selectedId.value = null
        if (!remaining.length) status.value = 'local_cleared'
      }
      feedback.value = { kind: 'ok', text: `Removed "${hotel.name ?? 'Unnamed place'}" and its saved nights from local storage.` }
    } catch (err) {
      feedback.value = { kind: 'error', text: `Couldn't remove "${hotel.name ?? 'Unnamed place'}": ${err.message}` }
    } finally {
      delete pending[id]
    }
  }

  function select(id) {
    selectedId.value = id
  }

  return { status, message, result, source, hotels, selectedId, selectedHotel, lastZip,
           savedIds, pending, feedback, search, select, add, remove, refreshSavedIds }
}
