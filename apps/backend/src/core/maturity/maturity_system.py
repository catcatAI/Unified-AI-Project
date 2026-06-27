"""
Angela AI v6.0 - Maturity Level System
成熟度等级系统 (L0-L11)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MaturityLevel(Enum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"
    L6 = "L6"
    L7 = "L7"
    L8 = "L8"
    L9 = "L9"
    L10 = "L10"
    L11 = "L11"


@dataclass
class ExperienceTracker:
    total_experience: int = 0
    level_experience: int = 0
    experience_history: List[Dict[str, Any]] = field(default_factory=list)
    level_history: List[Dict[str, Any]] = field(default_factory=list)

    def add_experience(self, amount: int, source: str = "") -> None:
        self.total_experience += amount
        self.level_experience += amount
        self.experience_history.append({
            "amount": amount,
            "source": source,
            "timestamp": datetime.now().isoformat(),
        })
        logger.debug(f"Added {amount} experience from {source}")

    def get_level(self) -> MaturityLevel:
        levels = [
            (0, MaturityLevel.L0), (100, MaturityLevel.L1), (300, MaturityLevel.L2),
            (600, MaturityLevel.L3), (1000, MaturityLevel.L4), (1500, MaturityLevel.L5),
            (2100, MaturityLevel.L6), (2800, MaturityLevel.L7), (3600, MaturityLevel.L8),
            (4500, MaturityLevel.L9), (5500, MaturityLevel.L10), (float("inf"), MaturityLevel.L11),
        ]
        for threshold, level in levels:
            if self.total_experience < threshold:
                return level
        return MaturityLevel.L11


class MaturityManager:
    def __init__(self, initial_level: MaturityLevel = MaturityLevel.L0):
        self.current_level = initial_level
        self.tracker = ExperienceTracker()
        self.milestones: Dict[str, Any] = {}
        logger.debug(f"MaturityManager initialized at {initial_level}")

    def advance(self, amount: int, source: str = "") -> MaturityLevel:
        self.tracker.add_experience(amount, source)
        new_level = self.tracker.get_level()
        if new_level != self.current_level:
            self.current_level = new_level
            self.milestones[f"level_{new_level.value}"] = {
                "reached_at": datetime.now().isoformat(),
                "source": source,
            }
            logger.info(f"Advanced to {new_level.value}")
        return self.current_level

    def get_status(self) -> Dict[str, Any]:
        return {
            "current_level": self.current_level.value,
            "total_experience": self.tracker.total_experience,
            "level_experience": self.tracker.level_experience,
            "milestones": self.milestones,
        }


def create_maturity_system(initial_level: MaturityLevel = MaturityLevel.L0) -> MaturityManager:
    return MaturityManager(initial_level)
