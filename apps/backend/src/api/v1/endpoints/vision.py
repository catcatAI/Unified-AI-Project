#!/usr/bin/env python3
"""
Vision API endpoints
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException

from services.vision_service import VisionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vision", tags=["Vision"])

# Shared VisionService instance used by the vision endpoints.
_vision_service = VisionService()


@router.get("/status")
async def get_vision_status() -> dict:
    return {"status": "ok", "service": "vision"}


@router.post("/sampling")
async def get_vision_sampling(params: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Run a visual sampling analysis and return attention statistics."""
    center = params.get("center", [0.5, 0.5])
    scale = params.get("scale", 1.0)
    deformation = params.get("deformation", 0.0)
    distribution = params.get("distribution", "GAUSSIAN")

    try:
        result = await _vision_service.get_sampling_analysis(
            center=(center[0], center[1]),
            scale=scale,
            deformation=deformation,
            distribution=distribution,
        )
        # Expose a stable API contract for the sampling statistics while keeping
        # the underlying sampler fields for callers that need them.
        raw_stats = dict(result.get("sampling_stats") or {})
        result["sampling_stats"] = {
            "status": "success",
            "sample_count": int(raw_stats.get("particle_count", 0)),
            "focus_distribution": distribution,
            **raw_stats,
        }
        return result
    except Exception as e:
        logger.error(f"Vision sampling error: {e}")
        raise HTTPException(status_code=500, detail="Vision sampling failed")


@router.post("/perceive")
async def vision_perceive(image_data: bytes = Body(...)) -> Dict[str, Any]:
    """Simulate the discover -> focus -> remember perception loop."""
    try:
        return await _vision_service.perceive_and_focus(image_data)
    except Exception as e:
        logger.error(f"Vision perceive error: {e}")
        raise HTTPException(status_code=500, detail="Vision perceive failed")


@router.post("/control")
async def vision_control(params: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Toggle the vision module (POST method)."""
    enabled = params.get("enabled", True)
    return {
        "status": "success",
        "module": "vision",
        "enabled": enabled,
        "mode": "post_method",
    }


@router.get("/control")
async def vision_control_get(enabled: bool = True) -> Dict[str, Any]:
    """Toggle the vision module (GET method)."""
    return {
        "status": "success",
        "module": "vision",
        "enabled": enabled,
        "mode": "get_method",
    }
