// All HTTP to our FastAPI backend. The browser never calls a model provider directly.
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8001";

// Demo/test switch: open the app with ?simulateFailure=1 to force model failures.
const simulateFailure = new URLSearchParams(window.location.search).get("simulateFailure") === "1";

async function call(path, { method = "GET", body, timeoutMs = 9000 } = {}) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  let resp;
  try {
    resp = await fetch(`${API_BASE}${path}`, {
      method,
      signal: ctrl.signal,
      headers: {
        "Content-Type": "application/json",
        ...(simulateFailure ? { "X-Simulate-Model-Failure": "1" } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    throw new Error(err.name === "AbortError" ? "timeout" : "unreachable");
  } finally {
    clearTimeout(t);
  }
  let data = null;
  try { data = await resp.json(); } catch { /* handled below */ }
  if (!resp.ok) throw new Error(data?.detail ?? `http_${resp.status}`);
  return data;
}

export const api = {
  health: () => call("/api/health", { timeoutMs: 2500 }),
  modelStatus: () => call("/api/model/status"),
  createSession: (fewer_options) => call("/api/sessions", { method: "POST", body: { fewer_options } }),
  endSession: (id) => call(`/api/sessions/${id}/end`, { method: "POST" }),
  chat: (session_id, message) => call("/api/chat", { method: "POST", body: { session_id, message } }),
  reframeAlternatives: (session_id, thought, evidence) =>
    call("/api/reframe/alternatives", { method: "POST", body: { session_id, thought, evidence } }),
  startRun: (session_id, skill, chosen_via) => call("/api/runs", { method: "POST", body: { session_id, skill, chosen_via } }),
  endRun: (runId, payload) => call(`/api/runs/${runId}/end`, { method: "POST", body: payload }),
  feedback: (runId, feedback) => call(`/api/runs/${runId}/feedback`, { method: "POST", body: { feedback } }),
  personalization: () => call("/api/personalization"),
  history: () => call("/api/history"),
  clearHistory: () => call("/api/history", { method: "DELETE" }),
};
