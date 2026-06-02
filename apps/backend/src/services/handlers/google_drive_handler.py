"""
ANGELA-MATRIX: [L3-L4] [βδ] [B] [L2]
GoogleDriveHandler — processes google_drive intents from ChatService dispatch.
Delegates to GoogleDriveService for actual Drive operations.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class GoogleDriveHandler:
    """Handles Google Drive intents (list, sync, auth, status, write, logout)."""

    def __init__(self):
        self._drive_service = None

    @property
    def _service(self):
        if self._drive_service is None:
            try:
                from integrations.google_drive_service import get_drive_service
                self._drive_service = get_drive_service()
            except Exception as e:
                logger.warning(f"[GoogleDriveHandler] GoogleDriveService unavailable: {e}", exc_info=True)
        return self._drive_service

    async def handle(self, text: str, intent: str) -> str:
        """Route Google Drive text to the appropriate action."""
        text_lower = text.lower()

        if any(kw in text_lower for kw in ["列出", "看", "列表", "有什麼"]):
            return await self._list_files()

        if any(kw in text_lower for kw in ["同步", "下載", "存到本地"]):
            return await self._sync()

        if any(kw in text_lower for kw in ["分析", "總結"]):
            return self._not_authenticated("分析")

        if any(kw in text_lower for kw in ["狀態", "status"]):
            return await self._status()

        if any(kw in text_lower for kw in ["儲存", "上傳", "存到", "創建"]):
            return self._not_authenticated("上傳")

        if any(kw in text_lower for kw in ["登出", "logout"]):
            return await self._logout()

        return "（Google Drive）請告訴我妳想做什麼：列出檔案、同步到本地、或查看狀態？"

    async def _list_files(self) -> str:
        svc = self._service
        if not svc:
            return "（Google Drive）Google Drive 服務尚未就緒。"
        try:
            if not svc.is_authenticated():
                return "（Google Drive）尚未認證，請先進行 Google Drive 認證。"
            files = svc.list_files(page_size=10)
            if not files:
                return "（Google Drive）雲端硬碟中沒有檔案。"
            lines = [f"📄 {f.get('name', 'unknown')} ({self._fmt_size(f.get('size', 0))})" for f in files[:10]]
            return "（Google Drive）最近檔案：\n" + "\n".join(lines)
        except Exception as e:
            logger.error(f"[GoogleDriveHandler] list failed: {e}", exc_info=True)
            return "（Google Drive）列出檔案時發生錯誤。"

    async def _sync(self) -> str:
        return "（Google Drive）同步功能需要指定要下載的檔案名稱或 ID。"

    async def _status(self) -> str:
        svc = self._service
        if not svc:
            return "（Google Drive）Google Drive 服務尚未就緒。"
        try:
            authed = svc.is_authenticated()
            if not authed:
                return "（Google Drive）目前未認證。請使用「google drive 認證」來開始 OAuth 流程。"
            info = svc.get_storage_info()
            return f"（Google Drive）已認證。儲存空間：已用 {self._fmt_size(info.get('used', 0))} / 總計 {self._fmt_size(info.get('total', 0))}"
        except Exception as e:
            logger.error(f"[GoogleDriveHandler] status failed: {e}", exc_info=True)
            return "（Google Drive）獲取狀態時發生錯誤。"

    async def _logout(self) -> str:
        svc = self._service
        if not svc:
            return "（Google Drive）Google Drive 服務尚未就緒。"
        try:
            svc.logout()
            return "（Google Drive）已登出 Google Drive。"
        except Exception as e:
            logger.error(f"[GoogleDriveHandler] logout failed: {e}", exc_info=True)
            return "（Google Drive）登出時發生錯誤。"

    def _not_authenticated(self, action: str) -> str:
        return f"（Google Drive）{action}功能需要先認證 Google Drive。請說「google drive 認證」開始 OAuth 流程。"

    @staticmethod
    def _fmt_size(size_bytes) -> str:
        try:
            size = int(size_bytes)
            if size < 1024:
                return f"{size} B"
            elif size < 1024 ** 2:
                return f"{size / 1024:.1f} KB"
            elif size < 1024 ** 3:
                return f"{size / 1024 ** 2:.1f} MB"
            else:
                return f"{size / 1024 ** 3:.1f} GB"
        except (ValueError, TypeError):
            logger.warning(f"_fmt_size failed for {size_bytes}", exc_info=True)
            return "unknown"
