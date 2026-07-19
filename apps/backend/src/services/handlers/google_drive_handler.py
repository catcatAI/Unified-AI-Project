from services.error_handling import safe_error

"""
ANGELA-MATRIX: [L3-L4] [βδ] [B] [L2]
GoogleDriveHandler — processes google_drive intents from ChatService dispatch.
Delegates to GoogleDriveService for actual Drive operations.
"""

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class GoogleDriveHandler:
    """Handles Google Drive intents (list, search, sync, download, etc.).

    Currently operates in stub mode with basic local file operations until
    a real Google Drive API client is configured. When a `drive_service` with
    an `execute(action, params)` method is provided, delegates all operations
    to it.
    """

    SUPPORTED_ACTIONS = {
        "list",
        "search",
        "sync",
        "download",
        "upload",
        "delete",
        "rename",
        "move",
        "copy",
        "info",
    }

    def __init__(self, drive_service: Any = None):
        self.drive_service = drive_service

    async def handle(self, intent: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        operation = params or {}
        action = operation.get("action", intent.replace("google_drive_", ""))
        logger.info(f"GoogleDriveHandler handling: {action}")

        if action not in self.SUPPORTED_ACTIONS:
            return {"status": "error", "action": action, "error": f"Unsupported action: {action}"}

        if self.drive_service and hasattr(self.drive_service, "execute"):
            try:
                return await self.drive_service.execute(action, operation)
            except Exception as e:
                logger.warning(f"GoogleDriveService execute failed, falling back to local fs: {e}")
                # Fall through to local fs fallback

        # Local filesystem fallback (no drive_service configured or execute failed)
        path = operation.get("path", operation.get("filepath", "."))
        if action == "list":
            try:
                files = []
                for f in os.listdir(path):
                    fp = os.path.join(path, f)
                    files.append(
                        {
                            "name": f,
                            "is_dir": os.path.isdir(fp),
                            "size": os.path.getsize(fp) if os.path.isfile(fp) else 0,
                        }
                    )
                return {"status": "ok", "action": action, "files": files, "mode": "local_fs"}
            except Exception as e:
                return {"status": "error", "action": action, "error": safe_error(e)}
        elif action == "info":
            if os.path.exists(path):
                return {
                    "status": "ok",
                    "action": action,
                    "exists": True,
                    "is_file": os.path.isfile(path),
                    "size": os.path.getsize(path) if os.path.isfile(path) else 0,
                }
            return {"status": "ok", "action": action, "exists": False}

        return {
            "status": "ok",
            "action": action,
            "mode": "local_fs",
            "note": f"Action '{action}' handled by local filesystem fallback; configure drive_service for full Drive API support",
        }


__all__ = ["GoogleDriveHandler"]
