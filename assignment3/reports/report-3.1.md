# Assignment 3.1: Research and Design (Steady)

- **Repository:** https://github.com/dbayode08-lgtm/expedia-lite (branch `assignment3`, folder `assignment3/`)
- **Commit:** `ae04d6a`
- **Submitted:** Oct 26, 2026

## Links
- Design notes (decisions ↔ R/D findings, model role, data, personalization, open questions): [https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/design.md](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/design.md)
- Flow diagram: [https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/flow.png](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/flow.png) (source [flow.mmd](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/docs/flow.mmd))
- Skill steps + planned timing: [https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/shared/skills.json](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/shared/skills.json)
- README / AGENTS.md: [https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/README.md](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/README.md), [https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/AGENTS.md](https://github.com/dbayode08-lgtm/expedia-lite/blob/assignment3/assignment3/AGENTS.md)

## Proposal in one paragraph
Steady is a coursework prototype that offers all four skills (paced breathing, 5-4-3-2-1 grounding, STOP, one-minute reframe) as equal options, one exercise and one instruction per screen, each planned at ≤ 90 s (63/54/42/65 s). A **Crisis support** button sits in the header of every screen. It's static content bundled into the page, so it doesn't depend on the backend, the model or any classifier (R2, D4). The model has two narrow jobs: an optional one-line check-in where it replies in ≤ 2 sentences and *names* one skill (shown as one more button, never auto-started, R4), and an opt-in "show two possible readings" inside the reframe to cut typing (D3). The app owns the steps, timing, Stop, saving and crisis handling. Model output is validated in code, not just constrained by the prompt.

## Key decisions and the findings behind them
- **R2/D4**: crisis access is persistent and model-independent. A regex check also runs before any model call, so crisis-like text is never sent to a model.
- **R3**: Stop is one tap with no confirmation, and stopping never counts against a skill.
- **R4 + D5**: "Your usual" comes from what was already finished (no setup), shown as an option, not a route. One "Not this time" tap corrects it.
- **D1**: the study can't detect distress, so contraction is *structural* (exercise screens keep only Stop/Pause/Crisis) and *user-chosen* (*Less on screen*). The app claims to know nothing about how someone feels.
- **D2/D3**: grounding needs no typing, and the reframe can be finished with taps only. Reframe text isn't saved.
- **D6**: plain neutral copy, muted palette, motion only for the breathing pace cue. A validator blocks "!", praise, advice and clinical terms in model output.

Full table with what each decision gains, gives up, and the alternatives considered: design.md §2.

## Data I expect to store
`sessions`, `exercise_runs` (skill, how chosen, completed/stopped, setup/duration/paused ms, optional feedback), `messages` (check-in only, with source), `model_calls` (for failure evidence and the 50-call cap), `skill_cards` (retrieval context). Details: design.md §4.

## Open questions at this stage
Should "usual" auto-start? 6 or 9 breathing cycles? Should STOP auto-advance? Should crisis-like input end the exercise? Is regex detection acceptable as a supplement? (Resolved later; see design.md §6 and report 3.3.)

## What's complete / unresolved
Complete: design, flow, data model, model role and limits, timing plan. Unresolved at this milestone: which live model to use (the class RAG activity's provider wasn't known; the model layer is provider-pluggable with a mock default).
