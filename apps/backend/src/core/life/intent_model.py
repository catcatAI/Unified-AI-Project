from __future__ import annotations

import logging
from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from core.system.state_store.global_store import state_store

logger = logging.getLogger(__name__)

_OUTCOME_HISTORY_MAX = 20


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
        self._outcome_history: Dict[str, List[bool]] = defaultdict(list)

    def record_intent_outcome(self, intent_mode: Optional[str], success: bool) -> None:
        """Record the outcome of an intent-driven routing decision.

        Stores whether the routing outcome was successful per intent_mode,
        enabling the model to down-weight poorly-performing modes.
        """
        key = intent_mode or "neutral"
        self._outcome_history[key].append(success)
        if len(self._outcome_history[key]) > _OUTCOME_HISTORY_MAX:
            self._outcome_history[key] = self._outcome_history[key][-_OUTCOME_HISTORY_MAX:]
        rate = self.get_intent_success_rate(key)
        logger.debug(
            f"Intent outcome recorded: mode={key}, success={success}, "
            f"rate={rate:.2f} ({len(self._outcome_history[key])} samples)"
        )
        state_store.emit_event("intent.outcome_recorded", {
            "intent_mode": key,
            "success": success,
            "success_rate": round(rate, 3),
            "sample_count": len(self._outcome_history[key]),
        })

    def get_intent_success_rate(self, intent_mode: str) -> float:
        """Return the success rate for a given intent mode.

        Returns 0.5 (neutral) if no history is available for this mode.
        """
        hist = self._outcome_history.get(intent_mode, [])
        if not hist:
            return 0.5
        return sum(1 for s in hist if s) / len(hist)

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

    def get_intent_routing_adjustment(self) -> Dict[str, Any]:
        """Map active intent vectors to routing_mode/response_style.

        Analyzes the balance of active intent dimensions to determine
        an appropriate routing mode. High exploration → exploratory,
        high homeostasis → conservative, high social_bond → empathetic.
        """
        alpha = self.active_intent_vector.get("alpha", (0.0, 0.0, 0.0))
        gamma = self.active_intent_vector.get("gamma", (0.0, 0.0, 0.0))
        delta = self.active_intent_vector.get("delta", (0.0, 0.0, 0.0))
        avg_mag = (
            sum(abs(v) for v in alpha) +
            sum(abs(v) for v in gamma) +
            sum(abs(v) for v in delta)
        ) / 9.0

        if avg_mag < 0.1:
            state_store.emit_event("intent.adjustment_computed", {
                "routing_mode": None,
                "intent_mode": "neutral",
                "intent_strength": 0.0,
                "avg_magnitude": round(avg_mag, 4),
            })
            return {"routing_mode": None, "response_style": None, "intent_mode": "neutral", "intent_strength": 0.0}

        exploration = sum(abs(v) for v in gamma) / 3.0
        bonding = sum(abs(v) for v in delta) / 3.0
        energy = sum(abs(v) for v in alpha) / 3.0

        # Highest-scoring dimension drives routing
        if exploration > bonding and exploration > energy:
            routing_mode = "exploratory"
            response_style = "curious"
        elif bonding > exploration and bonding > energy:
            routing_mode = "empathetic"
            response_style = "warm"
        elif energy > 0.5:
            routing_mode = "conservative"
            response_style = "cautious"
        else:
            routing_mode = "balanced"
            response_style = "neutral"

        raw_strength = round(min(1.0, avg_mag * 2.0), 2)
        success_rate = self.get_intent_success_rate(routing_mode)
        adjusted_strength = round(raw_strength * (0.5 + 0.5 * success_rate), 2)

        result = {
            "routing_mode": routing_mode,
            "response_style": response_style,
            "intent_mode": "active",
            "intent_strength": adjusted_strength,
            "raw_strength": raw_strength,
            "success_rate": round(success_rate, 3),
        }
        state_store.emit_event("intent.adjustment_computed", {
            "routing_mode": routing_mode,
            "intent_mode": "active",
            "intent_strength": adjusted_strength,
            "avg_magnitude": round(avg_mag, 4),
            "exploration": round(exploration, 4),
            "bonding": round(bonding, 4),
            "energy": round(energy, 4),
            "success_rate": round(success_rate, 3),
        })
        return result

    def scan_memory_proximity(self, bridge: Any, state: Dict[str, Any]) -> None:
        """Scan HAM memory for experiences near current state coordinates.

        Queries the memory bridge for items spatially proximate to each
        dimension's coordinate in the state, and creates Exploration intents
        from the results.
        """
        if bridge is None:
            return
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
                state_store.emit_event("intent.homeostatic_generated", {
                    "dimension": dimension,
                    "category": cat.value,
                    "urgency": intent.urgency,
                    "strength": intent.strength,
                })



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