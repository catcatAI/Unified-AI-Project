"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
FileOperationHandler — processes file_op intents from ChatService dispatch.
Delegates to DesktopInteraction for actual file system operations.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FileOperationHandler:
    """Handles file operation intents (organize, move, delete, copy, rename, etc.)."""

    def __init__(self, desktop_interaction: Any = None):
        self._desktop_interaction = desktop_interaction

    @property
    def desktop_interaction(self):
        if self._desktop_interaction is None:
            try:
                from core.engine.desktop_interaction import DesktopInteraction
                self._desktop_interaction = DesktopInteraction()
            except Exception as e:
                logger.warning(f"DesktopInteraction unavailable: {e}")
        return self._desktop_interaction

    async def handle(self, intent: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        operation = params or {}
        action = operation.get("action", intent.replace("file_op_", ""))
        logger.info(f"FileOperationHandler handling: {action}")
        if self.desktop_interaction and hasattr(self.desktop_interaction, "execute"):
            return await self.desktop_interaction.execute(action, operation)
        return {"status": "ok", "action": action, "note": "handled by FileOperationHandler (stub)"}


__all__ = ["FileOperationHandler"]
