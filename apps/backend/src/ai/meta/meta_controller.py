"""
MetaController — Metacognitive system for confidence calibration and strategy adjustment.

Monitors inference confidence across ED3N, GARDEN, and LLM subsystems,
detects miscalibration patterns, and recommends or applies threshold adjustments.

Calibration uses EWMA (Exponentially Weighted Moving Average) for the
confidence estimate, which weights recent samples more heavily than old ones.
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_DEFAULT_ALPHA = 0.15
_WINDOW_SIZE = 100


@dataclass
class ConfidenceSample:
    timestamp: float
    source: str
    confidence: float
    correct: Optional[bool] = None


@dataclass
class CalibrationReport:
    source: str
    sample_count: int
    avg_confidence: float
    ewma_confidence: float
    calibration_error: float
    overconfidence_ratio: float
    underconfidence_ratio: float
    suggested_threshold_adjustment: float
    is_reliable: bool


class MetaController:
    def __init__(self, window_size: int = _WINDOW_SIZE, alpha: float = _DEFAULT_ALPHA):
        self._samples: Dict[str, deque] = {}
        self._window_size = window_size
        self._alpha = alpha
        self._ewma: Dict[str, float] = {}
        self._threshold_adjustments: Dict[str, float] = {}
        self._total_samples = 0
        self._calibration_history: Dict[str, deque] = {}
        self._adjustment_multipliers: Dict[str, float] = {}
        # Calibration cache (C³ 4.5): avoids redundant recomputation
        self._calibration_cache: Dict[str, Optional[CalibrationReport]] = {}
        self._calibration_cache_dirty: bool = True
        # Raw (pre-multiplier) adjustments for cache-hit recomputation
        self._raw_adjustments: Dict[str, float] = {}

    def record_confidence(
        self, source: str, confidence: float, correct: Optional[bool] = None
    ) -> None:
        if source not in self._samples:
            self._samples[source] = deque(maxlen=self._window_size)
            self._ewma[source] = confidence
        else:
            self._ewma[source] = self._alpha * confidence + (1 - self._alpha) * self._ewma[source]
        self._samples[source].append(
            ConfidenceSample(timestamp=time.time(), source=source, confidence=confidence, correct=correct)
        )
        self._total_samples += 1
        self._calibration_cache_dirty = True
        # Invalidate cached entry for this source
        if source in self._calibration_cache:
            del self._calibration_cache[source]

    def get_ewma_confidence(self, source: str, default: float = 0.5) -> float:
        return self._ewma.get(source, default)

    def _update_closed_loop(self, source: str, adjustment: float) -> None:
        """Track calibration history and update adjustment multiplier (C³ 4.0).

        This runs on every get_calibration() call — both cache hit and cache miss —
        so that repeated observations of the same calibration state accumulate
        in the history and gradually amplify (or decay) the effective multiplier.
        """
        if source not in self._calibration_history:
            self._calibration_history[source] = deque(maxlen=5)
            self._adjustment_multipliers[source] = 1.0

        if abs(adjustment) > 0.001:
            self._calibration_history[source].append("over" if adjustment < 0 else "under")
        else:
            self._calibration_history[source].append("stable")

        hist = list(self._calibration_history[source])
        if len(hist) >= 3 and all(h == "over" for h in hist[-3:]):
            self._adjustment_multipliers[source] = min(3.0, self._adjustment_multipliers[source] * 1.5)
        elif len(hist) >= 3 and all(h == "under" for h in hist[-3:]):
            self._adjustment_multipliers[source] = min(3.0, self._adjustment_multipliers[source] * 1.5)
        elif len(hist) >= 2 and all(h == "stable" for h in hist[-2:]):
            self._adjustment_multipliers[source] = max(1.0, self._adjustment_multipliers[source] * 0.8)

    def get_calibration(self, source: str) -> Optional[CalibrationReport]:
        # Cache hit: return cached metrics with recomputed adjustment
        if not self._calibration_cache_dirty and source in self._calibration_cache:
            report = self._calibration_cache[source]
            # Use the stored raw (pre-multiplier) adjustment for closed-loop
            raw_adj = self._raw_adjustments.get(source, report.suggested_threshold_adjustment)
            self._update_closed_loop(source, raw_adj)
            multiplier = self._adjustment_multipliers.get(source, 1.0)
            # Recompute adjustment with current multiplier
            adjusted = round(raw_adj * multiplier, 3)
            self._threshold_adjustments[source] = adjusted
            from dataclasses import replace as _dc_replace
            return _dc_replace(report, suggested_threshold_adjustment=adjusted)

        samples = list(self._samples.get(source, []))
        if len(samples) < 3:
            return None

        avg_conf = sum(s.confidence for s in samples) / len(samples)
        ewma_conf = self._ewma.get(source, avg_conf)

        known_correct = [s for s in samples if s.correct is not None]
        calibration_error = 0.0
        overconfidence_ratio = 0.0
        underconfidence_ratio = 0.0

        if known_correct:
            accuracy = sum(1 for s in known_correct if s.correct) / len(known_correct)
            calibration_error = abs(ewma_conf - accuracy)
            overconfident = [s for s in known_correct if s.confidence > 0.7 and not s.correct]
            underconfident = [s for s in known_correct if s.confidence < 0.3 and s.correct]
            overconfidence_ratio = len(overconfident) / len(known_correct) if known_correct else 0.0
            underconfidence_ratio = len(underconfident) / len(known_correct) if known_correct else 0.0

        raw_adjustment = 0.0
        if overconfidence_ratio > 0.2:
            raw_adjustment = -0.05
        elif underconfidence_ratio > 0.2:
            raw_adjustment = 0.05

        # Store raw adjustment for future cache-hit recomputation
        self._raw_adjustments[source] = raw_adjustment

        # C³ 4.0: Closed-loop — track calibration history and adjust multiplier
        self._update_closed_loop(source, raw_adjustment)

        multiplier = self._adjustment_multipliers.get(source, 1.0)
        adjustment = round(raw_adjustment * multiplier, 3)

        is_reliable = calibration_error < 0.2 and len(known_correct) > 10

        # Cache the adjustment for auto-apply
        self._threshold_adjustments[source] = adjustment

        report = CalibrationReport(
            source=source,
            sample_count=len(samples),
            avg_confidence=round(avg_conf, 3),
            ewma_confidence=round(ewma_conf, 3),
            calibration_error=round(calibration_error, 3),
            overconfidence_ratio=round(overconfidence_ratio, 3),
            underconfidence_ratio=round(underconfidence_ratio, 3),
            suggested_threshold_adjustment=adjustment,
            is_reliable=is_reliable,
        )
        # Cache the computed report (C³ 4.5)
        self._calibration_cache[source] = report
        self._calibration_cache_dirty = False
        return report

    def get_weighted_adjustment(self) -> float:
        """Compute a single weighted aggregate adjustment across all sources.

        Unlike simple averaging (which can cancel out opposing adjustments),
        this uses reliability-weighted aggregation: reliable sources with more
        samples contribute more to the aggregate. This prevents one source's
        opposite adjustment from cancelling another's when they have different
        reliability levels.

        Returns:
            A single float adjustment value, biased toward the most reliable
            and well-sampled sources. Returns 0.0 if no calibrations available.
        """
        total_weight = 0.0
        weighted_sum = 0.0

        for source in self._samples:
            report = self.get_calibration(source)
            if report is None:
                continue
            # Weight = sample_count * (2 if reliable else 1)
            weight = report.sample_count * (2.0 if report.is_reliable else 1.0)
            weighted_sum += report.suggested_threshold_adjustment * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return round(weighted_sum / total_weight, 3)

    def auto_apply_thresholds(self) -> Dict[str, float]:
        """Auto-apply cached threshold adjustments to all tracked sources.

        Calls get_calibration() for each source to refresh adjustments,
        then returns a dict of {source: adjustment} showing what was applied.
        This enables downstream consumers (e.g. NeuroAutoSelector) to
        read and apply adjustments to actual decision parameters.
        Note: get_calibration() already populates _threshold_adjustments;
        this method just returns the non-zero adjustments for the caller.
        """
        applied: Dict[str, float] = {}
        for source in list(self._samples.keys()):
            report = self.get_calibration(source)
            if report and abs(report.suggested_threshold_adjustment) > 0.001:
                applied[source] = report.suggested_threshold_adjustment
                logger.debug(
                    f"[MetaController] Auto-applied threshold adjustment for {source}: "
                    f"{report.suggested_threshold_adjustment:+.3f} "
                    f"(overconfidence={report.overconfidence_ratio:.2f}, "
                    f"underconfidence={report.underconfidence_ratio:.2f})"
                )
        return applied

    def get_threshold_adjustment(self, source: str, default: float = 0.0) -> float:
        # Fast path: use cached adjustment if available and not dirty
        if (not self._calibration_cache_dirty
                and source in self._threshold_adjustments):
            adj = self._threshold_adjustments[source]
            if abs(adj) > 0.001:
                return adj
        # Fall back to full computation
        report = self.get_calibration(source)
        if report is None:
            return default
        return report.suggested_threshold_adjustment

    def get_summary(self) -> Dict[str, Dict]:
        """Return calibration summary for all tracked sources.

        Uses cached reports when available to avoid redundant recomputation.
        """
        summary = {}
        for source in self._samples:
            report = self.get_calibration(source)
            if report:
                summary[source] = {
                    "samples": report.sample_count,
                    "avg_confidence": report.avg_confidence,
                    "ewma_confidence": report.ewma_confidence,
                    "calibration_error": report.calibration_error,
                    "overconfidence_ratio": report.overconfidence_ratio,
                    "underconfidence_ratio": report.underconfidence_ratio,
                    "threshold_adjustment": report.suggested_threshold_adjustment,
                    "reliable": report.is_reliable,
                }
        return summary

    def get_stats(self) -> Dict:
        return {
            "total_samples": self._total_samples,
            "tracked_sources": list(self._samples.keys()),
            "window_size": self._window_size,
            "ewma_alpha": self._alpha,
        }
