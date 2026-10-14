#!/usr/bin/env python3
"""
Audio API endpoints
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Response
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


# ANGELA-MATRIX: [L6] [αβγδ] [B] [L4]
@router.post("/tts")
async def audio_tts(
    params: Dict[str, Any] = Body(...),
    svc: AudioService = Depends(get_audio_service),
) -> Response:
    """文字轉語音：回傳合成音訊串流（edge-tts mp3 bytes）

    契約 2026-10-14：crystal-cards `textToSpeech()` 呼叫
    ``POST /api/v1/audio/tts {text, voice}`` 並以 ``response.blob()`` 播放；
    此路由此前不存在（僅有服務層 ``text_to_speech()``），前端恆 404。
    合成失敗/edge-tts 未安裝回 503 — 前端 ``response.ok`` 判定後靜默退回無聲，
    不回假音訊。
    """
    text = str(params.get("text", "")).strip()
    if not text:
        raise HTTPException(status_code=422, detail="text is required")
    voice = params.get("voice")
    audio = await svc.text_to_speech(text, voice=str(voice) if voice else None)
    if not audio:
        raise HTTPException(
            status_code=503, detail="TTS unavailable (edge-tts missing or synthesis failed)"
        )
    return Response(content=audio, media_type="audio/mpeg")


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
    enabled = bool(params.get("enabled", True))
    actual = get_audio_service().set_enabled(enabled)
    return {"status": "success", "module": "audio", "enabled": actual, "requested": enabled}


@router.get("/control")
async def audio_control_get(enabled: Optional[bool] = None) -> dict:
    """讀取音頻模組開關狀態（GET 方法）

    裸 GET 不可寫入：舊簽名預設 ``enabled=True`` 並無條件呼叫 ``set_enabled``，
    導致任何狀態探測都會靜默把模組重新打開，
    ``POST /mobile/module-control {"enabled": false}`` 因此看起來沒有生效。
    明確帶上 ``?enabled=...`` 仍會寫入，保留原有的 GET 控制用法。
    """
    svc = get_audio_service()
    actual = bool(svc.enabled) if enabled is None else svc.set_enabled(enabled)
    return {
        "status": "success",
        "module": "audio",
        "enabled": actual,
        "requested": actual if enabled is None else bool(enabled),
    }
