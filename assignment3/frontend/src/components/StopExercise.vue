<script setup>
// One letter per screen (D2). Each step moves on by itself after its time; Next moves sooner.
import { computed, onMounted, onUnmounted, ref } from "vue";

const props = defineProps({ skill: Object, paused: Boolean, clock: Function });
const emit = defineEmits(["started", "step", "complete"]);
const steps = props.skill.steps;
const idx = ref(0);
const stepStart = ref(0);
const now = ref(0);
let raf = 0, done = false;

function next() {
  if (done) return;
  if (idx.value >= steps.length - 1) { done = true; emit("step", steps.length); emit("complete", steps.length); return; }
  idx.value += 1;
  emit("step", idx.value);
  stepStart.value = props.clock();
}
function tick() {
  now.value = props.clock();
  if (now.value - stepStart.value >= steps[idx.value].seconds * 1000) next();
  if (!done) raf = requestAnimationFrame(tick);
}
onMounted(() => { emit("started"); stepStart.value = props.clock(); raf = requestAnimationFrame(tick); });
onUnmounted(() => cancelAnimationFrame(raf));

const step = computed(() => steps[idx.value]);
const progress = computed(() => Math.min(1, (now.value - stepStart.value) / (step.value.seconds * 1000)));
</script>

<template>
  <section class="exercise stop-skill" data-test="stop-skill">
    <ol class="letters" aria-hidden="true">
      <li v-for="(s, i) in steps" :key="s.letter" :class="{ on: i === idx, past: i < idx }">{{ s.letter }}</li>
    </ol>
    <h2 class="step-title">{{ step.title }}</h2>
    <p class="instruction" aria-live="polite">{{ step.text }}</p>
    <div class="bar"><div class="bar-fill" :style="{ width: progress * 100 + '%' }"></div></div>
    <p class="muted small">{{ paused ? "Paused" : "Moves on by itself" }}</p>
    <button class="secondary" data-test="next" @click="next">{{ idx === steps.length - 1 ? "Finish" : "Next" }}</button>
  </section>
</template>
