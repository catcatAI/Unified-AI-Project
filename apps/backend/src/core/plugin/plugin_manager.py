"""
PluginManager — C3: backend plugin lifecycle and hook integration.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

from core.plugin.hook_registry import HookRegistry, hook_registry as _default_registry

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    name: str
    version: str
    description: str = ""
    enabled: bool = True
    hooks: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class PluginManager:
    """Manages plugin registration, lifecycle, and hook binding."""

    def __init__(self, hook_registry: Optional[HookRegistry] = None):
        self._hook_registry = hook_registry or _default_registry
        self._plugins: Dict[str, PluginInfo] = {}
        self._define_standard_hooks()

    def _define_standard_hooks(self) -> None:
        """Define and register the standard set of hooks."""
        standard_hooks = {
            "on_message": "Triggered when a user message is received",
            "on_response": "Triggered when a response is generated",
            "on_state_change": "Triggered when Angela's state changes",
            "on_bio_event": "Triggered on biological events (emotion, arousal, etc.)",
            "on_tick": "Periodic tick (every 30s)",
        }
        for name, desc in standard_hooks.items():
            self._hook_registry.define_hook(name, desc)

    def register_plugin(self, name: str, version: str, description: str = "",
                        hooks: Optional[List[str]] = None) -> PluginInfo:
        """Register a new plugin with the manager."""
        if name in self._plugins:
            logger.info(f"[PluginManager] Re-registering plugin: {name}")
        info = PluginInfo(
            name=name, version=version, description=description,
            enabled=True, hooks=hooks or [],
        )
        self._plugins[name] = info
        logger.info(f"[PluginManager] Plugin registered: {name} v{version}")
        return info

    def unregister_plugin(self, name: str) -> bool:
        """Unregister a plugin by name."""
        if name not in self._plugins:
            return False
        del self._plugins[name]
        return True

    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin by name."""
        if name not in self._plugins:
            return False
        self._plugins[name].enabled = True
        return True

    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin by name."""
        if name not in self._plugins:
            return False
        self._plugins[name].enabled = False
        return True

    def get_plugin(self, name: str) -> Optional[PluginInfo]:
        """Get a plugin's info by name."""
        return self._plugins.get(name)

    def list_plugins(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """List all registered plugins, optionally filtering by enabled."""
        plugins = self._plugins.values()
        if enabled_only:
            plugins = [p for p in plugins if p.enabled]
        return [
            {"name": p.name, "version": p.version, "description": p.description,
             "enabled": p.enabled, "hooks": p.hooks}
            for p in plugins
        ]

    def add_handler(self, plugin_name: str, hook_name: str, handler) -> bool:
        """Add a handler to a plugin's hook."""
        if plugin_name not in self._plugins:
            return False
        ok = self._hook_registry.register_handler(hook_name, plugin_name, handler)
        if ok and hook_name not in self._plugins[plugin_name].hooks:
            self._plugins[plugin_name].hooks.append(hook_name)
        return ok

    async def execute_hook(self, hook_name: str, data: Any = None) -> List[HookResult]:
        """Execute all handlers for a given hook."""
        return await self._hook_registry.execute_hook(hook_name, data)

    async def execute_pipeline(self, hook_name: str, initial_data: Any = None) -> Any:
        """Execute all handlers in pipeline mode — each receives and returns data."""
        return await self._hook_registry.execute_pipeline(hook_name, initial_data)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about registered plugins and hooks."""
        plugins = self.list_plugins()
        return {
            "plugin_count": len(plugins),
            "enabled_count": sum(1 for p in plugins if p["enabled"]),
            "plugins": plugins,
            "hook_registry": self._hook_registry.get_stats(),
        }


# Singleton
plugin_manager = PluginManager()
