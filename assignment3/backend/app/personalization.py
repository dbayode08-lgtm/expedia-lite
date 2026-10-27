"""D5: personalization without configuration.

"Your usual" is computed from what the person already did -- nothing to set up.
Rule (kept simple so it can be explained and corrected):
  look at the last 10 finished runs;
  score per skill = completed runs + 'helped' taps - 2 x 'not this time' taps;
  (a 'not this time' outweighs a completion, so the person's own signal corrects it quickly);
  a skill becomes "usual" only with >= 2 completed runs and the top score
  (ties -> most recently used).
Stopped runs never count against a skill (R3: stopping costs nothing).
The person can ignore it (all options stay one tap away) or clear history.
"""
WINDOW = 10
MIN_COMPLETIONS = 2


def usual_skill(conn) -> dict:
    rows = conn.execute(
        "SELECT id, skill, status, feedback FROM exercise_runs "
        "WHERE status IN ('completed','stopped') ORDER BY id DESC LIMIT ?",
        (WINDOW,),
    ).fetchall()
    scores: dict = {}
    completions: dict = {}
    last_seen: dict = {}
    for r in rows:
        s = r["skill"]
        last_seen.setdefault(s, r["id"])
        scores.setdefault(s, 0)
        completions.setdefault(s, 0)
        if r["status"] == "completed":
            scores[s] += 1
            completions[s] += 1
        if r["feedback"] == "helped":
            scores[s] += 1
        elif r["feedback"] == "not_this_time":
            scores[s] -= 2
    eligible = [s for s in scores if completions[s] >= MIN_COMPLETIONS and scores[s] > 0]
    if not eligible:
        return {"usual_skill": None, "reason": None, "scores": scores, "window": len(rows)}
    best = max(eligible, key=lambda s: (scores[s], last_seen[s]))
    return {
        "usual_skill": best,
        "reason": f"Finished {completions[best]} times recently",
        "scores": scores,
        "window": len(rows),
    }
