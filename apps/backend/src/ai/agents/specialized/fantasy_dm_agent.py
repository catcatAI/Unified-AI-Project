"""
Fantasy DM & Alchemy Agent
Responsible for Dungeon Master narration, Alchemy logic, and Fantasy RPG mechanics.
Migrated from 'Witch's Alchemy Chronicle' and 'TRPG Game' frontend logic.
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FantasyDMAgent:
    """Agent for generating RPG scenarios, creating characters, and resolving actions."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        self.config = config or {}
        self.agent_id = kwargs.get("agent_id")
        logger.info(f"FantasyDMAgent initialized with config: {self.config}")

    def handle_request(self, prompt: str) -> Dict[str, Any]:
        """Accept a natural-language request and delegate to the right method.

        WHY this exists: the intent table maps `roleplay` to this agent, but the
        router passes the user's message under generic keys (message/query/prompt/
        text), while every method here takes domain parameters (`setting`,
        `character_class`, `race`). The adapter therefore filled `setting` with a
        default and every request came back "No setting provided" — the agent was
        reachable and useless at the same time. Parsing RPG vocabulary belongs to
        the agent, not to the router.
        """
        text = (prompt or "").strip()
        if not text:
            return {"status": "error", "message": "No request provided"}

        lowered = text.lower()

        level = self._parse_level(text)
        if re.search(r"(角色|character|職業|class|種族|race|建立)", lowered):
            return self.create_character(
                character_class=self._parse_class(text),
                race=self._parse_race(text),
            )
        if re.search(r"(擲骰|骰子|攻擊|行動|判定|roll|dice|attack|action|resolve)", lowered):
            return self.resolve_action(action=text, context={})
        return self.generate_scenario(setting=self._parse_setting(text), player_level=level)

    # -- request parsing -------------------------------------------------- #
    _CLASS_WORDS = {
        "戰士": "warrior",
        "warrior": "warrior",
        "法師": "mage",
        "法师": "mage",
        "mage": "mage",
        "wizard": "mage",
        "盜賊": "rogue",
        "盜賊": "rogue",
        "rogue": "rogue",
        "thief": "rogue",
        "牧師": "cleric",
        "牧师": "cleric",
        "cleric": "cleric",
        "priest": "cleric",
    }
    _RACE_WORDS = {
        "精靈": "elf",
        "精灵": "elf",
        "elf": "elf",
        "矮人": "dwarf",
        "侏儒": "dwarf",
        "dwarf": "dwarf",
        "半獸人": "half-orc",
        "獅人": "lion",
        "人類": "human",
        "human": "human",
    }
    _LEVEL_RE = re.compile(r"(?:等級|等级|level|Lv\.?)\s*(\d{1,2})", re.IGNORECASE)

    def _parse_class(self, text: str) -> str:
        for word, canonical in self._CLASS_WORDS.items():
            if word in text:
                return canonical
        return "warrior"

    def _parse_race(self, text: str) -> str:
        for word, canonical in self._RACE_WORDS.items():
            if word in text:
                return canonical
        return "human"

    def _parse_level(self, text: str) -> int:
        m = self._LEVEL_RE.search(text)
        if m:
            try:
                return max(1, min(20, int(m.group(1))))
            except ValueError:
                return 1
        return 1

    # Longest hint first: with 「設定」 tried before 「設定是」, "設定是黑暗森林"
    # yielded "是黑暗森林" — the label matched inside the longer phrase.
    _SETTING_HINTS = (
        "setting is",
        "設定是",
        "設定為",
        "設定",
        "场景是",
        "場景是",
        "场景",
        "場景",
        "背景是",
        "背景",
        "世界觀",
        "世界",
        "地點",
        "地点",
        "setting",
    )
    # Everything from a level marker onwards belongs to the level, not the setting.
    _SETTING_TAIL_RE = re.compile(
        r"(?:等級|等级|等级|level|Lv\.?)\s*\d{1,2}.*$|，*$", re.IGNORECASE | re.DOTALL
    )

    def _parse_setting(self, text: str) -> str:
        for hint in self._SETTING_HINTS:
            idx = text.lower().find(hint)
            if idx != -1:
                tail = text[idx + len(hint) :].strip(" ：:,，、-—")
                tail = self._SETTING_TAIL_RE.sub("", tail).strip(" ，,、-—")
                if tail:
                    return tail
        return text.strip() or "未指定的世界"

    def generate_scenario(self, setting: str, player_level: int = 1) -> Dict[str, Any]:
        """Generate a fantasy RPG scenario based on setting and player level."""
        if not setting:
            return {"status": "error", "message": "No setting provided"}
        difficulty = "easy" if player_level < 3 else "medium" if player_level < 6 else "hard"
        logger.info(f"generate_scenario: setting='{setting}', player_level={player_level}")
        return {
            "status": "success",
            "message": f"Generated scenario in '{setting}' for level {player_level}",
            "setting": setting,
            "player_level": player_level,
            "difficulty": difficulty,
            "description": f"A {difficulty} encounter in {setting}",
        }

    def create_character(self, character_class: str, race: str) -> Dict[str, Any]:
        """Create a fantasy RPG character with stats."""
        if not character_class or not race:
            return {"status": "error", "message": "Both class and race are required"}
        base_stats = {
            "strength": 10,
            "dexterity": 10,
            "constitution": 10,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 10,
        }
        class_bonus = {
            "warrior": {"strength": 3, "constitution": 2},
            "mage": {"intelligence": 3, "wisdom": 1},
            "rogue": {"dexterity": 3, "charisma": 1},
            "cleric": {"wisdom": 3, "constitution": 1},
        }
        bonus = class_bonus.get(character_class.lower(), {})
        stats = {k: v + bonus.get(k, 0) for k, v in base_stats.items()}
        logger.info(f"create_character: class={character_class}, race={race}")
        return {
            "status": "success",
            "message": f"Created {race} {character_class}",
            "character_class": character_class,
            "race": race,
            "stats": stats,
            "level": 1,
        }

    def resolve_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve a player action based on context."""
        if not action:
            return {"status": "error", "message": "No action provided"}
        context = context or {}
        difficulty_class = context.get("difficulty_class", 10)
        outcome = (
            "success"
            if difficulty_class <= 10
            else "failure" if difficulty_class > 15 else "partial"
        )
        logger.info(f"resolve_action: action='{action}', dc={difficulty_class}")
        return {
            "status": "success",
            "message": f"Action '{action}' resolved as {outcome}",
            "action": action,
            "difficulty_class": difficulty_class,
            "outcome": outcome,
            "description": f"The action results in {outcome} (DC {difficulty_class})",
        }
