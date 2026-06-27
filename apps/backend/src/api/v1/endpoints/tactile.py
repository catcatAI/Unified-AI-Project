#!/usr/bin/env python3
"""
Tactile API endpoints
"""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tactile", tags=["Tactile"])


@router.get("/status")
async def get_tactile_status() -> dict:
    return {"status": "ok", "service": "tactile"}
