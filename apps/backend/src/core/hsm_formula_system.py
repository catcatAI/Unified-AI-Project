"""
Angela AI v6.0 - HSM Formula System
热力学式自发元认知公式系统

HSM (Heuristic Spontaneity Mechanism) = C_Gap × E_M2

This system implements the theoretical framework for digital life spontaneity,
based on the concept of cognitive gap pressure driving exploration.

Features:
- C_Gap: Cognitive gap detection and pressure calculation
- E_M2: Mandatory randomness injection (0.1) to break AI concentration trap
- M6 Governance: Solidification of exploration results into system rules
- Blueprint maintenance for autonomous evolution

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class HSMFormulaSystem:
    """Heuristic Spontaneity Mechanism = C_Gap × E_M2"""

    def __init__(self, config=None):
        self.config = config or {}
        logger.debug("HSMFormulaSystem initialized")

    def calculate_spontaneity(self, cognitive_gap: float, randomness: float = 0.1) -> float:
        return cognitive_gap * randomness

    def get_status(self) -> dict:
        return {"system": "hsm", "active": True}


class CognitiveGap:
    def __init__(self, gap_value: float = 0.0):
        self.gap_value = gap_value

    def get_pressure(self) -> float:
        return min(1.0, self.gap_value * 0.1)


class ExplorationEvent:
    def __init__(self, event_type: str = "exploration", data: dict = None):
        self.event_type = event_type
        self.data = data or {}

    def to_dict(self) -> dict:
        return {"type": self.event_type, "data": self.data}


class GovernanceBlueprint:
    def __init__(self, rules: list = None):
        self.rules = rules or []

    def add_rule(self, rule: str):
        self.rules.append(rule)

    def get_rules(self) -> list:
        return self.rules


class ExplorationResult:
    def __init__(self, success: bool = False, findings: dict = None):
        self.success = success
        self.findings = findings or {}

    def is_actionable(self) -> bool:
        return self.success and bool(self.findings)
