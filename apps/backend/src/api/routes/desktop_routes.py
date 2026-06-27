"""
ANGELA-MATRIX: [L4-L5] [βγ] [A] [L2]
Desktop interaction, action, tactile & brain API routes.
Extracted from main_api_server.py (A3 god module split).
"""

import logging
from typing import Any, Dict

from api.lifespan import (
    get_action_executor,
    get_desktop_interaction,
    get_digital_life,
    get_tactile_service,
)
from core.engine.action_executor import ActionExecutor
from core.engine.desktop_interaction import DesktopInteraction
from core.life.digital_life_integrator import DigitalLifeIntegrator
from fastapi import APIRouter, Body, Depends, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/desktop/state")
async def desktop_state(
    interaction: DesktopInteraction = Depends(get_desktop_interaction),
) -> dict:
    """Execute the desktop state operation."""
    if interaction is None:
        raise HTTPException(503, "DesktopInteraction not available")
    state = interaction.get_desktop_state()
    return {"success": True, "state": {
        "total_files": getattr(state, "total_files", 0),
        "total_size": getattr(state, "total_size", 0),
        "categories": getattr(state, "categories", {}),
        "clutter_level": getattr(state, "clutter_level", 0.0),
    }}


@router.post("/desktop/organize")
async def desktop_organize(
    interaction: DesktopInteraction = Depends(get_desktop_interaction),
) -> dict:
    """Execute the desktop organize operation."""
    if interaction is None:
        raise HTTPException(503, "DesktopInteraction not available")
    ops = await interaction.organize_desktop()
    return {"success": True, "operations": [{
        "source": str(op.source) if hasattr(op, "source") else "",
        "destination": str(op.destination) if hasattr(op, "destination") else "",
        "category": op.category if hasattr(op, "category") else "",
    } for op in ops]}


@router.post("/desktop/cleanup")
async def desktop_cleanup(
    days_old: int = 30,
    interaction: DesktopInteraction = Depends(get_desktop_interaction),
) -> dict:
    """Execute the desktop cleanup operation."""
    if interaction is None:
        raise HTTPException(503, "DesktopInteraction not available")
    ops = await interaction.cleanup_desktop(days_old=days_old)
    return {"success": True, "operations": [{
        "source": str(op.source) if hasattr(op, "source") else "",
        "category": op.category if hasattr(op, "category") else "",
    } for op in ops]}


@router.get("/actions/status")
async def actions_status(
    executor: ActionExecutor = Depends(get_action_executor),
) -> dict:
    """Execute the actions status operation."""
    if executor is None:
        raise HTTPException(503, "ActionExecutor not available")
    stats = executor.get_execution_stats()
    return {"success": True, "stats": stats}


@router.post("/actions/execute")
async def actions_execute(
    action_data: Dict[str, Any] = Body(...),
    executor: ActionExecutor = Depends(get_action_executor),
) -> dict:
    """Execute the actions execute operation."""
    if executor is None:
        raise HTTPException(503, "ActionExecutor not available")
    action_type = action_data.get("type", "general")
    parameters = action_data.get("parameters", {})
    priority = action_data.get("priority", "normal")
    result = await executor.handle_autonomous_action(action_type, parameters, priority)
    return {"success": True, "result": result}


@router.post("/tactile/touch")
async def tactile_touch(touch_data: Dict[str, Any] = Body(...)) -> dict:
    """Execute the tactile touch operation."""
    object_id = touch_data.get("object_id", "default")
    contact_point = touch_data.get("contact_point", {"body_part": "generic", "pressure": 0.5})
    origin = touch_data.get("origin", "System")
    service = get_tactile_service()
    if not service:
        return {"success": False, "error": "TactileService not available"}
    result = await service.simulate_touch(object_id, contact_point, origin)
    return {"success": True, "feedback": result}


@router.post("/brain/metrics")
async def brain_metrics(
    digital_life: DigitalLifeIntegrator = Depends(get_digital_life),
) -> dict:
    """Execute the brain metrics operation."""
    summary = digital_life.get_formula_metrics()
    return {"success": True, "metrics": summary.get("formula_status", {}) if summary else {}}


@router.post("/brain/dividend")
async def brain_dividend() -> dict:
    """Execute the brain dividend operation."""
    digital_life = get_digital_life()
    summary = digital_life.get_formula_metrics()
    if summary and "formula_status" in summary:
        return summary["formula_status"].get("cdm", {})
    return {"message": "Dividend data not available"}
