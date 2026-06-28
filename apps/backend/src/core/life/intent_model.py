from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


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
        """Scan HAM memory for experiences near current state coordinates.

        Queries the memory bridge for items spatially proximate to each
        dimension's coordinate in the state, and creates Exploration intents
        from the results.
        """
        for dimension, dim_state in state.items():
            if not isinstance(dim_state, dict):
                continue
            coord = dim_state.get("coordinate")
            if not coord or len(coord) < 3:
                continue
            x, y, z = coord[0], coord[1], coord[2]
            try:
                memories = bridge.retrieve_by_spatial_proximity(x, y, z, radius=5.0)
            except Exception as exc:
                logger.warning(f"Bridge proximity query failed for {dimension}: {exc}")
                memories = []
            for mem in memories:
                mem_id = getattr(mem, "id", None) or str(id(mem))
                intent = SelfIntent(
                    id=f"mem_{dimension}_{mem_id}",
                    category=IntentCategory.EXPLORATION,
                    target_dimension=dimension,
                    target_coordinate=(x, y, z),
                    urgency=0.3,
                    strength=0.5,
                    decay_rate=0.02,
                )
                self.add_intent(intent)

    def generate_homeostatic_intents(self, state: Dict[str, Any]) -> None:
        """Generate homeostatic intents to restore balance.

        Checks each dimension's energy/value against a threshold (default 0.3).
        If a value falls below the threshold, a HOMEOSTASIS intent is created
        to drive the system toward restoring balance.
        """
        dim_config: Dict[str, tuple] = {
            "alpha": (IntentCategory.HOMEOSTASIS, "energy", 0.3),
            "gamma": (IntentCategory.EXPLORATION, "happiness", 0.3),
            "delta": (IntentCategory.SOCIAL_BOND, "bond", 0.3),
        }
        for dimension, dim_state in state.items():
            if not isinstance(dim_state, dict):
                continue
            config = dim_config.get(dimension)
            if config is None:
                continue
            cat, threshold_key, default_threshold = config
            value = dim_state.get(threshold_key, 1.0)
            coordinate = dim_state.get("coordinate", (0.0, 0.0, 0.0))
            if value < default_threshold:
                intent_id = f"homeostasis_{dimension}_{len(self.intents)}"
                intent = SelfIntent(
                    id=intent_id,
                    category=cat,
                    target_dimension=dimension,
                    target_coordinate=coordinate,
                    urgency=1.0 - value,
                    strength=0.8,
                    decay_rate=0.05,
                )
                self.add_intent(intent)