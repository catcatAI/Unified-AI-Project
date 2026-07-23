# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================
"""
AudioQualityMonitor — quality tracking and reporting for audio pipeline.

Records SNR, processing time, and duration for each pipeline call.
Provides summary statistics for monitoring and alerting.

Analogous to VisionQualityMonitor for the vision pipeline.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AudioQualityMonitor:
    """Tracks audio pipeline quality over time.

    Records each pipeline call's metrics and provides
    rolling-window summary statistics.
    """

    def __init__(self, max_history: int = 500, log_path: Optional[str] = None):
        self._max_history = max_history
        self._log_path = log_path
        self._records: List[Dict[str, Any]] = []
        self._rolling_window = 50

    def record(self, result: Dict[str, Any]) -> None:
        """Record a pipeline result for quality tracking.

        Extracts relevant metrics and appends to history.
        """
        record = {
            "timestamp": time.time(),
            "snr": result.get("snr", 0.0),
            "time_ms": result.get("time_ms", 0.0),
            "duration": result.get("duration", 0.0),
            "cache_hit": result.get("cache_hit", False),
            "error": result.get("error"),
            "audio_hash": result.get("audio_hash", ""),
        }
        self._records.append(record)
        if len(self._records) > self._max_history:
            self._records = self._records[-self._max_history :]

        if self._log_path:
            try:
                path = Path(self._log_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            except Exception as e:
                logger.warning("Failed to write quality log: %s", e, exc_info=True)

    def report(self, window: Optional[int] = None) -> Dict[str, Any]:
        """Generate quality summary statistics.

        Args:
            window: Rolling window size (default: 50)

        Returns:
            dict with summary metrics
        """
        if not self._records:
            return {
                "total_calls": 0,
                "avg_snr": 0.0,
                "p95_time_ms": 0.0,
                "avg_time_ms": 0.0,
                "cache_hit_rate": 0.0,
                "error_rate": 0.0,
            }

        window = window or self._rolling_window
        recent = self._records[-window:]
        all_records = self._records

        snrs = [r["snr"] for r in all_records if r["snr"] is not None]
        times = [r["time_ms"] for r in all_records]
        cache_hits = sum(1 for r in all_records if r.get("cache_hit"))
        errors = sum(1 for r in all_records if r.get("error"))

        sorted_times = sorted(times)
        p95_idx = int(len(sorted_times) * 0.95)
        p95_time = (
            sorted_times[p95_idx]
            if p95_idx < len(sorted_times)
            else (sorted_times[-1] if sorted_times else 0)
        )

        return {
            "total_calls": len(all_records),
            "avg_snr": round(sum(snrs) / max(len(snrs), 1), 2),
            "p95_time_ms": round(p95_time, 1),
            "avg_time_ms": round(sum(times) / max(len(times), 1), 1),
            "cache_hit_rate": round(cache_hits / max(len(all_records), 1), 4),
            "error_rate": round(errors / max(len(all_records), 1), 4),
        }

    def clear(self) -> None:
        """Clear all records."""
        self._records.clear()

    def quality_trend(self, window: int = 10) -> Dict[str, Any]:
        """Calculate SNR quality trend over recent calls.

        Compares first half vs second half of recent window.

        Returns:
            dict with snr_delta, assessment
        """
        if len(self._records) < 4:
            return {"assessment": "insufficient_data"}

        recent = self._records[-window:]
        mid = len(recent) // 2
        first_half = recent[:mid]
        second_half = recent[mid:]

        snr_first = sum(r["snr"] for r in first_half if r["snr"]) / max(mid, 1)
        snr_second = sum(r["snr"] for r in second_half if r["snr"]) / max(len(second_half), 1)

        snr_delta = snr_second - snr_first

        if snr_delta > 3.0:
            assessment = "improving"
        elif snr_delta < -3.0:
            assessment = "degrading"
        else:
            assessment = "stable"

        return {
            "snr_delta": round(float(snr_delta), 2),
            "assessment": assessment,
        }
