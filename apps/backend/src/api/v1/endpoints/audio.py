#!/usr/bin/env python3
"""
Audio API endpoints
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException

from services.audio_service import AudioService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audio", tags=["Audio"])

_audio_service: Optional[AudioService] = None


def get_audio_service() -> AudioService:
    """Return the process-wide AudioService, creating it on first use.

    Tests may override the module-level ``_audio_service`` to inject a
    pre-configured instance.
    """
    global _audio_service
    if _audio_service is None:
        _audio_service = AudioService()
    return _audio_service


@router.get("/status")
async def get_audio_status() -> dict:
    return {"status": "ok", "service": "audio"}


@router.post("/scan")
async def audio_scan(
    audio_data: bytes = Body(...),
    duration: float = 1.0,
    svc: AudioService = Depends(get_audio_service),
) -> Dict[str, Any]:
    """模擬雞尾酒會效應：聆聽、識別並聚焦"""
    try:
        return await svc.scan_and_identify(audio_data, duration)
    except Exception as e:  # broad exception acceptable: audio scan endpoint should be resilient
        logger.error(f"Audio scan error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Audio scan failed")


@router.post("/register_user")
async def audio_register_user(
    audio_data: bytes = Body(...),
    svc: AudioService = Depends(get_audio_service),
) -> Dict[str, Any]:
    """註冊用戶聲紋"""
    try:
        return await svc.register_user_voice(audio_data)
    except Exception as e:  # broad exception acceptable: registration should not crash on errors
        logger.error(f"Audio registration error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Audio registration failed")


@router.post("/control")
async def audio_control(params: Dict[str, Any] = Body(...)) -> dict:
    """控制音頻模組開關"""
    enabled = params.get("enabled", True)
    return {"status": "success", "module": "audio", "enabled": enabled, "mode": "post_method"}


@router.get("/control")
async def audio_control_get(enabled: bool = True) -> dict:
    """控制音頻模組開關（GET 方法支持）"""
    return {"status": "success", "module": "audio", "enabled": enabled, "mode": "get_method"}
