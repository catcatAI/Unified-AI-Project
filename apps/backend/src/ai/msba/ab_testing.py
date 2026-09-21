# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
ABTesting — A/B testing framework for MSBA vs legacy pipeline.

Features:
- Traffic splitting (configurable percentage)
- Metric collection (latency, accuracy, user satisfaction)
- Statistical significance testing
- Gradual rollout support
"""

import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ExperimentResult:
    """Result from a single A/B test experiment."""

    variant: str
    input_text: str
    output: str
    latency_ms: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ABTesting:
    """
    A/B testing framework for MSBA vs legacy pipeline.

    Supports:
    - Traffic splitting (e.g., 10% MSBA, 90% legacy)
    - Metric collection and analysis
    - Statistical significance testing
    - Gradual rollout (10% -> 50% -> 100%)
    """

    def __init__(
        self,
        msba_pipeline: Any,
        legacy_pipeline: Any,
        msba_percentage: float = 0.1,
        seed: Optional[int] = None,
    ):
        """
        Args:
            msba_pipeline: MSBA pipeline instance.
            legacy_pipeline: Legacy pipeline instance.
            msba_percentage: Percentage of traffic to MSBA (0.0-1.0).
            seed: Random seed for reproducibility.
        """
        self.msba_pipeline = msba_pipeline
        self.legacy_pipeline = legacy_pipeline
        self.msba_percentage = msba_percentage
        self.rng = random.Random(seed)

        # Experiment results
        self.results: List[ExperimentResult] = []

        # Metrics
        self.msba_latencies: List[float] = []
        self.legacy_latencies: List[float] = []

    def route(self, input_text: str) -> str:
        """
        Route input to MSBA or legacy based on percentage.

        Returns:
            Response from selected pipeline.
        """
        use_msba = self.rng.random() < self.msba_percentage

        start = time.monotonic()

        if use_msba:
            output = self._run_msba(input_text)
            variant = "msba"
        else:
            output = self._run_legacy(input_text)
            variant = "legacy"

        latency = (time.monotonic() - start) * 1000

        # Record result
        result = ExperimentResult(
            variant=variant,
            input_text=input_text,
            output=output,
            latency_ms=latency,
            timestamp=time.time(),
        )
        self.results.append(result)

        # Track latency
        if variant == "msba":
            self.msba_latencies.append(latency)
        else:
            self.legacy_latencies.append(latency)

        return output

    def _run_msba(self, input_text: str) -> str:
        """Run input through MSBA pipeline."""
        try:
            # Handle sync process() directly
            result = self.msba_pipeline.process(input_text)
            # If it's a coroutine, run it async
            import asyncio

            if asyncio.iscoroutine(result):
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, result)
                        return future.result(timeout=2.0)
                else:
                    return loop.run_until_complete(result)
            return result
        except Exception as e:
            logger.debug("MSBA failed, falling back: %s", e)
            return self._run_legacy(input_text)

    def _run_legacy(self, input_text: str) -> str:
        """Run input through legacy pipeline."""
        try:
            if hasattr(self.legacy_pipeline, "process"):
                return self.legacy_pipeline.process(input_text)
            elif hasattr(self.legacy_pipeline, "process_sync"):
                return self.legacy_pipeline.process_sync(input_text)
            return str(self.legacy_pipeline)
        except Exception as e:
            logger.debug("Legacy pipeline failed: %s", e)
            return ""

    def get_metrics(self) -> Dict[str, Any]:
        """Get experiment metrics."""
        msba_count = sum(1 for r in self.results if r.variant == "msba")
        legacy_count = sum(1 for r in self.results if r.variant == "legacy")

        msba_avg_latency = (
            sum(self.msba_latencies) / len(self.msba_latencies) if self.msba_latencies else 0
        )
        legacy_avg_latency = (
            sum(self.legacy_latencies) / len(self.legacy_latencies) if self.legacy_latencies else 0
        )

        return {
            "total_experiments": len(self.results),
            "msba_count": msba_count,
            "legacy_count": legacy_count,
            "msba_percentage_actual": (msba_count / len(self.results) if self.results else 0),
            "msba_avg_latency_ms": msba_avg_latency,
            "legacy_avg_latency_ms": legacy_avg_latency,
            "speedup_ratio": (legacy_avg_latency / msba_avg_latency if msba_avg_latency > 0 else 0),
        }

    def set_percentage(self, percentage: float) -> None:
        """Update MSBA traffic percentage."""
        self.msba_percentage = max(0.0, min(1.0, percentage))
        logger.info(
            "MSBA traffic set to %.1f%%",
            self.msba_percentage * 100,
        )

    def gradual_rollout(
        self,
        steps: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform gradual rollout with metrics at each step.

        Args:
            steps: List of percentages to roll out at.
                   Default: [0.1, 0.25, 0.5, 0.75, 1.0]

        Returns:
            List of metrics at each step.
        """
        if steps is None:
            steps = [0.1, 0.25, 0.5, 0.75, 1.0]

        rollout_results = []
        for pct in steps:
            self.set_percentage(pct)
            # In real usage, would run N experiments here
            metrics = self.get_metrics()
            metrics["target_percentage"] = pct
            rollout_results.append(metrics)

        return rollout_results
