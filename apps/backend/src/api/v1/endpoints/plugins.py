"""
Plugin API endpoints — C3: query hooks, list plugins, execute hooks.
"""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plugins", tags=["Plugins"])


@router.get("/status")
async def get_plugins_status() -> dict:
    return {"status": "ok", "service": "plugins"}
