<script setup>
// Steps stay fixed: thought -> evidence -> alternative. Typing is kept small (D3):
// tap a common thought, skip evidence, or ask for two optional alternative readings.
// The text typed here is NOT saved to the database (only that steps were done).
import { computed, onMounted, ref } from "vue";
import { api } from "../services/api.js";
import { isCrisisText } from "../safety.js";

const props = defineProps({ skill: Object, paused: Boolean, clock: Function, sessionId: Number });
const emit = defineEmits(["started", "step", "complete", "crisis"]);
const steps = props.skill.steps;
const idx = ref(0);
const thought = ref("");
const evidence = ref("");
const alternative = ref("");
const typing = ref(false);
const assist = ref({ state: "idle", items: [] });   // idle | loading | ready | failed
onMounted(() => emit("started"));

const step = computed(() => steps[idx.value]);

function advance() {
  for (const v of [thought.value, evidence.value, alternative.value]) if (isCrisisText(v)) emit("crisis");
  if (idx.value >= steps.length - 1) { emit("step", steps.length); emit("complete", steps.length); return; }
  idx.value += 1;
  emit("step", idx.value);
}
function pickThought(t) { thought.value = t; advance(); }

async function askAlternatives() {
  assist.value = { state: "loading", items: [] };
  try {
    if (!props.sessionId) throw new Error("no session");
    const r = await api.reframeAlternatives(props.sessionId, thought.value, evidence.value);
    if (r.crisis) { emit("crisis"); assist.value = { state: "idle", items: [] }; return; }
    assist.value = r.alternatives.length ? { state: "ready", items: r.alternatives } : { state: "failed", items: [] };
  } catch {
    assist.value = { state: "failed", items: [] };
  }
}
</script>

<template>
  <section class="exercise reframe" data-test="reframe">
    <p class="muted small">Step {{ Math.min(idx + 1, 3) }} of 3</p>

    <template v-if="step.key === 'thought'">
      <p class="instruction">{{ step.text }}</p>
      <div v-if="!typing" class="chips">
        <button v-for="c in step.chips" :key="c" class="chip" @click="pickThought(c)">{{ c }}</button>
        <button class="chip outline" data-test="type-own" @click="typing = true">Something else</button>
      </div>
      <form v-else class="col" @submit.prevent="thought.trim() && advance()">
        <input v-model="thought" maxlength="200" placeholder="A few words is enough" data-test="thought-input" />
        <button class="primary-btn" :disabled="!thought.trim()">Next</button>
      </form>
    </template>

    <template v-else-if="step.key === 'evidence'">
      <p class="quote">"{{ thought }}"</p>
      <p class="instruction">{{ step.text }}</p>
      <form class="col" @submit.prevent="advance">
        <input v-model="evidence" maxlength="200" placeholder="Optional" data-test="evidence-input" />
        <div class="row">
          <button class="primary-btn" data-test="next">{{ evidence.trim() ? "Next" : "Skip" }}</button>
        </div>
      </form>
    </template>

    <template v-else-if="step.key === 'alternative'">
      <p class="quote">"{{ thought }}"</p>
      <p class="instruction">{{ step.text }}</p>
      <div v-if="assist.state === 'ready'" class="chips col">
        <button v-for="a in assist.items" :key="a" class="chip" :class="{ picked: alternative === a }" @click="alternative = a">{{ a }}</button>
      </div>
      <p v-else-if="assist.state === 'failed'" class="muted small" data-test="assist-failed">Other readings aren't available right now. You can write your own or skip.</p>
      <button v-if="assist.state === 'idle'" class="link" data-test="assist" @click="askAlternatives">Show two possible readings (written by an AI model)</button>
      <p v-if="assist.state === 'loading'" class="muted small">Getting two readings…</p>
      <form class="col" @submit.prevent="advance">
        <input v-model="alternative" maxlength="200" placeholder="Your own words (optional)" data-test="alt-input" />
        <button class="primary-btn" data-test="next">{{ alternative.trim() ? "Next" : "Skip" }}</button>
      </form>
    </template>

    <template v-else>
      <p class="instruction">{{ step.text }}</p>
      <p v-if="alternative" class="quote">"{{ alternative }}"</p>
      <button class="primary-btn" data-test="next" @click="advance">Finish</button>
    </template>
  </section>
</template>
