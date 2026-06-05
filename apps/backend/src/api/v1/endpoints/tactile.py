#!/usr/bin/env python3
"""
Tactile API endpoints
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tactile", tags=["Tactile"])


@router.get("/status")
async def get_tactile_status() -> dict:
    return {"status": "ok", "service": "tactile"}
