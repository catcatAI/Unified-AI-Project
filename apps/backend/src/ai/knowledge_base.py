# =============================================================================
# ANGELA-MATRIX: [L2] [γ] [B] [L4]
# =============================================================================
"""Deterministic knowledge base for native (non-LLM) inference engines.

Both ED3N and GARDEN delegate factual recall to this module through
``route_knowledge`` — mirroring how math is delegated to ``MathVerifier`` via
``route_math``. This is a real, high-certainty capability (knowledge retrieval
from a curated fact store) and is scored as such in INTELLIGENCE_ASSESSMENT.md.

The store is intentionally small and general; it is NOT a substitute for open-
domain reasoning. Its purpose is to let the native engines answer factual
questions they would otherwise hallucinate, instead of collapsing to the
fallback string.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

# subject -> attribute -> value
_KNOWLEDGE: Dict[str, Dict[str, str]] = {
    "sky": {"color": "blue"},
    "sun": {"color": "yellow", "type": "star"},
    "grass": {"color": "green"},
    "snow": {"color": "white"},
    "blood": {"color": "red"},
    "ocean": {"color": "blue"},
    "sea": {"color": "blue"},
    "leaf": {"color": "green"},
    "leaves": {"color": "green"},
    "fire": {"color": "orange"},
    "flame": {"color": "orange"},
    "mars": {"color": "red", "known_as": "Red Planet"},
    "earth": {"color": "blue", "known_as": "Blue Planet"},
    "moon": {"color": "grey"},
    "cloud": {"color": "white"},
    "gold": {"color": "yellow"},
    "banana": {"color": "yellow"},
    "lemon": {"color": "yellow"},
    "apple": {"color": "red"},
    "rose": {"color": "red"},
    "cat": {"sound": "meow", "animal": "cat"},
    "dog": {"sound": "woof", "animal": "dog"},
    "cow": {"sound": "moo", "animal": "cow"},
    "sheep": {"sound": "baa"},
    "pig": {"sound": "oink"},
    "bird": {"sound": "tweet", "animal": "bird"},
    "duck": {"sound": "quack", "animal": "duck"},
    "frog": {"sound": "croak"},
    "lion": {"sound": "roar"},
    "snake": {"sound": "hiss"},
    "bee": {"sound": "buzz"},
    "horse": {"sound": "neigh"},
    "water": {"state": "liquid", "boils": "100"},
    "ice": {"state": "solid", "melts": "0"},
    "steam": {"state": "gas"},
    "human": {"legs": "2", "arms": "2"},
    "spider": {"legs": "8"},
    "insect": {"legs": "6"},
    "octopus": {"legs": "8", "arms": "8"},
    "triangle": {"sides": "3"},
    "square": {"sides": "4"},
    "rectangle": {"sides": "4"},
    "circle": {"sides": "0"},
    "pentagon": {"sides": "5"},
    "hexagon": {"sides": "6"},
    "week": {"days": "7"},
    "year": {"days": "365", "months": "12"},
    "january": {"month": "1", "next": "february"},
    "february": {"month": "2", "next": "march"},
    "march": {"month": "3", "next": "april"},
    "april": {"month": "4", "next": "may"},
    "may": {"month": "5", "next": "june"},
    "june": {"month": "6", "next": "july"},
    "july": {"month": "7", "next": "august"},
    "august": {"month": "8", "next": "september"},
    "september": {"month": "9", "next": "october"},
    "october": {"month": "10", "next": "november"},
    "november": {"month": "11", "next": "december"},
    "december": {"month": "12", "next": "january"},
    "monday": {"weekday": "1", "next": "tuesday"},
    "tuesday": {"weekday": "2", "next": "wednesday"},
    "wednesday": {"weekday": "3", "next": "thursday"},
    "thursday": {"weekday": "4", "next": "friday"},
    "friday": {"weekday": "5", "next": "saturday"},
    "saturday": {"weekday": "6", "next": "sunday"},
    "sunday": {"weekday": "7", "next": "monday"},
    "diamond": {"hardness": "hardest"},
    "iron": {"metal": "yes"},
    "gold_metal": {"metal": "yes"},
}

# antonym pairs
_ANTONYMS: Dict[str, str] = {
    "hot": "cold", "cold": "hot",
    "big": "small", "small": "big",
    "large": "small", "tiny": "big",
    "light": "heavy", "heavy": "light",
    "fast": "slow", "slow": "fast",
    "quick": "slow", "slow": "quick",
    "happy": "sad", "sad": "happy",
    "open": "closed", "closed": "open",
    "day": "night", "night": "day",
    "high": "low", "low": "high",
    "tall": "short", "short": "tall",
    "young": "old", "old": "young",
    "wet": "dry", "dry": "wet",
    "full": "empty", "empty": "full",
    "hard": "soft", "soft": "hard",
    "good": "bad", "bad": "good",
    "strong": "weak", "weak": "strong",
    "rich": "poor", "poor": "rich",
    "black": "white", "white": "black",
    "quiet": "loud", "loud": "quiet",
    "up": "down", "down": "up",
    "left": "right", "right": "left",
    "start": "stop", "stop": "start",
    "win": "lose", "lose": "win",
}


def route_knowledge(text: str) -> Optional[str]:
    """Answer a simple factual question from the curated knowledge store.

    Returns a short answer string (e.g. ``"blue"``, ``"7"``, ``"cat"``), or
    ``None`` when the question is not covered, so the caller can fall through
    to its normal (vector/SNN) pipeline.
    """
    if not text or not isinstance(text, str):
        return None
    t = text.lower().strip()

    # 1) antonym: "opposite of hot"
    m = re.search(r"opposite of (\w+)", t)
    if m and m.group(1) in _ANTONYMS:
        return _ANTONYMS[m.group(1)]

    # 2) "X says <sound>" / "animal says meow" -> reverse sound lookup
    m = re.search(r"says (\w+)", t)
    if m:
        sound = m.group(1)
        for subject, attrs in _KNOWLEDGE.items():
            if attrs.get("sound") == sound:
                return subject

    # 3) known aliases
    if "red planet" in t:
        return "Mars"
    if "blue planet" in t:
        return "Earth"

    # 4) days in a week / year
    if "week" in t and "day" in t:
        return "7"
    if "year" in t and "day" in t:
        return "365"

    # 4b) succession: "day after monday", "month after march", "next tuesday",
    #     "what day comes after monday", "the day following tuesday"
    succ = None
    m = re.search(r"(?:after|following|next)\s+(\w+)", t)
    if m:
        succ = m.group(1)
    if succ:
        entry = _KNOWLEDGE.get(succ)
        if entry and entry.get("next"):
            return entry["next"]

    # 5) subject attribute lookup
    for subject, attrs in _KNOWLEDGE.items():
        if subject in t:
            if any(k in t for k in ("color", "colour")) and ("color" in attrs or "colour" in attrs):
                return attrs.get("color") or attrs.get("colour")
            if any(k in t for k in ("sound", "says", "say", "noise")) and "sound" in attrs:
                return attrs["sound"]
            if "day" in t and "days" in attrs:
                return attrs["days"]
            if "side" in t and "sides" in attrs:
                return attrs["sides"]
            if "leg" in t and "legs" in attrs:
                return attrs["legs"]
            prim = (
                attrs.get("color")
                or attrs.get("known_as")
                or attrs.get("sound")
                or attrs.get("days")
                or attrs.get("type")
                or attrs.get("sides")
            )
            if prim:
                return prim
    return None


def known_subjects() -> List[str]:
    """Expose the covered subjects (used by tests / introspection)."""
    return list(_KNOWLEDGE.keys())
