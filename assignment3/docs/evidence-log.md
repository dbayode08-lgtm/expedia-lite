# Evidence log (curated, redacted)

Connects selected prompts, changes, tests/browser observations and decisions. No keys, personal data or participant data. Full chat export not included.

| # | Date | Prompt / trigger | Change | Evidence | Decision |
|---|---|---|---|---|---|
| 1 | Oct 26 | Me → Claude: *"This is a 3 part and I haven't done any. Need all done by tonight… let me know what you need and you can take over my computer"* + the Assignment 3 brief | Agent read `~/Documents/expedia-lite` (README, AGENTS.md, handoff, A2 code) | List of reusable patterns (see README "Reused") | Build A3 as `assignment3/` inside the same repo on a new branch, so reuse is visible and the existing GitHub remote works |
| 2 | Oct 26 | Agent asked which model the class RAG activity used. I didn't know | Model layer made provider-pluggable: `mock` (default), `openai`, `anthropic`, `fail` | `backend/.env.example` | Default to mock. Live checks need a key (see evaluation §4) |
| 3 | Oct 26 | Design from R/D table | `shared/skills.json` planned durations 63/54/42/65 s | `test_every_skill_planned_within_90_seconds` | 6 breathing cycles, not 9 (R1: ~60 s comfortable) |
| 4 | Oct 26 | First browser walkthrough (`e2e/browser-check.cjs`) | — | Breathing measured `duration_ms` 63008 with `paused_ms` 4097 after 4 s in Crisis support | Timer excludes crisis time as the brief requires. Confirmed in DB |
| 5 | Oct 26 | Same walkthrough: DB check after the run | — | A reframe run in a closed tab stayed `status='started'` forever (shown as "not finished") | **Revised:** creating the next session marks leftover `started` runs as `stopped` (R3: leaving is leaving). Test `test_abandoned_run_becomes_stopped_on_next_visit`, scenario S18 |
| 6 | Oct 26 | First scenario run `python -m eval.scenarios` | — | **FAIL S08**: "this exam is killing me lol" → `crisis_rule` ([before](evidence/failure-s08/before-fix-mock-results.md)) | **Failed approach revised:** pattern `kill(ing)? (myself\|me)` → `kill(ing)? myself`. 17/17 after ([after](evidence/failure-s08/after-fix-mock-results.md)). Kept the S09 over-trigger on negation on purpose |
| 7 | Oct 26 | First pytest run with personalization test | — | `test_personalization_rules` failed: 2 "helped" + 3 "not this time" still left grounding as usual | **Revised:** "not this time" weighs −2. The person's signal should correct the app quickly (D5 vs R4 tension) |
| 8 | Oct 26 | Screenshot review (`docs/evidence/03-…`) | Header wrapped "Crisis support" onto two lines at phone width | Screenshot | `white-space: nowrap`; hide "class prototype" subtitle during exercises on narrow screens |
| 9 | Oct 26 | Simulated model failure (`?simulateFailure=1`) | — | Fallback line shown, `model_calls.ok=0`, Crisis support opens ([14](evidence/14-model-failure-checkin.png), [15](evidence/15-model-failure-reframe.png)) | No change needed. Behavior check B1 holds |
| 10 | Oct 26 | Backend unreachable (requests aborted) | — | "Not saving right now" notice, Crisis support opens ([16](evidence/16-backend-down-crisis.png)) | No change needed. Static crisis content works |
