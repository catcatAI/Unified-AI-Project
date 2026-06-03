"""
Plugin API endpoints — C3: query hooks, list plugins, execute hooks.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import logging, json

from core.plugin.plugin_manager import plugin_manager
from core.plugin.hook_registry import hook_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plugins", tags=["Plugins"])


@router.get("/hooks")
async def list_hooks() -> dict:
    """List all available backend hooks."""
    return {"hooks": hook_registry.list_hooks()}


@router.get("/plugins")
async def list_plugins(enabled_only: bool = False) -> dict:
    """List registered plugins."""
    return {"plugins": plugin_manager.list_plugins(enabled_only=enabled_only)}


@router.post("/plugins/{name}/enable")
async def enable_plugin(name: str) -> dict:
    """Enable a plugin."""
    if not plugin_manager.enable_plugin(name):
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")
    return {"status": "enabled", "name": name}


@router.post("/plugins/{name}/disable")
async def disable_plugin(name: str) -> dict:
    """Disable a plugin."""
    if not plugin_manager.disable_plugin(name):
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")
    return {"status": "disabled", "name": name}


@router.post("/hooks/{hook_name}/execute")
async def execute_hook(hook_name: str, data: Dict[str, Any] = {}) -> dict:
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


@router.post("/register")
async def register_plugin(name: str, version: str = "1.0", description: str = "") -> dict:
    """Register a plugin with the backend system."""
    info = plugin_manager.register_plugin(name, version, description)
    return {"status": "registered", "name": info.name, "version": info.version}


@router.get("/stats")
async def plugin_stats() -> dict:
    """Get plugin system statistics."""
    return plugin_manager.get_stats()


# ── Plugin data persistence ──────────────────────────────────────────────

@router.post("/data/{plugin_name}")
async def set_plugin_data(plugin_name: str, data: Dict[str, Any] = {}) -> dict:
    """Store key-value data for a plugin."""
    try:
        from core.interfaces.persistence import JsonFileStateStore
        store = JsonFileStateStore(f"data/plugins/{plugin_name}/")
        for key, value in data.items():
            await store.save_state(key, {plugin_name: {key: value}})
        return {"status": "stored", "keys": list(data.keys())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/{plugin_name}")
async def get_plugin_data(plugin_name: str) -> dict:
    """Retrieve all stored data for a plugin."""
    try:
        from core.interfaces.persistence import JsonFileStateStore
        store = JsonFileStateStore(f"data/plugins/{plugin_name}/")
        keys = await store.list_keys()
        result = {}
        for key in keys:
            val = await store.load_state(key)
            if val:
                result[key] = val
        return {"plugin": plugin_name, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/data/{plugin_name}/{key}")
async def delete_plugin_data(plugin_name: str, key: str) -> dict:
    """Delete a specific data key for a plugin."""
    try:
        from core.interfaces.persistence import JsonFileStateStore
        store = JsonFileStateStore(f"data/plugins/{plugin_name}/")
        ok = await store.delete_state(key)
        return {"status": "deleted" if ok else "not_found", "key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
