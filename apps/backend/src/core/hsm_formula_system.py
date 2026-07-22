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
import random
import uuid

from typing import Optional

from core.system.config.magic_numbers import cache_value, llm_param, threshold_value

logger = logging.getLogger(__name__)

_MAX_EXPLORATION_HISTORY = cache_value("hsm_max_exploration_history", 500)


class HSMFormulaSystem:
    """Heuristic Spontaneity Mechanism = C_Gap × E_M2"""

    def __init__(self, config=None):
        self.config = config or {}
        self.e_m2_constant = llm_param("hsm_em2_constant", 0.1)
        self.hsm_threshold = threshold_value("hsm_threshold", 0.5)
        self.cognitive_gaps: dict = {}
        self.exploration_history: list = []
        self.governance_blueprints: dict = {}
        self.rules_solidified = 0
        self._running = False
        logger.debug("HSMFormulaSystem initialized")

    def calculate_spontaneity(self, cognitive_gap: float, randomness: Optional[float] = None) -> float:
        if randomness is None:
            randomness = llm_param("hsm_default_randomness", 0.1)
        return cognitive_gap * randomness

    def get_status(self) -> dict:
        return {"system": "hsm", "active": True}

    def get_e_m2(self) -> float:
        return self.e_m2_constant

    def detect_cognitive_gap(
        self, domain: str, uncertainty_level: float, information_deficit: float
    ):
        gap = CognitiveGap(
            gap_id=domain,
            domain=domain,
            uncertainty_level=uncertainty_level,
            information_deficit=information_deficit,
        )
        self.cognitive_gaps[domain] = gap
        return gap

    def calculate_c_gap(self) -> float:
        if not self.cognitive_gaps:
            return 0.0
        pressures = [g.calculate_pressure() for g in self.cognitive_gaps.values()]
        return sum(pressures) / len(pressures)

    def calculate_hsm(self) -> float:
        return self.calculate_c_gap() * self.get_e_m2()

    def trigger_exploration(self, gap_id: Optional[str] = None) -> ExplorationEvent:
        triggered_by = gap_id or "general"
        # E_M2 injection: exploration carries the E_M2 randomness constant plus a
        # stochastic component, so the seed is always strictly positive.
        random_seed = self.get_e_m2() * (1.0 + random.random())
        event = ExplorationEvent(
            event_type="cognitive_exploration",
            data={"gap_id": gap_id, "source": "hsm"},
            triggered_by=triggered_by,
            random_seed=random_seed,
        )
        if gap_id and gap_id in self.cognitive_gaps:
            self.cognitive_gaps[gap_id].exploration_attempts += 1
        self.exploration_history.append(event)
        if len(self.exploration_history) > _MAX_EXPLORATION_HISTORY:
            self.exploration_history = self.exploration_history[-_MAX_EXPLORATION_HISTORY:]
        return event

    def update_cognitive_gap(self, gap_id: str, **kwargs):
        gap = self.cognitive_gaps.get(gap_id)
        if gap is None:
            return None
        for key, value in kwargs.items():
            if hasattr(gap, key):
                setattr(gap, key, value)
        return gap

    async def _simulate_discovery(self, exploration: ExplorationEvent) -> None:
        """M6: solidify RULE_CANDIDATE discoveries from an exploration into
        governance blueprints. Only discoveries whose confidence clears the HSM
        threshold are solidified.
        """
        for discovery in getattr(exploration, "discoveries", []):
            if discovery.get("type") != ExplorationResult.RULE_CANDIDATE:
                continue
            confidence = float(discovery.get("confidence", 0.0))
            if confidence < self.hsm_threshold:
                continue
            rule_id = str(uuid.uuid4())
            self.governance_blueprints[rule_id] = GovernanceBlueprint(
                rules=[discovery.get("description", "")],
                rule_id=rule_id,
                status="pending",
                confidence=confidence,
            )
            self.rules_solidified += 1

    def activate_governance_rule(self, rule_id: str) -> bool:
        blueprint = self.governance_blueprints.get(rule_id)
        if blueprint is None:
            return False
        blueprint.status = "active"
        return True

    def get_governance_summary(self) -> dict:
        return {
            "total_rules": len(self.governance_blueprints),
            "rules_solidified": self.rules_solidified,
        }

    def get_hsm_status(self) -> dict:
        return {
            "hsm_value": self.calculate_hsm(),
            "c_gap": self.calculate_c_gap(),
            "e_m2": self.get_e_m2(),
            "explorations": len(self.exploration_history),
            "governance": self.get_governance_summary(),
            "cognitive_gaps": {
                "total": len(self.cognitive_gaps),
                "ids": list(self.cognitive_gaps.keys()),
            },
            "is_running": self._running,
        }

    async def initialize(self):
        self._running = True

    async def shutdown(self):
        self._running = False


class CognitiveGap:
    def __init__(
        self,
        gap_id: str = "",
        domain: str = "",
        uncertainty_level: float = 0.0,
        information_deficit: float = 0.0,
        exploration_attempts: int = 0,
    ):
        self.gap_id = gap_id
        self.domain = domain
        self.uncertainty_level = uncertainty_level
        self.information_deficit = information_deficit
        self.exploration_attempts = exploration_attempts
        self.pressure_score = (uncertainty_level + information_deficit) / 2.0
        self.resolution_status = "exploring"

    def calculate_pressure(self) -> float:
        return self.pressure_score

    def get_pressure(self) -> float:
        return self.pressure_score


class ExplorationEvent:
    def __init__(
        self,
        event_type: str = "",
        data: Optional[dict] = None,
        triggered_by: str = "",
        random_seed: float = 0.0,
    ):
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.data = data or {}
        self.triggered_by = triggered_by or event_type
        self.random_seed = random_seed
        self.discoveries = []

    def to_dict(self) -> dict:
        return {"event_id": self.event_id, "event_type": self.event_type, "data": self.data}


class GovernanceBlueprint:
    def __init__(
        self,
        rules: Optional[list] = None,
        rule_id: str = "",
        status: str = "pending",
        confidence: float = 0.0,
    ):
        self.rules = rules or []
        self.rule_id = rule_id
        self.status = status
        self.confidence = confidence

    def add_rule(self, rule: str):
        self.rules.append(rule)

    def get_rules(self) -> list:
        return self.rules


class ExplorationResult:
    RULE_CANDIDATE = "rule_candidate"

    def __init__(self, success: bool = False, findings: Optional[list] = None):
        self.success = success
        self.findings = findings or []

    def is_actionable(self) -> bool:
        return self.success
