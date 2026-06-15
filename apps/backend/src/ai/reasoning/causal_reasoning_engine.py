# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CausalReasoningEngine:
    """Engine for causal reasoning and inference.

    Learns causal relationships from observations and uses them
    to make predictions and explanations.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._causality_threshold = self.config.get("causality_threshold", 0.5)
        self._relationships: List[Dict[str, Any]] = []
        self._observations: List[Dict[str, Any]] = []

    def learn(self, observation: Dict[str, Any]) -> None:
        self._observations.append(observation)
        rels = self._infer_relationships(observation)
        self._relationships.extend(rels)

    def _infer_relationships(self, observation: Dict[str, Any]) -> List[Dict[str, Any]]:
        variables = observation.get("variables", [])
        existing = observation.get("relationships", [])
        # If caller already specified relationships, trust them (no re-inference)
        if existing:
            return list(existing)
        # Otherwise, infer pairwise relationships from variables
        inferred = []
        if len(variables) >= 2:
            for i in range(len(variables)):
                for j in range(i + 1, len(variables)):
                    inferred.append({
                        "cause": variables[i],
                        "effect": variables[j],
                        "strength": self._causality_threshold,
                        "source": observation.get("id", "unknown"),
                    })
        return inferred

    async def _analyze_observation_causality(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        variables = observation.get("variables", [])
        data = observation.get("data", {})
        correlation_matrix = {}
        if len(variables) >= 2:
            for i in range(len(variables)):
                for j in range(i + 1, len(variables)):
                    v1, v2 = variables[i], variables[j]
                    d1, d2 = data.get(v1, []), data.get(v2, [])
                    key = f"{v1}_{v2}"
                    if len(d1) >= 2 and len(d2) >= 2:
                        n = min(len(d1), len(d2))
                        correlation_matrix[key] = self._pearson(d1[:n], d2[:n])
                    else:
                        correlation_matrix[key] = 0.0
        return {"correlation_matrix": correlation_matrix}

    @staticmethod
    def _pearson(x: List[float], y: List[float]) -> float:
        n = len(x)
        if n < 2:
            return 0.0
        mx, my = sum(x) / n, sum(y) / n
        num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
        dx = sum((xi - mx) ** 2 for xi in x) ** 0.5
        dy = sum((yi - my) ** 2 for yi in y) ** 0.5
        if dx == 0 or dy == 0:
            return 0.0
        return num / (dx * dy)

    def predict(self, cause: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return [r for r in self._relationships if r.get("cause") == cause]

    def explain(self, effect: str) -> List[Dict[str, Any]]:
        return [r for r in self._relationships if r.get("effect") == effect]

    def get_relationships(self) -> List[Dict[str, Any]]:
        return list(self._relationships)

    def get_observations(self) -> List[Dict[str, Any]]:
        return list(self._observations)


__all__ = ["CausalReasoningEngine"]
