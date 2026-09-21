# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
MetricsCollector — monitoring and metrics for MSBA pipeline.

Collects:
- Latency metrics (per-layer, end-to-end)
- Cache hit rates
- Block selection patterns
- Error rates
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LatencyRecord:
    """Single latency measurement."""

    layer: str
    latency_ms: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineMetrics:
    """Aggregated pipeline metrics."""

    total_requests: int = 0
    total_latency_ms: float = 0.0
    layer_latencies: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    cache_hits: int = 0
    cache_misses: int = 0
    errors: int = 0
    block_selections: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    seed_sources: Dict[str, int] = field(default_factory=lambda: defaultdict(int))


class MetricsCollector:
    """
    Collects and aggregates MSBA pipeline metrics.

    Supports:
    - Per-layer latency tracking
    - Cache hit rate calculation
    - Block selection frequency analysis
    - Error rate monitoring
    """

    def __init__(self, max_records: int = 10000):
        """
        Args:
            max_records: Maximum number of records to keep.
        """
        self.max_records = max_records
        self.metrics = PipelineMetrics()
        self._latency_records: List[LatencyRecord] = []
        self._start_time = time.time()

    def record_latency(
        self,
        layer: str,
        latency_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record latency for a specific layer.

        Args:
            layer: Layer name (e.g., "seed", "selection", "hit").
            latency_ms: Latency in milliseconds.
            metadata: Optional metadata.
        """
        record = LatencyRecord(
            layer=layer,
            latency_ms=latency_ms,
            timestamp=time.time(),
            metadata=metadata or {},
        )

        self._latency_records.append(record)
        self.metrics.layer_latencies[layer].append(latency_ms)
        self.metrics.total_latency_ms += latency_ms

        # Trim if too many records
        if len(self._latency_records) > self.max_records:
            self._latency_records = self._latency_records[-self.max_records :]

    def record_request(self) -> None:
        """Record a new request."""
        self.metrics.total_requests += 1

    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        self.metrics.cache_hits += 1

    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        self.metrics.cache_misses += 1

    def record_error(self) -> None:
        """Record an error."""
        self.metrics.errors += 1

    def record_block_selection(self, block_id: str) -> None:
        """Record a block selection."""
        self.metrics.block_selections[block_id] += 1

    def record_seed_source(self, source: str) -> None:
        """Record a seed source."""
        self.metrics.seed_sources[source] += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get summary metrics."""
        total_cache = self.metrics.cache_hits + self.metrics.cache_misses
        cache_hit_rate = self.metrics.cache_hits / total_cache if total_cache > 0 else 0

        avg_latency = (
            self.metrics.total_latency_ms / self.metrics.total_requests
            if self.metrics.total_requests > 0
            else 0
        )

        error_rate = (
            self.metrics.errors / self.metrics.total_requests
            if self.metrics.total_requests > 0
            else 0
        )

        return {
            "total_requests": self.metrics.total_requests,
            "avg_latency_ms": avg_latency,
            "total_latency_ms": self.metrics.total_latency_ms,
            "cache_hit_rate": cache_hit_rate,
            "cache_hits": self.metrics.cache_hits,
            "cache_misses": self.metrics.cache_misses,
            "error_rate": error_rate,
            "errors": self.metrics.errors,
            "uptime_seconds": time.time() - self._start_time,
        }

    def get_layer_breakdown(self) -> Dict[str, Dict[str, float]]:
        """Get per-layer latency breakdown."""
        breakdown = {}
        for layer, latencies in self.metrics.layer_latencies.items():
            if latencies:
                breakdown[layer] = {
                    "count": len(latencies),
                    "avg_ms": sum(latencies) / len(latencies),
                    "min_ms": min(latencies),
                    "max_ms": max(latencies),
                    "p50_ms": self._percentile(latencies, 50),
                    "p95_ms": self._percentile(latencies, 95),
                    "p99_ms": self._percentile(latencies, 99),
                }
        return breakdown

    def get_block_frequency(self) -> Dict[str, float]:
        """Get block selection frequency."""
        total = sum(self.metrics.block_selections.values())
        if total == 0:
            return {}

        return {block: count / total for block, count in self.metrics.block_selections.items()}

    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics = PipelineMetrics()
        self._latency_records.clear()
        self._start_time = time.time()

    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Calculate percentile."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        index = min(index, len(sorted_data) - 1)
        return sorted_data[index]
