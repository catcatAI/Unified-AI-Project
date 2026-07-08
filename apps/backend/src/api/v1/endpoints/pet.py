#!/usr/bin/env python3
"""
Desktop Pet API endpoints
"""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pet", tags=["Pet"])

_pet_manager = None


def get_pet_manager():
    """Return the module-level PetManager instance (set by wiring)."""
    return _pet_manager


def set_pet_manager(mgr):
    """Set the module-level PetManager instance."""
    global _pet_manager
    _pet_manager = mgr


def set_biological_integrator(bi):
    """Wire the biological integrator into the pet manager."""
    if _pet_manager is not None:
        _pet_manager.biological_integrator = bi


@router.get("/status")
async def get_pet_status() -> dict:
    return {"status": "ok", "service": "pet"}
