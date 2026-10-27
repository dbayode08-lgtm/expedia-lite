// Measures an exercise: setup (choice -> first instruction) and duration
// (first instruction -> final planned step) with user pauses and time in
// Crisis support excluded, as the assignment's timing rule requires.
import { ref } from "vue";

export function useRunTimer() {
  const chosenAt = ref(null);
  const startedAt = ref(null);
  const pausedMs = ref(0);
  let pauseStart = null;

  const now = () => performance.now();

  function choose() { chosenAt.value = now(); startedAt.value = null; pausedMs.value = 0; pauseStart = null; }
  function firstInstruction() { if (startedAt.value === null) startedAt.value = now(); }
  function pause() { if (pauseStart === null) pauseStart = now(); }
  function resume() { if (pauseStart !== null) { pausedMs.value += now() - pauseStart; pauseStart = null; } }
  function activeMs() {
    if (startedAt.value === null) return 0;
    const extra = pauseStart !== null ? now() - pauseStart : 0;
    return now() - startedAt.value - pausedMs.value - extra;
  }
  function summary() {
    const openPause = pauseStart !== null ? now() - pauseStart : 0;
    return {
      setup_ms: startedAt.value !== null && chosenAt.value !== null ? Math.round(startedAt.value - chosenAt.value) : null,
      duration_ms: startedAt.value !== null ? Math.max(0, Math.round(activeMs())) : null,
      paused_ms: Math.round(pausedMs.value + openPause),
    };
  }
  return { choose, firstInstruction, pause, resume, activeMs, summary };
}
