<script setup>
import ZipSearchForm from './ZipSearchForm.vue'
import HotelList from './HotelList.vue'
import HotelMap from './HotelMap.vue'
import { useHotelSearch } from '../composables/useHotelSearch'

const { status, message, result, hotels, selectedId, lastZip, search, select } = useHotelSearch()
</script>

<template>
  <section class="hotel-search">
    <header>
      <h2>Live hotel search by ZIP</h2>
      <ZipSearchForm :busy="status === 'loading'" @search="search" />
    </header>

    <!-- One live region announces every state change to screen readers. -->
    <div class="status" role="status" aria-live="polite">
      <p v-if="status === 'idle'" class="note">Enter a ZIP code to see nearby hotel-category places.</p>
      <p v-else-if="status === 'loading'" class="note">Looking up {{ lastZip }} and nearby hotels…</p>
      <p v-else-if="status === 'invalid'" class="warn">⚠ {{ message }}</p>
      <p v-else-if="status === 'not_found'" class="warn">⚠ {{ message }} Check the digits and try again. No search was run.</p>
      <p v-else-if="status === 'empty'" class="note">
        No hotel-category places found within 5 km of ZIP {{ result.center.zip }}'s center point.
        That's a successful search with zero results — the data source may simply have no hotels mapped here.
      </p>
      <p v-else-if="status === 'rate_limited'" class="error">⛔ {{ message }} (This is not an empty search.)</p>
      <p v-else-if="status === 'error'" class="error">⛔ Search failed: {{ message }}</p>
      <p v-else-if="status === 'results'" class="note">
        {{ result.count }} hotel-category place{{ result.count === 1 ? '' : 's' }} within 5 km of
        ZIP {{ result.center.zip }}<span v-if="result.center.label"> ({{ result.center.label }})</span>.
        <span class="sub">Location data from Geoapify/OpenStreetMap — not a complete inventory and not proof of room availability.
          Up to {{ result.result_limit }} results shown.</span>
      </p>
    </div>

    <div class="layout">
      <div class="list-pane">
        <HotelList v-if="status === 'results'" :hotels="hotels" :selected-id="selectedId" @select="select" />
      </div>
      <div class="map-pane">
        <HotelMap
          :center="result?.center ?? null"
          :radius-m="result?.radius_m ?? 5000"
          :hotels="hotels"
          :selected-id="selectedId"
          @select="select"
        />
      </div>
    </div>
  </section>
</template>

<style scoped>
.hotel-search { padding: 0; display: grid; gap: 12px; font-family: system-ui, sans-serif; color: #1b1f24; }
h2 { margin: 0 0 8px; }
.status p { margin: 0; padding: 10px 12px; border-radius: 6px; }
.note { background: #f3f5f8; }
.warn { background: #fff4d6; border: 1px solid #e0b43a; }
.error { background: #fde8e6; border: 1px solid #d0473b; }
.sub { display: block; font-size: .82rem; color: #555; margin-top: 4px; }
.layout { display: grid; grid-template-columns: minmax(260px, 380px) 1fr; gap: 12px; height: 70vh; }
.list-pane { overflow-y: auto; padding-right: 4px; }
.map-pane { min-height: 360px; }
@media (max-width: 760px) {
  .layout { grid-template-columns: 1fr; height: auto; }
  .list-pane { max-height: 40vh; }
  .map-pane { height: 50vh; }
}
</style>
