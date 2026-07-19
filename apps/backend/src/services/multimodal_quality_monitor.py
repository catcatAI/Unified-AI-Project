"""
MultimodalQualityMonitor — background quality monitoring for multimodal pipelines.

Analogous to ProactiveInteractionSystem background loop. Provides:
  - Periodic sampling (every 60s) of encoder/decoder quality
  - Quality degradation detection (>10% drop triggers alert)
  - Alert logging to crisis_log on significant degradation
  - Historical trend tracking for quality reports

P37: Production hardening — quality monitoring.

ANGELA-MATRIX: [L5] [βγδ] [B] [L4]
"""

import asyncio
import logging
import os
import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

from core.crisis_log import append_quality_log as _append_quality_log
from core.crisis_log import write_crisis_log as _write_crisis_log
from core.utils import safe_error

logger = logging.getLogger(__name__)


class MultimodalQualityMonitor:
    """Background quality monitor for multimodal pipelines.

    Samples encoder/decoder quality on a configurable interval,
    detects degradation trends, and logs alerts when quality drops.
    """

    DEFAULT_INTERVAL_SEC = 60.0
    DEGRADATION_THRESHOLD = 0.10  # 10% drop triggers alert
    MAX_HISTORY = 100  # Keep last 100 samples

    def __init__(self, service, interval_sec: Optional[float] = None):
        """Initialize with a MultimodalService instance.

        Args:
            service: Object with encode/decode/evaluate methods
            interval_sec: Sampling interval in seconds
        """
        self._service = service
        self._interval = interval_sec or self.DEFAULT_INTERVAL_SEC
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Quality history: list of {timestamp, vision_quality, audio_quality, ...}
        self._history: deque = deque(maxlen=self.MAX_HISTORY)

        # Summary statistics
        self._total_samples = 0
        self._alerts_triggered = 0
        self._last_vision_quality = 0.0
        self._last_audio_quality = 0.0

    # --- Lifecycle ---

    async def start(self) -> None:
        """Start the background quality monitoring loop."""
        if self._running:
            logger.warning("QualityMonitor already running")
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("QualityMonitor started (interval=%ss)", self._interval)

    async def stop(self) -> None:
        """Stop the background quality monitoring loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info(
            "QualityMonitor stopped (samples=%d, alerts=%d)",
            self._total_samples,
            self._alerts_triggered,
        )

    @property
    def is_running(self) -> bool:
        return self._running

    # --- Background loop ---

    async def _run_loop(self) -> None:
        """Main background sampling loop."""
        while self._running:
            try:
                await self._sample_quality()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("QualityMonitor sampling error: %s", e)
            await asyncio.sleep(self._interval)

    async def _sample_quality(self) -> None:
        """Take a quality sample of the multimodal pipeline.

        Samples both vision and audio quality using synthetic evaluation.
        Detects degradation and triggers alerts if quality drops.
        """
        t0 = time.time()
        sample: Dict[str, Any] = {
            "timestamp": t0,
            "sampling_time_ms": 0,
        }

        # Sample vision quality
        vision_quality = 0.0
        try:
            if hasattr(self._service, "evaluate"):
                vis_result = await self._service.evaluate(
                    item_id=None, modality="vision", n_samples=3
                )
                metrics = vis_result.get("metrics", {})
                if isinstance(metrics, dict):
                    vision_quality = metrics.get("ssim", 0.0)
                sample["vision"] = {
                    "quality": vision_quality,
                    "source": "synthetic_evaluation",
                }
        except Exception as e:
            sample["vision"] = {"quality": 0.0, "error": safe_error(e)}

        # Sample audio quality
        audio_quality = 0.0
        try:
            if hasattr(self._service, "evaluate"):
                aud_result = await self._service.evaluate(
                    item_id=None, modality="audio", n_samples=3
                )
                metrics = aud_result.get("metrics", {})
                if isinstance(metrics, dict):
                    audio_quality = metrics.get("snr", 0.0)
                sample["audio"] = {
                    "quality": audio_quality,
                    "source": "synthetic_evaluation",
                }
        except Exception as e:
            sample["audio"] = {"quality": 0.0, "error": safe_error(e)}

        sample["sampling_time_ms"] = round((time.time() - t0) * 1000, 1)

        # Detect degradation
        degradation = self._detect_degradation(vision_quality, audio_quality)
        if degradation:
            sample["degradation"] = degradation
            self._alerts_triggered += 1

            # Log to crisis log
            _write_crisis_log(
                2,
                {
                    "monitor": "multimodal_quality",
                    "degradation": degradation,
                    "vision_quality": vision_quality,
                    "audio_quality": audio_quality,
                },
            )

        # Store history
        self._history.append(sample)
        self._total_samples += 1
        self._last_vision_quality = vision_quality
        self._last_audio_quality = audio_quality

        # Append to quality log
        _append_quality_log(sample)

    # --- Degradation detection ---

    def _detect_degradation(self, vision_q: float, audio_q: float) -> Optional[Dict[str, Any]]:
        """Detect if quality has degraded significantly.

        Compares current sample to the rolling average of previous samples.
        Returns degradation info if threshold exceeded, None otherwise.
        """
        degradation_info: Dict[str, Any] = {}

        if len(self._history) < 3:
            return None  # Need at least 3 samples for baseline

        # Compute rolling average of vision quality
        prev_vision = [s.get("vision", {}).get("quality", 0.0) for s in list(self._history)[:-1]]
        prev_vision = [v for v in prev_vision if v > 0]
        vision_degraded = False
        if prev_vision and vision_q > 0:
            avg_vision = sum(prev_vision) / len(prev_vision)
            if avg_vision > 0:
                vision_drop = (avg_vision - vision_q) / avg_vision
                if vision_drop > self.DEGRADATION_THRESHOLD:
                    degradation_info["vision"] = {
                        "current": vision_q,
                        "baseline": round(avg_vision, 4),
                        "drop_pct": round(vision_drop * 100, 1),
                    }
                    vision_degraded = True

        # Compute rolling average of audio quality
        prev_audio = [s.get("audio", {}).get("quality", 0.0) for s in list(self._history)[:-1]]
        prev_audio = [a for a in prev_audio if a > 0]
        audio_degraded = False
        if prev_audio and audio_q > 0:
            avg_audio = sum(prev_audio) / len(prev_audio)
            if avg_audio > 0:
                audio_drop = (avg_audio - audio_q) / avg_audio
                if audio_drop > self.DEGRADATION_THRESHOLD:
                    degradation_info["audio"] = {
                        "current": audio_q,
                        "baseline": round(avg_audio, 4),
                        "drop_pct": round(audio_drop * 100, 1),
                    }
                    audio_degraded = True

        if vision_degraded or audio_degraded:
            return degradation_info
        return None

    # --- Reports ---

    def report(self) -> Dict[str, Any]:
        """Get the current quality report.

        Returns dict with vision_quality, audio_quality, total_samples, alerts,
        and recent history summary.
        """
        if not self._history:
            return {
                "status": "no_data",
                "total_samples": 0,
                "alerts_triggered": 0,
                "last_vision_quality": 0.0,
                "last_audio_quality": 0.0,
            }

        recent = list(self._history)[-min(10, len(self._history)) :]
        recent_vision = [
            s.get("vision", {}).get("quality", 0.0)
            for s in recent
            if s.get("vision", {}).get("quality")
        ]
        recent_audio = [
            s.get("audio", {}).get("quality", 0.0)
            for s in recent
            if s.get("audio", {}).get("quality")
        ]

        avg_vision = sum(recent_vision) / len(recent_vision) if recent_vision else 0.0
        avg_audio = sum(recent_audio) / len(recent_audio) if recent_audio else 0.0

        return {
            "status": "active" if self._running else "stopped",
            "total_samples": self._total_samples,
            "alerts_triggered": self._alerts_triggered,
            "last_vision_quality": self._last_vision_quality,
            "last_audio_quality": self._last_audio_quality,
            "vision_quality_avg": round(avg_vision, 4),
            "audio_quality_avg": round(avg_audio, 4),
            "interval_sec": self._interval,
            "history_count": len(self._history),
        }

    def quality_trend(self) -> Dict[str, Any]:
        """Analyze quality trend over the sampling history.

        Compares first half vs second half of history.
        Returns quality_trend (improving/degrading/stable) per modality.
        """
        if len(self._history) < 4:
            return {"status": "insufficient_data", "samples": len(self._history)}

        samples = list(self._history)
        mid = len(samples) // 2

        def _avg_quality(segment, key) -> float:
            vals = [
                s.get(key, {}).get("quality", 0.0)
                for s in segment
                if s.get(key, {}).get("quality", 0.0) > 0
            ]
            return sum(vals) / len(vals) if vals else 0.0

        first_vis = _avg_quality(samples[:mid], "vision")
        second_vis = _avg_quality(samples[mid:], "vision")
        first_aud = _avg_quality(samples[:mid], "audio")
        second_aud = _avg_quality(samples[mid:], "audio")

        def _trend(first, second, threshold=0.05):
            if first == 0:
                return "stable"
            change = (second - first) / abs(first)
            if change > threshold:
                return "improving"
            elif change < -threshold:
                return "degrading"
            return "stable"

        trend_dict = {
            "vision": _trend(first_vis, second_vis),
            "audio": _trend(first_aud, second_aud),
        }

        # Overall health
        degrading = [k for k, v in trend_dict.items() if v == "degrading"]
        overall = "healthy"
        if len(degrading) == 2:
            overall = "critical"
        elif len(degrading) == 1:
            overall = "degraded"

        return {
            "trend": trend_dict,
            "overall": overall,
            "first_half": {"vision": round(first_vis, 4), "audio": round(first_aud, 4)},
            "second_half": {"vision": round(second_vis, 4), "audio": round(second_aud, 4)},
            "samples_analyzed": len(samples),
        }

    def get_latest_sample(self) -> Dict[str, Any]:
        """Get the most recent quality sample."""
        if not self._history:
            return {"status": "no_data"}
        return dict(self._history[-1])
