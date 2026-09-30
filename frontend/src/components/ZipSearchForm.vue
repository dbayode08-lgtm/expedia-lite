<script setup>
import { ref } from 'vue'

const props = defineProps({ busy: Boolean })
const emit = defineEmits(['search'])
const zip = ref('')

function submit() {
  emit('search', zip.value)
}
</script>

<template>
  <form class="zip-form" role="search" @submit.prevent="submit">
    <label for="zip-input">U.S. ZIP code</label>
    <div class="row">
      <input
        id="zip-input"
        v-model="zip"
        type="text"
        inputmode="numeric"
        autocomplete="postal-code"
        maxlength="5"
        placeholder="e.g. 16801"
        aria-describedby="zip-hint"
      />
      <button type="submit" :disabled="props.busy">
        {{ props.busy ? 'Searching…' : 'Find hotels' }}
      </button>
    </div>
    <p id="zip-hint" class="hint">Five digits. Shows hotel-category places within 5 km of the ZIP's center point.</p>
  </form>
</template>

<style scoped>
.zip-form { display: grid; gap: 6px; }
label { font-weight: 600; }
.row { display: flex; gap: 8px; }
input { flex: 1; max-width: 180px; padding: 8px 10px; font-size: 1rem; border: 1px solid #9aa3ad; border-radius: 6px; letter-spacing: .08em; }
button { padding: 8px 16px; font-size: 1rem; border: 0; border-radius: 6px; background: #1f5fbf; color: #fff; cursor: pointer; }
button:disabled { opacity: .6; cursor: progress; }
input:focus-visible, button:focus-visible { outline: 3px solid #f2a900; outline-offset: 2px; }
.hint { margin: 0; font-size: .85rem; color: #555; }
</style>
