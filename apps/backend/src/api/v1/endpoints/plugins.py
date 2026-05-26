"""
Plugin API endpoints — C3: query hooks, list plugins, execute hooks.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging

from core.plugin.plugin_manager import plugin_manager
from core.plugin.hook_registry import hook_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plugins", tags=["Plugins"])


@router.get("/hooks")
async def list_hooks():
    """List all available backend hooks."""
    return {"hooks": hook_registry.list_hooks()}


@router.get("/plugins")
async def list_plugins(enabled_only: bool = False):
    """List registered plugins."""
    return {"plugins": plugin_manager.list_plugins(enabled_only=enabled_only)}


@router.post("/plugins/{name}/enable")
async def enable_plugin(name: str):
    """Enable a plugin."""
    if not plugin_manager.enable_plugin(name):
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")
    return {"status": "enabled", "name": name}


@router.post("/plugins/{name}/disable")
async def disable_plugin(name: str):
    """Disable a plugin."""
    if not plugin_manager.disable_plugin(name):
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")
    return {"status": "disabled", "name": name}


@router.post("/hooks/{hook_name}/execute")
async def execute_hook(hook_name: str, data: Dict[str, Any] = {}):
    """Execute a hook with the given data."""
    hook = hook_registry.get_hook(hook_name)
    if not hook:
        raise HTTPException(status_code=404, detail=f"Hook '{hook_name}' not defined")
    results = await plugin_manager.execute_hook(hook_name, data)
    return {
        "hook": hook_name,
        "results": [
            {"handler": r.handler_name, "success": r.success, "result": r.result, "error": r.error}
            for r in results
        ],
    }


@router.get("/stats")
async def plugin_stats():
    """Get plugin system statistics."""
    return plugin_manager.get_stats()
