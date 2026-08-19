"""
=============================================================================
ANGELA-MATRIX: [L3] [βγδ] [C] [L2-L3]
=============================================================================

Physics formula solver — the MD-identified gap for the three-axis domain
engines (THREE_AXIS_SCALEUP.md §4.1/§6-D/§8.1).

Solves single-unknown physics formulas from natural-language word problems:

  * F = m·a          force = mass × acceleration
  * E = ½·m·v²       kinetic energy = ½ mass × velocity²
  * v = a·t          velocity = acceleration × time
  * p = m·v          momentum = mass × velocity
  * W = F·d          work = force × distance
  * P = W/t          power = work / time
  * F = m·g          weight = mass × gravity (g = 9.8 m/s²)

Input is parsed for known quantities via unit anchors (kg/m/s²/...) and
keyword-adjacent numbers (``mass = 5``). The target unknown is either the
explicitly named quantity or the single missing variable across all formulas.

This is a *deterministic* engine (domain axis value) — it does not claim
understanding, only symbolic evaluation of constrained word problems.
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [C] [L2-L3]
# =============================================================================

from __future__ import annotations

import re
from typing import Dict, List, Optional

# Canonical quantity names.
MASS = "mass"
ACCEL = "acceleration"
FORCE = "force"
VELOCITY = "velocity"
TIME = "time"
DISTANCE = "distance"
ENERGY = "energy"
MOMENTUM = "momentum"
WORK = "work"
POWER = "power"
WEIGHT = "weight"

# Quantity -> unit anchors (English + Chinese). Longer/specific units first so
# regex alternation matches "m/s²" before the bare "m" in "m/s²". The bare
# "m"/"meter" anchors use a negative lookahead so "m/s²" does not also count as
# a distance measurement. Joule is both energy AND work (same SI unit).
UNITS: Dict[str, List[str]] = {
    MASS: ["kg", "g", "公斤", "千克", "克"],
    ACCEL: ["m/s²", "m/s2", "m/s^2", "米每二次方秒", "米每秒方"],
    VELOCITY: ["m/s", "米每秒", "m/sec"],
    TIME: ["seconds", "second", "secs", "sec", "minute", "minutes", "秒"],
    DISTANCE: ["m(?![/a-zA-Z])", "meters", "metres", "meter", "metre", "米", "公尺"],
    FORCE: ["N(?!\\w)", "newton", "newtons", "牛頓", "牛顿"],
    ENERGY: ["J(?!\\w)", "joule", "joules", "焦耳"],
    WORK: ["J(?!\\w)", "joule", "joules", "焦耳"],
    POWER: ["W(?!\\w)", "watt", "watts", "瓦特"],
    WEIGHT: ["N(?!\\w)", "newton", "newtons", "牛頓", "牛顿"],
}

# Keyword -> quantity (English + Chinese), for keyword-adjacent numbers.
KEYWORDS: Dict[str, str] = {
    "mass": MASS,
    "質量": MASS,
    "质量": MASS,
    "acceleration": ACCEL,
    "加速度": ACCEL,
    "force": FORCE,
    "力": FORCE,
    "weight": WEIGHT,
    "重力": WEIGHT,
    "重量": WEIGHT,
    "weight of": WEIGHT,
    "velocity": VELOCITY,
    "speed": VELOCITY,
    "速度": VELOCITY,
    "time": TIME,
    "時間": TIME,
    "时间": TIME,
    "distance": DISTANCE,
    "distance travelled": DISTANCE,
    "distance traveled": DISTANCE,
    "displacement": DISTANCE,
    "距離": DISTANCE,
    "位移": DISTANCE,
    "kinetic energy": ENERGY,
    "energy": ENERGY,
    "動能": ENERGY,
    "能量": ENERGY,
    "momentum": MOMENTUM,
    "動量": MOMENTUM,
    "work": WORK,
    "功": WORK,
    "power": POWER,
    "功率": POWER,
}

# Target hints — explicitly asked quantity. "power" before "work" so "what is
# the power if 100 J of work is done" targets power, not the given work data.
TARGET_HINTS: List[str] = [
    "kinetic energy",
    "動能",
    "energy",
    "能量",
    "force",
    "力",
    "velocity",
    "speed",
    "速度",
    "acceleration",
    "加速度",
    "momentum",
    "動量",
    "power",
    "功率",
    "work",
    "功",
    "mass",
    "質量",
    "time",
    "時間",
    "distance",
    "距離",
]

# Standard gravity used by the weight formula (F = m·g).
GRAVITY = 9.8

# Formulas: each is (unknown, [(var1, expr), (var2, expr)], solved-expr-for-unknown).
# solved-expr uses Python-safe names matching the vars.
_FORMULAS: Dict[str, Dict[str, object]] = {
    FORCE: {
        "vars": [MASS, ACCEL],
        "solve": {FORCE: "m * a", MASS: "F / a", ACCEL: "F / m"},
    },
    ENERGY: {
        "vars": [MASS, VELOCITY],
        "solve": {
            ENERGY: "0.5 * m * v ** 2",
            MASS: "2 * E / v ** 2",
            VELOCITY: "(2 * E / m) ** 0.5",
        },
    },
    VELOCITY: {
        "vars": [ACCEL, TIME],
        "solve": {VELOCITY: "a * t", ACCEL: "v / t", TIME: "v / a"},
    },
    MOMENTUM: {
        "vars": [MASS, VELOCITY],
        "solve": {MOMENTUM: "m * v", MASS: "p / v", VELOCITY: "p / m"},
    },
    WORK: {
        "vars": [FORCE, DISTANCE],
        "solve": {WORK: "F * d", FORCE: "W / d", DISTANCE: "W / F"},
    },
    POWER: {
        "vars": [WORK, TIME],
        "solve": {POWER: "W / t", WORK: "P * t", TIME: "W / P"},
    },
    WEIGHT: {
        "vars": [MASS],
        "solve": {WEIGHT: "m * g", MASS: "W / g"},
        "const": GRAVITY,
    },
}

# Short var names for solving expressions.
_VAR_NAMES: Dict[str, str] = {
    MASS: "m",
    ACCEL: "a",
    FORCE: "F",
    VELOCITY: "v",
    TIME: "t",
    DISTANCE: "d",
    ENERGY: "E",
    MOMENTUM: "p",
    WORK: "W",
    POWER: "P",
    WEIGHT: "W",
}

_NUMBER_RE = re.compile(r"(\d+(?:\.\d+)?)")


def _unit_quantity(unit: str) -> Optional[str]:
    for qty, anchors in UNITS.items():
        if unit in anchors:
            return qty
    return None


def extract_known_quantities(text: str) -> Dict[str, float]:
    """Parse ``text`` into {quantity_name: value} using unit anchors first,
    then keyword-adjacent numbers. Prefers unit-anchored values."""
    known: Dict[str, float] = {}
    lowered = text.lower().replace("²", "2")

    # 1. Unit anchors: "<number> <unit>" or "<number><unit>". Anchors are
    #    lowercased to match the lowercased input (units like N/J/W are
    #    case-sensitive in SI but word problems are not).
    for qty, anchors in UNITS.items():
        for unit in sorted(anchors, key=len, reverse=True):
            pattern = r"(\d+(?:\.\d+)?)\s*" + unit.lower() + r"\b"
            for m in re.finditer(pattern, lowered):
                known.setdefault(qty, float(m.group(1)))
                break

    # N is both force and weight (newton). Only count it as weight when the
    # text actually talks about weight/gravity — a plain "force of 10 N" must
    # not become a weight measurement (else mass-from-force would be misread as
    # mass-from-weight = force/9.8).
    if "weight" in known and not any(
        w in lowered for w in ("weight", "weighs", "重", "重力", "falls", "falling")
    ):
        del known["weight"]

    # 2. Keyword-adjacent numbers: "mass = 5", "質量 5", "force of 10".
    #    Skip keywords shadowed by a longer keyword in the text (e.g. "速度"
    #    is a substring of "加速度").
    shadowed = _shadowed_keywords(text)
    for kw, qty in KEYWORDS.items():
        if kw in shadowed:
            continue
        if qty in known:
            continue
        pattern = re.escape(kw) + r"\s*(?:=|\sof\s|:|\bof\b|，|,)?\s*(\d+(?:\.\d+)?)"
        m = re.search(pattern, lowered)
        if m:
            known.setdefault(qty, float(m.group(1)))
    return known


def _shadowed_keywords(text: str) -> set:
    """Keywords that appear only as a substring of a longer keyword in text."""
    lowered = text.lower()
    result: set = set()
    keys = sorted(KEYWORDS, key=len, reverse=True)
    for i, kw in enumerate(keys):
        if kw not in lowered:
            continue
        for longer in keys[:i]:
            if kw in longer and longer in lowered:
                result.add(kw)
                break
    return result


# Question markers — the ask clause begins after these. Given data (e.g. "a
# force of 10 N") must not be mistaken for the asked quantity.
_QUESTION_MARKERS = [
    "what is the",
    "what's the",
    "what is",
    "find the",
    "compute the",
    "calculate the",
    "求",
    "试求",
    "試求",
    "find",
    "compute",
    "calculate",
]


def find_target(text: str) -> Optional[str]:
    """Identify the explicitly asked quantity from the *question clause* only.

    Searching the whole sentence would pick up quantities that appear in the
    given data (e.g. "a force of 10 N ... what is the work done" would wrongly
    target force). The ask is the substring after the last question marker.
    """
    lowered = text.lower()
    ask = lowered
    last_marker = -1
    for marker in _QUESTION_MARKERS:
        idx = lowered.rfind(marker)
        if idx >= 0:
            last_marker = max(last_marker, idx)
    if last_marker >= 0:
        ask = lowered[last_marker:]
    for hint in TARGET_HINTS:
        if hint in ask:
            return KEYWORDS.get(hint, hint)
    return None


def solve(text: str) -> Optional[Dict[str, object]]:
    """Solve a single-unknown physics word problem.

    Returns {``value``: float, ``quantity``: str, ``formula``: str} on success,
    or None when the problem is under-specified / not a formula problem.
    """
    if not text or not re.search(r"\d", text):
        return None
    known = extract_known_quantities(text)
    if not known:
        return None

    target = find_target(text)

    # Try each formula: exactly one unknown, and the unknown (or the formula's
    # own quantity) must be what was asked when a target is explicit.
    for qty, spec in _FORMULAS.items():
        vars_ = spec["vars"]  # type: ignore[attr-defined]
        missing = [var for var in vars_ + [qty] if var not in known]
        if len(missing) != 1:
            continue
        unknown = missing[0]
        if target is not None and unknown != target and qty != target:
            continue
        values = {_VAR_NAMES[k]: v for k, v in known.items()}
        if spec.get("const"):  # type: ignore[attr-defined]
            values["g"] = float(spec["const"])  # type: ignore[attr-defined]
        solve_map = spec["solve"]  # type: ignore[attr-defined]
        expr = solve_map.get(unknown)
        if expr is None:
            continue
        try:
            result = _eval_safe(expr, values)
        except (ZeroDivisionError, ValueError, TypeError):
            continue
        if result is None:
            continue
        return {
            "value": round(float(result), 6),
            "quantity": unknown,
            "formula": qty,
        }
    return None


def _eval_safe(expr: str, values: Dict[str, float]) -> Optional[float]:
    """Evaluate a whitelisted formula expression with the given values."""
    allowed = {"__builtins__": {}}
    env = dict(values)
    env.update({"abs": abs, "max": max, "min": min})
    try:
        result = eval(expr, allowed, env)  # noqa: S307 - whitelisted names only
        return float(result) if isinstance(result, (int, float)) else None
    except Exception:  # noqa: BLE001 - any eval failure = not solvable
        return None


__all__ = ["solve", "extract_known_quantities", "find_target", "GRAVITY"]
