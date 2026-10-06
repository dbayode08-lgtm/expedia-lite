<script setup>
import ZipSearchForm from './ZipSearchForm.vue'
import HotelList from './HotelList.vue'
import HotelMap from './HotelMap.vue'
import { onMounted } from 'vue'
import { useHotelSearch } from '../composables/useHotelSearch'

const { status, message, result, source, hotels, selectedId, lastZip, savedIds, pending, feedback,
        search, select, add, remove, refreshSavedIds } = useHotelSearch()

onMounted(refreshSavedIds)   // saved status comes from the database, so it survives a page refresh
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
      <p v-else-if="status === 'local_cleared'" class="note">
        No saved hotels remain for ZIP {{ lastZip }}. Search again to see API results.
      </p>
      <p v-else-if="status === 'results' && source === 'local'" class="note">
        <span class="badge local">Saved locally</span>
        {{ result.count }} saved hotel{{ result.count === 1 ? '' : 's' }} for ZIP {{ result.center.zip }}<span v-if="result.center.label"> ({{ result.center.label }})</span>.
        <span class="sub">Read from your local database — no hotel-provider lookup was made. This is only the subset you saved,
          not a complete list of hotels in the area. Nightly rates and rooms are simulated classroom data.</span>
      </p>
      <p v-else-if="status === 'results'" class="note">
        <span class="badge api">API results</span>
        {{ result.count }} hotel-category place{{ result.count === 1 ? '' : 's' }} within 5 km of
        ZIP {{ result.center.zip }}<span v-if="result.center.label"> ({{ result.center.label }})</span>.
        <span class="sub">Location data from Geoapify/OpenStreetMap — not a complete inventory and not proof of room availability.
          Up to {{ result.result_limit }} results shown.</span>
      </p>
    </div>

    <p v-if="feedback" :class="feedback.kind === 'ok' ? 'ok' : 'error'" role="alert">{{ feedback.text }}</p>

    <div class="layout">
      <div class="list-pane">
        <HotelList
          v-if="status === 'results'"
          :hotels="hotels"
          :selected-id="selectedId"
          :saved-ids="savedIds"
          :pending="pending"
          @select="select"
          @add="add"
          @remove="remove"
        />
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
.ok { margin: 0; padding: 8px 12px; border-radius: 6px; background: #e6f4ea; border: 1px solid #1a7f37; }
.badge { display: inline-block; font-size: .78rem; font-weight: 700; padding: 2px 8px; border-radius: 999px; margin-right: 6px; }
.badge.local { background: #1a7f37; color: #fff; }
.badge.api { background: #1f5fbf; color: #fff; }
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
