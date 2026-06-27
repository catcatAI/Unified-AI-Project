"""
Economy API endpoints
"""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/economy", tags=["Economy"])


@router.get("/status")
async def get_economy_status() -> dict:
    return {"status": "ok", "service": "economy"}
