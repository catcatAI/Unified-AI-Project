#!/usr/bin/env python3
"""
Plugin API endpoints — C3: query hooks, list plugins, execute hooks.

Backed by core/plugin/ (PluginManager, HookRegistry).
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plugins", tags=["Plugins"])

_PLUGIN_MANAGER = None


def _get_plugin_manager():
    """Get the global PluginManager singleton from core/plugin/."""
    global _PLUGIN_MANAGER
    if _PLUGIN_MANAGER is None:
        try:
            from core.plugin.plugin_manager import plugin_manager

            _PLUGIN_MANAGER = plugin_manager
        except Exception as e:
            logger.warning("PluginManager not available: %s", e)
    return _PLUGIN_MANAGER


@router.get("/status")
async def get_plugins_status() -> dict:
    """Get plugin system status with stats."""
    pm = _get_plugin_manager()
    if pm is None:
        return {"status": "unavailable", "service": "plugins", "error": "PluginManager not loaded"}
    stats = pm.get_stats()
    return {"status": "ok", "service": "plugins", "stats": stats}


@router.get("/list")
async def list_plugins(enabled_only: bool = Query(False)) -> dict:
    """List all registered plugins."""
    pm = _get_plugin_manager()
    if pm is None:
        raise HTTPException(status_code=503, detail="PluginManager not available")
    plugins = pm.list_plugins(enabled_only=enabled_only)
    return {"plugins": plugins, "total": len(plugins)}


@router.post("/{name}/enable")
async def enable_plugin(name: str) -> dict:
    """Enable a plugin by name."""
    pm = _get_plugin_manager()
    if pm is None:
        raise HTTPException(status_code=503, detail="PluginManager not available")
    ok = pm.enable_plugin(name)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {name}")
    return {"status": "enabled", "name": name}


@router.post("/{name}/disable")
async def disable_plugin(name: str) -> dict:
    """Disable a plugin by name."""
    pm = _get_plugin_manager()
    if pm is None:
        raise HTTPException(status_code=503, detail="PluginManager not available")
    ok = pm.disable_plugin(name)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {name}")
    return {"status": "disabled", "name": name}


@router.get("/{name}")
async def get_plugin(name: str) -> dict:
    """Get plugin info by name."""
    pm = _get_plugin_manager()
    if pm is None:
        raise HTTPException(status_code=503, detail="PluginManager not available")
    info = pm.get_plugin(name)
    if info is None:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {name}")
    return {
        "name": info.name,
        "version": info.version,
        "description": info.description,
        "enabled": info.enabled,
        "hooks": info.hooks,
    }


@router.get("/hooks/list")
async def list_hooks() -> dict:
    """List all defined hooks and their handlers."""
    try:
        from core.plugin.hook_registry import hook_registry

        stats = hook_registry.get_stats()
        return {"hooks": stats}
    except Exception as e:
        logger.error("Failed to list hooks: %s", e)
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/hook/{hook_name}/execute")
async def execute_hook(hook_name: str, data: Dict[str, Any] = Body(default={})) -> dict:
    """Execute all handlers for a given hook."""
    pm = _get_plugin_manager()
    if pm is None:
        raise HTTPException(status_code=503, detail="PluginManager not available")
    try:
        results = await pm.execute_hook(hook_name, data)
        return {
            "hook": hook_name,
            "results": [{"handler": r.handler_name, "success": r.success, "data": r.data} for r in results],
            "count": len(results),
        }
    except Exception as e:
        logger.error("Hook execution failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
