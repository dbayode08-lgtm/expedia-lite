<script setup>
// The circle carries the pace (4 s in, 6 s out). Timing comes from the run clock,
// so Pause / Crisis support freeze the exercise instead of letting it run on.
import { computed, onMounted, onUnmounted, ref } from "vue";

const props = defineProps({ skill: Object, paused: Boolean, clock: Function });
const emit = defineEmits(["started", "step", "complete"]);

const intro = props.skill.steps[0];
const cyc = props.skill.steps[1];
const INTRO_S = intro.seconds, IN_S = cyc.inhale, OUT_S = cyc.exhale, N = cyc.cycles;
const t = ref(0);
let raf = 0, done = false, lastStep = 0;

function tick() {
  t.value = props.clock() / 1000;
  const cyclesDone = Math.min(N, Math.max(0, Math.floor((t.value - INTRO_S) / (IN_S + OUT_S))));
  if (cyclesDone !== lastStep) { lastStep = cyclesDone; emit("step", cyclesDone); }
  if (!done && t.value >= INTRO_S + N * (IN_S + OUT_S)) { done = true; emit("complete", N); return; }
  raf = requestAnimationFrame(tick);
}
onMounted(() => { emit("started"); raf = requestAnimationFrame(tick); });
onUnmounted(() => cancelAnimationFrame(raf));

const phase = computed(() => {
  if (t.value < INTRO_S) return { name: "ready", p: 0, count: 0 };
  const inCycle = (t.value - INTRO_S) % (IN_S + OUT_S);
  if (inCycle < IN_S) return { name: "in", p: inCycle / IN_S, count: Math.floor(inCycle) + 1 };
  return { name: "out", p: (inCycle - IN_S) / OUT_S, count: Math.floor(inCycle - IN_S) + 1 };
});
const scale = computed(() => {
  const ease = (x) => 0.5 - Math.cos(Math.PI * x) / 2;
  if (phase.value.name === "ready") return 0.55;
  return phase.value.name === "in" ? 0.55 + 0.45 * ease(phase.value.p) : 1 - 0.45 * ease(phase.value.p);
});
const cycleNo = computed(() => Math.min(N, Math.floor(Math.max(0, t.value - INTRO_S) / (IN_S + OUT_S)) + 1));
const label = computed(() => (phase.value.name === "ready" ? intro.text : phase.value.name === "in" ? "Breathe in" : "Breathe out"));
</script>

<template>
  <section class="exercise breathing" data-test="breathing">
    <div class="circle-wrap" aria-hidden="true">
      <div class="circle" :style="{ transform: `scale(${scale})` }"></div>
    </div>
    <p class="instruction" aria-live="polite">{{ label }}</p>
    <p class="count" aria-hidden="true">{{ phase.name === "ready" ? "" : phase.count }}</p>
    <p class="muted small">{{ paused ? "Paused" : phase.name === "ready" ? "" : `Breath ${cycleNo} of ${N}` }}</p>
  </section>
</template>
