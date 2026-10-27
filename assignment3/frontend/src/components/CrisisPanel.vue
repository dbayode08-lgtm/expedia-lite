<script setup>
// Static content bundled at build time: works with no backend, no model, no network.
import { onMounted, onUnmounted, ref } from "vue";
import { CRISIS } from "../safety.js";

const emit = defineEmits(["close"]);
const closeBtn = ref(null);
function onKey(e) { if (e.key === "Escape") emit("close"); }
onMounted(() => { closeBtn.value?.focus(); window.addEventListener("keydown", onKey); });
onUnmounted(() => window.removeEventListener("keydown", onKey));
</script>

<template>
  <div class="crisis-backdrop" @click.self="emit('close')">
    <section class="crisis-panel" role="dialog" aria-modal="true" aria-labelledby="crisis-h" data-test="crisis-panel">
      <h2 id="crisis-h">{{ CRISIS.heading }}</h2>
      <p>{{ CRISIS.intro }}</p>
      <ul class="crisis-list">
        <li v-for="r in CRISIS.resources" :key="r.label">
          <a :href="r.href">{{ r.label }}</a>
          <span>{{ r.detail }}</span>
        </li>
      </ul>
      <p class="muted">Anything you were doing is paused. Close this to go back to it, or leave the app.</p>
      <button ref="closeBtn" class="secondary" @click="emit('close')">Close</button>
    </section>
  </div>
</template>
