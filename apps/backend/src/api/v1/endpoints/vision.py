#!/usr/bin/env python3
"""
Vision API 端點
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Optional
import logging
from ....services.vision_service import VisionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vision", tags=["Vision"])

# 共享的 VisionService 實例
_vision_service = VisionService()

@router.post("/sampling")
async def get_vision_sampling(params: Dict[str, Any] = Body(...)):
    """獲取視覺採樣分析"""
    center = params.get("center", [0.5, 0.5])
    scale = params.get("scale", 1.0)
    deformation = params.get("deformation", 0.0)
    distribution = params.get("distribution", "GAUSSIAN")
    
    try:
        result = await _vision_service.get_sampling_analysis(
            center=(center[0], center[1]),
            scale=scale,
            deformation=deformation,
            distribution=distribution
        )
        return result
    except Exception as e:
        logger.error(f"Vision sampling error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/perceive")
async def vision_perceive(image_data: bytes = Body(...)):
    """模擬發現-聚焦-記憶循環"""
    try:
        result = await _vision_service.perceive_and_focus(image_data)
        return result
    except Exception as e:
        logger.error(f"Vision perceive error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/control")
async def vision_control(params: Dict[str, Any] = Body(...)):
    """控制視覺模組開關"""
    enabled = params.get("enabled", True)
    try:
        from ....core.sync.realtime_sync import sync_manager, SyncEvent
        await sync_manager.broadcast_event(SyncEvent(
            event_type="module_control",
            data={"module": "vision", "enabled": enabled},
            source="api_endpoint"
        ))
        return {"status": "success", "module": "vision", "enabled": enabled}
    except Exception as e:
        logger.error(f"Vision control error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
