#!/usr/bin/env python3
"""
Vision API endpoints
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vision", tags=["Vision"])


@router.get("/status")
async def get_vision_status() -> dict:
    return {"status": "ok", "service": "vision"}
