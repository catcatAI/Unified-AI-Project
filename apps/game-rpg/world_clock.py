"""
世界時鐘 (WorldClock) — 多元宇宙的時間引擎。

依卡片文本（《世界線錨定 — 補充欄位》/《世界線總表》/ CC-32 學府曆 / CC-38 迴廊原生種）：
- 每個世界線擁有自己的時鐘、曆法與時間錨點（W01-A 冷戰線、W01-B 大正線、
  W01-C 灰燼線、W02 琥珀紀元、W03 軌道、W04 灰燼紀元、SL-10 魔女學府、
  迴廊／多元）。
- 「整體時鐘」(master_clock) 只存在於程式碼中（文本外），用於跨線換算
  （如學府曆與 W01 時間流速比約 1:7），不向玩家顯示。
- 迴廊原生種（如晞咕萊雅）時間錨點不固定；各故事線（艦娘世界、秋狐神明
  世界等）以內部相對年標記，不對應統一曆法。

角色能根據世界時鐘來確定：
- 現在幾歲（出生年 vs 所屬世界線當前年）
- 什麼事件發生過
- 事件導致人生有啥不同
- 現在是死是活
- 生活圈啥樣
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
CLOCK_PATH = DATA_DIR / "world_clock.json"
CARDS_PATH = DATA_DIR / "game_cards.json"

# 向後相容：未指定世界線時預設的活躍世界線
_DEFAULT_WORLD_LINE = "W01-A"

# ── Cache ──
_CLOCK_DATA: dict | None = None
_CARDS_DATA: dict | None = None

# master 鐘「不足一天」的累積（僅記憶體，不持久化）
_MASTER_DAY_ACCUM = 0.0


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
# World line queries
# ══════════════════════════════════════════════════════════════

def get_active_world_line() -> str:
    """Get the currently active world line id (e.g. 'W01-A')."""
    clock = _load_clock()
    return clock.get("active_world_line", _DEFAULT_WORLD_LINE)


def set_active_world_line(wl_id: str) -> str:
    """Switch the active world line (in-memory only; call save() to persist)."""
    clock = _load_clock()
    if wl_id not in clock.get("world_lines", {}):
        raise KeyError(f"Unknown world line: {wl_id}")
    clock["active_world_line"] = wl_id
    return wl_id


def get_master_clock() -> dict:
    """Get the hidden master clock (text-external, used for cross-line conversion)."""
    return _load_clock().get("master_clock", {})


def get_world_lines() -> dict:
    """Get all world line definitions keyed by id."""
    return _load_clock().get("world_lines", {})


def get_world_line(wl_id: str | None = None) -> dict:
    """Get a world line definition (default: active world line)."""
    clock = _load_clock()
    wl = wl_id or clock.get("active_world_line", _DEFAULT_WORLD_LINE)
    lines = clock.get("world_lines", {})
    if wl in lines:
        return lines[wl]
    return lines.get(_DEFAULT_WORLD_LINE, {})


def get_world_line_name(wl_id: str | None = None) -> str:
    """Get the display name of a world line."""
    line = get_world_line(wl_id)
    return line.get("name", wl_id or get_active_world_line())


def get_world_line_ids() -> list[str]:
    """Get all world line ids."""
    return list(_load_clock().get("world_lines", {}).keys())


def get_calendar(wl_id: str | None = None) -> str:
    """Get the calendar label of a world line (e.g. 西曆 / 學府曆)."""
    return get_world_line(wl_id).get("calendar", "西曆")


def get_time_anchor(wl_id: str | None = None) -> str:
    """Get the time anchor description of a world line."""
    return get_world_line(wl_id).get("time_anchor", "未知")


def get_time_flow_ratio(wl_id: str | None = None) -> float | None:
    """Get years-per-master-year flow ratio of a world line (None if timeless)."""
    r = get_world_line(wl_id).get("years_per_master_year")
    return r if isinstance(r, (int, float)) else None


# ══════════════════════════════════════════════════════════════
# Core time accessors (world-line aware; default = active line)
# ══════════════════════════════════════════════════════════════

def get_current_year(wl_id: str | None = None) -> int | None:
    """Get the current year of a world line (None if the line has no fixed time)."""
    return get_world_line(wl_id).get("current_year")


def get_current_month(wl_id: str | None = None) -> int | None:
    return get_world_line(wl_id).get("current_month")


def get_current_day(wl_id: str | None = None) -> int | None:
    return get_world_line(wl_id).get("current_day")


def get_days_per_month(wl_id: str | None = None) -> int:
    return get_world_line(wl_id).get("days_per_month", 30)


def get_months_per_year(wl_id: str | None = None) -> int:
    return get_world_line(wl_id).get("months_per_year", 12)


def set_current_time(year: int | None, month: int = 1, day: int = 1, wl_id: str | None = None):
    """Update the current time of a world line (in-memory; call save() to persist).

    The hidden master clock is re-aligned so cross-line conversion stays consistent.
    """
    clock = _load_clock()
    wl_id = wl_id or clock.get("active_world_line", _DEFAULT_WORLD_LINE)
    line = get_world_line(wl_id)
    old_year = line.get("current_year")
    line["current_year"] = year
    line["current_month"] = month
    line["current_day"] = day
    # Re-align master clock (hidden): master + (Δline_year / ratio)
    ratio = get_time_flow_ratio(wl_id)
    if ratio and ratio > 0 and old_year is not None and year is not None:
        master = clock.get("master_clock", {})
        if master:
            master["current_year"] = int(round(
                master.get("current_year", year) + (year - old_year) / ratio
            ))


def save():
    """Persist world clock (all world lines + master clock) to disk."""
    clock = _load_clock()
    with open(CLOCK_PATH, "w", encoding="utf-8") as f:
        json.dump(clock, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════
# Master clock conversion (hidden, text-external)
# ══════════════════════════════════════════════════════════════

def _master_base() -> tuple[int | None, int | None]:
    """Return (master_current_year, line_current_year) base pair."""
    master = get_master_clock()
    line = get_world_line()
    return master.get("current_year"), line.get("current_year")


def master_to_world(master_year: int, wl_id: str | None = None) -> int | None:
    """Convert a master-clock year to a world line year (None if timeless line)."""
    line = get_world_line(wl_id)
    ratio = line.get("years_per_master_year")
    line_year = line.get("current_year")
    master_year_now = get_master_clock().get("current_year")
    if not ratio or ratio <= 0 or line_year is None or master_year_now is None:
        return None
    return int(round(line_year + (master_year - master_year_now) * ratio))


def world_to_master(year: int, wl_id: str | None = None) -> int | None:
    """Convert a world line year to master-clock year (None if timeless line)."""
    line = get_world_line(wl_id)
    ratio = line.get("years_per_master_year")
    line_year = line.get("current_year")
    master_year_now = get_master_clock().get("current_year")
    if not ratio or ratio <= 0 or line_year is None or master_year_now is None:
        return None
    return int(round(master_year_now + (year - line_year) / ratio))


def convert_between_lines(year: int, from_wl: str, to_wl: str) -> int | None:
    """Convert a year from one world line's calendar to another via the hidden master clock."""
    m = world_to_master(year, from_wl)
    if m is None:
        return None
    return master_to_world(m, to_wl)


def format_master_year(master_year: int) -> str:
    """Format a master-clock year (text-external, usually not displayed)."""
    return f"整體時鐘 {master_year}"


# ══════════════════════════════════════════════════════════════
# Era detection (world-line aware)
# ══════════════════════════════════════════════════════════════

def get_eras(wl_id: str | None = None) -> list[dict]:
    """Get all era definitions of a world line."""
    return get_world_line(wl_id).get("eras", [])


def get_era(year: int | None = None, wl_id: str | None = None) -> dict | None:
    """Get the era definition for a given year (default: line's current year)."""
    if year is None:
        year = get_current_year(wl_id)
    if year is None:
        return None
    for era in get_eras(wl_id):
        if era["start_year"] <= year <= era["end_year"]:
            return era
    return None


def get_era_name(year: int | None = None, wl_id: str | None = None) -> str:
    """Get the Chinese era name for a given year."""
    era = get_era(year, wl_id)
    return era["name"] if era else "未知紀元"


def get_era_name_en(year: int | None = None, wl_id: str | None = None) -> str:
    era = get_era(year, wl_id)
    return era["name_en"] if era else "Unknown Era"


# ══════════════════════════════════════════════════════════════
# Event queries (world-line aware; get_event* by id/name search all lines)
# ══════════════════════════════════════════════════════════════

def get_all_events(wl_id: str | None = None) -> list[dict]:
    """Get all major world events of a world line (default: active line)."""
    return get_world_line(wl_id).get("events", [])


def _all_events_across_lines() -> list[dict]:
    """Get events from every world line (for id/name lookups)."""
    out = []
    for line in get_world_lines().values():
        out.extend(line.get("events", []))
    return out


def get_events_by_year(year: int, wl_id: str | None = None) -> list[dict]:
    """Get events that occurred in a specific year (on a world line)."""
    return [e for e in get_all_events(wl_id) if e.get("year") == year]


def get_events_in_range(start_year: int, end_year: int, wl_id: str | None = None) -> list[dict]:
    """Get events in a year range (inclusive) on a world line."""
    return [e for e in get_all_events(wl_id)
            if e.get("year") is not None and start_year <= e["year"] <= end_year]


def get_events_by_era(era_id: str, wl_id: str | None = None) -> list[dict]:
    """Get events belonging to a specific era on a world line."""
    return [e for e in get_all_events(wl_id) if e.get("era") == era_id]


def get_events_before(year: int, wl_id: str | None = None) -> list[dict]:
    """Get events that happened before a given year on a world line."""
    if year is None:
        return []
    return [e for e in get_all_events(wl_id)
            if e.get("year") is not None and e["year"] < year]


def get_events_after(year: int, wl_id: str | None = None) -> list[dict]:
    """Get events that happened after a given year on a world line."""
    if year is None:
        return []
    return [e for e in get_all_events(wl_id)
            if e.get("year") is not None and e["year"] > year]


def event_has_occurred(event_id: str, current_year: int | None = None, wl_id: str | None = None) -> bool:
    """Check if a specific event has occurred by the current year (of a world line)."""
    if current_year is None:
        current_year = get_current_year(wl_id)
    for e in _all_events_across_lines():
        if e.get("id") == event_id:
            ey = e.get("year")
            return ey is not None and current_year is not None and ey <= current_year
    return False


def get_event(event_id: str) -> dict | None:
    """Get a specific event by ID (searches all world lines)."""
    for e in _all_events_across_lines():
        if e.get("id") == event_id:
            return dict(e)
    return None


def get_event_by_name(name: str) -> dict | None:
    """Get a specific event by name (searches all world lines)."""
    for e in _all_events_across_lines():
        if e.get("name") == name:
            return dict(e)
    return None


# ══════════════════════════════════════════════════════════════
# Start time selection & past event resolution (world-line aware)
# ══════════════════════════════════════════════════════════════

def get_era_start_year_options(wl_id: str | None = None) -> list[dict]:
    """Get curated start year options by era for the given world line.

    Start years are derived from the line's own events so the player starts at
    meaningful moments on that line's calendar. Timeless lines (迴廊) return a
    single option with year=None.
    """
    line = get_world_line(wl_id)
    wl_id = line.get("id", wl_id or get_active_world_line())
    calendar = line.get("calendar", "西曆")
    current = line.get("current_year")

    if current is None:
        return [{
            "label": "當前（時間錨點不固定）",
            "year": None,
            "desc": f"{line.get('name', wl_id)}沒有固定曆法，時間由敘事決定。",
        }]

    options = [{
        "label": f"當前（{calendar} {current}年）",
        "year": current,
        "desc": "現在。",
    }]
    seen = {current}
    for e in sorted(line.get("events", []), key=lambda x: x.get("year") or 0, reverse=True):
        ey = e.get("year")
        if ey is None or ey >= current or ey in seen:
            continue
        seen.add(ey)
        options.append({
            "label": f"{e.get('name', '?')}（{calendar} {ey}年）",
            "year": ey,
            "desc": (e.get("description") or "")[:60],
        })
        if len(options) >= 5:
            break
    return options


def resolve_past_events(start_year: int, seed: str = "", wl_id: str | None = None) -> dict:
    """Pseudo-randomly resolve world events (of a world line) before start_year.

    Uses a seeded RNG for deterministic results. Probabilities are weighted
    to favor the player (~65% favorable outcome).

    Returns a dict of {event_id: {favorable, event_name, description, ...}}
    """
    if start_year is None:
        return {}
    events = get_events_before(start_year, wl_id)
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
# Character time queries (world-line aware, from game_cards.json)
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


def get_character_world_line(card_id: str) -> str | None:
    """Determine which world line a character belongs to (from time_data/stats)."""
    td = get_character_time_data(card_id)
    if td and td.get("world_line"):
        return td["world_line"]
    card = get_card(card_id)
    if card:
        stats = card.get("stats", {})
        wl = stats.get("world_line") or stats.get("主世界線") or stats.get("worldline")
        if wl:
            return wl
    return None


def _resolve_character_line(card_id: str) -> str:
    """Resolve a character's world line with fallback to the active line."""
    wl = get_character_world_line(card_id)
    return wl if wl else get_active_world_line()


def _resolve_line_year(wl_id: str | None, card_id: str | None = None) -> int | None:
    """Resolve a usable reference year for a world line.

    Timeless lines (CORRIDOR/MULTI) fall back to their internal relative year
    marker when one is defined.
    """
    line = get_world_line(wl_id)
    y = line.get("current_year")
    if y is not None:
        return y
    y = line.get("internal_current_year")
    if y is not None:
        return y
    if card_id:
        td = get_character_time_data(card_id)
        if td and td.get("internal_current_year") is not None:
            return td["internal_current_year"]
    return None


def get_character_birth_year(card_id: str) -> int | None:
    """Get the birth year of a character (on their own world line's calendar)."""
    td = get_character_time_data(card_id)
    if td:
        return td.get("birth_year")
    # Fallback: check stats
    card = get_card(card_id)
    if card and "age" in card.get("stats", {}):
        age = card["stats"]["age"]
        if isinstance(age, (int, float)):
            wl = _resolve_character_line(card_id)
            ref = _resolve_line_year(wl, card_id)
            if ref is not None:
                return ref - int(age)
    return None


def get_character_death_year(card_id: str) -> int | None:
    """Get the death year of a character (None if still alive)."""
    td = get_character_time_data(card_id)
    if td:
        return td.get("death_year")
    return None


def get_character_age(card_id: str, at_year: int | None = None, wl_id: str | None = None) -> int | None:
    """Calculate a character's age at a given year (default: their world line's current year).

    Returns None if the character's timeline is unfixed (迴廊原生種) or they are
    not yet born at the given year. Returns age at death if they died before.
    """
    wl = wl_id or _resolve_character_line(card_id)
    if at_year is None:
        at_year = _resolve_line_year(wl, card_id)
    if at_year is None:
        return None
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


def is_character_alive(card_id: str, at_year: int | None = None, wl_id: str | None = None) -> bool:
    """Check if a character is alive at a given year (default: their line's current)."""
    wl = wl_id or _resolve_character_line(card_id)
    if at_year is None:
        at_year = _resolve_line_year(wl, card_id)
    birth = get_character_birth_year(card_id)
    if birth is None:
        return True  # Unknown / unfixed timeline = assumed alive (immortal concepts, etc.)
    death = get_character_death_year(card_id)
    if at_year is None:
        # No reference year on a timeless line — assume alive unless dead
        return death is None
    if death is not None and at_year > death:
        return False
    if death is not None and at_year < birth:
        return False  # Not yet born
    return at_year >= birth


def get_character_life_stage(card_id: str, at_year: int | None = None, wl_id: str | None = None) -> dict | None:
    """Get the current life stage of a character at a given year.

    Returns the life_stage entry whose year range contains at_year; on timeless
    lines (no fixed year) returns the first (narrative-order) stage.
    """
    wl = wl_id or _resolve_character_line(card_id)
    if at_year is None:
        at_year = _resolve_line_year(wl, card_id)
    td = get_character_time_data(card_id)
    if not td:
        return None
    stages = td.get("life_stages", [])
    if at_year is None:
        return stages[0] if stages else None
    for stage in stages:
        start = stage.get("start_year", -9999)
        end = stage.get("end_year", 9999)
        if start is None or end is None:
            # 時間錨點不固定的階段（迴廊原生種）：任何時間都適用
            return stage
        if start <= at_year <= end:
            return stage
    return None


def get_character_status_summary(card_id: str, at_year: int | None = None, wl_id: str | None = None) -> dict:
    """Get a comprehensive status summary for a character.

    Defaults to the character's own world line and that line's current year, so
    e.g. 大正線角色照西曆 1920s 計算，迴廊原生種顯示「時間錨點不固定」。

    Returns:
        {
            "alive": bool, "age": int or None, "era": str, "life_stage": str or None,
            "birth_year": int or None, "death_year": int or None,
            "events_lived_through": list[str], "location": str or None,
            "world_line": str, "world_line_name": str, "calendar": str,
            "current_year": int or None,
        }
    """
    wl = wl_id or _resolve_character_line(card_id)
    line = get_world_line(wl)
    calendar = line.get("calendar", "西曆")
    if at_year is None:
        at_year = _resolve_line_year(wl, card_id)

    card = get_card(card_id)
    td = get_character_time_data(card_id) if card_id else None
    birth = get_character_birth_year(card_id)
    death = get_character_death_year(card_id)
    alive = is_character_alive(card_id, at_year, wl)
    age = get_character_age(card_id, at_year, wl)
    stage = get_character_life_stage(card_id, at_year, wl)

    # Events this character has lived through
    events_lived = []
    if at_year is None:
        # Timeless line: surface concept-level events from all lines
        for e in _all_events_across_lines():
            events_lived.append(e.get("name", "?"))
    elif birth is not None:
        evt_end = death if (death is not None and death <= at_year) else at_year
        for e in get_events_in_range(birth, evt_end, wl):
            events_lived.append(e.get("name", "?"))
    else:
        for e in get_events_before(at_year + 1, wl):
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

    if at_year is None:
        era = "（時間錨點不固定）"
    else:
        era = get_era_name(at_year, wl)

    return {
        "alive": alive,
        "age": age,
        "era": era,
        "life_stage": stage.get("name") if stage else None,
        "birth_year": birth,
        "death_year": death,
        "events_lived_through": events_lived,
        "location": location,
        "current_year": at_year,
        "world_line": wl,
        "world_line_name": line.get("name", wl),
        "calendar": calendar,
    }


# ══════════════════════════════════════════════════════════════
# Time advancement (world-line aware)
# ══════════════════════════════════════════════════════════════

def advance_time(hours: int = 1, wl_id: str | None = None) -> dict:
    """Advance a world line's clock by a number of hours (default: active line).

    The hidden master clock advances proportionally (÷ time-flow ratio) so
    cross-line conversion stays consistent.

    Returns a dict with changes that occurred:
        {
            "day_passed": bool, "month_passed": bool, "year_passed": bool,
            "new_year": int|None, "new_month": int|None, "new_day": int|None,
            "era_changed": bool, "new_era": str or None,
            "events_triggered": list[str], "world_line": str, "timeless": bool,
        }
    """
    global _MASTER_DAY_ACCUM
    clock = _load_clock()
    wl_id = wl_id or clock.get("active_world_line", _DEFAULT_WORLD_LINE)
    line = get_world_line(wl_id)

    if line.get("current_year") is None:
        # Timeless line (迴廊/多元): no calendar to advance
        return {
            "day_passed": False, "month_passed": False, "year_passed": False,
            "new_year": None, "new_month": None, "new_day": None,
            "era_changed": False, "new_era": None, "events_triggered": [],
            "world_line": wl_id, "timeless": True,
        }

    days_per_month = line.get("days_per_month", 30)
    months_per_year = line.get("months_per_year", 12)

    old_year = line["current_year"]
    old_month = line["current_month"]
    old_day = line["current_day"]
    old_era = get_era(old_year, wl_id)
    old_era_id = old_era.get("id") if old_era else None

    # Convert hours → days (24h per day)
    days_to_add = hours // 24
    new_day = old_day + days_to_add
    new_month = old_month
    new_year = old_year
    while new_day > days_per_month:
        new_day -= days_per_month
        new_month += 1
        if new_month > months_per_year:
            new_month = 1
            new_year += 1

    line["current_day"] = new_day
    line["current_month"] = new_month
    line["current_year"] = new_year

    # Detect changes
    day_passed = new_day != old_day
    month_passed = new_month != old_month
    year_passed = new_year != old_year

    new_era = get_era(new_year, wl_id)
    new_era_id = new_era.get("id") if new_era else None
    era_changed = new_era_id != old_era_id

    # Events triggered by this time advancement
    events_triggered = []
    if year_passed or era_changed:
        for evt in get_events_by_year(new_year, wl_id):
            events_triggered.append(evt.get("name", "?"))

    # Advance hidden master clock proportionally (ratio = years_per_master_year)
    ratio = get_time_flow_ratio(wl_id)
    if ratio and ratio > 0:
        master = clock.get("master_clock")
        if master and master.get("current_year") is not None:
            _MASTER_DAY_ACCUM += hours / 24.0 / ratio
            mdpm = master.get("days_per_month", 30)
            mmpy = master.get("months_per_year", 12)
            while _MASTER_DAY_ACCUM >= 1.0:
                _MASTER_DAY_ACCUM -= 1.0
                nd = master["current_day"] + 1
                nm = master["current_month"]
                ny = master["current_year"]
                if nd > mdpm:
                    nd = 1
                    nm += 1
                    if nm > mmpy:
                        nm = 1
                        ny += 1
                master["current_day"] = nd
                master["current_month"] = nm
                master["current_year"] = ny

    return {
        "day_passed": day_passed,
        "month_passed": month_passed,
        "year_passed": year_passed,
        "new_year": new_year,
        "new_month": new_month,
        "new_day": new_day,
        "era_changed": era_changed,
        "new_era": new_era["name"] if (era_changed and new_era) else None,
        "events_triggered": events_triggered,
        "world_line": wl_id,
        "timeless": False,
    }


# ══════════════════════════════════════════════════════════════
# Season helpers
# ══════════════════════════════════════════════════════════════

def get_season(year: int | None = None, month: int | None = None, wl_id: str | None = None) -> str:
    """Get the season name for a given year and month."""
    if month is None:
        month = get_current_month(wl_id)
    if month is None:
        return "春"
    clock = _load_clock()
    seasons = clock.get("season_cycle", {})
    for sid, sdata in seasons.items():
        if sdata["start_month"] <= month <= sdata["end_month"]:
            return sdata["name"]
    return "春"  # Default


def get_season_en(year: int | None = None, month: int | None = None, wl_id: str | None = None) -> str:
    if month is None:
        month = get_current_month(wl_id)
    if month is None:
        return "Spring"
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
    if at_year is None:
        return None
    lm = get_landmark(name)
    if lm is None:
        return None
    founded = lm.get("founded_year") or lm.get("discovered_year")
    if founded is None:
        return None
    return at_year - founded


# ══════════════════════════════════════════════════════════════
# Timeline display (world-line aware)
# ══════════════════════════════════════════════════════════════

def format_date(year: int | None = None, month: int | None = None, day: int | None = None,
                wl_id: str | None = None) -> str:
    """Format a date using a world line's own calendar, e.g. '西曆 1965年3月15日'."""
    line = get_world_line(wl_id)
    calendar = line.get("calendar", "西曆")
    y = line.get("current_year") if year is None else year
    m = line.get("current_month") if month is None else month
    d = line.get("current_day") if day is None else day
    if y is None:
        return f"{calendar}"
    if m is None or d is None:
        return f"{calendar} {y}年"
    return f"{calendar} {y}年{m}月{d}日"


def format_era_date(year: int | None = None, month: int | None = None, day: int | None = None,
                    wl_id: str | None = None) -> str:
    """Format with era prefix: '冷戰時期·西曆 1965年3月15日'.
    Timeless lines (迴廊/多元) return just their calendar label."""
    if get_current_year(wl_id) is None:
        return format_date(year, month, day, wl_id)
    era_name = get_era_name(year, wl_id)
    date = format_date(year, month, day, wl_id)
    return f"{era_name}·{date}"


def print_timeline(start_year: int | None = None, end_year: int | None = None,
                   max_events: int = 20, wl_id: str | None = None):
    """Print a formatted timeline of events for a world line."""
    line = get_world_line(wl_id)
    wl_name = line.get("name", wl_id or get_active_world_line())
    if start_year is None:
        start_year = 0
    if end_year is None:
        end_year = line.get("current_year")

    if end_year is None:
        # timeless line (迴廊/多元): show all events incl. year-less (concept) ones
        events = list(get_all_events(wl_id))
        events.sort(key=lambda e: (e.get("year") is None, e.get("year") or 0))
    else:
        events = get_events_in_range(start_year, end_year, wl_id)
        events.sort(key=lambda e: e.get("year") or 0)

    print(f"\n{'='*60}")
    print(f"  世界時間線 — {wl_name} ({format_era_date(wl_id=wl_id)})")
    print(f"{'='*60}")

    for evt in events[:max_events]:
        year = evt.get("year")
        era = get_era_name(year, wl_id)
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
        year_str = "∞" if year is None else f"{year}"
        print(f"\n  {icon} [{year_str}] {era}")
        print(f"     {name}")
        if desc:
            print(f"     {desc[:80]}")

    print(f"\n{'='*60}")


# ══════════════════════════════════════════════════════════════
# Integrated time string for game display (world-line aware)
# ══════════════════════════════════════════════════════════════

def get_full_time_string(hour: int = 8, wl_id: str | None = None) -> str:
    """Get a full time string for game display: world line, era, season, date, period."""
    line = get_world_line(wl_id)
    wl_name = line.get("name", wl_id or get_active_world_line())
    era = get_era_name(None, wl_id)
    season = get_season(None, None, wl_id)
    date = format_date(None, None, None, wl_id)
    year = line.get("current_year")
    if year is None:
        return f"{wl_name} · {season}·{date}"

    # Chinese time period
    periods = {
        0: "子時·深夜", 2: "丑時·凌晨", 4: "寅時·黎明",
        6: "卯時·清晨", 8: "辰時·早晨", 10: "巳時·近午",
        12: "午時·正午", 14: "未時·午後", 16: "申時·傍晚",
        18: "酉時·黃昏", 20: "戌時·夜晚", 22: "亥時·深夜",
    }
    period = periods.get(hour // 2 * 2, f"{hour}:00")

    return f"{wl_name} · {era}·{season}·{date} {period}"
