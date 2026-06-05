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
        inferred = list(existing)
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

    def predict(self, cause: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return [r for r in self._relationships if r.get("cause") == cause]

    def explain(self, effect: str) -> List[Dict[str, Any]]:
        return [r for r in self._relationships if r.get("effect") == effect]

    def get_relationships(self) -> List[Dict[str, Any]]:
        return list(self._relationships)

    def get_observations(self) -> List[Dict[str, Any]]:
        return list(self._observations)


__all__ = ["CausalReasoningEngine"]
