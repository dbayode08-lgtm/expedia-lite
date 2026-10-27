"""Skill definitions (from shared/skills.json) and retrieval cards for the model.

The app -- not the model -- owns the skill steps. The model only sees these short
cards as context so its check-in reply names real skills accurately.
"""
import json
from pathlib import Path

SHARED = Path(__file__).resolve().parents[2] / "shared"
SKILLS_DOC = json.loads((SHARED / "skills.json").read_text(encoding="utf-8"))
SKILLS = {s["id"]: s for s in SKILLS_DOC["skills"]}
SKILL_IDS = list(SKILLS)
MAX_EXERCISE_SECONDS = SKILLS_DOC["max_exercise_seconds"]

# Retrieval context ("stored information" from the RAG activity, re-used here).
SKILL_CARDS = [
    {"skill": "breathing", "title": "Paced breathing (4-6)",
     "body": "Breathe in for a count of four and out for a count of six, about 60 seconds. "
             "The app shows a circle that carries the pace; nothing to type.",
     "keywords": "breath breathing breathe chest heart racing panic tight fast shaky calm slow body"},
    {"skill": "grounding", "title": "5-4-3-2-1 grounding",
     "body": "Notice five things you can see, four you can feel, three you can hear, two you can smell, "
             "and one you can taste. Tap once per step; nothing to type.",
     "keywords": "spacey unreal numb foggy zoned disconnected far away floating overwhelmed loud senses here present"},
    {"skill": "stop", "title": "STOP",
     "body": "Stop; take a step back; observe what is happening inside and around you; proceed mindfully. "
             "About 40 seconds, the steps move on their own.",
     "keywords": "angry urge snap react impulse yell text send argument fight rush about to do something"},
    {"skill": "reframe", "title": "One-minute reframe",
     "body": "Name one distressing thought, note what makes it feel true, and consider another way to read it. "
             "Takes a few words of typing, or tapping a choice.",
     "keywords": "thought thinking always never stupid failure fault blame mess messed upset with me hate worst ruined"},
]
