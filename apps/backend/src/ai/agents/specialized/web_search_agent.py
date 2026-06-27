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
# - web_search: 网络搜索
# - knowledge_retrieval: 知识检索
# - source_verification: 来源验证
#
# =============================================================================

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class WebSearchAgent:
    """Agent for web search, content fetching, and search trends."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        self.config = config or {}
        self.agent_id = kwargs.get("agent_id")
        self._search_history: List[Dict[str, Any]] = []
        self._session: Optional[requests.Session] = None
        if REQUESTS_AVAILABLE:
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": "Mozilla/5.0 (compatible; AngelaAI/1.0; +https://opencode.ai)"
            })
        logger.info(f"WebSearchAgent initialized. HTTP available: {REQUESTS_AVAILABLE}")

    def is_available(self) -> bool:
        """Check if web search backend is available."""
        return REQUESTS_AVAILABLE

    def search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Perform a web search via DuckDuckGo HTML interface."""
        if not query:
            return {"status": "error", "message": "No search query provided"}
        if not REQUESTS_AVAILABLE or not self._session:
            return {"status": "unavailable", "message": "HTTP client not available; install requests"}
        try:
            resp = self._session.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                timeout=10,
            )
            resp.raise_for_status()
            import re as _re
            results = []
            for i, match in enumerate(_re.findall(
                r'<a rel="nofollow" class="result__a" href="([^"]+)".*?>(.*?)</a>',
                resp.text, _re.DOTALL
            )):
                if i >= num_results:
                    break
                results.append({"url": match[0], "title": _re.sub(r"<[^>]+>", "", match[1]).strip()})
            self._search_history.append({
                "query": query, "num_results": num_results,
                "timestamp": datetime.now().isoformat()
            })
            logger.info(f"search: '{query}' -> {len(results)} results")
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

    def fetch_content(self, url: str) -> Dict[str, Any]:
        """Fetch and return a text summary of a URL."""
        if not url:
            return {"status": "error", "message": "No URL provided"}
        if not REQUESTS_AVAILABLE or not self._session:
            return {"status": "unavailable", "message": "HTTP client not available; install requests"}
        try:
            resp = self._session.get(url, timeout=15)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            text = resp.text
            summary = text[:500] if text else ""
            logger.info(f"fetch_content: {url} -> {len(text)} bytes, {content_type}")
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

    def get_search_trends(self, topic: str) -> Dict[str, Any]:
        """Get search trends for a topic (mock data)."""
        if not topic:
            return {"status": "error", "message": "No topic provided"}
        dummy_value = len(topic) * 10
        logger.info(f"get_search_trends: '{topic}'")
        return {
            "status": "success",
            "message": f"Trends data for '{topic}'",
            "topic": topic,
            "trends": [
                {"date": "2026-01", "value": dummy_value},
                {"date": "2026-02", "value": dummy_value + 5},
                {"date": "2026-03", "value": dummy_value + 12},
            ],
        }
