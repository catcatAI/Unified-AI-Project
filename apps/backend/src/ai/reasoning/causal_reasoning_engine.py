# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
import math
from typing import Any, Dict, List, Optional, Set

from core.system.state_store.global_store import state_store

logger = logging.getLogger(__name__)


class CausalReasoningEngine:
    """Engine for causal reasoning and inference.

    Learns causal relationships from observations using Pearson correlation,
    Granger causality (temporal precedence), and confounding variable detection.
    Supports basic do-calculus intervention simulation.
    """

    _MAX_RELATIONSHIPS = 1000
    _MAX_OBSERVATIONS = 500

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._causality_threshold = self.config.get("causality_threshold", 0.3)
        self._granger_lag = self.config.get("granger_lag", 3)
        self._relationships: List[Dict[str, Any]] = []
        self._observations: List[Dict[str, Any]] = []
        self._graph: Dict[str, Set[str]] = {}

    def learn(self, observation: Dict[str, Any]) -> None:
        self._observations.append(observation)
        rels = self._infer_relationships(observation)
        self._add_relationships(rels)
        self._evict_old()
        state_store.emit_event(
            "causal.learned",
            {
                "observation_keys": list(observation.keys()),
                "new_relationships": len(rels),
                "total_relationships": len(self._relationships),
                "total_observations": len(self._observations),
            },
        )

    async def learn_causal_relationships(
        self, observations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Async wrapper: learn from multiple observations at once."""
        for obs in observations:
            self.learn(obs)
        return list(self._relationships)

    async def plan_intervention(
        self, target_variable: str, desired_outcome: str, context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Plan an intervention by finding the best handle variable.

        Returns ranked list of intervention candidates, each with estimated effect.
        """
        causes = self.explain(desired_outcome)
        candidates = []
        for rel in causes:
            cause = rel.get("cause", "")
            if cause == target_variable or cause == desired_outcome:
                continue
            intervene = self._do_calculus_intervene(cause, 1.0, context or {})
            for result in intervene:
                if result.get("effect") == desired_outcome:
                    candidates.append(
                        {
                            "handle_variable": cause,
                            "target_variable": desired_outcome,
                            "estimated_effect": result.get("estimated_value", 0.0),
                            "strength": result.get("strength", 0.0),
                            "method": "do_calculus",
                        }
                    )
        candidates.sort(key=lambda c: c.get("strength", 0), reverse=True)
        return candidates

    def predict(self, cause: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Predict effects of a cause, optionally via do-calculus intervention."""
        if context and "intervene" in context:
            results = self._do_calculus_intervene(cause, context["intervene"], context)
        else:
            results = sorted(
                [r for r in self._relationships if r.get("cause") == cause],
                key=lambda r: r.get("strength", 0),
                reverse=True,
            )
        state_store.emit_event(
            "causal.prediction",
            {
                "cause": cause,
                "results_count": len(results),
                "top_strength": round(results[0].get("strength", 0), 3) if results else 0.0,
                "intervened": bool(context and "intervene" in context),
            },
        )
        return results

    def explain(self, effect: str) -> List[Dict[str, Any]]:
        return sorted(
            [r for r in self._relationships if r.get("effect") == effect],
            key=lambda r: r.get("strength", 0),
            reverse=True,
        )

    def ingest_temporal_state(self, temporal_state: Any, window: int = 50) -> int:
        """Ingest data from a TemporalState into causal inference.

        Calls TemporalState.to_observations() and learns each observation.
        Returns the number of observations ingested.
        """
        from core.state.temporal import TemporalState

        if not isinstance(temporal_state, TemporalState):
            return 0
        observations = temporal_state.to_observations(window=window)
        for obs in observations:
            self.learn(obs)
        return len(observations)

    def get_relationships(self) -> List[Dict[str, Any]]:
        return list(self._relationships)

    def get_observations(self) -> List[Dict[str, Any]]:
        return list(self._observations)

    def get_graph(self) -> Dict[str, List[str]]:
        return {k: sorted(v) for k, v in self._graph.items()}

    # ------------------------------------------------------------------
    # Warm-start: retrospective baseline relationships
    # ------------------------------------------------------------------

    def retrospective_warm_start(self) -> int:
        """Seed the engine with baseline causal relationships so that
        predict() returns meaningful results from Round 1 instead of
        requiring 5+ rounds of live data before Granger fires.

        Creates synthetic retrospective observations that encode common
        conversational cause-effect patterns with moderate strengths.

        Returns the number of baseline relationships created.
        """
        if self._relationships:
            logger.debug(
                "CausalReasoningEngine already has %d relationships — skipping warm-start",
                len(self._relationships),
            )
            return 0

        before = len(self._relationships)
        baseline_observations = [
            {
                "variables": ["user_input", "angela_response", "conversation_momentum"],
                "data": {
                    "user_input": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
                    "angela_response": [1.5, 2.8, 4.2, 5.1, 6.3, 7.0, 7.5],
                    "conversation_momentum": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
                },
                "id": "warm_start_baseline_1",
                "relationships": [
                    {
                        "cause": "user_input",
                        "effect": "angela_response",
                        "strength": 0.65,
                        "method": "warm_start",
                        "confounders": ["conversation_momentum"],
                    },
                    {
                        "cause": "conversation_momentum",
                        "effect": "user_input",
                        "strength": 0.45,
                        "method": "warm_start",
                        "confounders": [],
                    },
                ],
            },
            {
                "variables": ["user_input", "angela_response", "query_complexity"],
                "data": {
                    "user_input": [1.0, 2.0, 3.0, 4.0, 5.0],
                    "angela_response": [1.2, 2.5, 4.0, 5.5, 6.8],
                    "query_complexity": [0.5, 0.6, 0.7, 0.8, 0.9],
                },
                "id": "warm_start_baseline_2",
                "relationships": [
                    {
                        "cause": "user_input",
                        "effect": "angela_response",
                        "strength": 0.55,
                        "method": "warm_start",
                        "confounders": ["query_complexity"],
                    },
                    {
                        "cause": "query_complexity",
                        "effect": "angela_response",
                        "strength": 0.35,
                        "method": "warm_start",
                        "confounders": [],
                    },
                ],
            },
            {
                "variables": ["user_input", "angela_response", "interaction_value"],
                "data": {
                    "user_input": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                    "angela_response": [2.0, 3.5, 4.5, 5.0, 5.5, 6.0],
                    "interaction_value": [0.3, 0.4, 0.5, 0.55, 0.6, 0.65],
                },
                "id": "warm_start_baseline_3",
                "relationships": [
                    {
                        "cause": "user_input",
                        "effect": "angela_response",
                        "strength": 0.50,
                        "method": "warm_start",
                        "confounders": ["interaction_value"],
                    },
                    {
                        "cause": "interaction_value",
                        "effect": "user_input",
                        "strength": 0.30,
                        "method": "warm_start",
                        "confounders": [],
                    },
                ],
            },
        ]

        for obs in baseline_observations:
            self.learn(obs)

        added = len(self._relationships) - before
        logger.info(
            "CausalReasoningEngine warm-started with %d baseline relationships "
            "— predict() now functional from Round 1",
            added,
        )
        return added

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _add_relationships(self, rels: List[Dict[str, Any]]) -> None:
        for r in rels:
            cause = r.get("cause", "")
            effect = r.get("effect", "")
            if cause and effect:
                self._graph.setdefault(cause, set()).add(effect)
                self._graph.setdefault(effect, set())
        self._relationships.extend(rels)

    def _evict_old(self) -> None:
        if len(self._relationships) > self._MAX_RELATIONSHIPS:
            self._relationships = self._relationships[-self._MAX_RELATIONSHIPS :]
        if len(self._observations) > self._MAX_OBSERVATIONS:
            self._observations = self._observations[-self._MAX_OBSERVATIONS :]

    def _infer_relationships(self, observation: Dict[str, Any]) -> List[Dict[str, Any]]:
        variables = observation.get("variables", [])
        existing = observation.get("relationships", [])
        if existing:
            return self._infer_from_existing(existing, observation)

        data = observation.get("data", {})
        inferred = []
        if len(variables) >= 2:
            has_temporal = self._has_temporal_data(data, variables)
            for i in range(len(variables)):
                for j in range(len(variables)):
                    if i == j:
                        continue
                    v1, v2 = variables[i], variables[j]
                    rel = self._compute_relationship(
                        v1, v2, data, variables, has_temporal, observation
                    )
                    if rel:
                        inferred.append(rel)
        return inferred

    @staticmethod
    def _infer_from_existing(
        existing: List[Dict[str, Any]], observation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        result = []
        for rel in existing:
            entry = dict(rel)
            entry.setdefault("source", observation.get("id", "unknown"))
            result.append(entry)
        return result

    @staticmethod
    def _has_temporal_data(data: Dict[str, Any], variables: List[str]) -> bool:
        return any(isinstance(data.get(v), list) and len(data[v]) >= 5 for v in variables)

    def _compute_relationship(
        self,
        v1: str,
        v2: str,
        data: Dict[str, Any],
        variables: List[str],
        has_temporal: bool,
        observation: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        d1, d2 = data.get(v1, []), data.get(v2, [])

        if isinstance(d1, list) and isinstance(d2, list) and len(d1) >= 2 and len(d2) >= 2:
            n = min(len(d1), len(d2))
            corr = abs(self._pearson(d1[:n], d2[:n]))
        else:
            corr = self._causality_threshold

        confounders = self._find_confounders(v1, v2, data, variables)

        direction_strength = corr * (
            1.0 - max((c.get("strength", 0) for c in confounders), default=0.0)
        )
        if direction_strength < self._causality_threshold:
            return None

        if has_temporal:
            granger = self._granger_test(v1, v2, data)
            if granger is not None and granger > direction_strength:
                direction_strength = min(1.0, granger)

        return {
            "cause": v1,
            "effect": v2,
            "strength": round(direction_strength, 4),
            "confounders": [c["confounder"] for c in confounders],
            "method": "granger" if (has_temporal and granger is not None) else "correlation",
            "source": observation.get("id", "unknown"),
        }

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

    def _granger_test(self, cause: str, effect: str, data: Dict[str, Any]) -> Optional[float]:
        """Granger causality: does 'cause' temporally precede 'effect'?

        Returns causal strength [0,1] based on F-test of restricted vs. unrestricted
        autoregressive models.  Returns None if insufficient data.
        """
        xs = data.get(cause, [])
        ys = data.get(effect, [])
        lag = self._granger_lag
        n = min(len(xs), len(ys))
        if n < lag + 5:
            return None

        rss_r = self._rss_restricted(ys, lag)
        rss_u = self._rss_unrestricted(ys, xs, lag)

        if rss_u >= rss_r or rss_r == 0.0:
            return 0.0

        t = n - 2 * lag
        if t <= 0:
            return 0.0

        f_stat = ((rss_r - rss_u) / lag) / (rss_u / t)
        if not math.isfinite(f_stat) or f_stat < 0:
            return 0.0
        return min(1.0, 1.0 - 1.0 / (1.0 + f_stat * 0.05))

    @staticmethod
    def _rss_restricted(y: List[float], lag: int) -> float:
        n = len(y)
        if n <= lag + 2:
            return float("inf")
        y_t = y[lag:]
        rss = 0.0
        for i in range(len(y_t)):
            pred = sum(y[lag - 1 - j : n - 1 - j][i] for j in range(lag)) / lag
            rss += (y_t[i] - pred) ** 2
        return rss

    @staticmethod
    def _rss_unrestricted(y: List[float], x: List[float], lag: int) -> float:
        n = min(len(y), len(x))
        if n <= lag + 2:
            return float("inf")
        y_t = y[lag:n]
        rss = 0.0
        for i in range(len(y_t)):
            y_mean = sum(y[lag - 1 - j : n - 1 - j][i] for j in range(lag)) / lag
            x_mean = sum(x[lag - 1 - j : n - 1 - j][i] for j in range(lag)) / lag
            pred = 0.5 * y_mean + 0.5 * x_mean
            rss += (y_t[i] - pred) ** 2
        return rss

    def _find_confounders(
        self, x: str, y: str, data: Dict[str, Any], variables: List[str]
    ) -> List[Dict[str, Any]]:
        """Detect variables Z that could confound X→Y.

        A confounder Z is correlated with both X and Y.
        Uses partial correlation to test conditional independence.
        """
        candidates = [v for v in variables if v not in (x, y)]
        confounders = []
        for z in candidates:
            dz = data.get(z, [])
            dx = data.get(x, [])
            dy = data.get(y, [])
            if not (isinstance(dz, list) and isinstance(dx, list) and isinstance(dy, list)):
                continue
            n = min(len(dx), len(dy), len(dz))
            if n < 3:
                continue
            r_xy = self._pearson(dx[:n], dy[:n])
            r_xz = self._pearson(dx[:n], dz[:n])
            r_yz = self._pearson(dy[:n], dz[:n])
            if abs(r_xz) < self._causality_threshold or abs(r_yz) < self._causality_threshold:
                continue
            try:
                denom = (1.0 - r_xz**2) * (1.0 - r_yz**2)
                if denom <= 0:
                    continue
                r_xy_given_z = (r_xy - r_xz * r_yz) / (denom**0.5)
            except (ZeroDivisionError, ValueError):
                continue
            if abs(r_xy_given_z) < abs(r_xy) * 0.5:
                confounders.append(
                    {
                        "confounder": z,
                        "strength": round(min(abs(r_xz), abs(r_yz)), 4),
                        "r_xz": round(r_xz, 4),
                        "r_yz": round(r_yz, 4),
                    }
                )
        return confounders

    def _do_calculus_intervene(
        self, variable: str, value: float, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Simulate do(X=x): estimate effects under intervention.

        Uses basic adjustment: causal strength × value, reduced by confounder influence.
        """
        effects = [r for r in self._relationships if r.get("cause") == variable]
        results = []
        data = context.get("data", {})
        variables = list({r["effect"] for r in effects})
        all_vars = list(
            set(variables + [variable] + [v for r in effects for v in r.get("confounders", [])])
        )

        for r in effects:
            y = r["effect"]
            confounders = self._find_confounders(variable, y, data, all_vars)
            cf_penalty = max((c["strength"] for c in confounders), default=0.0)
            adjusted = r["strength"] * (1.0 - cf_penalty)
            results.append(
                {
                    "intervention": f"do({variable}={value})",
                    "effect": y,
                    "estimated_value": round(value * adjusted, 4),
                    "strength": round(adjusted, 4),
                }
            )
        return results


__all__ = ["CausalReasoningEngine"]
