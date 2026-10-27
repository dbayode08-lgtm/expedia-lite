# Recording script (Part 3.3): ~8–10 min total, one recording with marked sections

Before recording: run `start-steady.command` (or the README steps). Use **mock** mode. In DB Browser, open `assignment3/backend/steady.db`. Optional: clear history in the app so you start clean. Say at the start: *"This is a coursework prototype tested only with fictional scenarios."*

## Section 1: Demo of the finished app (~4 min)
1. **Start screen.** "Four skills, offered as options, not routed (R4). Crisis support is in the header on every screen (R2, D4)."
2. **Check-in.** Type *my chest is tight and my heart is racing* → Send. "The model reply is two sentences and names one skill; it shows up as one more button. The skill steps come from `skills.json`, not from the model."
3. **Breathing.** Start it. "The circle carries the pace, 4 in, 6 out, 6 breaths, 63 seconds (R1)." Click **Crisis support**: "This pauses the exercise, and this time isn't counted." Close it.
4. While it runs, point at **Stop**: "One tap, no confirmation (R3)." Let it finish → **Done** → tap *Helped a bit*. "Feedback is optional."
5. **Grounding.** Tap through 2 steps, then **Stop** → "Stopped. That's fine." "Stopping costs nothing; it never lowers a skill's ranking."
6. **Reframe.** Tap *They're upset with me* → Skip → *Show two possible readings* → pick one → Next → Finish. "Finished with zero typing (D3). The thought text isn't saved."
7. Back on Start, show **Your usual** (finish breathing twice before recording, or use the existing history). "Personalized from what I already did, no setup (D5)."
8. **Less on screen** checkbox: "D1. The person chooses when there's less; the app doesn't pretend to detect distress."
9. **History** → expand a check-in. Then show the same rows in DB Browser: `exercise_runs` (status, duration_ms, paused_ms) and `messages` (source column).

## Section 2: Process screencast, one failure → evidence → decision (~3 min)
Failure: **scenario S08, "this exam is killing me lol" opened crisis mode.**
1. Open `docs/evidence/failure-s08/before-fix-mock-results.md`, find the S08 row: expected `crisis:false`, observed `crisis:true`, source `crisis_rule`.
2. Show the pattern that caused it: in `shared/crisis.json` it was `\bkill(ing)? (myself|me)\b`, and "killing me" is an everyday idiom.
3. Decision: narrow it to `\bkill(ing)? myself\b`. Show the after-fix results (17/17) and the new unit test `test_crisis_patterns` ("my feet are killing me" → False).
4. Then say what I **didn't** change: S09 "I'm not suicidal, just stressed" still triggers. I kept that on purpose, because a false alarm only shows resources the person can close, while a miss is worse. And the Crisis support button never depended on the regex anyway.
5. Second, smaller one: run the app with `?simulateFailure=1`, send a check-in, then show the fallback line, the `model_calls` row with `ok=0`, and that Crisis support still opens.

## Section 3: Explain generated code (~2 min)
Walk through `run_model()` in `backend/app/llm.py` using `docs/code-walkthrough.md`: cap → provider → validator → failure → fallback → log. Stress that **the validator, not the prompt**, is what keeps the model inside its role.

Save the recording(s), upload (Kaltura/YouTube unlisted/OneDrive), and paste the links into `reports/report-3.3.md`.
