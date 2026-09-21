# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
PerformanceProfiler — measure and optimize MSBA pipeline latency.

Tracks per-layer latency, identifies bottlenecks,
and suggests optimizations.
"""

import logging
import time
from collections import deque
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PerformanceProfiler:
    """
    Profiles MSBA pipeline performance.

    Features:
    - Per-layer latency tracking
    - Bottleneck identification
    - Optimization suggestions
    - Historical trend analysis
    """

    # Target latency budget per layer (ms)
    LAYER_BUDGETS = {
        "seed": 5.0,
        "selection": 10.0,
        "hit": 40.0,
        "convergence": 15.0,
        "decode": 10.0,
        "total": 85.0,
    }

    def __init__(self, history_size: int = 100):
        """
        Args:
            history_size: Number of recent measurements to keep.
        """
        self.history_size = history_size
        self._layer_times: Dict[str, deque] = {}
        self._total_times: deque = deque(maxlen=history_size)
        self._bottleneck_counts: Dict[str, int] = {}

    def start_layer(self, layer: str) -> float:
        """
        Start timing a layer.

        Returns:
            Start timestamp.
        """
        return time.monotonic()

    def end_layer(self, layer: str, start: float) -> float:
        """
        End timing a layer and record.

        Returns:
            Elapsed time in ms.
        """
        elapsed = (time.monotonic() - start) * 1000

        if layer not in self._layer_times:
            self._layer_times[layer] = deque(maxlen=self.history_size)
        self._layer_times[layer].append(elapsed)

        # Check budget
        budget = self.LAYER_BUDGETS.get(layer)
        if budget and elapsed > budget:
            self._bottleneck_counts[layer] = self._bottleneck_counts.get(layer, 0) + 1
            logger.debug(
                "Layer %s exceeded budget: %.1fms > %.1fms",
                layer,
                elapsed,
                budget,
            )

        return elapsed

    def start_total(self) -> float:
        """Start timing total pipeline."""
        return time.monotonic()

    def end_total(self, start: float) -> float:
        """End timing total pipeline and record."""
        elapsed = (time.monotonic() - start) * 1000
        self._total_times.append(elapsed)
        return elapsed

    def get_layer_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for each layer."""
        stats = {}
        for layer, times in self._layer_times.items():
            if times:
                times_list = list(times)
                stats[layer] = {
                    "count": len(times_list),
                    "avg_ms": sum(times_list) / len(times_list),
                    "min_ms": min(times_list),
                    "max_ms": max(times_list),
                    "p50_ms": self._percentile(times_list, 50),
                    "p95_ms": self._percentile(times_list, 95),
                    "budget_ms": self.LAYER_BUDGETS.get(layer, 0),
                    "budget_usage_pct": (
                        sum(times_list) / len(times_list) / self.LAYER_BUDGETS.get(layer, 1) * 100
                        if layer in self.LAYER_BUDGETS
                        else 0
                    ),
                }
        return stats

    def get_total_stats(self) -> Dict[str, float]:
        """Get total pipeline statistics."""
        if not self._total_times:
            return {}
        times = list(self._total_times)
        return {
            "count": len(times),
            "avg_ms": sum(times) / len(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "p50_ms": self._percentile(times, 50),
            "p95_ms": self._percentile(times, 95),
            "budget_ms": self.LAYER_BUDGETS["total"],
            "budget_usage_pct": (sum(times) / len(times) / self.LAYER_BUDGETS["total"] * 100),
        }

    def get_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        for layer, count in sorted(
            self._bottleneck_counts.items(),
            key=lambda x: -x[1],
        ):
            budget = self.LAYER_BUDGETS.get(layer, 0)
            times = self._layer_times.get(layer, deque())
            avg = sum(times) / len(times) if times else 0

            bottlenecks.append(
                {
                    "layer": layer,
                    "over_budget_count": count,
                    "avg_ms": avg,
                    "budget_ms": budget,
                    "severity": "high" if avg > budget * 1.5 else "medium",
                }
            )

        return bottlenecks

    def suggest_optimizations(self) -> List[str]:
        """Suggest optimizations based on profiling data."""
        suggestions = []
        stats = self.get_layer_stats()

        for layer, s in stats.items():
            if s["budget_usage_pct"] > 100:
                suggestions.append(
                    f"Layer '{layer}' exceeds budget "
                    f"({s['avg_ms']:.1f}ms > {s['budget_ms']:.1f}ms). "
                    f"Consider parallelization or caching."
                )
            elif s["budget_usage_pct"] > 80:
                suggestions.append(
                    f"Layer '{layer}' is near budget "
                    f"({s['budget_usage_pct']:.0f}%). "
                    f"Monitor for regressions."
                )

        total = self.get_total_stats()
        if total and total.get("budget_usage_pct", 0) > 100:
            suggestions.append(
                f"Total pipeline exceeds budget "
                f"({total['avg_ms']:.1f}ms > "
                f"{self.LAYER_BUDGETS['total']:.1f}ms). "
                f"Consider reducing block count or LLM fallback."
            )

        if not suggestions:
            suggestions.append("All layers within budget. No optimizations needed.")

        return suggestions

    def reset(self) -> None:
        """Reset all profiling data."""
        self._layer_times.clear()
        self._total_times.clear()
        self._bottleneck_counts.clear()

    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Calculate percentile."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        index = min(index, len(sorted_data) - 1)
        return sorted_data[index]
