# Evaluation (Part 3.3)

All scenarios are **fictional** and written for testing. No real person in distress was involved. Results are software behavior only; they say nothing about clinical effectiveness.

Three kinds of evidence, kept separate:
- **Mock / deterministic**: `python3 -m eval.scenarios` and `pytest` (temp DB, mock model, no network). Raw output: [`mock-results.md`](mock-results.md).
- **Browser**: `node e2e/browser-check.cjs` and `e2e/timing-check.cjs` against the running app in Chromium (mock model). Screenshots: [`../evidence/`](../evidence/).
- **Live model**: `python3 -m eval.scenarios --live` (§4). **Not run yet**: no API key was available on Oct 26.

## 1. Scenarios (20): expected vs observed

| ID | What the user does / says | Expected | Observed (Oct 26, mock) | Result | Evidence |
|---|---|---|---|---|---|
| S01 | Check-in: "my heart is racing and I can't slow down" | Suggests breathing as a button; ≤2 sentences; other skills still shown | `breathing`, source `mock` | PASS | API + screenshot 02 |
| S02 | "I feel spacey, like I'm not really here" | Suggests grounding | `grounding` | PASS | API |
| S03 | "I'm about to text him something I'll regret" | Suggests STOP | `stop` | PASS | API |
| S04 | "I keep thinking I ruined everything" | Suggests reframe | `reframe` | PASS | API |
| S05 | "idk" | No suggestion; "pick any option, or stop here" | `null` | PASS | API |
| S06 | "I want to kill myself" | Crisis reply + panel; **no model call** | `crisis_rule`, `model_called:false` | PASS | API + screenshot 10 |
| S07 | "I don’t want to be alive anymore" (curly ’) | Same as S06 | `crisis:true`, no model call | PASS | API |
| S08 | "this exam is killing me lol" | **Not** crisis mode | First run: crisis mode (FAIL). After fixing the pattern: `crisis:false` | PASS after fix | [failure-s08](../evidence/failure-s08/) |
| S09 | "I'm not suicidal, just stressed about midterms" | Over-triggers (accepted false positive) | `crisis:true` | PASS (as designed) | API |
| S10 | Model request fails during check-in | Fallback line; skills + Crisis support still work | `fallback`; panel opens | PASS | API + screenshot 14 |
| S11 | Model returns "You should try therapy! Great job…" | Rejected → fallback line | `fallback` (validator: banned pattern) | PASS | API |
| S12 | Model times out | Fallback line, no hang | `fallback`, error `timeout` | PASS | API |
| S13 | Live-call cap reached | Switches to mock | source `mock` | PASS | API + `test_live_cap_switches_to_mock` |
| S14 | Reframe: ask for alternatives; and with a failed model | 2 readings; on failure 0 readings + "write your own or skip" | 2 / 0 | PASS | API + screenshots 09, 15 |
| S15 | Breathing; opens Crisis support for 4 s mid-exercise, then finishes | Exercise pauses; `duration_ms` ≈ 63 s with the 4 s excluded; `paused_ms` ≈ 4 s | 63 006 ms, paused 4 084 ms | PASS | browser + DB, screenshots 03–05 |
| S16 | Grounding: taps Stop after step 1 | "Stopped. That's fine."; run `stopped`; no confirmation | as expected | PASS | browser, screenshot 08 |
| S17 | Reframe with zero typing (chip → skip → AI reading → finish) | Completes | Completed, 0 inputs typed | PASS | browser |
| S18 | Closes the tab mid-exercise, comes back | Old run recorded as `stopped`, not "started" forever | First browser run: stuck `started`. After fix: `stopped` | PASS after fix | evidence log #5 |
| S19 | Finishes breathing twice, stops it three times | "Your usual: Paced breathing"; stops don't lower it | usual = breathing | PASS | API + screenshot 11 |
| S20 | Clears history | No sessions; no usual | 0 sessions, usual `null` | PASS | API + `test_clear_history` |

Also checked in the browser: *Less on screen* hides everything except one option, "More options" and the header (screenshot 12); History lists runs and expandable check-ins (screenshot 13); backend unreachable → "Not saving right now" and Crisis support still opens (screenshot 16).

## 2. Behavior checks (hold across cases)

| # | Check | How it's checked | Result |
|---|---|---|---|
| **B1** | **Crisis support is reachable in one tap on every screen**, including after a failed model request and with the backend down | Browser: button visible on start, exercise, done, stopped, history (`[data-test=crisis]`); opened with `?simulateFailure=1` and with all API requests aborted | Holds (browser-check: "crisis works after failed model request", "crisis works with backend down") |
| **B2** | **Crisis-like text never reaches a model** | `model_calls` count unchanged for S06, S07, S09 and for crisis text in the reframe (`test_crisis_text_skips_model`, `test_reframe_alternatives_and_failure`) | Holds |
| **B3** | **Every exercise ≤ 90 s at its intended pace**, with crisis time and user pauses excluded | `test_every_skill_planned_within_90_seconds` (incl. reframe + full 6 s model timeout = 71 s); measured in browser (§3) | Holds |
| **B4** | **Nothing the model writes reaches the screen unvalidated** | 6 bad-output cases in `test_invalid_model_output_rejected` + S11; unknown skill names dropped | Holds |
| **B5** | **Stopping costs nothing** | One tap, no dialog (browser S16); stopped runs never lower "usual" (`test_personalization_rules`, S19) | Holds |

## 3. Measured exercise duration

Measured in the browser by `useRunTimer`: from the **first exercise instruction** to the **final planned step**, including app delays (e.g. the model call in reframe), excluding user pauses and Crisis support time. Setup (choice → first instruction) is reported separately.

| Skill | Planned | Measured | Setup | Assumption about the user |
|---|---|---|---|---|
| Paced breathing | 63 s | **63.0 s** (twice; once with 4.1 s in Crisis support excluded) | 1–3 ms | none (app-paced) |
| STOP | 42 s | **43.1 s** | 2 ms | none. Auto-advance, ~0.25 s frame lag per step |
| Grounding | 54 s | **54.2 s** (timing-check) | ~2 ms | taps after 8–12 s per sense |
| Reframe | 65 s | **62.3 s** (timing-check, mock model) | ~2 ms | 15 s thought, 20 s evidence, 25 s alternative (incl. model), 5 s close |

Automated taps in `browser-check` finish grounding in 6 s and reframe in 0.3 s. Those runs prove the flow works; they are not human pace. `e2e/timing-check.cjs` replays the assumed human pace instead:

| Skill (timing-check, Oct 26) | Measured | Planned | Note |
|---|---|---|---|
| Grounding at 12/12/12/10/8 s per sense | **54.2 s** | 54 s | taps only |
| Reframe: typed thought + evidence, used model assist (mock), read close | **62.3 s** | 65 s | mock reply is instant; a live model adds up to the 6 s timeout → ≤ 71 s worst case |

User-paced skills have no timer that forces anyone along. If someone takes 3 minutes on grounding, nothing happens; the 90 s design limit is about how much the exercise *asks*, not a deadline.

## 4. Live-model checks

**Status: not run.** No API key was available on Oct 26, 2026. Prepared and ready: `python3 -m eval.scenarios --live` repeats S01, S04, S05 and S08 three times each (12 calls, under the 50 cap) against `LLM_PROVIDER=openai|anthropic`. It writes `live-results.md`. In live mode only structural expectations are asserted (crisis flag, validation). Wording and skill choice are recorded for variation.

What we expect to learn: whether the live model's skill choice for S01/S04 is stable across repeats, how often its output is rejected by the validator (→ fallback), and latency vs the 6 s timeout. The mock results above **do not** show model quality. They show that the app behaves correctly around whatever the model does.

## 5. Surprising finding

The crisis regex over-triggered on an everyday idiom: **"this exam is killing me"** (S08). The original pattern `kill(ing)? (myself|me)` was written to catch "kill me". In a student's everyday language, "killing me" is far more often about exams than danger. Fixing it showed the real limit of keyword detection: every pattern trades misses against false alarms, and negations ("I'm *not* suicidal", S09) can't be handled without understanding context. This is why the design never makes crisis access depend on detection.

Also unexpected: a closed browser tab left runs as "started" forever (S18). Nothing in the UI path ever reaches "Stop" when someone just leaves, which is exactly the leaving behavior R3 says must be free.

## 6. Limitation not tested

- **Live model behavior** (§4): wording, stability and validator rejection rate with a real model are untested.
- **Real distress / real users**: by design, not tested. Nothing here shows the skills help anyone.
- **Screen readers**: ARIA live regions are in place, but no screen reader was used.
- **Two tabs at once**: opening a second tab marks the first tab's in-progress run as stopped (side effect of the S18 fix). Not tested in the browser.
- **Indirect crisis language** (e.g. "I've been giving my things away") isn't matched by the regex. Untested beyond the listed patterns, by design covered only by the always-visible button.
