"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
网络搜索工具 — 使用 DuckDuckGo Lite 或 Wikipedia API。
"""

import json
import logging
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from core.utils import safe_error

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "AngelaAI/7.5.0"
_DDG_URL = "https://lite.duckduckgo.com/lite/"
_WIKI_API = "https://en.wikipedia.org/w/api.php"


class WebSearchTool:
    """Simple web search tool using DuckDuckGo Lite + Wikipedia fallback."""

    def __init__(self):
        self.user_agent = DEFAULT_USER_AGENT

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        results = self._ddg_search(query, num_results)
        if results and not any("error" in r for r in results):
            return results
        return self._wiki_search(query, num_results)

    def _ddg_search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        try:
            data = urllib.parse.urlencode({"q": query, "kl": ""}).encode()
            req = urllib.request.Request(
                _DDG_URL, data=data,
                headers={"User-Agent": self.user_agent, "Content-Type": "application/x-www-form-urlencoded"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            results: List[Dict[str, Any]] = []
            for m in re.finditer(
                r'<a[^>]+rel="nofollow"[^>]+href="([^"]+)"[^>]*>\s*<span>([^<]+)</span>',
                html,
            ):
                url, title = m.group(1), m.group(2).strip()
                if url.startswith("/"):
                    continue
                results.append({"title": title, "url": url, "snippet": ""})
                if len(results) >= num_results:
                    break
            return results
        except Exception as e:
            logger.debug(f"DDG search failed: {e}")
            return [{"error": safe_error(e)}]

    def _wiki_search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        try:
            params = urllib.parse.urlencode({
                "action": "query", "list": "search", "srsearch": query,
                "srlimit": num_results, "format": "json",
            })
            url = f"{_WIKI_API}?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            results = []
            for item in data.get("query", {}).get("search", []):
                title = item.get("title", "")
                snippet = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
                results.append({
                    "title": title,
                    "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title)}",
                    "snippet": snippet,
                })
            return results
        except Exception as e:
            logger.debug(f"Wikipedia search failed: {e}")
            return [{"error": safe_error(e)}]


__all__ = ["WebSearchTool"]
