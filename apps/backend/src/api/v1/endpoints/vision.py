#!/usr/bin/env python3
"""
Vision API endpoints
"""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vision", tags=["Vision"])


@router.get("/status")
async def get_vision_status() -> dict:
    return {"status": "ok", "service": "vision"}
