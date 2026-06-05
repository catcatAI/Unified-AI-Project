#!/usr/bin/env python3
"""
Desktop Pet API endpoints
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pet", tags=["Pet"])


@router.get("/status")
async def get_pet_status() -> dict:
    return {"status": "ok", "service": "pet"}
