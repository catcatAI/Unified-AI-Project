"""
MetaController confidence monitoring API.

Exposes MetaController calibration state:
- Summary of all tracked sources
- Per-source calibration reports
- Global stats

ANGELA-MATRIX: L6[执行层] αβγδ [B] L4
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["meta"])

_META_CONTROLLER = None


def _get_controller():
    global _META_CONTROLLER
    if _META_CONTROLLER is None:
        try:
            from ai.meta.meta_controller import MetaController
            _META_CONTROLLER = MetaController()
        except Exception as e:
            logger.warning("MetaController not available: %s", e)
    return _META_CONTROLLER


def set_meta_controller(controller) -> None:
    global _META_CONTROLLER
    _META_CONTROLLER = controller


@router.get("/meta/confidence/summary")
async def get_confidence_summary():
    """Return calibration summary for all tracked confidence sources."""
    mc = _get_controller()
    if mc is None:
        raise HTTPException(status_code=503, detail="MetaController not available")
    return {
        "success": True,
        "summary": mc.get_summary(),
        "stats": mc.get_stats(),
    }


@router.get("/meta/confidence/calibration/{source}")
async def get_source_calibration(source: str):
    """Return calibration report for a specific confidence source."""
    mc = _get_controller()
    if mc is None:
        raise HTTPException(status_code=503, detail="MetaController not available")
    report = mc.get_calibration(source)
    if report is None:
        return {
            "success": True,
            "source": source,
            "calibration": None,
            "message": "Not enough samples yet (need >= 3)",
        }
    return {
        "success": True,
        "source": source,
        "calibration": {
            "sample_count": report.sample_count,
            "avg_confidence": report.avg_confidence,
            "ewma_confidence": report.ewma_confidence,
            "calibration_error": report.calibration_error,
            "overconfidence_ratio": report.overconfidence_ratio,
            "underconfidence_ratio": report.underconfidence_ratio,
            "suggested_threshold_adjustment": report.suggested_threshold_adjustment,
            "is_reliable": report.is_reliable,
        },
    }
