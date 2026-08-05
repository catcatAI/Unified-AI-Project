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
from typing import Dict, List, Optional, Tuple

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
    "chicken": {"legs": "2", "head": "1", "sound": "cluck", "animal": "chicken"},
    "rabbit": {"legs": "4", "head": "1", "sound": "thump", "animal": "rabbit"},
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

# unit conversion table: (unit_a, unit_b) -> multiplier from a to b
_UNIT_CONVERSIONS: Dict[Tuple[str, str], Tuple[float, str]] = {
    # length
    ("km", "m"): (1000.0, "kilometer"),
    ("m", "km"): (0.001, "meter"),
    ("km", "cm"): (100000.0, "kilometer"),
    ("cm", "km"): (1e-5, "centimeter"),
    ("cm", "m"): (0.01, "centimeter"),
    ("m", "cm"): (100.0, "meter"),
    ("mm", "m"): (0.001, "millimeter"),
    ("m", "mm"): (1000.0, "meter"),
    ("mm", "m"): (0.001, "millimeter"),
    ("m", "mm"): (1000.0, "meter"),
    ("km", "mile"): (0.621371, "kilometer"),
    ("mile", "km"): (1.60934, "mile"),
    ("m", "yard"): (1.09361, "meter"),
    ("yard", "m"): (0.9144, "yard"),
    ("m", "foot"): (3.28084, "meter"),
    ("foot", "m"): (0.3048, "foot"),
    ("foot", "inch"): (12.0, "foot"),
    ("inch", "cm"): (2.54, "inch"),
    ("cm", "inch"): (0.393701, "centimeter"),
    # weight / mass
    ("kg", "g"): (1000.0, "kilogram"),
    ("g", "kg"): (0.001, "gram"),
    ("kg", "lb"): (2.20462, "kilogram"),
    ("lb", "kg"): (0.453592, "pound"),
    ("g", "mg"): (1000.0, "gram"),
    ("mg", "g"): (0.001, "milligram"),
    ("tonne", "kg"): (1000.0, "tonne"),
    ("kg", "tonne"): (0.001, "kilogram"),
    # volume
    ("l", "ml"): (1000.0, "liter"),
    ("ml", "l"): (0.001, "milliliter"),
    ("l", "gallon"): (0.264172, "liter"),
    ("gallon", "l"): (3.78541, "gallon"),
    # temperature (special: conversion formulas, not simple multiplier)
    # time
    ("minute", "second"): (60.0, "minute"),
    ("hour", "minute"): (60.0, "hour"),
    ("day", "hour"): (24.0, "day"),
    ("week", "day"): (7.0, "week"),
}

# chemical formula map: common_name -> formula
_CHEMICAL_FORMULAS: Dict[str, str] = {
    "water": "H2O",
    "salt": "NaCl",
    "sodium chloride": "NaCl",
    "carbon dioxide": "CO2",
    "oxygen": "O2",
    "hydrogen": "H2",
    "nitrogen": "N2",
    "methane": "CH4",
    "ammonia": "NH3",
    "glucose": "C6H12O6",
    "ethanol": "C2H5OH",
    "sulfuric acid": "H2SO4",
    "hydrochloric acid": "HCl",
    "nitric acid": "HNO3",
    "sodium hydroxide": "NaOH",
    "calcium carbonate": "CaCO3",
    "carbon monoxide": "CO",
    "sulfur dioxide": "SO2",
    "hydrogen peroxide": "H2O2",
    "ozone": "O3",
    "aspirin": "C9H8O4",
    "caffeine": "C8H10N4O2",
}

# antonym pairs
_ANTONYMS: Dict[str, str] = {
    "hot": "cold",
    "cold": "hot",
    "big": "small",
    "small": "big",
    "large": "small",
    "tiny": "big",
    "light": "heavy",
    "heavy": "light",
    "fast": "slow",
    "slow": "fast",
    "quick": "slow",
    "happy": "sad",
    "sad": "happy",
    "open": "closed",
    "closed": "open",
    "day": "night",
    "night": "day",
    "high": "low",
    "low": "high",
    "tall": "short",
    "short": "tall",
    "young": "old",
    "old": "young",
    "wet": "dry",
    "dry": "wet",
    "full": "empty",
    "empty": "full",
    "hard": "soft",
    "soft": "hard",
    "good": "bad",
    "bad": "good",
    "strong": "weak",
    "weak": "strong",
    "rich": "poor",
    "poor": "rich",
    "black": "white",
    "white": "black",
    "quiet": "loud",
    "loud": "quiet",
    "up": "down",
    "down": "up",
    "left": "right",
    "right": "left",
    "start": "stop",
    "stop": "start",
    "win": "lose",
    "lose": "win",
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

    # 6) unit conversion: "how many m in a km", "convert 5 km to m"
    m = re.search(r"(?:convert|how many|how much)\s+(-?\d+(?:\.\d+)?)?\s*(\w+)\s+(?:to|in a|in|per)\s+(\w+)", t)
    if m:
        value_str, src_unit, dst_unit = m.group(1), m.group(2), m.group(3)
        conv = _UNIT_CONVERSIONS.get((src_unit, dst_unit))
        if conv is not None:
            multiplier, src_name = conv
            if value_str:
                value = float(value_str)
                converted = value * multiplier
                return f"{value} {src_unit} = {converted:.4f} {dst_unit}"
            else:
                return f"1 {src_unit} = {multiplier} {dst_unit}"

    # 7) chemical formula: "formula of water", "what is the formula of salt"
    m = re.search(r"(?:formula|composition|chemical)\s+(?:of|for|is)?\s*(\w+(?:\s+\w+)?)", t)
    if m:
        name = m.group(1).strip()
        formula = _CHEMICAL_FORMULAS.get(name)
        if formula:
            return f"{name} = {formula}"

    return None


def known_subjects() -> List[str]:
    """Expose the covered subjects (used by tests / introspection)."""
    return list(_KNOWLEDGE.keys())
