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
from datetime import datetime
from typing import Any, Dict, List, Optional

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
        """研究管線（排序/抓內文/事實抽取/交叉比對）；message 即終答。

        舊版 message=\"Found N results\" 只給連結快取級回應——
        ``_agent_route_result`` 直接拿 message 當回覆，主 AI 路徑同源。
        """
        if not query:
            return {"status": "error", "message": "No search query provided"}
        try:
            from core.tools.research_pipeline import run_research

            research = run_research(query, tool=self._tool(), num_results=num_results)
            if not research.get("ok"):
                return {"status": "error", "message": f"Search failed: {research.get('error')}"}
            sources = research.get("sources") or []
            if not sources:
                return {
                    "status": "success",
                    "message": f"沒有找到「{query}」的相關結果。",
                    "query": query,
                    "result_count": 0,
                    "results": [],
                }
            results = [
                {
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "snippet": r.get("snippet", ""),
                    "trust": r.get("trust", "中"),
                }
                for r in sources
                if isinstance(r, dict)
            ]
            self._search_history.append(
                {
                    "query": query,
                    "num_results": len(results),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            if len(self._search_history) > self._MAX_SEARCH_HISTORY:
                self._search_history = self._search_history[-self._MAX_SEARCH_HISTORY :]
            logger.info(
                "search: '%s' -> %d sources, %d facts (via research pipeline)",
                query,
                len(results),
                len(research.get("facts") or []),
            )
            return {
                "status": "success",
                "message": research.get("answer") or f"找到 {len(results)} 個來源。",
                "answer": research.get("answer") or "",
                "query": query,
                "result_count": len(results),
                "results": results,
            }
        except Exception as e:
            logger.error(f"search failed for '{query}': {e}")
            return {"status": "error", "message": f"Search failed: {e}"}

    def fetch_content(self, url: str) -> Dict[str, Any]:
        """Fetch a URL → plain-text summary（共用 research_pipeline.fetch_page_text）。"""
        if not url:
            return {"status": "error", "message": "No URL provided"}
        try:
            from core.tools.research_pipeline import fetch_page_text

            text = fetch_page_text(url, min_chars=0)
            if not text:
                logger.info(f"fetch_content: {url} -> no extractable text")
                return {
                    "status": "error",
                    "message": f"No extractable text from {url}",
                    "url": url,
                }
            summary = text[:500]
            logger.info(f"fetch_content: {url} -> {len(text)} chars, summary={len(summary)}")
            return {
                "status": "success",
                "message": f"Fetched {url} ({len(text)} chars)",
                "url": url,
                "content_type": "text/plain",
                "content_summary": summary,
                "content_length": len(text),
            }
        except Exception as e:
            logger.error(f"fetch_content failed for {url}: {e}")
            return {"status": "error", "message": f"Failed to fetch content: {e}"}
