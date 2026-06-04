"""
η (Eta) Axis — Execution/Operation Layer
========================================

η is the 7th axis (after αβγδεθ) that handles execution/operation,
contrasting θ's cognitive/evaluation role.

Layer 0 — Atomic Modules: LogicGate, ArithmeticOp, Aggregator, Router
Layer 1 — Composed Modules: Built from atoms
Layer 2 — Adjusted Modules: Parameter-adjusted versions

Trigger Curve:
  modules_to_call = floor(min(12, 3 × sigmoid(complexity × axis_count / 6)))
  adjustment_magnitude = min(0.2, 0.15 × sigmoid(complexity - 0.5))

The Eta Axis represents "resonance" — how different state dimensions harmonize.

Author: Angela AI v6.2.1
Version: 6.2.1
Date: 2026-05-15
"""

from __future__ import annotations
import math
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class EtaAxis:
    """η (Eta) Axis — resonance/harmony dimension."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._resonance_history: list = []
        logger.debug(f"[EtaAxis] Initialized with config keys: {list(self.config.keys())}")

    def calculate_resonance(self, state_vector: Dict[str, float]) -> float:
        """Compute resonance score from a state vector of dimension values."""
        if not state_vector:
            return 0.5

        values = [v for v in state_vector.values() if isinstance(v, (int, float))]
        if not values:
            return 0.5

        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance)

        coherence = 1.0 / (1.0 + std_dev)
        activation = mean
        resonance = 0.6 * coherence + 0.4 * activation
        resonance = max(0.0, min(1.0, resonance))
        self._resonance_history.append(resonance)
        return resonance

    def apply_resonance_boost(self, score: float, context: Dict[str, Any]) -> float:
        """Boost score based on context match with current resonance profile."""
        if not context:
            return score

        context_resonance = self.calculate_resonance(context)
        boost = 0.0
        if context_resonance > 0.6:
            boost = (context_resonance - 0.6) * 0.5
        elif context_resonance < 0.3:
            boost = (context_resonance - 0.3) * 0.3

        return max(0.0, min(1.0, score + boost))

    def get_resonance_profile(self) -> Dict[str, Any]:
        """Return current resonance profile with stats."""
        if not self._resonance_history:
            return {
                "current_resonance": 0.5,
                "history_length": 0,
                "trend": "stable",
                "config": self.config,
            }
        recent = self._resonance_history[-10:]
        current = recent[-1]
        avg = sum(recent) / len(recent)
        trend = "rising" if len(recent) > 1 and recent[-1] > recent[0] else (
            "falling" if len(recent) > 1 and recent[-1] < recent[0] else "stable"
        )
        return {
            "current_resonance": round(current, 4),
            "average_resonance": round(avg, 4),
            "history_length": len(self._resonance_history),
            "trend": trend,
            "config": self.config,
        }
