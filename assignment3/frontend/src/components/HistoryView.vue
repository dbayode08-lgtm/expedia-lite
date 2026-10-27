<script setup>
// What is saved, shown back plainly. The person can clear all of it.
import { onMounted, ref } from "vue";
import { api } from "../services/api.js";
import skillsDoc from "../../../shared/skills.json";

const emit = defineEmits(["home", "changed"]);
const names = Object.fromEntries(skillsDoc.skills.map((s) => [s.id, s.name]));
const sessions = ref([]);
const state = ref("loading");     // loading | ready | failed
const confirming = ref(false);
const open = ref({});

async function load() {
  state.value = "loading";
  try { sessions.value = (await api.history()).sessions; state.value = "ready"; } catch { state.value = "failed"; }
}
onMounted(load);

async function clearAll() {
  try { await api.clearHistory(); confirming.value = false; await load(); emit("changed"); } catch { state.value = "failed"; }
}
function fmt(ms) { if (ms == null) return ""; const s = Math.round(ms / 1000); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; }
function when(iso) { try { return new Date(iso).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }); } catch { return iso; } }
const FB = { helped: "helped a bit", not_this_time: "not this time" };
</script>

<template>
  <section class="history" data-test="history-view">
    <div class="row between">
      <h2>History</h2>
      <button class="link" @click="emit('home')">Back</button>
    </div>
    <p class="muted small">Saved on this computer only: which exercises you started, whether you finished or stopped, and the short check-in messages. Reframe answers are not saved.</p>

    <p v-if="state === 'loading'" class="muted">Loading…</p>
    <p v-else-if="state === 'failed'" class="muted">History isn't available right now.</p>
    <p v-else-if="!sessions.length" class="muted" data-test="history-empty">Nothing saved yet.</p>

    <ul v-else class="sessions">
      <li v-for="s in sessions" :key="s.id" class="session">
        <div class="muted small">{{ when(s.started_at) }}</div>
        <div v-for="r in s.runs" :key="r.id" class="run">
          <strong>{{ names[r.skill] ?? r.skill }}</strong>
          <span>{{ r.status === 'completed' ? 'finished' : r.status === 'stopped' ? 'stopped' : 'not finished' }}</span>
          <span v-if="r.duration_ms != null" class="muted">{{ fmt(r.duration_ms) }}</span>
          <span v-if="r.feedback && FB[r.feedback]" class="muted">· {{ FB[r.feedback] }}</span>
        </div>
        <button v-if="s.messages.length" class="link small" @click="open[s.id] = !open[s.id]">
          {{ open[s.id] ? "Hide" : "Show" }} check-in ({{ s.messages.length }})
        </button>
        <div v-if="open[s.id]" class="msgs">
          <div v-for="(m, i) in s.messages" :key="i" class="msg" :class="m.role">{{ m.content }}</div>
        </div>
      </li>
    </ul>

    <div v-if="state === 'ready' && sessions.length" class="clear">
      <button v-if="!confirming" class="link" data-test="clear" @click="confirming = true">Clear history</button>
      <span v-else class="row">
        <span class="small">Remove everything saved?</span>
        <button class="secondary" data-test="clear-yes" @click="clearAll">Remove</button>
        <button class="link" @click="confirming = false">Keep</button>
      </span>
    </div>
  </section>
</template>
