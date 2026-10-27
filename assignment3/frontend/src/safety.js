// Same crisis patterns as the backend (shared/crisis.json), checked in the browser
// too, so crisis-like text opens Crisis support even if the backend is down.
import crisis from "../../shared/crisis.json";

export const CRISIS = crisis;
const patterns = crisis.patterns.map((p) => new RegExp(p, "i"));

export function isCrisisText(text) {
  const t = (text || "").replace(/[‘’]/g, "'");
  return patterns.some((rx) => rx.test(t));
}
