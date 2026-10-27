<script setup>
// R3: leaving costs nothing. No "are you sure", no lost progress message, no nudge back.
defineProps({ summary: Object });
const emit = defineEmits(["home"]);
</script>

<template>
  <section class="done" data-test="stopped">
    <h2>Stopped.</h2>
    <p class="muted">That's fine. Nothing else is needed.</p>
    <button class="secondary" data-test="home" @click="emit('home')">Back to start</button>
    <p class="muted small">You can also just close this window.</p>
  </section>
</template>
