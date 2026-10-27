# Assignment 3.3: Integration, Evaluation, and Demonstration (Steady)

- **Repository:** https://github.com/dbayode08-lgtm/expedia-lite (branch `assignment3`, folder `assignment3/`)
- **Commit:** `COMMIT_HASH`
- **Recordings:** Demo: _LINK_  ·  Process screencast (failure → evidence → decision) + code explanation: _LINK_
- **Run from a clean checkout:** [README](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/README.md)

## Links
- Evaluation (20 scenarios, 5 behavior checks, timing, live-model plan, surprising finding, untested limitation): [https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evaluation/evaluation.md](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evaluation/evaluation.md)
- Raw mock results: [mock-results.md](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evaluation/mock-results.md)
- Design (updated, with changes marked): [https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/design.md](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/design.md)
- Evidence log (prompts → changes → evidence → decisions, incl. failed approaches): [https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence-log.md](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence-log.md)
- Code walkthrough used in the screencast: [https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/code-walkthrough.md](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/code-walkthrough.md)
- AI use: [https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/AI-USE.md](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/AI-USE.md)

## What is complete
All four skills; check-in with retrieval + model suggestion; reframe alternatives; persistent sessions, runs, messages and model-call logs; History with *Clear history*; "Your usual" personalization; *Less on screen*; Crisis support that works with the model failing or the backend down; 50-call live cap with automatic switch to mock; failure simulation for demos.

## What the evidence shows
- **pytest 50/50**, **API scenarios 17/17** (mock), **browser checks 15/15**. These show the app behaves correctly *around* the model: crisis text never reaches it, bad or failed output becomes a fallback, Stop is free, timing excludes pauses.
- Measured durations: breathing 63.0 s, STOP 43.1 s, grounding 54.2 s and reframe 62.3 s at the assumed human pace (evaluation §3). All ≤ 90 s; reframe worst case with a full 6 s model timeout is 71 s.
- They do **not** show live-model quality (not run, no key) or any clinical effect.

## Changes since 3.1, and why
| 3.1 plan | Now | Why (evidence) |
|---|---|---|
| Crisis pattern included "killing me" | Only "kill(ing) myself" | S08 "this exam is killing me" opened crisis mode ([before](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence/failure-s08/before-fix-mock-results.md) / [after](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/evidence/failure-s08/after-fix-mock-results.md)) |
| A run ends only via Done or Stop | Next visit records abandoned runs as `stopped` | Browser test left a run `started` forever (S18) |
| "Not this time" = −1 | −2 | 2 "helped" + 3 "not this time" still kept a skill as usual (failing test) |
| Open: auto-advance STOP? | Yes, with Next to go sooner | Fewer decisions. Measured 43 s |
| Open: should crisis input end the exercise? | No. Panel opens over it and pauses it | R3/R4: the person decides. Paused time excluded (63.0 s + 4.1 s) |

## Personalization vs control vs effort
"Your usual" saves one decision without any setup (D5) but is never auto-started (R4). It's built from completions and one optional tap, so the person can correct it, and stopping never feeds it (R3). What we give up: no adaptation from stopped runs, and no detection of distress (D1 is left to the person via *Less on screen*).

## Unresolved
Live-model repeats (`python3 -m eval.scenarios --live` is ready; needs a key). Screen-reader testing. Two-tab edge case. Indirect crisis language beyond the regex, covered only by the always-visible button.
