#!/usr/bin/env python3
"""
Tactile API 端點
"""

from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, Any, List, Optional
import logging

from ._deps import get_tactile_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tactile", tags=["Tactile"])


@router.post("/model")
async def tactile_model(visual_data: Dict[str, Any] = Body(...), svc=Depends(get_tactile_service)) -> str:
    """基於視覺數據建模觸覺反饋"""
    try:
        result = await svc.model_tactile_feedback(visual_data)
        return result
    except Exception as e:  # broad exception acceptable: tactile modeling should be resilient to errors
        logger.error(f"Tactile modeling error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model")
async def tactile_model_get() -> dict:
    """獲取觸覺模型狀態（GET 方法支持）"""
    try:
        return {"status": "active", "model": "tactile_feedback_v1", "enabled": True}
    except Exception as e:  # broad exception acceptable: model status endpoint should not crash
        logger.error(f"Tactile model status error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger")
async def trigger_tactile(trigger_data: Dict[str, Any] = Body(...), svc=Depends(get_tactile_service)) -> str:
    """觸發物理觸覺設備"""
    try:
        device_id = trigger_data.get("device_id")
        intensity = trigger_data.get("intensity", 0.5)
        pattern = trigger_data.get("pattern", "default")

        result = await svc.trigger_physical_feedback(device_id, intensity, pattern)
        return result
    except Exception as e:  # broad exception acceptable: tactile trigger should be resilient to errors
        logger.error(f"Tactile trigger error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/control")
async def tactile_control(params: Dict[str, Any] = Body(...)) -> dict:
    """控制觸覺模組開關"""
    enabled = params.get("enabled", True)
    try:
        # 簡化實現，不依賴 sync_manager
        return {"status": "success", "module": "tactile", "enabled": enabled, "mode": "post_method"}
    except Exception as e:  # broad exception acceptable: graceful degradation on failure
        logger.error(f"Tactile control error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
