<script setup>
// Lightweight, optional feedback (D5). Skipping it is the default; no streaks, no scores.
import { ref } from "vue";
const props = defineProps({ summary: Object });
const emit = defineEmits(["feedback", "home"]);
const sent = ref(false);
function give(v) { sent.value = true; emit("feedback", v); }
function fmt(ms) { if (ms == null) return "–"; const s = Math.round(ms / 1000); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; }
</script>

<template>
  <section class="done" data-test="done">
    <h2>Done.</h2>
    <p class="muted">{{ summary?.skill?.name }} · {{ fmt(summary?.duration_ms) }}</p>
    <div v-if="!sent" class="chips">
      <button class="chip" data-test="fb-helped" @click="give('helped')">Helped a bit</button>
      <button class="chip" data-test="fb-not" @click="give('not_this_time')">Not this time</button>
    </div>
    <p v-else class="muted small">Noted.</p>
    <button class="secondary" data-test="home" @click="emit('home')">Back to start</button>
  </section>
</template>
