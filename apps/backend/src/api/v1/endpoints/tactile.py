#!/usr/bin/env python3
"""
Tactile API endpoints

NOTE: TactileService was intentionally removed in Phase 11 (was a stub with
no hardware support). All callers handle None gracefully. See desktop_routes.py
for the only consumption point, which returns an error message when unavailable.
"""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tactile", tags=["Tactile"])


@router.get("/status")
async def get_tactile_status() -> dict:
    """Tactile system status (TactileService was removed in Phase 11)."""
    return {"status": "unavailable", "service": "tactile", "note": "TactileService removed in Phase 11"}
