"""
CrossModalQualityDashboard — integrated quality monitoring dashboard.

Integrates VisionQualityMonitor + AudioQualityMonitor into a single
dashboard with overall health assessment.

P33: Cross-modal integration layer for quality monitoring.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CrossModalQualityDashboard:
    """Integrated quality dashboard for all multimodal pipelines.

    Provides unified access to vision and audio quality monitors,
    plus cross-modal quality assessment.

    Attributes:
        vision_log_path: Optional path for JSONL vision quality logs
        audio_log_path: Optional path for JSONL audio quality logs
    """

    def __init__(self, vision_log_path: Optional[str] = None,
                 audio_log_path: Optional[str] = None,
                 max_history: int = 500):
        self._max_history = max_history
        self._vision_log_path = vision_log_path
        self._audio_log_path = audio_log_path
        self._vision_monitor = None
        self._audio_monitor = None

    # --- Lazy initialization ---

    def _get_vision_monitor(self):
        if self._vision_monitor is None:
            from ai.vision.quality_monitor import VisionQualityMonitor
            self._vision_monitor = VisionQualityMonitor(
                max_history=self._max_history,
                log_path=self._vision_log_path,
            )
        return self._vision_monitor

    def _get_audio_monitor(self):
        if self._audio_monitor is None:
            from ai.audio.quality_monitor import AudioQualityMonitor
            self._audio_monitor = AudioQualityMonitor(
                max_history=self._max_history,
                log_path=self._audio_log_path,
            )
        return self._audio_monitor

    # --- Recording ---

    def record_vision(self, result: Dict[str, Any]) -> None:
        """Record a vision pipeline result."""
        try:
            self._get_vision_monitor().record(result)
        except Exception as e:
            logger.debug("Failed to record vision quality: %s", e)

    def record_audio(self, result: Dict[str, Any]) -> None:
        """Record an audio pipeline result."""
        try:
            self._get_audio_monitor().record(result)
        except Exception as e:
            logger.debug("Failed to record audio quality: %s", e)

    def record_cross_modal(self, result: Dict[str, Any]) -> None:
        """Record a cross-modal operation result."""
        # Cross-modal quality is derived from vision + audio quality
        # and the similarity score
        logger.debug("Cross-modal operation recorded: similarity=%.4f",
                     result.get("similarity", 0.0))

    # --- Dashboard ---

    def dashboard(self, window: Optional[int] = None) -> Dict[str, Any]:
        """Generate integrated quality dashboard.

        Args:
            window: Rolling window size for recent metrics

        Returns:
            dict with vision_summary, audio_summary, cross_modal_summary,
                  overall_health
        """
        vision_report = self._get_vision_monitor().report(window)
        audio_report = self._get_audio_monitor().report(window)

        # Overall health assessment
        overall = self._compute_overall_health(vision_report, audio_report)

        return {
            "vision_summary": vision_report,
            "audio_summary": audio_report,
            "overall": overall,
            "total_requests": vision_report.get("total_calls", 0) + audio_report.get("total_calls", 0),
        }

    def dashboard_simple(self) -> Dict[str, Any]:
        """Generate a simplified dashboard (suitable for quick API responses)."""
        full = self.dashboard()
        v = full["vision_summary"]
        a = full["audio_summary"]
        return {
            "vision": {
                "avg_ssim": v.get("avg_ssim", 0.0),
                "avg_psnr": v.get("avg_psnr", 0.0),
                "total_calls": v.get("total_calls", 0),
            },
            "audio": {
                "avg_snr": a.get("avg_snr", 0.0),
                "total_calls": a.get("total_calls", 0),
            },
            "overall_health": full["overall"]["health"],
            "total_requests": full["total_requests"],
        }

    # --- Health computation ---

    def _compute_overall_health(self, vision: Dict[str, Any],
                                audio: Dict[str, Any]) -> Dict[str, Any]:
        """Compute overall system health from vision + audio reports.

        Returns dict with health status, score, and degradation flags.
        """
        v_calls = vision.get("total_calls", 0)
        a_calls = audio.get("total_calls", 0)
        v_err = vision.get("error_rate", 0.0)
        a_err = audio.get("error_rate", 0.0)
        v_ssim = vision.get("avg_ssim", 0.0)
        a_snr = audio.get("avg_snr", 0.0)

        # Health score: weighted combination of quality and error rate
        quality_score = 0.0
        if v_calls > 0:
            quality_score += 0.4 * v_ssim
        if a_calls > 0:
            quality_score += 0.3 * min(a_snr / 30.0, 1.0)

        error_penalty = 0.5 * (v_err + a_err)
        health_score = max(0.0, min(1.0, quality_score + 0.5 - error_penalty))

        if health_score >= 0.8:
            health = "healthy"
        elif health_score >= 0.5:
            health = "degraded"
        else:
            health = "unhealthy"

        flags = []
        if v_err > 0.1:
            flags.append("high_vision_error_rate")
        if a_err > 0.1:
            flags.append("high_audio_error_rate")
        if v_calls > 0 and v_ssim < 0.3:
            flags.append("low_vision_quality")
        if a_calls > 0 and a_snr < 5.0:
            flags.append("low_audio_quality")

        return {
            "health": health,
            "health_score": round(health_score, 4),
            "flags": flags,
            "vision_calls": v_calls,
            "audio_calls": a_calls,
        }

    # --- Trend analysis ---

    def quality_trend(self, window: int = 10) -> Dict[str, Any]:
        """Analyze quality trend across all pipelines.

        Args:
            window: Number of recent calls to analyze

        Returns:
            dict with vision_trend, audio_trend, overall_assessment
        """
        v_trend = self._get_vision_monitor().quality_trend(window)
        a_trend = self._get_audio_monitor().quality_trend(window)

        v_assess = v_trend.get("assessment", "insufficient_data")
        a_assess = a_trend.get("assessment", "insufficient_data")

        # Overall assessment
        if "degrading" in (v_assess, a_assess):
            overall = "degrading"
        elif "improving" in (v_assess, a_assess) and "degrading" not in (v_assess, a_assess):
            overall = "improving"
        else:
            overall = "stable"

        return {
            "vision_trend": v_trend,
            "audio_trend": a_trend,
            "overall_assessment": overall,
        }

    def clear_all(self) -> None:
        """Clear all quality monitors."""
        try:
            self._get_vision_monitor().clear()
        except Exception:
            pass
        try:
            self._get_audio_monitor().clear()
        except Exception:
            pass
