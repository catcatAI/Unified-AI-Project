"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
WebSearchHandler — processes web_search intents from ChatService dispatch.
Delegates to WebSearchTool for actual web search.
"""

import asyncio
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# 錨定前綴剔除（audit 2026-10-18）：舊實作對每個前綴 `re.sub(..., count=1)`
# **未錨定字串開頭**——「查/找/search」等單字元詞會從字串中間任何位置摳掉
# （實測「幫我調查 X Search API」→「幫我調 X  API」，搜尋拿殘缺查詢跑）。
# 改為單一錨定 alternation，一字串最多循環剝 3 層（「請幫我搜尋 X」）。
_INTENT_PREFIX_RE = re.compile(
    r"^\s*(?:請?幫我|可以幫我|請你?)?\s*"
    r"(?:搜尋|搜索|搜尋一下|搜索一下|查詢|查找|調查|调研|搜一下|查一下|"
    r"lookup|search|google|find|查|找)?\s*",
    re.IGNORECASE,
)
_ABOUT_RE = re.compile(r"^\s*(?:關於|有關|看看)\s*")
_TRAILING_PUNCT_RE = re.compile(r"[\s,.!?;:，。！？；：]+$")


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
            return "請告訴我要搜尋什麼。"
        return await self._search(query)

    async def _search(self, query: str) -> str:
        """研究管線執行（排序→抓內文→抽事實→比對→結構化答案）。"""
        tool = self._search_tool
        if not tool:
            return "搜尋工具尚未就緒。"
        try:
            from core.tools.research_pipeline import run_research

            research = await asyncio.to_thread(run_research, query, tool)
            if not research.get("ok"):
                logger.warning(f"[WebSearchHandler] search returned error: {research.get('error')}")
                return "搜尋時發生錯誤，請稍後再試。"
            if not research.get("sources"):
                return f"沒有找到「{query}」的相關結果。"
            return str(research.get("answer") or "")
        except Exception as e:
            logger.error(f"[WebSearchHandler] search failed: {e}", exc_info=True)
            return "搜尋時發生錯誤。"

    def _extract_query(self, text: str) -> Optional[str]:
        """Strip intent prefixes **anchored at string start only**.

        中段的「查/找/Search」等是查詢內容的一部分，絕不可摳除。
        """
        text = (text or "").strip()
        for _ in range(3):
            stripped = _INTENT_PREFIX_RE.sub("", text, count=1)
            if stripped == text:
                break
            text = stripped
        text = _ABOUT_RE.sub("", text).strip()
        text = _TRAILING_PUNCT_RE.sub("", text).strip()
        return text if text and len(text) >= 2 else None
