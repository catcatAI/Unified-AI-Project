"""
C3: Backend plugin system — hook registry, plugin manager, handlers, and API.
"""

from core.plugin.hook_registry import HookRegistry, hook_registry
from core.plugin.plugin_manager import PluginInfo, PluginManager, plugin_manager

__all__ = [
    "HookRegistry",
    "hook_registry",
    "PluginManager",
    "PluginInfo",
    "plugin_manager",
]
