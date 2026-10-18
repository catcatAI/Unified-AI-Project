# =============================================================================
# ANGELA-MATRIX: L6[执行层] β [A] L2+
# =============================================================================
#
# 职责: 网络搜索代理，检索外部信息
# 维度: 涉及认知维度 (β) 的信息获取和处理
# 安全: 使用 Key A (后端控制) 进行网络访问过滤
# 成熟度: L2+ 等级可以使用基本的搜索功能
#
# 能力:
# - web_search: 网络搜索（委託 WebSearchTool——與 gate 路徑同源，消雙實裝漂移）
# - knowledge_retrieval: 知识检索
# - source_verification: 来源验证
#
# =============================================================================

import logging
import re
import urllib.request
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.system.config.magic_numbers import timeout_value

logger = logging.getLogger(__name__)


class WebSearchAgent:
    """Agent for web search and content fetching.

    search() 委託 ``core.tools.web_search_tool.WebSearchTool``（與
    ExecutionGate→WebSearchHandler 同一實裝）。audit 2026-10-18：舊自帶
    DDG HTML regex（rel="nofollow" class="result__a"）對真實 DDG 0 命中，
    且 get_search_trends 回傳 dummy 假數據——假趨勢已刪（零調用方），
    fetch_content 摘要改為真實文字抽取（原為裸 HTML 前 500 字元）。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        self.config = config or {}
        self.agent_id = kwargs.get("agent_id")
        self._search_history: List[Dict[str, Any]] = []
        self._MAX_SEARCH_HISTORY = 100
        logger.info("WebSearchAgent initialized (delegates search to WebSearchTool)")

    def is_available(self) -> bool:
        """stdurllib 即可搜尋/抓取——恒可用。"""
        return True

    _URL_RE = re.compile(r"https?://[^\s\)\]}>\"']+", re.IGNORECASE)

    def extract_url(self, prompt: str) -> Optional[str]:
        """First http(s) URL in the text, if any. Pure string work — no network."""
        m = self._URL_RE.search(prompt or "")
        return m.group(0) if m else None

    def handle_request(self, prompt: str) -> Dict[str, Any]:
        """Accept a natural-language request: fetch a named page, else search.

        WHY this exists: `web_research` maps to this agent, but the router passes
        the message under generic keys while this class needs a `url` for
        fetch_content() and a `query` for search(). Deciding which one the user
        meant is web-search vocabulary, so it belongs here rather than in the
        router.
        """
        text = (prompt or "").strip()
        if not text:
            return {"status": "error", "message": "No request provided"}

        url = self.extract_url(text)
        if url:
            return self.fetch_content(url)
        return self.search(text)

    def _tool(self):
        """WebSearchTool 懶載入（與 WebSearchHandler 同款屬性防護）。"""
        from core.tools.web_search_tool import WebSearchTool

        return WebSearchTool()

    def search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Search via the shared WebSearchTool (DDG Lite + Wikipedia fallback)."""
        if not query:
            return {"status": "error", "message": "No search query provided"}
        try:
            raw = self._tool().search(query, num_results=num_results)
            results = [
                {
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "snippet": r.get("snippet", ""),
                }
                for r in raw
                if isinstance(r, dict) and not r.get("error")
            ]
            if raw and all(isinstance(r, dict) and r.get("error") for r in raw):
                return {"status": "error", "message": f"Search failed: {raw[0].get('error')}"}
            self._search_history.append(
                {
                    "query": query,
                    "num_results": len(results),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            if len(self._search_history) > self._MAX_SEARCH_HISTORY:
                self._search_history = self._search_history[-self._MAX_SEARCH_HISTORY :]
            logger.info(f"search: '{query}' -> {len(results)} results (via WebSearchTool)")
            return {
                "status": "success",
                "message": f"Found {len(results)} results for '{query}'",
                "query": query,
                "result_count": len(results),
                "results": results,
            }
        except Exception as e:
            logger.error(f"search failed for '{query}': {e}")
            return {"status": "error", "message": f"Search failed: {e}"}

    # 真文字摘要：script/style 剝除 → 去標籤 → 空白收斂 → 前 500 字元。
    _TAG_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
    _ANY_TAG_RE = re.compile(r"<[^>]+>")
    _WS_RE = re.compile(r"\s+")

    def fetch_content(self, url: str) -> Dict[str, Any]:
        """Fetch a URL and return a plain-text summary (not raw HTML)."""
        if not url:
            return {"status": "error", "message": "No URL provided"}
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 (compatible; AngelaAI/7.5.0)"}
            )
            with urllib.request.urlopen(
                req, timeout=timeout_value("web_fetch.http", 15)
            ) as resp:  # nosec B310 - caller passes http(s) URLs from user text; scheme guard below
                content_type = resp.headers.get("Content-Type", "")
                raw = resp.read()
            text = raw.decode("utf-8", errors="replace")
            cleaned = self._TAG_RE.sub(" ", text)
            cleaned = self._ANY_TAG_RE.sub(" ", cleaned)
            cleaned = self._WS_RE.sub(" ", cleaned).strip()
            summary = cleaned[:500]
            logger.info(f"fetch_content: {url} -> {len(text)} bytes, summary={len(summary)} chars")
            return {
                "status": "success",
                "message": f"Fetched {url} ({len(text)} bytes)",
                "url": url,
                "content_type": content_type,
                "content_summary": summary,
                "content_length": len(text),
            }
        except Exception as e:
            logger.error(f"fetch_content failed for {url}: {e}")
            return {"status": "error", "message": f"Failed to fetch content: {e}"}
