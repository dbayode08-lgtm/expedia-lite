<script setup>
import { nextTick, watch } from 'vue'

const props = defineProps({
  hotels: { type: Array, required: true },
  selectedId: { type: String, default: null },
  savedIds: { type: Set, default: () => new Set() },
  pending: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['select', 'add', 'remove'])

function km(m) {
  return m == null ? null : (m / 1000).toFixed(1)
}

function dollars(cents) {
  return `$${(cents / 100).toFixed(2)}`
}

function shortDate(iso) {
  return new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })
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
    <li
      v-for="h in props.hotels"
      :key="h.provider_place_id"
      class="card"
      :class="{ selected: h.provider_place_id === props.selectedId }"
    >
      <button
        :id="`hotel-${h.provider_place_id}`"
        type="button"
        class="hotel"
        :aria-pressed="h.provider_place_id === props.selectedId"
        @click="emit('select', h.provider_place_id)"
      >
        <span class="name" :class="{ missing: !h.name }">{{ h.name ?? 'Unnamed place (no name in data)' }}</span>
        <span v-if="h.address" class="addr">{{ h.address }}</span>
        <span v-else class="addr missing">Address not provided</span>
        <span v-if="km(h.distance_m) !== null" class="dist">{{ km(h.distance_m) }} km from ZIP center</span>
      </button>

      <table v-if="h.nights?.length" class="nights">
        <caption>Simulated classroom rates &amp; availability (not hotel API data)</caption>
        <thead><tr><th scope="col">Night</th><th scope="col">Rate</th><th scope="col">Rooms</th></tr></thead>
        <tbody>
          <tr v-for="n in h.nights" :key="n.stay_date">
            <td><time :datetime="n.stay_date">{{ shortDate(n.stay_date) }}</time> <span class="iso">{{ n.stay_date }}</span></td>
            <td>{{ dollars(n.nightly_rate_cents) }}</td>
            <td>{{ n.rooms_available }}</td>
          </tr>
        </tbody>
      </table>

      <div class="actions">
        <template v-if="props.savedIds.has(h.provider_place_id)">
          <button type="button" class="add" disabled>✓ Saved</button>
          <button
            type="button"
            class="remove"
            :disabled="!!props.pending[h.provider_place_id]"
            :aria-label="`Remove ${h.name ?? 'unnamed place'} from local storage`"
            @click="emit('remove', h)"
          >{{ props.pending[h.provider_place_id] === 'remove' ? 'Removing…' : 'Remove from Local' }}</button>
        </template>
        <button
          v-else
          type="button"
          class="add"
          :disabled="!!props.pending[h.provider_place_id]"
          :aria-label="`Add ${h.name ?? 'unnamed place'} to local storage`"
          @click="emit('add', h)"
        >{{ props.pending[h.provider_place_id] === 'add' ? 'Saving…' : 'Add to Local' }}</button>
      </div>
    </li>
  </ol>
</template>

<style scoped>
.hotel-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }
.card { border: 1px solid #d5dae0; border-radius: 8px; background: #fff; overflow: hidden; }
.card:hover { border-color: #1f5fbf; }
.card.selected { border: 2px solid #1f5fbf; background: #eaf1fd; }
.hotel { width: 100%; text-align: left; display: grid; gap: 2px; padding: 10px 12px; border: 0; background: transparent; cursor: pointer; font: inherit; }
.hotel:focus-visible, .actions button:focus-visible { outline: 3px solid #f2a900; outline-offset: 2px; }
.name { font-weight: 600; }
.addr, .dist { font-size: .88rem; color: #444; }
.missing { font-style: italic; color: #777; font-weight: normal; }
.nights { width: calc(100% - 24px); margin: 0 12px 8px; border-collapse: collapse; font-size: .85rem; }
.nights caption { text-align: left; font-size: .75rem; color: #8a5a00; padding-bottom: 2px; }
.nights th, .nights td { border-bottom: 1px solid #e3e6ea; padding: 3px 4px; text-align: left; }
.iso { color: #888; font-size: .75rem; }
.actions { display: flex; gap: 6px; padding: 0 12px 10px; }
.actions button { font: inherit; font-size: .85rem; padding: 5px 10px; border-radius: 6px; cursor: pointer; }
.add { border: 1px solid #1a7f37; background: #fff; color: #1a7f37; }
.remove { border: 1px solid #b00020; background: #fff; color: #b00020; }
.actions button:disabled { opacity: .55; cursor: not-allowed; }
</style>
