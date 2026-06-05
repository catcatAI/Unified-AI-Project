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
        self.desktop_interaction = desktop_interaction

    async def handle(self, intent: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        operation = params or {}
        action = operation.get("action", intent.replace("file_op_", ""))
        logger.info(f"FileOperationHandler handling: {action}")
        if self.desktop_interaction and hasattr(self.desktop_interaction, "execute"):
            return await self.desktop_interaction.execute(action, operation)
        return {"status": "ok", "action": action, "note": "handled by FileOperationHandler (stub)"}


__all__ = ["FileOperationHandler"]
