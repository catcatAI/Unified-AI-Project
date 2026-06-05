"""
Economy API endpoints
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/economy", tags=["Economy"])


@router.get("/status")
async def get_economy_status() -> dict:
    return {"status": "ok", "service": "economy"}
