#!/usr/bin/env python3
"""
Audio API endpoints
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audio", tags=["Audio"])


@router.get("/status")
async def get_audio_status() -> dict:
    return {"status": "ok", "service": "audio"}
