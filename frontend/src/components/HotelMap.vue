<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  center: { type: Object, default: null },   // { lat, lon, zip, label }
  radiusM: { type: Number, default: 5000 },
  hotels: { type: Array, required: true },
  selectedId: { type: String, default: null },
})
const emit = defineEmits(['select'])

const mapEl = ref(null)
let map = null
let layer = null
const markers = new Map()   // provider_place_id -> L.Marker

// divIcon markers: no image assets, and (unlike circle markers) they are
// keyboard-focusable -- Tab to a pin, press Enter to select it.
const pin = on => L.divIcon({ className: on ? 'hotel-pin selected' : 'hotel-pin', iconSize: on ? [22, 22] : [16, 16] })

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))
}

function draw() {
  if (!map) return
  layer.clearLayers()
  markers.clear()
  if (!props.center) return

  const c = [props.center.lat, props.center.lon]
  L.circle(c, { radius: props.radiusM, color: '#888', weight: 1, dashArray: '4 4', fill: false, interactive: false }).addTo(layer)
  L.marker(c, { title: `ZIP ${props.center.zip} center`, keyboard: false, interactive: false,
    icon: L.divIcon({ className: 'zip-center', html: '✕', iconSize: [16, 16] }) }).addTo(layer)

  const bounds = L.latLngBounds([c])
  for (const h of props.hotels) {
    const label = h.name ?? 'Unnamed place'
    const m = L.marker([h.lat, h.lon], { icon: pin(false), keyboard: true, title: label, alt: label })
      .bindTooltip(escapeHtml(label))
      .bindPopup(`<strong>${escapeHtml(label)}</strong>${h.address ? `<br>${escapeHtml(h.address)}` : ''}`)
      .on('click', () => emit('select', h.provider_place_id))
      .addTo(layer)
    markers.set(h.provider_place_id, m)
    bounds.extend([h.lat, h.lon])
  }
  map.fitBounds(bounds.pad(0.15), { maxZoom: 15 })
  highlight()
}

function highlight() {
  for (const [id, m] of markers) {
    const on = id === props.selectedId
    m.setIcon(pin(on))
    m.setZIndexOffset(on ? 1000 : 0)
    if (on) {
      map.panTo(m.getLatLng())
      m.openPopup()
    }
  }
}

onMounted(() => {
  map = L.map(mapEl.value, { keyboard: true }).setView([39.8, -98.6], 4)   // continental U.S. until a search
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | Places: <a href="https://www.geoapify.com/">Geoapify</a>',
  }).addTo(map)
  layer = L.layerGroup().addTo(map)
  draw()
})

onBeforeUnmount(() => map?.remove())

watch(() => [props.center, props.hotels], draw)
watch(() => props.selectedId, highlight)
</script>

<template>
  <div ref="mapEl" class="map" role="region" aria-label="Map of hotel results"></div>
</template>

<style scoped>
.map { width: 100%; height: 100%; min-height: 360px; border-radius: 8px; border: 1px solid #d5dae0; }
:global(.hotel-pin) { background: #fff; border: 3px solid #1f5fbf; border-radius: 50%; box-sizing: border-box; }
:global(.hotel-pin.selected) { background: #1f5fbf; border-color: #0b3d91; box-shadow: 0 0 0 3px rgba(31,95,191,.35); }
:global(.hotel-pin:focus-visible) { outline: 3px solid #f2a900; outline-offset: 2px; }
:global(.zip-center) { color: #c0392b; font-weight: 700; font-size: 16px; line-height: 16px; text-align: center; }
</style>
