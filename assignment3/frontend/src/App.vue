<script setup>
// App controls the journey: which screen is shown, saving, Stop, and Crisis support.
// The model never decides any of these (see docs/design.md).
import { computed, onMounted, ref } from "vue";
import skillsDoc from "../../shared/skills.json";
import { api } from "./services/api.js";
import { useRunTimer } from "./composables/useRunTimer.js";
import CrisisPanel from "./components/CrisisPanel.vue";
import HomeView from "./components/HomeView.vue";
import BreathingExercise from "./components/BreathingExercise.vue";
import GroundingExercise from "./components/GroundingExercise.vue";
import StopExercise from "./components/StopExercise.vue";
import ReframeExercise from "./components/ReframeExercise.vue";
import DoneView from "./components/DoneView.vue";
import StoppedView from "./components/StoppedView.vue";
import HistoryView from "./components/HistoryView.vue";

const SKILLS = Object.fromEntries(skillsDoc.skills.map((s) => [s.id, s]));
const EXERCISES = { breathing: BreathingExercise, grounding: GroundingExercise, stop: StopExercise, reframe: ReframeExercise };

function readPref(key, fallback) { try { return localStorage.getItem(key) ?? fallback; } catch { return fallback; } }
function writePref(key, val) { try { localStorage.setItem(key, val); } catch { /* per-device convenience only */ } }

const view = ref("home");               // home | exercise | done | stopped | history
const sessionId = ref(null);
const saving = ref(true);               // false when the backend can't be reached
const fewerOptions = ref(readPref("steady.fewerOptions", "0") === "1");
const crisisOpen = ref(false);
const userPaused = ref(false);
const personal = ref({ usual_skill: null });
const modelInfo = ref(null);

const skill = ref(null);
const runId = ref(null);
const stepsDone = ref(0);
const lastSummary = ref(null);
const timer = useRunTimer();

const paused = computed(() => userPaused.value || crisisOpen.value);
const canPause = computed(() => skill.value && ["timed", "timed_skippable"].includes(skill.value.mode));

async function ensureSession() {
  if (sessionId.value) return sessionId.value;
  try {
    sessionId.value = (await api.createSession(fewerOptions.value)).session_id;
    saving.value = true;
  } catch {
    saving.value = false;
  }
  return sessionId.value;
}

async function refreshPersonal() {
  try { personal.value = await api.personalization(); } catch { personal.value = { usual_skill: null }; }
}

onMounted(async () => {
  await ensureSession();
  refreshPersonal();
  try { modelInfo.value = await api.modelStatus(); } catch { modelInfo.value = null; }
});

function setFewer(v) { fewerOptions.value = v; writePref("steady.fewerOptions", v ? "1" : "0"); }

async function startSkill(id, via = "menu") {
  skill.value = SKILLS[id];
  stepsDone.value = 0;
  userPaused.value = false;
  runId.value = null;
  timer.choose();
  view.value = "exercise";
  const sid = await ensureSession();
  if (sid) {
    try { runId.value = (await api.startRun(sid, id, via)).run_id; } catch { saving.value = false; }
  }
}

function onStarted() { timer.firstInstruction(); }
function onStep(n) { stepsDone.value = n; }

function togglePause() {
  userPaused.value = !userPaused.value;
  syncTimer();
}
function syncTimer() { paused.value ? timer.pause() : timer.resume(); }

function openCrisis() { crisisOpen.value = true; syncTimer(); }
function closeCrisis() { crisisOpen.value = false; syncTimer(); }

async function finishRun(status) {
  timer.resume();
  const summary = timer.summary();
  lastSummary.value = { ...summary, skill: skill.value, status, steps: stepsDone.value };
  if (runId.value) {
    try { await api.endRun(runId.value, { status, steps_done: stepsDone.value, ...summary }); } catch { saving.value = false; }
  }
  view.value = status === "completed" ? "done" : "stopped";
  refreshPersonal();
}

function onComplete(n) { stepsDone.value = n ?? stepsDone.value; finishRun("completed"); }
function stopNow() { finishRun("stopped"); }    // R3: one tap, no confirmation, no penalty

async function sendFeedback(value) {
  if (runId.value) { try { await api.feedback(runId.value, value); } catch { /* optional */ } }
  refreshPersonal();
}

function goHome() { view.value = "home"; skill.value = null; userPaused.value = false; }
function openHistory() { view.value = "history"; }
</script>

<template>
  <div class="page" :class="{ quiet: view === 'exercise' }">
    <!-- D4 / R2: crisis access is in the header on EVERY screen, outside any model logic. -->
    <header class="topbar">
      <span class="brand">Steady <small>class prototype</small></span>
      <div class="top-actions">
        <button v-if="view === 'exercise' && canPause" class="ghost" @click="togglePause">
          {{ userPaused ? "Resume" : "Pause" }}
        </button>
        <button v-if="view === 'exercise'" class="ghost stop" data-test="stop" @click="stopNow">Stop</button>
        <button class="crisis-btn" data-test="crisis" @click="openCrisis">Crisis support</button>
      </div>
    </header>

    <main class="content">
      <HomeView
        v-if="view === 'home'"
        :skills="skillsDoc.skills"
        :session-id="sessionId"
        :saving="saving"
        :usual="personal"
        :fewer-options="fewerOptions"
        :model-info="modelInfo"
        @start="startSkill"
        @crisis="openCrisis"
        @set-fewer="setFewer"
        @history="openHistory"
      />

      <component
        :is="EXERCISES[skill.id]"
        v-else-if="view === 'exercise' && skill"
        :key="skill.id + '-' + (runId ?? 'local')"
        :skill="skill"
        :paused="paused"
        :clock="timer.activeMs"
        :session-id="sessionId"
        @started="onStarted"
        @step="onStep"
        @complete="onComplete"
        @crisis="openCrisis"
      />

      <DoneView v-else-if="view === 'done'" :summary="lastSummary" @feedback="sendFeedback" @home="goHome" />
      <StoppedView v-else-if="view === 'stopped'" :summary="lastSummary" @home="goHome" />
      <HistoryView v-else-if="view === 'history'" @home="goHome" @changed="refreshPersonal" />

      <p v-if="!saving" class="notice" data-test="not-saving">Not saving right now. Exercises still work.</p>
    </main>

    <CrisisPanel v-if="crisisOpen" @close="closeCrisis" />
  </div>
</template>
