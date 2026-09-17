"""
ANGELA-MATRIX: [L4] [β] [B] [L0]
Card Import Pipeline — quality subpackage.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.card.quality.gravity_calibration import GravityCalibrator
    from core.card.quality.import_quality_checker import ImportQualityChecker, QualityScore
else:
    try:
        from core.card.quality.gravity_calibration import GravityCalibrator
    except ImportError:
        GravityCalibrator = None
    try:
        from core.card.quality.import_quality_checker import ImportQualityChecker, QualityScore
    except ImportError:
        ImportQualityChecker = None
        QualityScore = None

__all__ = [
    "GravityCalibrator",
    "ImportQualityChecker",
    "QualityScore",
]
