<script setup>
// R4: options, not routing. D5: "your usual" from history, no setup. D1: "Less on screen" is the user's switch.
import { computed, ref } from "vue";
import { api } from "../services/api.js";
import { isCrisisText } from "../safety.js";

const props = defineProps({
  skills: Array, sessionId: Number, saving: Boolean, usual: Object, fewerOptions: Boolean, modelInfo: Object,
});
const emit = defineEmits(["start", "crisis", "set-fewer", "history"]);

const showAll = ref(false);
const draft = ref("");
const sending = ref(false);
const exchange = ref([]);      // this visit's check-in messages
const suggested = ref(null);

const usualId = computed(() => props.usual?.usual_skill ?? null);
const usualSkill = computed(() => props.skills.find((s) => s.id === usualId.value));
const others = computed(() => props.skills.filter((s) => s.id !== usualId.value));
const compact = computed(() => props.fewerOptions && !showAll.value);
const providerLabel = computed(() => {
  const p = props.modelInfo?.effective_provider;
  if (!p) return null;
  return p === "mock" ? "Text helper: saved test responses" : p === "fail" ? "Text helper: failure test mode" : `Text helper: live model (${p})`;
});

async function send() {
  const text = draft.value.trim();
  if (!text || sending.value) return;
  if (isCrisisText(text)) emit("crisis");    // client-side check: works even if backend is down
  exchange.value.push({ role: "user", content: text });
  draft.value = "";
  sending.value = true;
  try {
    const r = await api.chat(props.sessionId, text);
    exchange.value.push({ role: "assistant", content: r.reply, source: r.source });
    suggested.value = r.suggested_skill;
    if (r.crisis) emit("crisis");
  } catch {
    exchange.value.push({ role: "assistant", content: "The text helper isn't available right now. You can pick any option below, or stop here.", source: "fallback" });
    suggested.value = null;
  } finally {
    sending.value = false;
  }
}
function nameOf(id) { return props.skills.find((s) => s.id === id)?.name; }
</script>

<template>
  <section class="home">
    <h1>What would help right now?</h1>
    <p class="muted">Each takes about a minute. You can stop at any point. Nothing is lost.</p>

    <div class="choices">
      <button v-if="usualSkill" class="choice primary" data-test="usual" @click="emit('start', usualSkill.id, 'usual')">
        <span class="choice-name">Your usual: {{ usualSkill.name }}</span>
        <span class="choice-sub">{{ usual.reason }}</span>
      </button>
      <button v-else-if="compact" class="choice primary" @click="emit('start', 'breathing', 'menu')">
        <span class="choice-name">Paced breathing</span>
        <span class="choice-sub">Breathe in 4, out 6</span>
      </button>

      <template v-if="!compact">
        <button v-for="s in others" :key="s.id" class="choice" :data-test="'skill-' + s.id" @click="emit('start', s.id, suggested === s.id ? 'suggested' : 'menu')">
          <span class="choice-name">{{ s.name }}</span>
          <span class="choice-sub">{{ s.short }}</span>
        </button>
      </template>
      <button v-else class="link" @click="showAll = true">More options</button>
    </div>

    <div v-if="!compact" class="checkin">
      <label for="checkin" class="muted">Or say what's going on, in a few words (optional)</label>
      <div v-for="(m, i) in exchange" :key="i" class="msg" :class="m.role">
        <span>{{ m.content }}</span>
        <small v-if="m.role === 'assistant' && m.source !== 'live_model'" class="src">{{ m.source === 'crisis_rule' ? 'fixed safety message' : m.source === 'fallback' ? 'fallback message' : 'test response' }}</small>
      </div>
      <button v-if="suggested" class="choice suggested" data-test="suggested" @click="emit('start', suggested, 'suggested')">
        <span class="choice-name">Start {{ nameOf(suggested) }}</span>
        <span class="choice-sub">or pick anything above</span>
      </button>
      <form class="row" @submit.prevent="send">
        <input id="checkin" v-model="draft" maxlength="500" autocomplete="off" placeholder="e.g. my chest feels tight" data-test="checkin-input" />
        <button class="secondary" :disabled="sending || !draft.trim()" data-test="checkin-send">{{ sending ? "…" : "Send" }}</button>
      </form>
    </div>

    <footer class="home-foot">
      <label class="toggle"><input type="checkbox" :checked="fewerOptions" data-test="fewer" @change="emit('set-fewer', $event.target.checked); showAll = false" /> Less on screen</label>
      <button class="link" data-test="history" @click="emit('history')">History</button>
      <span v-if="providerLabel" class="muted small">{{ providerLabel }}</span>
    </footer>
    <p class="muted small about">IST 402 coursework prototype. Not therapy, not a support service, and no one monitors it.</p>
  </section>
</template>
