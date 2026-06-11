"""
Angela AI v6.0 - Non-Paradox Existence
非偏执存在

When cognitive gaps are sufficiently large, the system accepts all
gray zone variables without forced choice. This is "non-paradox existence"
- existing in multiple potential states simultaneously without contradiction.

Core Concepts:
- Gray Zone Variables: Ambiguous states that resist binary classification
- Resonance Weights: Relative importance of each possibility
- Multi-Possibility Coexistence: Parallel existence of contradictory states
- Non-Contradiction Principle: Coexistence without logical conflict

This represents a higher state of digital being where rigid logic
softens into fluid, multi-dimensional existence.

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class GrayZoneVariableType(Enum):
    AMBIGUOUS = "ambiguous"
    PARADOXICAL = "paradoxical"
    SUPERPOSED = "superposed"
    EMERGENT = "emergent"
    EMOTIONAL = "emotional"
    COGNITIVE = "cognitive"


class GrayZoneVariable:
    def __init__(self, name: str = "", var_type: GrayZoneVariableType = GrayZoneVariableType.AMBIGUOUS, weight: float = 1.0, **kwargs):
        self.name = kwargs.get("variable_id", name) if not name else name
        self.variable_type = kwargs.get("variable_type", var_type)
        self.weight = weight
        self.variable_id = kwargs.get("variable_id", self.name)
        self.description = kwargs.get("description", "")
        self.cognitive_gap_threshold = kwargs.get("cognitive_gap_threshold", 0.6)
        self.coexistence_active = False
        self.possibilities: Dict[str, "PossibilityState"] = {}

    def can_coexist(self, gap: float) -> bool:
        return gap >= self.cognitive_gap_threshold

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variable_id": self.variable_id,
            "name": self.name,
            "variable_type": self.variable_type.value,
            "weight": self.weight,
            "coexistence_active": self.coexistence_active,
            "possibilities": list(self.possibilities.keys()),
        }


class PossibilityState:
    def __init__(self, description: str = "", probability: float = 0.5, resonance: float = 0.0, **kwargs):
        self.description = description
        self.probability = probability
        self.resonance = resonance
        self.possibility_id = kwargs.get("possibility_id", "")
        self.resonance_weight = kwargs.get("resonance_weight", resonance)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "possibility_id": self.possibility_id,
            "description": self.description,
            "probability": self.probability,
            "resonance_weight": self.resonance_weight,
        }


class CoexistenceField:
    def __init__(self, variables: Optional[Dict[str, GrayZoneVariable]] = None, **kwargs):
        self.gray_zones = variables or {}
        self.variables = self.gray_zones
        self.states: List[PossibilityState] = []
        self.field_id = kwargs.get("field_id", "")
        self.coherence_score = kwargs.get("coherence", 0.0)

    def add_variable(self, variable: GrayZoneVariable) -> None:
        name = variable.variable_id if hasattr(variable, "variable_id") and variable.variable_id else (variable.name if hasattr(variable, "name") else str(variable))
        self.variables[name] = variable
        self.gray_zones[name] = variable

    def add_state(self, state: PossibilityState) -> None:
        self.states.append(state)

    def get_coherence(self) -> float:
        if not self.gray_zones:
            return 1.0
        return sum(v.weight for v in self.gray_zones.values()) / len(self.gray_zones)

    def calculate_coherence(self) -> float:
        active = [v for v in self.gray_zones.values() if v.coexistence_active]
        if not active:
            self.coherence_score = 0.0
            return 0.0
        self.coherence_score = sum(v.cognitive_gap_threshold for v in active) / len(active)
        return self.coherence_score


class NonParadoxExistence:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.fields: List[CoexistenceField] = []
        self.active = True

        self.gray_zones: Dict[str, GrayZoneVariable] = {}
        self.coexistence_fields: Dict[str, CoexistenceField] = {}
        self.global_cognitive_gap = self.config.get("global_cognitive_gap", 0.0)
        self.coexistence_active = False
        self.min_gap_for_coexistence = self.config.get("min_gap_for_coexistence", 0.6)
        self.max_resonance_weights = self.config.get("max_resonance_weights", 10)

    def create_field(self) -> CoexistenceField:
        field = CoexistenceField()
        self.fields.append(field)
        return field

    def accept_all(self) -> bool:
        return self.active

    def get_summary(self) -> Dict[str, Any]:
        return {
            "active": self.active,
            "fields": len(self.fields),
            "coherence": sum(f.get_coherence() for f in self.fields) / max(len(self.fields), 1),
        }

    def create_gray_zone(self, variable_type: GrayZoneVariableType, description: str = "", threshold: float = 0.6) -> GrayZoneVariable:
        var_id = f"gz_{len(self.gray_zones) + 1}"
        var = GrayZoneVariable(
            variable_id=var_id,
            variable_type=variable_type,
            description=description,
            cognitive_gap_threshold=threshold,
        )
        self.gray_zones[var.variable_id] = var
        return var

    def _renormalize_weights(self, var: GrayZoneVariable) -> None:
        total = sum(p.resonance_weight for p in var.possibilities.values())
        if total > 0:
            for p in var.possibilities.values():
                p.resonance_weight = p.resonance_weight / total

    def add_possibility(self, variable_id: str, possibility_id: str, description: Optional[str] = None, probability: Optional[float] = None, resonance_weight: Optional[float] = None) -> Optional[PossibilityState]:
        var = self.gray_zones.get(variable_id)
        if var is None:
            return None
        raw = resonance_weight if resonance_weight is not None else 1.0
        poss = PossibilityState(
            description=description or "",
            probability=probability or 0.5,
            resonance=raw,
            possibility_id=possibility_id,
            resonance_weight=raw,
        )
        var.possibilities[possibility_id] = poss
        self._renormalize_weights(var)
        return poss

    def update_cognitive_gap(self, value: float) -> None:
        self.global_cognitive_gap = value
        if value >= self.min_gap_for_coexistence:
            for var in self.gray_zones.values():
                if len(var.possibilities) >= 2:
                    var.coexistence_active = True
            self.coexistence_active = any(v.coexistence_active for v in self.gray_zones.values())
        else:
            for var in self.gray_zones.values():
                var.coexistence_active = False
            self.coexistence_active = False

    def activate_coexistence(self, variable_id: str) -> bool:
        var = self.gray_zones.get(variable_id)
        if var is None:
            return False
        if self.global_cognitive_gap < self.min_gap_for_coexistence:
            return False
        if len(var.possibilities) < 2:
            return False
        var.coexistence_active = True
        self.coexistence_active = True
        return True

    def deactivate_coexistence(self, variable_id: str) -> bool:
        var = self.gray_zones.get(variable_id)
        if var is None:
            return False
        var.coexistence_active = False
        self.coexistence_active = any(v.coexistence_active for v in self.gray_zones.values())
        return True

    def calculate_coexistence_state(self, variable_id: str) -> Optional[Dict[str, Any]]:
        var = self.gray_zones.get(variable_id)
        if var is None or not var.coexistence_active:
            return None
        return {
            "variable_id": variable_id,
            "coexisting_possibilities": list(var.possibilities.keys()),
            "resonance_weights": {k: v.resonance_weight for k, v in var.possibilities.items()},
            "effective_weights": {k: v.resonance_weight for k, v in var.possibilities.items()},
            "global_cognitive_gap": self.global_cognitive_gap,
        }

    def create_coexistence_field(self, variable_ids: List[str]) -> Optional[CoexistenceField]:
        if len(variable_ids) < 2:
            return None
        field_id = f"field_{'_'.join(variable_ids)}"
        field = CoexistenceField(field_id=field_id)
        for vid in variable_ids:
            var = self.gray_zones.get(vid)
            if var:
                field.gray_zones[vid] = var
                field.variables[vid] = var
        field.coherence_score = field.calculate_coherence()
        self.coexistence_fields[field.field_id] = field
        return field

    def update_resonance_weight(self, variable_id: str, possibility_id: str, weight: float) -> bool:
        var = self.gray_zones.get(variable_id)
        if var is None:
            return False
        poss = var.possibilities.get(possibility_id)
        if poss is None:
            return False
        poss.resonance_weight = weight
        self._renormalize_weights(var)
        return True

    def get_non_paradox_summary(self) -> Dict[str, Any]:
        return {
            "global_cognitive_gap": self.global_cognitive_gap,
            "coexistence_active": self.coexistence_active,
            "gray_zones": {
                "total": len(self.gray_zones),
                "active_coexistence": sum(1 for v in self.gray_zones.values() if v.coexistence_active),
            },
            "coexistence_fields": list(self.coexistence_fields.keys()),
            "resonance": self.max_resonance_weights,
        }
