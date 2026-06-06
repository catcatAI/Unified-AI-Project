# =============================================================================
# ANGELA-MATRIX: [L3] [γδ] [B] [L2]
# =============================================================================
"""
GARDEN HybridRouter — Three-tier routing between ED3N, GARDEN-1G, and cloud LLM.

Implements Phase 4 of the GARDEN-1G roadmap.

Routing strategy:
  - < 10ms latency expected: ED3N (reflex / ultra-lightweight)
  - 10ms - 50ms: GARDEN-1G (vector dictionary + SNN)
  - > 50ms or low confidence: Cloud LLM (OpenAI, Anthropic, Ollama, etc.)

The router monitors confidence scores from each tier and can dynamically
adjust routing thresholds based on recent performance.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class TierResult:
    """The result from one tier in the hybrid pipeline."""

    tier: str                # "ed3n", "garden", "cloud"
    text: str                # Generated response text
    confidence: float        # 0.0 to 1.0
    latency_ms: float        # Inference latency in ms
    keys: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class RoutingDecision:
    """Record of a routing decision for diagnostics."""

    query: str
    selected_tier: str
    results: Dict[str, TierResult]
    total_latency_ms: float
    confidence: float
    decision_reason: str


# ---------------------------------------------------------------------------
# HybridRouter
# ---------------------------------------------------------------------------


class HybridRouter:
    """
    Three-tier router that selects the best backend for each query.

    Usage:
        router = HybridRouter()
        router.set_ed3n(ed3n_engine)
        router.set_garden(garden_engine)
        router.set_cloud(cloud_backend)

        result = router.route("你好")
        print(result.text)
    """

    def __init__(
        self,
        ed3n_threshold: float = 0.90,
        garden_threshold: float = 0.60,
        max_latency_ms: float = 1000.0,
        enable_adaptive_routing: bool = True,
    ):
        self.ed3n_threshold = ed3n_threshold
        self.garden_threshold = garden_threshold
        self.max_latency_ms = max_latency_ms
        self.enable_adaptive_routing = enable_adaptive_routing

        # Backends (lazy set)
        self._ed3n_engine: Optional[Any] = None
        self._garden_engine: Optional[Any] = None
        self._cloud_backend: Optional[Any] = None

        # Performance tracking for adaptive routing
        self._history: Dict[str, List[TierResult]] = {
            "ed3n": [],
            "garden": [],
            "cloud": [],
        }
        self._decisions: List[RoutingDecision] = []

    def set_ed3n(self, engine: Any) -> None:
        """Set the ED3N engine (ultra-lightweight tier)."""
        self._ed3n_engine = engine

    def set_garden(self, engine: Any) -> None:
        """Set the GARDEN engine (lightweight tier)."""
        self._garden_engine = engine

    def set_cloud(self, backend: Any) -> None:
        """Set the cloud LLM backend (full-power tier)."""
        self._cloud_backend = backend

    @property
    def has_ed3n(self) -> bool:
        return self._ed3n_engine is not None

    @property
    def has_garden(self) -> bool:
        return self._garden_engine is not None

    @property
    def has_cloud(self) -> bool:
        return self._cloud_backend is not None

    # ------------------------------------------------------------------
    # Core routing
    # ------------------------------------------------------------------

    async def route(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        force_tier: Optional[str] = None,
    ) -> TierResult:
        """
        Route a query through the best available tier.

        Args:
            text: User input text.
            context: Optional context dict.
            force_tier: If set, skip routing logic and use this tier directly.
                       One of "ed3n", "garden", "cloud".

        Returns:
            TierResult with the final response.
        """
        if not text:
            return TierResult(
                tier="none",
                text="",
                confidence=0.0,
                latency_ms=0.0,
                error="Empty input",
            )

        if force_tier:
            return await self._route_forced(text, force_tier, context)

        t_start = time.time()

        # Step 1: Try ED3N (fast reflex)
        if self.has_ed3n:
            ed3n_result = await self._try_ed3n(text)
            self._record("ed3n", ed3n_result)
            if ed3n_result.confidence >= self.ed3n_threshold:
                elapsed = (time.time() - t_start) * 1000
                decision = RoutingDecision(
                    query=text[:50],
                    selected_tier="ed3n",
                    results={"ed3n": ed3n_result},
                    total_latency_ms=elapsed,
                    confidence=ed3n_result.confidence,
                    decision_reason=f"ED3N confidence {ed3n_result.confidence:.2f} >= threshold {self.ed3n_threshold}",
                )
                self._decisions.append(decision)
                ed3n_result.latency_ms = elapsed
                return ed3n_result
        else:
            ed3n_result = None

        # Step 2: Try GARDEN (vector + SNN)
        if self.has_garden:
            garden_result = await self._try_garden(text, context)
            self._record("garden", garden_result)

            if garden_result.confidence >= self.garden_threshold:
                elapsed = (time.time() - t_start) * 1000
            results_dict: Dict[str, TierResult] = {}
            if ed3n_result is not None and ed3n_result.text:
                results_dict["ed3n"] = ed3n_result
            results_dict["garden"] = garden_result
            decision = RoutingDecision(
                query=text[:50],
                selected_tier="garden",
                results=results_dict,
                total_latency_ms=elapsed,
                confidence=garden_result.confidence,
                decision_reason=(
                    f"GARDEN confidence {garden_result.confidence:.2f} >= threshold {self.garden_threshold}"
                ),
            )
            self._decisions.append(decision)
                garden_result.latency_ms = elapsed
                return garden_result
        else:
            garden_result = None

        # Step 3: Fallback to cloud LLM
        if self.has_cloud:
            cloud_result = await self._try_cloud(text)
            self._record("cloud", cloud_result)
            elapsed = (time.time() - t_start) * 1000
            cloud_results: Dict[str, TierResult] = {}
            if ed3n_result is not None and ed3n_result.text:
                cloud_results["ed3n"] = ed3n_result
            if garden_result is not None and garden_result.text:
                cloud_results["garden"] = garden_result
            cloud_results["cloud"] = cloud_result
            decision = RoutingDecision(
                query=text[:50],
                selected_tier="cloud",
                results=cloud_results,
                total_latency_ms=elapsed,
                confidence=cloud_result.confidence,
                decision_reason="Fallback to cloud LLM (ED3N+GARDEN insufficient)",
            )
            self._decisions.append(decision)
            cloud_result.latency_ms = elapsed
            return cloud_result

        # No backend available
        elapsed = (time.time() - t_start) * 1000
        return TierResult(
            tier="none",
            text="No AI backend available.",
            confidence=0.0,
            latency_ms=elapsed,
            error="No backends configured",
        )

    async def _route_forced(
        self,
        text: str,
        tier: str,
        context: Optional[Dict[str, Any]],
    ) -> TierResult:
        """Route to a specific tier, bypassing routing logic."""
        t_start = time.time()
        if tier == "ed3n" and self.has_ed3n:
            result = await self._try_ed3n(text)
        elif tier == "garden" and self.has_garden:
            result = await self._try_garden(text, context)
        elif tier == "cloud" and self.has_cloud:
            result = await self._try_cloud(text)
        else:
            result = TierResult(
                tier="none",
                text=f"Tier '{tier}' not available.",
                confidence=0.0,
                latency_ms=(time.time() - t_start) * 1000,
                error=f"Tier '{tier}' not configured",
            )
        result.latency_ms = (time.time() - t_start) * 1000
        return result

    # ------------------------------------------------------------------
    # Individual tier calls
    # ------------------------------------------------------------------

    async def _try_ed3n(self, text: str) -> TierResult:
        """Call ED3N engine and wrap result."""
        if self._ed3n_engine is None:
            return TierResult(tier="ed3n", text="", confidence=0.0, latency_ms=0.0, error="Not configured")
        try:
            t0 = time.time()
            response = self._ed3n_engine.process(text)
            elapsed = (time.time() - t0) * 1000
            if response:
                return TierResult(
                    tier="ed3n",
                    text=response,
                    confidence=0.85,
                    latency_ms=elapsed,
                )
            return TierResult(tier="ed3n", text="", confidence=0.0, latency_ms=elapsed, error="Empty response")
        except Exception as e:
            logger.warning("HybridRouter: ED3N error: %s", e)
            return TierResult(tier="ed3n", text="", confidence=0.0, latency_ms=0.0, error=str(e))

    async def _try_garden(
        self,
        text: str,
        context: Optional[Dict[str, Any]],
    ) -> TierResult:
        """Call GARDEN engine and wrap result."""
        if self._garden_engine is None:
            return TierResult(tier="garden", text="", confidence=0.0, latency_ms=0.0, error="Not configured")
        try:
            t0 = time.time()
            response = self._garden_engine.process(text, context=context)
            elapsed = (time.time() - t0) * 1000
            if response:
                return TierResult(
                    tier="garden",
                    text=response,
                    confidence=0.75,
                    latency_ms=elapsed,
                )
            return TierResult(tier="garden", text="", confidence=0.0, latency_ms=elapsed, error="Empty response")
        except Exception as e:
            logger.warning("HybridRouter: GARDEN error: %s", e)
            return TierResult(tier="garden", text="", confidence=0.0, latency_ms=0.0, error=str(e))

    async def _try_cloud(self, text: str) -> TierResult:
        """Call cloud LLM backend and wrap result."""
        if self._cloud_backend is None:
            return TierResult(tier="cloud", text="", confidence=0.0, latency_ms=0.0, error="Not configured")
        try:
            t0 = time.time()
            response = await self._cloud_backend.generate(text)
            elapsed = (time.time() - t0) * 1000
            if response and response.text:
                return TierResult(
                    tier="cloud",
                    text=response.text,
                    confidence=0.90,
                    latency_ms=elapsed,
                )
            return TierResult(tier="cloud", text="", confidence=0.0, latency_ms=elapsed, error="Empty response")
        except Exception as e:
            logger.warning("HybridRouter: cloud error: %s", e)
            return TierResult(tier="cloud", text="", confidence=0.0, latency_ms=0.0, error=str(e))

    # ------------------------------------------------------------------
    # Adaptive routing (performance tracking)
    # ------------------------------------------------------------------

    def _record(self, tier: str, result: TierResult) -> None:
        """Store result in history for adaptive threshold tuning."""
        self._history.setdefault(tier, []).append(result)
        if len(self._history[tier]) > 100:
            self._history[tier] = self._history[tier][-100:]

    def get_average_latency(self, tier: str) -> float:
        """Get average latency for a tier over recent history."""
        results = self._history.get(tier, [])
        if not results:
            return 0.0
        return sum(r.latency_ms for r in results) / len(results)

    def get_success_rate(self, tier: str) -> float:
        """Get fraction of non-empty responses for a tier."""
        results = self._history.get(tier, [])
        if not results:
            return 0.0
        successes = sum(1 for r in results if r.text and not r.error)
        return successes / len(results)

    def tune_thresholds(self) -> Dict[str, float]:
        """
        Dynamically adjust routing thresholds based on recent performance.
        Returns the new thresholds.
        """
        if not self.enable_adaptive_routing:
            return {"ed3n": self.ed3n_threshold, "garden": self.garden_threshold}

        ed3n_success = self.get_success_rate("ed3n")
        garden_success = self.get_success_rate("garden")

        # If ED3N is very reliable, raise threshold to catch more queries
        if ed3n_success > 0.95:
            self.ed3n_threshold = min(0.95, self.ed3n_threshold + 0.01)
        elif ed3n_success < 0.70:
            self.ed3n_threshold = max(0.60, self.ed3n_threshold - 0.02)

        # If GARDEN is very reliable, lower threshold to use it more
        if garden_success > 0.90:
            self.garden_threshold = max(0.40, self.garden_threshold - 0.01)
        elif garden_success < 0.60:
            self.garden_threshold = min(0.75, self.garden_threshold + 0.02)

        return {"ed3n": self.ed3n_threshold, "garden": self.garden_threshold}

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return router statistics for monitoring."""
        return {
            "thresholds": {
                "ed3n": self.ed3n_threshold,
                "garden": self.garden_threshold,
                "max_latency_ms": self.max_latency_ms,
            },
            "adaptive_routing": self.enable_adaptive_routing,
            "backends": {
                "ed3n": self.has_ed3n,
                "garden": self.has_garden,
                "cloud": self.has_cloud,
            },
            "performance": {
                tier: {
                    "avg_latency_ms": round(self.get_average_latency(tier), 1),
                    "success_rate": round(self.get_success_rate(tier), 3),
                    "samples": len(history),
                }
                for tier, history in self._history.items()
            },
            "total_decisions": len(self._decisions),
        }

    def get_recent_decisions(self, n: int = 10) -> List[Dict[str, Any]]:
        """Return the last N routing decisions for analysis."""
        recent = self._decisions[-n:]
        return [
            {
                "query": d.query,
                "selected_tier": d.selected_tier,
                "confidence": round(d.confidence, 3),
                "total_latency_ms": round(d.total_latency_ms, 1),
                "reason": d.decision_reason,
            }
            for d in recent
        ]

    def clear_history(self) -> None:
        """Reset all performance tracking data."""
        self._history = {"ed3n": [], "garden": [], "cloud": []}
        self._decisions.clear()
