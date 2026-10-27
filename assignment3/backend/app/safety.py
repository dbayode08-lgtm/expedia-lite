"""Deterministic crisis-language check. Runs BEFORE any model call.

Limits (documented in docs/design.md): keyword/regex matching misses indirect
phrasing and can over-trigger on quotes or negations ("I'm not suicidal").
That is why the Crisis support button never depends on this check -- it is
always on screen and works with the backend down.
"""
import json
import re
from pathlib import Path

CRISIS = json.loads((Path(__file__).resolve().parents[2] / "shared" / "crisis.json").read_text(encoding="utf-8"))
_PATTERNS = [re.compile(p, re.IGNORECASE) for p in CRISIS["patterns"]]


def normalize(text: str) -> str:
    return (text or "").replace("’", "'").replace("‘", "'")


def is_crisis_text(text: str) -> bool:
    t = normalize(text)
    return any(p.search(t) for p in _PATTERNS)


CRISIS_REPLY = (
    "What you wrote sounds serious. This prototype can't help with that, and no one is "
    "reading these messages. Please use one of the crisis contacts shown now. "
    "You can still choose a skill or leave whenever you want."
)
