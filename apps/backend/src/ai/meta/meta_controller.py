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

    def get_ewma_confidence(self, source: str, default: float = 0.5) -> float:
        return self._ewma.get(source, default)

    def get_calibration(self, source: str) -> Optional[CalibrationReport]:
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

        adjustment = 0.0
        if overconfidence_ratio > 0.2:
            adjustment = -0.05
        elif underconfidence_ratio > 0.2:
            adjustment = 0.05

        is_reliable = calibration_error < 0.2 and len(known_correct) > 10

        return CalibrationReport(
            source=source,
            sample_count=len(samples),
            avg_confidence=round(avg_conf, 3),
            ewma_confidence=round(ewma_conf, 3),
            calibration_error=round(calibration_error, 3),
            overconfidence_ratio=round(overconfidence_ratio, 3),
            underconfidence_ratio=round(underconfidence_ratio, 3),
            suggested_threshold_adjustment=round(adjustment, 3),
            is_reliable=is_reliable,
        )

    def get_threshold_adjustment(self, source: str, default: float = 0.0) -> float:
        report = self.get_calibration(source)
        if report is None:
            return default
        return report.suggested_threshold_adjustment

    def get_summary(self) -> Dict[str, Dict]:
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
