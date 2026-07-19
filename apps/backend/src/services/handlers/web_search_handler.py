"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
WebSearchHandler — processes web_search intents from ChatService dispatch.
Delegates to WebSearchTool for actual web search.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class WebSearchHandler:
    """Handles web search intents using WebSearchTool."""

    def __init__(self):
        self._tool = None

    @property
    def _search_tool(self):
        if self._tool is None:
            try:
                from core.tools.web_search_tool import WebSearchTool

                self._tool = WebSearchTool()
            except Exception as e:
                logger.warning(f"[WebSearchHandler] WebSearchTool unavailable: {e}", exc_info=True)
        return self._tool

    async def handle(self, text: str, intent: str) -> str:
        """Extract query from text, execute search, return formatted results."""
        query = self._extract_query(text)
        if not query:
            return "（網路搜尋）請告訴我要搜尋什麼。"
        return await self._search(query)

    async def _search(self, query: str) -> str:
        """Search."""
        tool = self._search_tool
        if not tool:
            return "（網路搜尋）搜尋工具尚未就緒。"
        try:
            results = await asyncio.to_thread(tool.search, query)
            if not results:
                return f"（網路搜尋）沒有找到「{query}」的相關結果。"
            if isinstance(results[0], dict) and "error" in results[0]:
                logger.warning(f"[WebSearchHandler] search returned error: {results[0]['error']}")
                return "（網路搜尋）搜尋時發生錯誤，請稍後再試。"
            lines = [
                f"• {r.get('title', '?')} — {r.get('url', '?')}"
                for r in results
                if isinstance(r, dict)
            ]
            return f"（網路搜尋）「{query}」的搜尋結果：\n" + "\n".join(lines[:5])
        except Exception as e:
            logger.error(f"[WebSearchHandler] search failed: {e}", exc_info=True)
            return "（網路搜尋）搜尋時發生錯誤。"

    def _extract_query(self, text: str) -> Optional[str]:
        """Extract the search query from user text by removing intent keywords."""
        import re

        prefixes = sorted(
            ["搜尋", "搜索", "幫我搜", "幫我查", "google", "search", "lookup", "查", "找"],
            key=len,
            reverse=True,
        )
        for prefix in prefixes:
            pattern = re.compile(re.escape(prefix), re.IGNORECASE)
            text = pattern.sub("", text, count=1).strip()
        text = re.sub(r"^(關於|有關|看看|幫我|請幫我|可以幫我)\s*", "", text).strip()
        text = re.sub(r"[\s,.!?;:，。！？；：]+$", "", text).strip()
        return text if text and len(text) >= 2 else None
