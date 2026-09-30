<script setup>
import { nextTick, watch } from 'vue'

const props = defineProps({
  hotels: { type: Array, required: true },
  selectedId: { type: String, default: null },
})
const emit = defineEmits(['select'])

function km(m) {
  return m == null ? null : (m / 1000).toFixed(1)
}

// When the map selects a hotel, scroll it into view in the list.
watch(() => props.selectedId, async id => {
  if (!id) return
  await nextTick()
  document.getElementById(`hotel-${CSS.escape(id)}`)?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
})
</script>

<template>
  <ol class="hotel-list" aria-label="Hotels near this ZIP code">
    <li v-for="h in props.hotels" :key="h.provider_place_id">
      <button
        :id="`hotel-${h.provider_place_id}`"
        type="button"
        class="hotel"
        :class="{ selected: h.provider_place_id === props.selectedId }"
        :aria-pressed="h.provider_place_id === props.selectedId"
        @click="emit('select', h.provider_place_id)"
      >
        <span class="name" :class="{ missing: !h.name }">{{ h.name ?? 'Unnamed place (no name in data)' }}</span>
        <span v-if="h.address" class="addr">{{ h.address }}</span>
        <span v-else class="addr missing">Address not provided</span>
        <span v-if="km(h.distance_m) !== null" class="dist">{{ km(h.distance_m) }} km from ZIP center</span>
      </button>
    </li>
  </ol>
</template>

<style scoped>
.hotel-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }
.hotel { width: 100%; text-align: left; display: grid; gap: 2px; padding: 10px 12px; border: 1px solid #d5dae0; border-radius: 8px; background: #fff; cursor: pointer; font: inherit; }
.hotel:hover { border-color: #1f5fbf; }
.hotel.selected { border: 2px solid #1f5fbf; background: #eaf1fd; }
.hotel:focus-visible { outline: 3px solid #f2a900; outline-offset: 2px; }
.name { font-weight: 600; }
.addr, .dist { font-size: .88rem; color: #444; }
.missing { font-style: italic; color: #777; font-weight: normal; }
</style>
