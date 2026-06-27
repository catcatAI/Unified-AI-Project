from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class IntentCategory(Enum):
    HOMEOSTASIS = "homeostasis"
    EXPLORATION = "exploration"
    SOCIAL_BOND = "social_bond"
    SELF_PRESERVATION = "self_preservation"


class SelfIntent:
    def __init__(
        self,
        id: str,
        category: IntentCategory,
        target_dimension: str,
        target_coordinate: Tuple[float, float, float],
        urgency: float = 0.5,
        strength: float = 1.0,
        decay_rate: float = 0.01,
    ):
        self.id = id
        self.category = category
        self.target_dimension = target_dimension
        self.target_coordinate = target_coordinate
        self.urgency = urgency
        self.strength = strength
        self.decay_rate = decay_rate

    def is_expired(self) -> bool:
        return self.strength <= 0.0


class IntentManager:
    def __init__(self):
        self.intents: List[SelfIntent] = []
        self.active_intent_vector: Dict[str, Tuple[float, float, float]] = {
            "alpha": (0.0, 0.0, 0.0),
            "gamma": (0.0, 0.0, 0.0),
            "delta": (0.0, 0.0, 0.0),
        }

    def add_intent(self, intent: SelfIntent) -> None:
        self.intents.append(intent)

    def update_intents(self, delta_time: float) -> None:
        remaining = []
        for intent in self.intents:
            intent.strength *= (1.0 - intent.decay_rate) ** delta_time
            if not intent.is_expired():
                remaining.append(intent)
        self.intents = remaining
        self._calculate_active_vectors()

    def get_intent_influence(self, dimension: str) -> Tuple[float, float, float]:
        return self.active_intent_vector.get(dimension, (0.0, 0.0, 0.0))

    def _calculate_active_vectors(self) -> None:
        vectors: Dict[str, List[Tuple[float, float, float, float]]] = {}
        for intent in self.intents:
            dim = intent.target_dimension
            if dim not in vectors:
                vectors[dim] = []
            weighted = (
                intent.target_coordinate[0] * intent.urgency * intent.strength,
                intent.target_coordinate[1] * intent.urgency * intent.strength,
                intent.target_coordinate[2] * intent.urgency * intent.strength,
                intent.urgency * intent.strength,
            )
            vectors[dim].append(weighted)

        for dim, dim_vectors in vectors.items():
            total_weight = sum(v[3] for v in dim_vectors)
            if total_weight > 0:
                avg_x = sum(v[0] for v in dim_vectors) / total_weight
                avg_y = sum(v[1] for v in dim_vectors) / total_weight
                avg_z = sum(v[2] for v in dim_vectors) / total_weight
                self.active_intent_vector[dim] = (avg_x, avg_y, avg_z)
            else:
                self.active_intent_vector[dim] = (0.0, 0.0, 0.0)

    def scan_memory_proximity(self, bridge: Any, state: Dict[str, Any]) -> None:
        pass

    def generate_homeostatic_intents(self, state: Dict[str, Any]) -> None:
        pass