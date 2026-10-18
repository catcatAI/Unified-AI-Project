"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
网络搜索工具 — 使用 DuckDuckGo Lite 或 Wikipedia API。
"""

import json
import logging
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.utils import safe_error

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "AngelaAI/7.5.0"
_DDG_URL = "https://lite.duckduckgo.com/lite/"
_WIKI_API = "https://en.wikipedia.org/w/api.php"
_WIKI_API_ZH = "https://zh.wikipedia.org/w/api.php"
# CJK（含 Extension A）→ 中文查詢走 zh.wikipedia（原一律英語 API，中文
# 備援語種不對；實測審計 2026-10-18 未觸發但屬確定缺陷）。
_CJK_RE = re.compile(r"[㐀-䶿一-鿿]")
# 稽核軌跡：TTL RAM session 是研究結果唯一落地處 → append-only jsonl。
_HISTORY_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "research_history" / "web_search.jsonl"
)
_HISTORY_ROTATE_BYTES = 5_000_000


def _load_web_search_config() -> dict:
    """Load the centralized web_search config from system/llm (with fallback)."""
    try:
        from core.system.config.tiered_loader import get_config

        ws = (get_config("system/llm") or {}).get("web_search", {})
        if isinstance(ws, dict):
            return ws
    except Exception:
        logger.warning("web_search config read failed, using defaults", exc_info=True)
    return {}


def read_recent_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Read the newest ``limit`` research audit records (jsonl tail, oldest first).

    稽核入口：`GET /api/v1/web-search/history` 與人工 grep 同源。
    """
    path = _HISTORY_PATH
    try:
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        out: List[Dict[str, Any]] = []
        for line in lines[-max(1, limit) :]:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                out.append(record)
        return out
    except Exception as e:
        logger.warning("web_search history read failed: %s", e, exc_info=True)
        return []


class WebSearchTool:
    """Simple web search tool using DuckDuckGo Lite + Wikipedia fallback."""

    def __init__(self):
        ws = _load_web_search_config()
        self.enabled = ws.get("enabled", True)
        self.provider = ws.get("provider", "duckduckgo")
        self.ddg_url = ws.get("ddg_url", _DDG_URL)
        self.wiki_api = ws.get("wiki_api", _WIKI_API)
        # Only http(s) endpoints are reachable: a config-supplied file:// or
        # custom-scheme URL would otherwise be opened verbatim by urlopen.
        if not self.ddg_url.startswith(("http://", "https://")):
            self.ddg_url = _DDG_URL
        if not self.wiki_api.startswith(("http://", "https://")):
            self.wiki_api = _WIKI_API
        self.user_agent = ws.get("user_agent", DEFAULT_USER_AGENT)
        self.max_results = ws.get("max_results", 5)
        self.timeout = ws.get("timeout", 10)

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        num = min(num_results, self.max_results) if self.max_results else num_results
        provider = ""  # falsy sentinel — "none" is truthy and would block fallback
        results: List[Dict[str, Any]] = []
        if self.provider in ("duckduckgo", "both"):
            results = self._ddg_search(query, num)
            if results and not any("error" in r for r in results):
                provider = "duckduckgo"
        if not provider and self.provider in ("wikipedia", "both"):
            results = self._wiki_search(query, num)
            provider = "wikipedia"
        if not provider:
            # Fallback: if DDG was primary and failed, try Wikipedia.
            results = self._wiki_search(query, num)
            provider = "wikipedia"
        n_ok = sum(1 for r in results if isinstance(r, dict) and "error" not in r)
        logger.info("[WebSearch] query=%r provider=%s n=%d", query, provider, n_ok)
        self._record_history(query, provider, results)
        return results

    def _record_history(self, query: str, provider: str, results: List[Dict[str, Any]]) -> None:
        """Append one audit record (RAM TTL session 不落盤，此為稽核落地處)。"""
        try:
            _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
            if _HISTORY_PATH.exists() and _HISTORY_PATH.stat().st_size > _HISTORY_ROTATE_BYTES:
                _HISTORY_PATH.replace(_HISTORY_PATH.with_suffix(".jsonl.old"))
            urls = [
                r.get("url")
                for r in results[:5]
                if isinstance(r, dict) and r.get("url") and not r.get("error")
            ]
            error = next(
                (r.get("error") for r in results if isinstance(r, dict) and r.get("error")),
                None,
            )
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "query": query,
                "provider": provider,
                "n_results": len([u for u in urls if u]),
                "urls": urls,
                "error": error,
            }
            with open(_HISTORY_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning("web_search history append failed: %s", e, exc_info=True)

    _ANCHOR_RE = re.compile(r"<a\s([^>]*?)>(.*?)</a>", re.DOTALL | re.IGNORECASE)
    _HREF_ATTR_RE = re.compile(r"""href=["']([^"']+)["']""", re.IGNORECASE)
    _CLASS_ATTR_RE = re.compile(r"""class=['"]([^'"]+)['"]""", re.IGNORECASE)
    _SNIPPET_CELL_RE = re.compile(
        r"<td class=['\"]result-snippet['\"]>(.*?)</td>", re.DOTALL | re.IGNORECASE
    )

    @staticmethod
    def _clean_markup(fragment: str) -> str:
        return unescape(re.sub(r"<[^>]+>", "", fragment)).strip()

    def _parse_ddg_lite(self, html_text: str, num_results: int) -> List[Dict[str, Any]]:
        """Parse DDG Lite HTML → [{title, url, snippet}]（snippet 配對真抓）。

        實測（2026-10-18）：Lite 逐結果交錯
        ``<a class='result-link'>`` 與 ``<td class='result-snippet'>``
        ——舊解析硬寫 snippet=""（10 個摘要儲存格全被丟掉）。錨定
        result-link 主解析 + 摘要 cursor 配對；無 result-link 時回退
        裸錨點（R29 錄製夾具路徑，摘要缺失僅降級為空）。
        """
        snippets = [
            (m.start(), self._clean_markup(m.group(1)))
            for m in self._SNIPPET_CELL_RE.finditer(html_text)
        ]
        anchors: List[Tuple[int, int, str, str, bool]] = []
        for m in self._ANCHOR_RE.finditer(html_text):
            attrs, inner = m.group(1), m.group(2)
            href_m = self._HREF_ATTR_RE.search(attrs)
            if not href_m:
                continue
            url = href_m.group(1)
            if url.startswith("/") or "duckduckgo.com" in url or not url.startswith("http"):
                continue
            cls_m = self._CLASS_ATTR_RE.search(attrs)
            is_result = bool(cls_m and "result-link" in cls_m.group(1))
            anchors.append((m.start(), m.end(), url, self._clean_markup(inner), is_result))
        primary = [a for a in anchors if a[4]]
        used = primary if primary else anchors
        # 摘要 cursor：每個錚定錨點消費其後第一個未用儲存格（交錯序配對）
        results: List[Dict[str, Any]] = []
        snip_i = 0
        for start, end, url, title, _cls in used:
            while snip_i < len(snippets) and snippets[snip_i][0] < end:
                snip_i += 1
            snippet = ""
            if snip_i < len(snippets):
                snippet = snippets[snip_i][1]
                snip_i += 1
            if len(title) < 2:
                continue
            results.append({"title": title, "url": url, "snippet": snippet[:400]})
            if len(results) >= num_results:
                break
        return results

    def _ddg_search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        try:
            data = urllib.parse.urlencode({"q": query, "kl": ""}).encode()
            req = urllib.request.Request(
                self.ddg_url,
                data=data,
                headers={
                    "User-Agent": self.user_agent,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            with urllib.request.urlopen(
                req, timeout=self.timeout
            ) as resp:  # nosec B310 - scheme-validated in __init__
                html_text = resp.read().decode("utf-8", errors="replace")
            return self._parse_ddg_lite(html_text, num_results)
        except Exception as e:
            logger.warning(f"DDG search failed: {e}", exc_info=True)
            return [{"error": safe_error(e)}]

    def _wiki_endpoint(self, query: str) -> tuple:
        """(api_url, host) — 中文查詢走 zh.wikipedia；自訂 config 優先。"""
        if self.wiki_api != _WIKI_API:
            host = urllib.parse.urlparse(self.wiki_api).netloc or "en.wikipedia.org"
            return self.wiki_api, host
        if _CJK_RE.search(query or ""):
            return _WIKI_API_ZH, "zh.wikipedia.org"
        return self.wiki_api, "en.wikipedia.org"

    def _wiki_search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        try:
            api, host = self._wiki_endpoint(query)
            params = urllib.parse.urlencode(
                {
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "srlimit": num_results,
                    "format": "json",
                }
            )
            url = f"{api}?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(
                req, timeout=self.timeout
            ) as resp:  # nosec B310 - scheme-validated in __init__
                data = json.loads(resp.read().decode())
            results = []
            for item in data.get("query", {}).get("search", []):
                title = item.get("title", "")
                snippet = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
                results.append(
                    {
                        "title": title,
                        "url": f"https://{host}/wiki/{urllib.parse.quote(title)}",
                        "snippet": snippet,
                    }
                )
            return results
        except Exception as e:
            logger.warning(f"Wikipedia search failed: {e}", exc_info=True)
            return [{"error": safe_error(e)}]


__all__ = ["WebSearchTool", "read_recent_history"]
