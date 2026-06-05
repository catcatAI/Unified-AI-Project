"""
Plugin API endpoints — C3: query hooks, list plugins, execute hooks.
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plugins", tags=["Plugins"])


@router.get("/status")
async def get_plugins_status() -> dict:
    return {"status": "ok", "service": "plugins"}
