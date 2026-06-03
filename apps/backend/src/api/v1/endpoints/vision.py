#!/usr/bin/env python3
"""
Vision API 端點
"""

from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, Any, List, Optional
import logging

from ._deps import get_vision_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vision", tags=["Vision"])


@router.post("/sampling")
async def get_vision_sampling(params: Dict[str, Any] = Body(...), svc=Depends(get_vision_service)) -> str:
    """獲取視覺採樣分析"""
    center = params.get("center", [0.5, 0.5])
    scale = params.get("scale", 1.0)
    deformation = params.get("deformation", 0.0)
    distribution = params.get("distribution", "GAUSSIAN")

    try:
        result = await svc.get_sampling_analysis(
            center=(center[0], center[1]),
            scale=scale,
            deformation=deformation,
            distribution=distribution,
        )
        return result
    except Exception as e:  # broad exception acceptable: vision sampling endpoint should be resilient
        logger.error(f"Vision sampling error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/perceive")
async def vision_perceive(image_data: bytes = Body(...), svc=Depends(get_vision_service)) -> str:
    """模擬發現-聚焦-記憶循環"""
    try:
        result = await svc.perceive_and_focus(image_data)
        return result
    except Exception as e:  # broad exception acceptable: perceive operation should be resilient to errors
        logger.error(f"Vision perceive error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/control")
async def vision_control(params: Dict[str, Any] = Body(...)) -> dict:
    """控制視覺模組開關"""
    enabled = params.get("enabled", True)
    try:
        # 簡化實現，不依賴 sync_manager
        return {"status": "success", "module": "vision", "enabled": enabled, "mode": "post_method"}
    except Exception as e:  # broad exception acceptable: vision control endpoint should be resilient
        logger.error(f"Vision control error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/control")
async def vision_control_get(enabled: bool = True) -> dict:
    """控制視覺模組開關（GET 方法支持）"""
    try:
        # 返回簡單的狀態，不依賴 sync_manager
        return {"status": "success", "module": "vision", "enabled": enabled, "mode": "get_method"}
    except Exception as e:  # broad exception acceptable: graceful degradation on failure
        logger.error(f"Vision control error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
