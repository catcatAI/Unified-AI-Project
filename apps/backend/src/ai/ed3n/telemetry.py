# =============================================================================
# ANGELA-MATRIX: [L3] [γ] [C] [L2]
# =============================================================================

import logging
import statistics
import threading
import time
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TelemetryCollector:
    """
    Collects per-query telemetry for the ED3N pipeline.
    Thread-safe singletons tracked by query_id.
    """

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._lock = threading.Lock()
        self._records: List[dict] = []
        self._reflex_counts: Dict[str, int] = {}
        self._fallback_count = 0
        self._total_queries = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._stage_times: Dict[str, List[float]] = {}

    def record_query(
        self,
        query_id: str,
        input_text: str,
        stages: Dict[str, float],
        reflex_match: Optional[str],
        cache_hit: bool,
        matched_keys: List[str],
        output_text: str,
        confidence: float,
        is_fallback: bool,
    ) -> dict:
        record = {
            "query_id": query_id,
            "input_text": input_text,
            "stages": dict(stages),
            "reflex_match": reflex_match,
            "cache_hit": cache_hit,
            "matched_keys": list(matched_keys),
            "output_text": output_text,
            "confidence": confidence,
            "is_fallback": is_fallback,
            "timestamp": time.time(),
        }
        with self._lock:
            self._records.append(record)
            if len(self._records) > self.max_history:
                self._records.pop(0)
            self._total_queries += 1
            if is_fallback:
                self._fallback_count += 1
            if cache_hit:
                self._cache_hits += 1
            else:
                self._cache_misses += 1
            if reflex_match is not None:
                self._reflex_counts[reflex_match] = (
                    self._reflex_counts.get(reflex_match, 0) + 1
                )
            for stage_name, latency_ms in stages.items():
                if stage_name not in self._stage_times:
                    self._stage_times[stage_name] = []
                self._stage_times[stage_name].append(latency_ms)
                if len(self._stage_times[stage_name]) > self.max_history:
                    self._stage_times[stage_name].pop(0)
        return record

    def get_summary(self) -> dict:
        with self._lock:
            total = self._total_queries
            if total == 0:
                return {"total_queries": 0}
            fallback_rate = self._fallback_count / total
            cache_total = self._cache_hits + self._cache_misses
            cache_hit_rate = self._cache_hits / cache_total if cache_total > 0 else 0.0

            stage_summary = {}
            for stage_name, times in self._stage_times.items():
                if not times:
                    continue
                sorted_t = sorted(times)
                n = len(sorted_t)
                stage_summary[stage_name] = {
                    "count": n,
                    "avg_ms": round(sum(sorted_t) / n, 3),
                    "min_ms": round(sorted_t[0], 3),
                    "max_ms": round(sorted_t[-1], 3),
                    "p50_ms": self._percentile(sorted_t, 50),
                    "p95_ms": self._percentile(sorted_t, 95),
                    "p99_ms": self._percentile(sorted_t, 99),
                }

            confidences = [
                r["confidence"]
                for r in self._records
                if r["confidence"] is not None
            ]

            return {
                "total_queries": total,
                "fallback_count": self._fallback_count,
                "fallback_rate": round(fallback_rate, 4),
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "cache_hit_rate": round(cache_hit_rate, 4),
                "stages": stage_summary,
                "confidence_avg": round(
                    sum(confidences) / len(confidences), 4
                ) if confidences else 0.0,
                "reflex_pattern_count": len(self._reflex_counts),
            }

    def get_reflex_report(self) -> List[Tuple[str, int, float]]:
        with self._lock:
            total = self._total_queries
            if total == 0:
                return []
            sorted_patterns = sorted(
                self._reflex_counts.items(), key=lambda x: x[1], reverse=True
            )
            return [
                (pattern, count, round(count / total * 100, 2))
                for pattern, count in sorted_patterns
            ]

    def get_latency_histogram(
        self, stage: str, buckets: Optional[List[float]] = None
    ) -> dict:
        if buckets is None:
            buckets = [1.0, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0]
        with self._lock:
            times = self._stage_times.get(stage, [])
            if not times:
                return {}
            bucket_counts = {f"<={b}ms": 0 for b in buckets}
            bucket_counts[">max"] = 0
            for t in times:
                placed = False
                for b in buckets:
                    if t <= b:
                        bucket_counts[f"<={b}ms"] += 1
                        placed = True
                        break
                if not placed:
                    bucket_counts[">max"] += 1
            n = len(times)
            return {
                "stage": stage,
                "total_samples": n,
                "buckets": bucket_counts,
            }

    @staticmethod
    def _percentile(sorted_data: List[float], percentile: float) -> float:
        if not sorted_data:
            return 0.0
        k = (percentile / 100.0) * (len(sorted_data) - 1)
        f = int(k)
        c = f + 1
        if f >= len(sorted_data):
            return round(sorted_data[-1], 3)
        if c >= len(sorted_data):
            return round(sorted_data[-1], 3)
        return round(sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f]), 3)
