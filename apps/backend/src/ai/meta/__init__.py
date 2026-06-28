# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================
"""
Meta module — adaptive control and confidence calibration.

MetaController: confidence tracking with EWMA calibration + decay.
CalibrationReport: periodic calibration summaries for router feedback.
ConfidenceSample: per-decision confidence/outcome pair.
"""

from .meta_controller import CalibrationReport, ConfidenceSample, MetaController

__all__ = [
    "MetaController",
    "CalibrationReport",
    "ConfidenceSample",
]
