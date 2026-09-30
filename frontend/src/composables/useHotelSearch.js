// View-side controller: owns search state + which hotel is selected.
// Both the list and the map read `selectedId` from here, which is what keeps them in sync.
import { computed, ref } from 'vue'
import { searchHotels, ZIP_PATTERN } from '../services/hotelSearchApi'

export function useHotelSearch() {
  const status = ref('idle')   // idle | loading | results | empty | invalid | not_found | rate_limited | error
  const message = ref('')
  const result = ref(null)     // { center, radius_m, result_limit, count, hotels }
  const selectedId = ref(null)
  const lastZip = ref('')
  let controller = null

  const hotels = computed(() => result.value?.hotels ?? [])
  const selectedHotel = computed(() => hotels.value.find(h => h.provider_place_id === selectedId.value) ?? null)

  async function search(rawZip) {
    const zip = (rawZip ?? '').trim()
    lastZip.value = zip
    selectedId.value = null

    if (!ZIP_PATTERN.test(zip)) {       // instant feedback; backend validates again
      controller?.abort()
      result.value = null
      status.value = 'invalid'
      message.value = 'Enter exactly five digits, e.g. 16801 or 02134.'
      return
    }

    controller?.abort()                 // a newer search wins over a slower older one
    controller = new AbortController()
    status.value = 'loading'
    message.value = ''
    result.value = null

    try {
      const out = await searchHotels(zip, { signal: controller.signal })
      status.value = out.kind
      message.value = out.message ?? ''
      result.value = out.data ?? null
    } catch (err) {
      if (err.name !== 'AbortError') {
        status.value = 'error'
        message.value = 'Something went wrong while searching.'
      }
    }
  }

  function select(id) {
    selectedId.value = id
  }

  return { status, message, result, hotels, selectedId, selectedHotel, lastZip, search, select }
}
