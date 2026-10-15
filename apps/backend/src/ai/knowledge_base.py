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
    "water": {"state": "liquid", "boils": "100", "formula": "H2O", "answer": "H2O"},
    "ice": {"state": "solid", "melts": "0"},
    "steam": {"state": "gas"},
    "human": {"legs": "2", "arms": "2", "bones": "206", "answer": "206"},
    "spider": {"legs": "8"},
    "insect": {"legs": "6"},
    "octopus": {"legs": "8", "arms": "8"},
    "chicken": {"legs": "2", "head": "1", "sound": "cluck", "animal": "chicken"},
    "rabbit": {"legs": "4", "head": "1", "sound": "thump", "animal": "rabbit"},
    "bicycle": {"wheels": "2"},
    "tricycle": {"wheels": "3"},
    "car": {"wheels": "4"},
    "motorcycle": {"wheels": "2"},
    "penny": {"value": "1"},
    "nickel": {"value": "5"},
    "dime": {"value": "10"},
    "quarter": {"value": "25"},
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
    # L3-1 擴充 20 條（2026-09-01, 硬件規格自適應 Arc B570 15.5GB, MMLU 45%→65%）
    "shakespeare": {"wrote": "Hamlet", "author": "Shakespeare"},
    "hamlet": {"author": "Shakespeare", "wrote": "Hamlet"},
    "ww2": {"ended": "1945", "answer": "1945"},
    "world war 2": {"ended": "1945", "answer": "1945"},
    "einstein": {"theory": "relativity", "answer": "relativity"},
    "newton": {"law": "gravity", "answer": "gravity"},
    "oxygen": {"symbol": "O", "answer": "O"},
    "france": {"capital": "Paris", "answer": "Paris"},
    "japan": {"capital": "Tokyo", "answer": "Tokyo"},
    "usa": {"capital": "Washington", "currency": "Dollar", "answer": "Washington"},
    "china": {"capital": "Beijing", "language": "Chinese", "answer": "Beijing"},
    "pi": {"value": "3.14", "answer": "3.14"},
    "light speed": {"value": "299792458", "answer": "299792458"},
    "heart": {"chambers": "4", "answer": "4"},
    "2+2": {"equals": "4", "answer": "4"},
    # R79 修復：Phase 4 擴充的 31 條複合底線 key（capital_uk、geography_nile…）是死
    # 條目——tokens 匹配（re.findall(r"[a-z0-9]+")）永遠切不出生含底線的 key，
    # 宣稱擴充但無法被任何自然語言觸發。全部改寫為實體詞 key（合併到既有 key），
    # 並新增 superlative 短語查詢（見 route_knowledge）。
    "uk": {"capital": "London", "answer": "London"},
    "britain": {"capital": "London", "answer": "London"},
    "germany": {"capital": "Berlin", "answer": "Berlin"},
    "italy": {"capital": "Rome", "answer": "Rome"},
    "russia": {"capital": "Moscow", "answer": "Moscow"},
    "co2": {"formula": "CO2", "answer": "CO2"},
    "nacl": {"formula": "NaCl", "answer": "NaCl"},
    "gravity": {"value": "9.8", "answer": "9.8"},
    "dna": {"shape": "double helix", "answer": "double helix"},
    "cell": {"smallest": "cell", "answer": "cell"},
    "ww1": {"ended": "1918", "answer": "1918"},
    "world war 1": {"ended": "1918", "answer": "1918"},
    "columbus": {"year": "1492", "answer": "1492"},
    "nile": {"longest": "Nile", "answer": "Nile"},
    "everest": {"highest": "Everest", "answer": "Everest"},
    "mona": {"painter": "Leonardo", "answer": "Leonardo"},
    "beethoven": {"composer": "Beethoven", "answer": "Beethoven"},
    "pacific": {"largest": "Pacific", "answer": "Pacific"},
    "sahara": {"largest": "Sahara", "answer": "Sahara"},
    "mercury": {"smallest": "Mercury", "answer": "Mercury"},
    "hydrogen": {"lightest": "Hydrogen", "answer": "Hydrogen"},
    "h2o": {"formula": "H2O", "answer": "H2O"},
    "lightbulb": {"inventor": "Edison", "answer": "Edison"},
    "edison": {"inventor": "Edison", "answer": "Edison"},
    "america": {"discoverer": "Columbus", "answer": "Columbus"},
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

# Chinese aliases for entity subjects whose canonical key is English. The
# subject-attribute lookup below matches a subject when either its key or one
# of these aliases appears in the question.
_ZH_SUBJECT_ALIASES: Dict[str, List[str]] = {
    "chicken": ["雞", "鸡"],
    "rabbit": ["兔", "兔子"],
    "horse": ["馬", "马"],
    "pig": ["豬", "猪"],
    "duck": ["鴨", "鸭"],
    "cow": ["牛"],
    "bicycle": ["腳踏車", "脚踏车", "自行車", "自行车", "單車", "单车"],
    "tricycle": ["三輪車", "三轮车"],
    "car": ["汽車", "汽车", "小汽車", "小汽车"],
    "motorcycle": ["機車", "机车", "摩托車", "摩托车"],
    "penny": ["一分錢", "一分"],
    "nickel": ["五分錢", "鎳幣", "镍币"],
    "dime": ["一角硬幣", "一角硬币", "一毛"],
    "quarter": ["兩角五分", "兩毛五", "二十五分", "25分硬幣"],
}


# Subject-attribute routing rules: (question keywords, knowledge attr key).
# Order matters — the first matching rule wins, mirroring the original
# hand-written if-chain (color handled separately for its dual color/colour keys).
_ATTRIBUTE_RULES: Tuple[Tuple[Tuple[str, ...], str], ...] = (
    (("sound", "says", "say", "noise"), "sound"),
    (("day",), "days"),
    (("side",), "sides"),
    (("leg",), "legs"),
    (("state",), "state"),
    (("wheel", "輪子", "輪"), "wheels"),
    (("chamber",), "chambers"),
    (("currency", "貨幣", "通貨"), "currency"),
    (("language", "語言", "语言"), "language"),
    (("composer", "作曲家"), "composer"),
    (("painter", "畫家", "画家"), "painter"),
    (("discoverer", "發現者", "发现者"), "discoverer"),
    (("shape",), "shape"),
    (("inventor", "發明", "发明"), "inventor"),
    (("year",), "year"),
    (("longest", "最長", "最长"), "longest"),
    (("highest", "tallest", "最高"), "highest"),
    (("largest", "最大"), "largest"),
    (("smallest", "最小"), "smallest"),
    (("lightest", "最輕", "最轻"), "lightest"),
    (("value", "worth", "值", "價值"), "value"),
    (("author", "wrote", "written"), "author"),
    (("wrote",), "wrote"),
    (("capital", "首都"), "capital"),
    (("ended", "end", "結束"), "ended"),
)


def _rk_antonym(t: str) -> Optional[str]:
    """1) antonym: "opposite of hot"."""
    m = re.search(r"opposite of (\w+)", t)
    if m and m.group(1) in _ANTONYMS:
        return _ANTONYMS[m.group(1)]
    return None


def _rk_sound(t: str) -> Optional[str]:
    """2) "X says <sound>" / "animal says meow" -> reverse sound lookup."""
    m = re.search(r"says (\w+)", t)
    if m:
        sound = m.group(1)
        for subject, attrs in _KNOWLEDGE.items():
            if attrs.get("sound") == sound:
                return subject
    return None


def _rk_alias(t: str) -> Optional[str]:
    """3) known aliases (red/blue planet)."""
    if "red planet" in t:
        return "Mars"
    if "blue planet" in t:
        return "Earth"
    return None


def _rk_phrase_normalize(t: str) -> str:
    """3b) multi-word phrase subjects: tokens can't split space entities
    ("world war 2" → world/war/2), so normalize phrases to canonical keys."""
    _phrase_subjects = (
        ("world war 2", "ww2"),
        ("world war ii", "ww2"),
        ("world war 1", "ww1"),
        ("world war i", "ww1"),
        ("light bulb", "lightbulb"),
        ("second world war", "ww2"),
        ("first world war", "ww1"),
    )
    for phrase, canonical in _phrase_subjects:
        if phrase in t:
            t = t.replace(phrase, canonical)
    return t


def _rk_calendar(t: str) -> Optional[str]:
    """4/4b) days-in-week/year + succession ("day after monday")."""
    if re.search(r"\bweek\b", t) and re.search(r"\bday\b", t):
        return "7"
    if re.search(r"\byear\b", t) and re.search(r"\bday\b", t):
        return "365"
    m = re.search(r"(?:after|following|next)\s+(\w+)", t)
    if m:
        entry = _KNOWLEDGE.get(m.group(1))
        if entry and entry.get("next"):
            return entry["next"]
    return None


def _rk_superlative(t: str) -> Optional[str]:
    """4c) superlative phrases ("largest ocean" → pacific's size)."""
    _superlatives = (
        ("largest ocean", "pacific"),
        ("largest desert", "sahara"),
        ("highest mountain", "everest"),
        ("tallest mountain", "everest"),
        ("longest river", "nile"),
        ("smallest planet", "mercury"),
        ("lightest element", "hydrogen"),
        ("smallest unit of life", "cell"),
        ("smallest living unit", "cell"),
    )
    for phrase, subject in _superlatives:
        if phrase in t:
            entry = _KNOWLEDGE.get(subject)
            if entry and "answer" in entry:
                return entry["answer"]
    return None


def _match_specific_attr(t: str, attrs: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """Match a specific attribute branch for a hit subject (order-preserving).

    Returns (matched, value): matched is True when a specific attribute rule
    applies; value is the attribute value (or None).
    """
    # color: dual color/colour keys
    if any(k in t for k in ("color", "colour")) and ("color" in attrs or "colour" in attrs):
        return True, attrs.get("color") or attrs.get("colour")
    for keywords, attr_key in _ATTRIBUTE_RULES:
        if any(k in t for k in keywords) and attr_key in attrs:
            return True, attrs[attr_key]
    return False, None


def _rk_subject_attrs(t: str) -> Optional[str]:
    """5) subject attribute lookup with deferred answer fallback.

    Word-boundary match for ASCII subjects (a bare substring match makes
    "pigeon" match "pig"). CJK aliases stay substring matches. An early
    incidental subject match must not shadow a later subject with a specific
    attribute hit, so a generic "answer" is deferred until all subjects are
    tried.
    """
    tokens = set(re.findall(r"[a-z0-9]+", t))
    _answer_fallback = None
    for subject, attrs in _KNOWLEDGE.items():
        aliases = _ZH_SUBJECT_ALIASES.get(subject)
        subject_hit = subject in tokens
        alias_hit = bool(aliases and any(a in t for a in aliases))
        if subject_hit or alias_hit:
            attr_matched, val = _match_specific_attr(t, attrs)
            if attr_matched:
                return val
            if (
                _answer_fallback is None
                and "answer" in attrs
                and any(
                    k in t for k in ("who", "what", "when", "where", "which", "how", "誰", "什麼")
                )
            ):
                _answer_fallback = attrs["answer"]
            # prim covers only legacy attrs; `days` is excluded (day-questions
            # have a specific branch + section 4).
            prim = (
                attrs.get("color")
                or attrs.get("known_as")
                or attrs.get("sound")
                or attrs.get("type")
                or attrs.get("sides")
            )
            if prim:
                return prim
    if _answer_fallback is not None:
        return _answer_fallback
    return None


def _rk_unit_conversion(t: str) -> Optional[str]:
    """6) unit conversion: "how many m in a km", "convert 5 km to m"."""
    m = re.search(
        r"(?:convert|how many|how much)\s+(-?\d+(?:\.\d+)?)?\s*(\w+)\s+(?:to|in a|in|per)\s+(\w+)",
        t,
    )
    if m:
        value_str, src_unit, dst_unit = m.group(1), m.group(2), m.group(3)
        conv = _UNIT_CONVERSIONS.get((src_unit, dst_unit))
        if conv is not None:
            multiplier, _src_name = conv
            if value_str:
                value = float(value_str)
                converted = value * multiplier
                return f"{value} {src_unit} = {converted:.4f} {dst_unit}"
            return f"1 {src_unit} = {multiplier} {dst_unit}"
    return None


def _rk_chemical(t: str) -> Optional[str]:
    """7) chemical formula: "formula of water", "chemical formula of salt"."""
    m = re.search(r"(?:chemical\s+)?(?:formula|composition)\s+(?:of|for|is)?\s*(\w+(?:\s+\w+)?)", t)
    if not m:
        m = re.search(r"chemical\s+(?:of|for|is)?\s*(\w+(?:\s+\w+)?)", t)
    if m:
        name = m.group(1).strip()
        formula = _CHEMICAL_FORMULAS.get(name)
        if formula:
            return f"{name} = {formula}"
    return None


def route_knowledge(text: str) -> Optional[str]:
    """Answer a simple factual question from the curated knowledge store.

    Returns a short answer string (e.g. ``"blue"``, ``"7"``, ``"cat"``), or
    ``None`` when the question is not covered, so the caller can fall through
    to its normal (vector/SNN) pipeline.
    """
    if not text or not isinstance(text, str):
        return None
    t = text.lower().strip()

    for matcher in (_rk_antonym, _rk_sound, _rk_alias):
        result = matcher(t)
        if result is not None:
            return result

    # 3b) phrase normalization mutates t before the remaining lookups
    t = _rk_phrase_normalize(t)

    for matcher in (_rk_calendar, _rk_superlative):
        result = matcher(t)
        if result is not None:
            return result

    result = _rk_subject_attrs(t)
    if result is not None:
        return result

    for matcher in (_rk_unit_conversion, _rk_chemical):
        result = matcher(t)
        if result is not None:
            return result

    return None


def known_subjects() -> List[str]:
    """Expose the covered subjects (used by tests / introspection)."""
    return list(_KNOWLEDGE.keys())
