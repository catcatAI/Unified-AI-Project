"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
FileOperationHandler — processes file_op intents from ChatService dispatch.
Delegates to DesktopInteraction for actual file system operations.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class FileOperationHandler:
    """Handles file operation intents (organize, cleanup, create, etc.)."""

    def __init__(self):
        self._desktop = None

    @property
    def _desktop_interaction(self):
        if self._desktop is None:
            try:
                from api.lifespan import get_desktop_interaction
                self._desktop = get_desktop_interaction()
            except Exception as e:
                logger.warning(f"[FileOperationHandler] DesktopInteraction unavailable: {e}", exc_info=True)
        return self._desktop

    async def handle(self, text: str, intent: str) -> str:
        """Route file operation text to the appropriate action."""
        text_lower = text.lower()

        if any(kw in text_lower for kw in ["整理", "organize", "分類"]):
            return await self._organize()

        if any(kw in text_lower for kw in ["清理", "cleanup", "刪除舊"]):
            return await self._cleanup(text_lower)

        if any(kw in text_lower for kw in ["創建", "create", "建立", "新增"]):
            return await self._create(text)

        return "（檔案操作）請告訴我妳想做什麼：整理桌面、清理舊檔案、或創建新檔案？"

    async def _organize(self) -> str:
        """Organize."""
        di = self._desktop_interaction
        if not di:
            return "（檔案操作）桌面互動服務尚未就緒。"
        try:
            results = await di.organize_desktop()
            count = len(results)
            return f"（檔案操作）已整理 {count} 個檔案，桌面現在更整齊了！" if count else "（檔案操作）桌面已經很整齊，沒有需要整理的檔案。"
        except Exception as e:
            logger.error(f"[FileOperationHandler] organize failed: {e}", exc_info=True)
            return "（檔案操作）整理桌面時發生錯誤。"

    async def _cleanup(self, text_lower: str) -> str:
        """Cleanup."""
        di = self._desktop_interaction
        if not di:
            return "（檔案操作）桌面互動服務尚未就緒。"
        try:
            days_match = re.search(r"(\d+)\s*天", text_lower)
            days_old = int(days_match.group(1)) if days_match else 30
            results = await di.cleanup_desktop(days_old=days_old)
            count = len(results)
            return f"（檔案操作）已清理 {count} 個超過 {days_old} 天的檔案。" if count else f"（檔案操作）沒有發現超過 {days_old} 天的檔案需要清理。"
        except Exception as e:
            logger.error(f"[FileOperationHandler] cleanup failed: {e}", exc_info=True)
            return "（檔案操作）清理桌面時發生錯誤。"

    async def _create(self, text: str) -> str:
        """Create."""
        di = self._desktop_interaction
        if not di:
            return "（檔案操作）桌面互動服務尚未就緒。"
        name_match = re.search(r"(?:創建|create|建立|新增)\s*(?:檔案|文件)?\s*[：:，]?\s*(.+)", text)
        if not name_match:
            return "（檔案操作）請告訴我要創建什麼檔案。"
        file_name = name_match.group(1).strip()
        try:
            from core.engine.desktop_interaction import FileOperation, FileOperationType
            from pathlib import Path
            from datetime import datetime
            op = FileOperation(
                operation_id=f"create_{datetime.now().timestamp():.0f}",
                operation_type=FileOperationType.CREATE,
                source_path=Path(file_name),
            )
            result = await di.execute_operation(op)
            status = result.status if hasattr(result, "status") else "completed"
            return f"（檔案操作）已{'創建' if status == 'completed' else '嘗試創建'}檔案：{file_name}" if status != "failed" else f"（檔案操作）創建檔案失敗：{file_name}"
        except Exception as e:
            logger.error(f"[FileOperationHandler] create failed: {e}", exc_info=True)
            return "（檔案操作）創建檔案時發生錯誤。"
