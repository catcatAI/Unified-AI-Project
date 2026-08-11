# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================
"""
Meta module — adaptive control, confidence calibration, and project review.

MetaController: confidence tracking with EWMA calibration + decay.
CalibrationReport: periodic calibration summaries for router feedback.
ConfidenceSample: per-decision confidence/outcome pair.
AngelaReviewEngine: multi-dimensional project review system.
"""

from .meta_controller import CalibrationReport, ConfidenceSample, MetaController
from .angela_review_engine import AngelaReviewEngine, get_review_engine, run_full_review

__all__ = [
    "MetaController",
    "CalibrationReport",
    "ConfidenceSample",
    "AngelaReviewEngine",
    "get_review_engine",
    "run_full_review",
]
