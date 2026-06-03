"""
ANGELA-MATRIX: [L4-L5] [βγ] [A] [L2]
Desktop interaction, action, tactile & brain API routes.
Extracted from main_api_server.py (A3 god module split).
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, Body

from api.lifespan import (
    get_desktop_interaction,
    get_action_executor,
    get_tactile_service,
    get_digital_life,
)
from core.engine.desktop_interaction import DesktopInteraction
from core.engine.action_executor import ActionExecutor
from core.life.digital_life_integrator import DigitalLifeIntegrator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/desktop/state")
async def desktop_state(
    interaction: DesktopInteraction = Depends(get_desktop_interaction),
):
    """Execute the desktop state operation."""
    state = interaction.get_desktop_state()
    return {"success": True, "state": {
        "total_files": getattr(state, "total_files", 0),
        "total_size": getattr(state, "total_size", 0),
        "categories": getattr(state, "categories", {}),
        "clutter_level": getattr(state, "clutter_level", 0.0),
    }}


@router.post("/desktop/organize")
async def desktop_organize() -> dict:
    """Execute the desktop organize operation."""
    ops = await get_desktop_interaction().organize_desktop()
    return {"success": True, "operations": [{
        "source": str(op.source) if hasattr(op, "source") else "",
        "destination": str(op.destination) if hasattr(op, "destination") else "",
        "category": op.category if hasattr(op, "category") else "",
    } for op in ops]}


@router.post("/desktop/cleanup")
async def desktop_cleanup(days_old: int = 30) -> dict:
    """Execute the desktop cleanup operation."""
    ops = await get_desktop_interaction().cleanup_desktop(days_old=days_old)
    return {"success": True, "operations": [{
        "source": str(op.source) if hasattr(op, "source") else "",
        "category": op.category if hasattr(op, "category") else "",
    } for op in ops]}


@router.get("/actions/status")
async def actions_status(
    executor: ActionExecutor = Depends(get_action_executor),
):
    """Execute the actions status operation."""
    stats = executor.get_execution_stats()
    return {"success": True, "stats": stats}


@router.post("/actions/execute")
async def actions_execute(action_data: Dict[str, Any] = Body(...)) -> dict:
    """Execute the actions execute operation."""
    action_type = action_data.get("type", "general")
    parameters = action_data.get("parameters", {})
    priority = action_data.get("priority", "normal")
    result = await get_action_executor().handle_autonomous_action(action_type, parameters, priority)
    return {"success": True, "result": result}


@router.post("/tactile/touch")
async def tactile_touch(touch_data: Dict[str, Any] = Body(...)) -> dict:
    """Execute the tactile touch operation."""
    object_id = touch_data.get("object_id", "default")
    contact_point = touch_data.get("contact_point", {"body_part": "generic", "pressure": 0.5})
    origin = touch_data.get("origin", "System")
    result = await get_tactile_service().simulate_touch(object_id, contact_point, origin)
    return {"success": True, "feedback": result}


@router.post("/brain/metrics")
async def brain_metrics(
    digital_life: DigitalLifeIntegrator = Depends(get_digital_life),
):
    """Execute the brain metrics operation."""
    summary = digital_life.get_formula_metrics()
    return {"success": True, "metrics": summary.get("formula_status", {}) if summary else {}}


@router.post("/brain/dividend")
async def brain_dividend():
    """Execute the brain dividend operation."""
    digital_life = get_digital_life()
    summary = digital_life.get_formula_metrics()
    if summary and "formula_status" in summary:
        return summary["formula_status"].get("cdm", {})
    return {"message": "Dividend data not available"}
