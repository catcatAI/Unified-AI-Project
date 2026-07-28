"""
世界時鐘 (WorldClock) — 遊戲世界的時間引擎。

角色能根據世界時鐘來確定：
- 現在幾歲（出生年 vs 當前年）
- 什麼事件發生過
- 事件導致人生有啥不同
- 現在是死是活
- 生活圈啥樣
"""

from __future__ import annotations

import json
import os
import math
import hashlib
from pathlib import Path
from typing import Optional, Any, Dict, List

DATA_DIR = Path(__file__).resolve().parent / "data"
CLOCK_PATH = DATA_DIR / "world_clock.json"
CARDS_PATH = DATA_DIR / "game_cards.json"

# ── Cache ──
_CLOCK_DATA: dict | None = None
_CARDS_DATA: dict | None = None


def _load_clock() -> dict:
    global _CLOCK_DATA
    if _CLOCK_DATA is None:
        if not CLOCK_PATH.exists():
            raise FileNotFoundError(f"World clock data not found: {CLOCK_PATH}")
        with open(CLOCK_PATH, "r", encoding="utf-8") as f:
            _CLOCK_DATA = json.load(f)
    return _CLOCK_DATA


def _load_cards() -> dict:
    global _CARDS_DATA
    if _CARDS_DATA is None:
        if not CARDS_PATH.exists():
            raise FileNotFoundError(f"Card data not found: {CARDS_PATH}")
        with open(CARDS_PATH, "r", encoding="utf-8") as f:
            _CARDS_DATA = json.load(f)
    return _CARDS_DATA


def reload():
    """Force reload all data from disk."""
    global _CLOCK_DATA, _CARDS_DATA
    _CLOCK_DATA = None
    _CARDS_DATA = None


# ══════════════════════════════════════════════════════════════
# Core time accessors
# ══════════════════════════════════════════════════════════════

def get_current_year() -> int:
    """Get the current world year (靈子曆 AL)."""
    return _load_clock().get("current_year", 1024)


def get_current_month() -> int:
    return _load_clock().get("current_month", 3)


def get_current_day() -> int:
    return _load_clock().get("current_day", 15)


def get_days_per_month() -> int:
    return _load_clock().get("days_per_month", 30)


def get_months_per_year() -> int:
    return _load_clock().get("months_per_year", 12)


def set_current_time(year: int, month: int = 1, day: int = 1):
    """Update the current world time (in-memory only; call save() to persist)."""
    clock = _load_clock()
    clock["current_year"] = year
    clock["current_month"] = month
    clock["current_day"] = day


def save():
    """Persist current world clock to disk."""
    clock = _load_clock()
    with open(CLOCK_PATH, "w", encoding="utf-8") as f:
        json.dump(clock, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════
# Era detection
# ══════════════════════════════════════════════════════════════

def get_eras() -> list[dict]:
    """Get all era definitions."""
    return _load_clock().get("eras", [])


def get_era(year: int | None = None) -> dict | None:
    """Get the era definition for a given year (default: current year)."""
    if year is None:
        year = get_current_year()
    clock = _load_clock()
    for era in clock.get("eras", []):
        if era["start_year"] <= year <= era["end_year"]:
            return era
    return None


def get_era_name(year: int | None = None) -> str:
    """Get the Chinese era name for a given year."""
    era = get_era(year)
    return era["name"] if era else "未知紀元"


def get_era_name_en(year: int | None = None) -> str:
    era = get_era(year)
    return era["name_en"] if era else "Unknown Era"


# ══════════════════════════════════════════════════════════════
# Event queries
# ══════════════════════════════════════════════════════════════

def get_all_events() -> list[dict]:
    """Get all major world events."""
    return _load_clock().get("major_events", [])


def get_events_by_year(year: int) -> list[dict]:
    """Get events that occurred in a specific year."""
    return [e for e in get_all_events() if e.get("year") == year]


def get_events_in_range(start_year: int, end_year: int) -> list[dict]:
    """Get events in a year range (inclusive)."""
    return [e for e in get_all_events() if start_year <= e.get("year", 0) <= end_year]


def get_events_by_era(era_id: str) -> list[dict]:
    """Get events belonging to a specific era."""
    return [e for e in get_all_events() if e.get("era") == era_id]


def get_events_before(year: int) -> list[dict]:
    """Get events that happened before a given year."""
    return [e for e in get_all_events() if e.get("year", 0) < year]


def get_events_after(year: int) -> list[dict]:
    """Get events that happened after a given year."""
    return [e for e in get_all_events() if e.get("year", 0) > year]


def event_has_occurred(event_id: str, current_year: int | None = None) -> bool:
    """Check if a specific event has occurred by the current year."""
    if current_year is None:
        current_year = get_current_year()
    for e in get_all_events():
        if e.get("id") == event_id:
            return e.get("year", 0) <= current_year
    return False


def get_event(event_id: str) -> dict | None:
    """Get a specific event by ID."""
    for e in get_all_events():
        if e.get("id") == event_id:
            return dict(e)
    return None


def get_event_by_name(name: str) -> dict | None:
    """Get a specific event by name (for runtime event display)."""
    for e in get_all_events():
        if e.get("name") == name:
            return dict(e)
    return None


# ══════════════════════════════════════════════════════════════
# Start time selection & past event resolution
# ══════════════════════════════════════════════════════════════

def get_era_start_year_options() -> list[dict]:
    """Get curated start year options by era for easier player selection.

    Start years are chosen so that most NPCs are alive at game start.
    Earliest viable start is ~950 when the oldest non-immortal NPCs are born.
    """
    current = get_current_year()
    return [
        {"label": "當前 (靈子曆 1024年)", "year": current,
         "desc": "現在。世界正處於動盪之中，迴廊共鳴事件剛過去4年。"},
        {"label": "迴廊共鳴後 (靈子曆 1020年)", "year": 1020,
         "desc": "迴廊共鳴事件當年。多個世界線交疊，混亂與機遇並存。"},
        {"label": "鏡湖異變時 (靈子曆 1010年)", "year": 1010,
         "desc": "鏡湖深處的迴廊入口出現異常，概念實體開始在物質世界具現化。"},
        {"label": "千年轉折 (靈子曆 1000年)", "year": 1000,
         "desc": "靈子曆第二個千年。世界各地出現異常概念波動，預言中的動盪時代開始。"},
        {"label": "新世界集團活躍期 (靈子曆 950年)", "year": 950,
         "desc": "新世界集團開始浮上檯面。年輕一代角色陸續出生，動盪前的寧靜。"},
    ]


def resolve_past_events(start_year: int, seed: str = "") -> dict:
    """Pseudo-randomly resolve world events that occurred before start_year.

    Uses a seeded RNG for deterministic results. Probabilities are weighted
    to favor the player (~65% favorable outcome).

    Returns a dict of {event_id: {favorable, event_name, description, ...}}
    """
    events = get_events_before(start_year)
    result = {}

    for evt in events:
        eid = evt.get("id", "?")
        ename = evt.get("name", "?")
        etype = evt.get("type", "unknown")

        # Create deterministic seed
        raw_seed = f"{seed}_{eid}_{start_year}"
        hash_val = int(hashlib.md5(raw_seed.encode()).hexdigest()[:8], 16)
        rng_val = (hash_val % 10000) / 10000.0

        # Base favorable probability: 65%, adjusted by event type
        type_bonus = {
            "disaster": -0.1, "war": -0.05, "world_forming": 0.0,
            "discovery": 0.1, "technological": 0.1, "political": 0.05, "cultural": 0.15,
        }
        favorable_threshold = max(0.3, min(0.85, 0.65 + type_bonus.get(etype, 0.0)))
        favorable = rng_val < favorable_threshold

        # Use event-specific outcome descriptions when available
        fav_desc = evt.get("favorable_outcome") or "在混亂中出現了轉機，局勢朝著有利的方向發展"
        unfav_desc = evt.get("unfavorable_outcome") or "事件留下了深刻的傷痕，其影響至今仍在"
        desc = f"{ename} — {fav_desc if favorable else unfav_desc}"

        result[eid] = {
            "resolved": True,
            "favorable": favorable,
            "event_name": ename,
            "description": desc,
            "roll": round(rng_val, 4),
            "threshold": round(favorable_threshold, 4),
        }

    return result


# ══════════════════════════════════════════════════════════════
# Character time queries (from game_cards.json)
# ══════════════════════════════════════════════════════════════

def get_card(card_id: str) -> dict | None:
    """Get a card by its ID from game_cards.json."""
    cards = _load_cards().get("cards", [])
    for c in cards:
        if c.get("card_id") == card_id:
            return c
    return None


def get_character_time_data(card_id: str) -> dict | None:
    """Get the time_data block from a character card (if enriched)."""
    card = get_card(card_id)
    if card is None:
        return None
    return card.get("time_data")


def get_character_birth_year(card_id: str) -> int | None:
    """Get the birth year of a character."""
    td = get_character_time_data(card_id)
    if td:
        return td.get("birth_year")
    # Fallback: check stats
    card = get_card(card_id)
    if card and "age" in card.get("stats", {}):
        age = card["stats"]["age"]
        if isinstance(age, (int, float)):
            return get_current_year() - int(age)
    return None


def get_character_death_year(card_id: str) -> int | None:
    """Get the death year of a character (None if still alive)."""
    td = get_character_time_data(card_id)
    if td:
        return td.get("death_year")
    return None


def get_character_age(card_id: str, at_year: int | None = None) -> int | None:
    """Calculate a character's age at a given year (default: current).
    Returns None if character is not yet born at the given year.
    Returns age at death if character died before the given year."""
    if at_year is None:
        at_year = get_current_year()
    birth = get_character_birth_year(card_id)
    if birth is None:
        return None
    if at_year < birth:
        return None  # Not yet born
    death = get_character_death_year(card_id)
    if death is not None and at_year > death:
        # Dead at that point — return age at death
        return death - birth
    return at_year - birth


def is_character_alive(card_id: str, at_year: int | None = None) -> bool:
    """Check if a character is alive at a given year."""
    if at_year is None:
        at_year = get_current_year()
    birth = get_character_birth_year(card_id)
    if birth is None:
        return True  # Unknown = assumed alive (immortal concepts, etc.)
    death = get_character_death_year(card_id)
    if death is not None and at_year > death:
        return False
    if death is not None and at_year < birth:
        return False  # Not yet born
    return at_year >= birth


def get_character_life_stage(card_id: str, at_year: int | None = None) -> dict | None:
    """Get the current life stage of a character at a given year.

    Returns the life_stage entry whose year range contains at_year.
    """
    if at_year is None:
        at_year = get_current_year()
    td = get_character_time_data(card_id)
    if not td:
        return None
    stages = td.get("life_stages", [])
    for stage in stages:
        start = stage.get("start_year", -9999)
        end = stage.get("end_year", 9999)
        if start <= at_year <= end:
            return stage
    return None


def get_character_status_summary(card_id: str, at_year: int | None = None) -> dict:
    """Get a comprehensive status summary for a character.

    Returns:
        {
            "alive": bool,
            "age": int or None,
            "era": str,
            "life_stage": str or None,
            "birth_year": int or None,
            "death_year": int or None,
            "events_lived_through": list[str],
            "location": str or None,
        }
    """
    if at_year is None:
        at_year = get_current_year()

    card = get_card(card_id)
    td = get_character_time_data(card_id) if card_id else None
    birth = get_character_birth_year(card_id)
    death = get_character_death_year(card_id)
    alive = is_character_alive(card_id, at_year)
    age = get_character_age(card_id, at_year)
    stage = get_character_life_stage(card_id, at_year)

    # Events this character has lived through
    events_lived = []
    if birth is not None:
        evt_end = death if (death is not None and death <= at_year) else at_year
        for e in get_events_in_range(birth, evt_end):
            events_lived.append(e.get("name", "?"))
    else:
        # For immortal beings, show events up to current year
        for e in get_events_before(at_year + 1):
            events_lived.append(e.get("name", "?"))

    # Location from card stats or time_data
    location = None
    if card:
        stats = card.get("stats", {})
        location = stats.get("location") or stats.get("位置")
    if not location and stage:
        location = stage.get("location")
    if not location and card:
        location = card.get("location")

    return {
        "alive": alive,
        "age": age,
        "era": get_era_name(at_year),
        "life_stage": stage.get("name") if stage else None,
        "birth_year": birth,
        "death_year": death,
        "events_lived_through": events_lived,
        "location": location,
        "current_year": at_year,
    }


# ══════════════════════════════════════════════════════════════
# Time advancement
# ══════════════════════════════════════════════════════════════

def advance_time(hours: int = 1) -> dict:
    """Advance the world clock by a number of hours.

    Returns a dict with changes that occurred:
        {
            "day_passed": bool,
            "month_passed": bool,
            "year_passed": bool,
            "new_year": int,
            "new_month": int,
            "new_day": int,
            "era_changed": bool,
            "new_era": str or None,
            "events_triggered": list[str],
        }
    """
    clock = _load_clock()
    days_per_month = clock.get("days_per_month", 30)
    months_per_year = clock.get("months_per_year", 12)

    old_year = clock["current_year"]
    old_month = clock["current_month"]
    old_day = clock["current_day"]
    old_era_id = get_era(old_year).get("id") if get_era(old_year) else None

    # Convert hours → days (24h per day)
    total_minutes = hours * 60
    days_to_add = total_minutes // (24 * 60)  # Full days
    remaining_hours = (total_minutes % (24 * 60)) // 60  # Remainder hours

    # Apply days
    new_day = old_day + days_to_add
    new_month = old_month
    new_year = old_year

    while new_day > days_per_month:
        new_day -= days_per_month
        new_month += 1
        if new_month > months_per_year:
            new_month = 1
            new_year += 1

    clock["current_day"] = new_day
    clock["current_month"] = new_month
    clock["current_year"] = new_year

    # Detect changes
    day_passed = new_day != old_day
    month_passed = new_month != old_month
    year_passed = new_year != old_year

    new_era_id = get_era(new_year).get("id") if get_era(new_year) else None
    era_changed = new_era_id != old_era_id

    # Events triggered by this time advancement
    events_triggered = []
    if year_passed or era_changed:
        for evt in get_events_by_year(new_year):
            events_triggered.append(evt.get("name", "?"))

    return {
        "day_passed": day_passed,
        "month_passed": month_passed,
        "year_passed": year_passed,
        "new_year": new_year,
        "new_month": new_month,
        "new_day": new_day,
        "era_changed": era_changed,
        "new_era": get_era_name(new_year) if era_changed else None,
        "events_triggered": events_triggered,
    }


# ══════════════════════════════════════════════════════════════
# Season helpers
# ══════════════════════════════════════════════════════════════

def get_season(year: int | None = None, month: int | None = None) -> str:
    """Get the season name for a given year and month."""
    if month is None:
        month = get_current_month()
    if year is None:
        year = get_current_year()

    clock = _load_clock()
    seasons = clock.get("season_cycle", {})

    for sid, sdata in seasons.items():
        if sdata["start_month"] <= month <= sdata["end_month"]:
            return sdata["name"]
    return "春"  # Default


def get_season_en(year: int | None = None, month: int | None = None) -> str:
    if month is None:
        month = get_current_month()
    clock = _load_clock()
    seasons = clock.get("season_cycle", {})
    for sid, sdata in seasons.items():
        if sdata["start_month"] <= month <= sdata["end_month"]:
            return sdata["name_en"]
    return "Spring"


# ══════════════════════════════════════════════════════════════
# Landmark queries
# ══════════════════════════════════════════════════════════════

def get_landmark(name: str) -> dict | None:
    """Get information about a world landmark."""
    landmarks = _load_clock().get("world_landmarks", {})
    return landmarks.get(name)


def get_landmark_age(name: str, at_year: int | None = None) -> int | None:
    """Calculate how many years old a landmark is at a given year."""
    if at_year is None:
        at_year = get_current_year()
    lm = get_landmark(name)
    if lm is None:
        return None
    founded = lm.get("founded_year") or lm.get("discovered_year")
    if founded is None:
        return None
    return at_year - founded


# ══════════════════════════════════════════════════════════════
# Timeline display
# ══════════════════════════════════════════════════════════════

def format_date(year: int | None = None, month: int | None = None, day: int | None = None) -> str:
    """Format a date as '靈子曆 YYYY年M月D日'."""
    if year is None:
        year = get_current_year()
    if month is None:
        month = get_current_month()
    if day is None:
        day = get_current_day()
    return f"靈子曆 {year}年{month}月{day}日"


def format_era_date(year: int | None = None, month: int | None = None, day: int | None = None) -> str:
    """Format with era prefix: '平衡紀元·靈子曆 750年3月15日'."""
    if year is None:
        year = get_current_year()
    era_name = get_era_name(year)
    date = format_date(year, month, day)
    return f"{era_name}·{date}"


def print_timeline(start_year: int | None = None, end_year: int | None = None, max_events: int = 20):
    """Print a formatted timeline of events."""
    if start_year is None:
        start_year = 0
    if end_year is None:
        end_year = get_current_year()

    events = get_events_in_range(start_year, end_year)
    events.sort(key=lambda e: e.get("year", 0))

    print(f"\n{'='*60}")
    print(f"  世界時間線 ({format_era_date()})")
    print(f"{'='*60}")

    for evt in events[:max_events]:
        year = evt.get("year", 0)
        era = get_era_name(year)
        name = evt.get("name", "?")
        desc = evt.get("description", "")
        icon = {
            "world_forming": "🌍",
            "discovery": "🔬",
            "technological": "⚙️",
            "war": "⚔️",
            "political": "🏛️",
            "cultural": "📚",
            "disaster": "⚠️",
        }.get(evt.get("type", ""), "📌")
        year_str = f"{year}" if year >= 0 else f"{abs(year)} BC"
        print(f"\n  {icon} [{year_str}] {era}")
        print(f"     {name}")
        if desc:
            print(f"     {desc[:80]}")

    print(f"\n{'='*60}")


# ══════════════════════════════════════════════════════════════
# Integrated time string for game display
# ══════════════════════════════════════════════════════════════

def get_full_time_string(hour: int = 8) -> str:
    """Get a full time string for game display, including era and season."""
    year = get_current_year()
    month = get_current_month()
    day = get_current_day()
    season = get_season()
    era = get_era_name()

    # Chinese time period
    periods = {
        0: "子時·深夜", 2: "丑時·凌晨", 4: "寅時·黎明",
        6: "卯時·清晨", 8: "辰時·早晨", 10: "巳時·近午",
        12: "午時·正午", 14: "未時·午後", 16: "申時·傍晚",
        18: "酉時·黃昏", 20: "戌時·夜晚", 22: "亥時·深夜"
    }
    period = periods.get(hour // 2 * 2, f"{hour}:00")

    return f"{era}·{season}·{format_date(year, month, day)} {period}"
