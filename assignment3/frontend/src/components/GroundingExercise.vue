<script setup>
// D3: no typing. The person notices silently and taps once per step.
import { computed, onMounted, ref } from "vue";

const props = defineProps({ skill: Object, paused: Boolean, clock: Function });
const emit = defineEmits(["started", "step", "complete"]);
const steps = props.skill.steps;
const idx = ref(0);
onMounted(() => emit("started"));

function next() {
  if (idx.value >= steps.length - 1) { emit("step", steps.length); emit("complete", steps.length); return; }
  idx.value += 1;
  emit("step", idx.value);
}
const step = computed(() => steps[idx.value]);
</script>

<template>
  <section class="exercise grounding" data-test="grounding">
    <p class="big-number" aria-hidden="true">{{ step.count }}</p>
    <p class="instruction" aria-live="polite">{{ step.text }}</p>
    <p class="muted small">No need to write anything. Tap when you're ready.</p>
    <button class="primary-btn" data-test="next" @click="next">{{ idx === steps.length - 1 ? "Finish" : "Next" }}</button>
    <p class="muted small">{{ idx + 1 }} of {{ steps.length }}</p>
  </section>
</template>
