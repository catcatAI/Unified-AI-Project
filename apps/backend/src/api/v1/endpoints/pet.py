#!/usr/bin/env python3
"""
Desktop Pet API endpoints

NOTE: PetManager was removed in Phase 12. This module provides only a
status-check endpoint. If a PetManager is re-implemented in the future,
wire it via lifespan.py and add endpoints here.
"""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pet", tags=["Pet"])


@router.get("/status")
async def get_pet_status() -> dict:
    """Pet system status (PetManager was removed — placeholder only)."""
    return {"status": "unavailable", "service": "pet", "note": "PetManager removed"}
