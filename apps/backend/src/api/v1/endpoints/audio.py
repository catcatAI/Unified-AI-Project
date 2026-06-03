#!/usr/bin/env python3
"""
Audio API 端點
"""

from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, Any, List, Optional
import logging

from ._deps import get_audio_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audio", tags=["Audio"])


@router.post("/scan")
async def audio_scan(audio_data: bytes = Body(...), duration: float = 1.0, svc=Depends(get_audio_service)) -> str:
    """模擬雞尾酒會效應：聆聽、識別並聚焦"""
    try:
        result = await svc.scan_and_identify(audio_data, duration)
        return result
    except Exception as e:  # broad exception acceptable: audio scan endpoint should be resilient to errors
        logger.error(f"Audio scan error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register_user")
async def audio_register_user(audio_data: bytes = Body(...), svc=Depends(get_audio_service)) -> str:
    """註冊用戶聲紋"""
    try:
        result = await svc.register_user_voice(audio_data)
        return result
    except Exception as e:  # broad exception acceptable: user registration should not crash on errors
        logger.error(f"Audio registration error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/control")
async def audio_control(params: Dict[str, Any] = Body(...)) -> dict:
    """控制音頻模組開關"""
    enabled = params.get("enabled", True)
    try:
        return {"status": "success", "module": "audio", "enabled": enabled, "mode": "post_method"}
    except Exception as e:  # broad exception acceptable: audio control endpoint should be resilient
        logger.error(f"Audio control error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/control")
async def audio_control_get(enabled: bool = True) -> dict:
    """控制音頻模組開關（GET 方法支持）"""
    try:
        return {"status": "success", "module": "audio", "enabled": enabled, "mode": "get_method"}
    except Exception as e:  # broad exception acceptable: graceful degradation on failure
        logger.error(f"Audio control error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
