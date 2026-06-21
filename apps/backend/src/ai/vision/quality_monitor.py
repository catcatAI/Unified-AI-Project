# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================
"""
VisionQualityMonitor — quality tracking and reporting for vision pipeline.

Records SSIM/PSNR, processing time, and image size for each pipeline call.
Provides summary statistics for monitoring and alerting.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VisionQualityMonitor:
    """Tracks vision pipeline quality over time.

    Records each pipeline call's metrics and provides
    rolling-window summary statistics.

    Attributes:
        max_history: Maximum number of records to keep in memory
        log_path: Optional path to write JSONL quality logs
    """

    def __init__(self, max_history: int = 500,
                 log_path: Optional[str] = None):
        self._max_history = max_history
        self._log_path = log_path
        self._records: List[Dict[str, Any]] = []
        self._rolling_window = 50

    def record(self, result: Dict[str, Any]) -> None:
        """Record a pipeline result for quality tracking.

        Extracts relevant metrics and appends to history.
        Limits history to max_history entries.
        """
        record = {
            "timestamp": time.time(),
            "ssim": result.get("ssim", 0.0),
            "psnr": result.get("psnr", 0.0),
            "time_ms": result.get("time_ms", 0.0),
            "image_size": result.get("original_size", (0, 0)),
            "cache_hit": result.get("cache_hit", False),
            "error": result.get("error"),
            "image_hash": result.get("image_hash", ""),
        }
        self._records.append(record)
        if len(self._records) > self._max_history:
            self._records = self._records[-self._max_history:]

        # Write to log file if configured
        if self._log_path:
            try:
                path = Path(self._log_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            except Exception as e:
                logger.debug("Failed to write quality log: %s", e)

    def report(self, window: Optional[int] = None) -> Dict[str, Any]:
        """Generate quality summary statistics.

        Args:
            window: Rolling window size (default: self._rolling_window)

        Returns:
            dict with summary metrics:
              - total_calls (int)
              - avg_ssim (float)
              - avg_psnr (float)
              - p95_time_ms (float)
              - avg_time_ms (float)
              - cache_hit_rate (float)
              - error_rate (float)
              - recent_quality (dict with last `window` entries)
        """
        if not self._records:
            return {
                "total_calls": 0,
                "avg_ssim": 0.0,
                "avg_psnr": 0.0,
                "p95_time_ms": 0.0,
                "avg_time_ms": 0.0,
                "cache_hit_rate": 0.0,
                "error_rate": 0.0,
                "recent_quality": [],
            }

        window = window or self._rolling_window
        recent = self._records[-window:]
        all_records = self._records

        ssims = [r["ssim"] for r in all_records if r["ssim"] is not None]
        psnrs = [r["psnr"] for r in all_records if r["psnr"] is not None]
        times = [r["time_ms"] for r in all_records]
        cache_hits = sum(1 for r in all_records if r.get("cache_hit"))
        errors = sum(1 for r in all_records if r.get("error"))

        # P95 calculation
        sorted_times = sorted(times)
        p95_idx = int(len(sorted_times) * 0.95)
        p95_time = sorted_times[p95_idx] if p95_idx < len(sorted_times) else (sorted_times[-1] if sorted_times else 0)

        return {
            "total_calls": len(all_records),
            "avg_ssim": round(sum(ssims) / max(len(ssims), 1), 6),
            "avg_psnr": round(sum(psnrs) / max(len(psnrs), 1), 2),
            "p95_time_ms": round(p95_time, 1),
            "avg_time_ms": round(sum(times) / max(len(times), 1), 1),
            "cache_hit_rate": round(cache_hits / max(len(all_records), 1), 4),
            "error_rate": round(errors / max(len(all_records), 1), 4),
            "recent_quality": [
                {
                    "ssim": r["ssim"],
                    "psnr": r["psnr"],
                    "time_ms": r["time_ms"],
                }
                for r in recent[-10:]  # Last 10 for detailed view
            ],
        }

    def clear(self) -> None:
        """Clear all records."""
        self._records.clear()

    def quality_trend(self, window: int = 10) -> Dict[str, Any]:
        """Calculate quality trend over recent calls.

        Compares first half vs second half of recent window.

        Args:
            window: Number of recent calls to compare

        Returns:
            dict with ssim_delta, psnr_delta, time_delta, assessment
        """
        if len(self._records) < 4:
            return {"assessment": "insufficient_data"}

        recent = self._records[-window:]
        mid = len(recent) // 2
        first_half = recent[:mid]
        second_half = recent[mid:]

        ssim_first = sum(r["ssim"] for r in first_half if r["ssim"]) / max(mid, 1)
        ssim_second = sum(r["ssim"] for r in second_half if r["ssim"]) / max(len(second_half), 1)
        psnr_first = sum(r["psnr"] for r in first_half if r["psnr"]) / max(mid, 1)
        psnr_second = sum(r["psnr"] for r in second_half if r["psnr"]) / max(len(second_half), 1)

        ssim_delta = ssim_second - ssim_first
        psnr_delta = psnr_second - psnr_first

        if ssim_delta > 0.01 and psnr_delta > 1.0:
            assessment = "improving"
        elif ssim_delta < -0.01 or psnr_delta < -1.0:
            assessment = "degrading"
        else:
            assessment = "stable"

        return {
            "ssim_delta": round(float(ssim_delta), 6),
            "psnr_delta": round(float(psnr_delta), 2),
            "assessment": assessment,
        }
