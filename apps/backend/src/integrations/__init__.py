"""
Unified AI Project - 集成模块
提供与外部服务和平台的集成功能

All imports are lazy: integrations/__init__ must never pull optional
third-party stacks (googleapiclient etc.) — importing ANY submodule
(e.g. integrations.os_bridge_adapter for Heartbeat/vision) runs this
package init first, and an eager google import here used to take down
Heartbeat init, vision listener registration, and the whole v1 endpoint
router bundle when the `google` extra was not installed.
"""

import importlib
import logging
from typing import Any, List

logger = logging.getLogger(__name__)

_LAZY_INTEGRATIONS: dict = {
    "GoogleDriveService": ("integrations.google_drive_service", "GoogleDriveService"),
    "OSBridgeAdapter": ("integrations.os_bridge_adapter", "OSBridgeAdapter"),
}

_lazy_cache: dict = {}
_warned: set = set()


def __getattr__(name: str) -> Any:
    if name in _LAZY_INTEGRATIONS:
        if name in _lazy_cache:
            return _lazy_cache[name]
        module_path, attr = _LAZY_INTEGRATIONS[name]
        try:
            module = importlib.import_module(module_path)
            result = getattr(module, attr)
            _lazy_cache[name] = result
            return result
        except Exception as e:
            if name not in _warned:
                logger.warning(
                    "integrations.%s unavailable: %s (install the [google] extra for Drive support)",
                    name,
                    e,
                )
                _warned.add(name)
            _lazy_cache[name] = None
            return None
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> List[str]:
    return sorted(__all__)


__all__ = [
    "GoogleDriveService",
    "OSBridgeAdapter",
]
