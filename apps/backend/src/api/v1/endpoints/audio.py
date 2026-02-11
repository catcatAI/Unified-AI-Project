#!/usr/bin/env python3
"""
Audio API 端點
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Optional
import logging
from services.audio_service import AudioService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audio", tags=["Audio"])

# 共享的 AudioService 實例
_audio_service = AudioService()

@router.post("/scan")
async def audio_scan(audio_data: bytes = Body(...), duration: float = 1.0):
    """模擬雞尾酒會效應：聆聽、識別並聚焦"""
    try:
        result = await _audio_service.scan_and_identify(audio_data, duration)
        return result
    except Exception as e:
        logger.error(f"Audio scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/register_user")
async def audio_register_user(audio_data: bytes = Body(...)):
    """註冊用戶聲紋"""
    try:
        result = await _audio_service.register_user_voice(audio_data)
        return result
    except Exception as e:
        logger.error(f"Audio registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/control")
async def audio_control(params: Dict[str, Any] = Body(...)):
    """控制音頻模組開關"""
    enabled = params.get("enabled", True)
    try:
        from ....core.sync.realtime_sync import sync_manager, SyncEvent
        await sync_manager.broadcast_event(SyncEvent(
            event_type="module_control",
            data={"module": "audio", "enabled": enabled},
            source="api_endpoint"
        ))
        return {"status": "success", "module": "audio", "enabled": enabled}
    except Exception as e:
        logger.error(f"Audio control error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
