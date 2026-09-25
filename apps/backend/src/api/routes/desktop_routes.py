"""
ANGELA-MATRIX: [L4-L5] [βγ] [A] [L2]
Desktop interaction, action & brain API routes.
Extracted from main_api_server.py (A3 god module split).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict

from api.lifespan import (
    get_action_executor,
    get_agent_workspace,
    get_desktop_interaction,
    get_digital_life,
    get_tactile_service,
)
from core.engine.action_executor import ActionExecutor
from core.engine.desktop_interaction import DesktopInteraction
from fastapi import APIRouter, Body, Depends, HTTPException

if TYPE_CHECKING:
    from core.life.digital_life_integrator import DigitalLifeIntegrator
    from services.agent_workspace import UnifiedWorkspace

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
    return {
        "success": True,
        "state": {
            "total_files": getattr(state, "total_files", 0),
            "total_size": getattr(state, "total_size", 0),
            "categories": getattr(state, "categories", {}),
            "clutter_level": getattr(state, "clutter_level", 0.0),
        },
    }


@router.post("/desktop/organize")
async def desktop_organize(
    body: Dict[str, Any] = Body(default={}),
    interaction: DesktopInteraction = Depends(get_desktop_interaction),
    workspace: "UnifiedWorkspace" = Depends(get_agent_workspace),
) -> dict:
    """桌面整理——統一經代理工作區會話閉環執行（非旁路）。

    危險操作：第一次呼叫回 pending_confirmation，需 confirm=True 重送。
    每次呼叫（成敗）皆寫入學習日誌（source="api"）。
    """
    if interaction is None:
        raise HTTPException(503, "DesktopInteraction not available")
    if workspace is None:
        raise HTTPException(503, "AgentWorkspace not available")
    confirm = bool(body.get("confirm", False))
    if workspace.workspace.sessions.get_session("desktop") is None:
        opened = await workspace.open_app("desktop", purpose="API 桌面整理", source="api")
        if not opened.get("ok"):
            return {"success": False, **opened}
    result = await workspace.act("desktop", "organize", confirm=confirm, source="api")
    if result.get("status") == "pending_confirmation":
        return {"success": False, **result}
    if not result.get("ok"):
        return {"success": False, **result}
    moved = int(result.get("result", {}).get("moved", 0))
    return {"success": True, "moved": moved, "operations": [], "session_loop": True}


@router.post("/desktop/cleanup")
async def desktop_cleanup(
    body: Dict[str, Any] = Body(default={}),
    interaction: DesktopInteraction = Depends(get_desktop_interaction),
    workspace: "UnifiedWorkspace" = Depends(get_agent_workspace),
) -> dict:
    """桌面清理——統一經代理工作區會話閉環執行（非旁路）。

    危險操作：第一次呼叫回 pending_confirmation，需 confirm=True 重送。
    """
    if interaction is None:
        raise HTTPException(503, "DesktopInteraction not available")
    if workspace is None:
        raise HTTPException(503, "AgentWorkspace not available")
    confirm = bool(body.get("confirm", False))
    days_old = int(body.get("days_old", 30))
    if workspace.workspace.sessions.get_session("desktop") is None:
        opened = await workspace.open_app("desktop", purpose="API 桌面清理", source="api")
        if not opened.get("ok"):
            return {"success": False, **opened}
    result = await workspace.act(
        "desktop", "cleanup", params={"days_old": days_old}, confirm=confirm, source="api"
    )
    if result.get("status") == "pending_confirmation":
        return {"success": False, **result}
    if not result.get("ok"):
        return {"success": False, **result}
    cleaned = int(result.get("result", {}).get("cleaned", 0))
    return {"success": True, "cleaned": cleaned, "operations": [], "session_loop": True}


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
async def brain_dividend() -> Dict[str, Any]:
    """Execute the brain dividend operation."""
    digital_life = get_digital_life()
    summary = digital_life.get_formula_metrics()
    if summary and "formula_status" in summary:
        cdm = summary["formula_status"].get("cdm")
        if isinstance(cdm, dict):
            return cdm
    return {"message": "Dividend data not available"}
