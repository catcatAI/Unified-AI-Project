"""Tests for core/tools/web_search_tool.py — matches actual WebSearchTool API"""

import pytest


class TestWebSearchTool:
    """Tests for WebSearchTool"""

    def test_import(self):
        from core.tools.web_search_tool import WebSearchTool

        assert WebSearchTool is not None

    def test_instantiation_defaults(self):
        from core.tools.web_search_tool import WebSearchTool

        instance = WebSearchTool()
        assert instance.user_agent is not None
        assert len(instance.user_agent) > 0

    def test_user_agent_default(self):
        from core.tools.web_search_tool import WebSearchTool

        instance = WebSearchTool()
        assert "AngelaAI" in instance.user_agent

    def test_search_returns_list(self):
        from core.tools.web_search_tool import WebSearchTool

        instance = WebSearchTool()
        result = instance.search("test")
        assert isinstance(result, list)


class TestDdgParserRegression:
    """R29: 舊正則對真實 DDG Lite 0 命中（誤掉英文 wiki 出歌手）。

    用錄製的真實結構夾具（非線上），鎖寬容解析：氣象署/AccuWeather
    在前，站內連結與短標題丟棄。
    """

    HTML = (
        "<html><body>"
        '<a href="/dc/audit/">內部稽核</a>'
        '<a href="https://www.cwa.gov.tw/V8/C/">首頁 | 交通部中央氣象署</a>'
        '<a href="https://duckduckgo.com/y.js?uddg=x">跳轉</a>'
        '<a href="https://www.accuweather.com/zh/tw/taipei">臺北市<b>每小時天氣</b></a>'
        '<a href="https://x.example/y">x</a>'
        "</body></html>"
    )

    def _tool_with_html(self, monkeypatch, html_text):
        from core.tools import web_search_tool as wst

        class FakeResp:
            def __init__(self, data):
                self._data = data.encode("utf-8")

            def read(self):
                return self._data

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        monkeypatch.setattr(
            wst.urllib.request, "urlopen", lambda req, timeout=10: FakeResp(html_text)
        )
        return wst.WebSearchTool()

    def test_bare_anchors_parsed(self, monkeypatch):
        tool = self._tool_with_html(monkeypatch, self.HTML)
        results = tool._ddg_search("台北天氣", 5)
        urls = [r["url"] for r in results]
        assert "https://www.cwa.gov.tw/V8/C/" in urls
        assert "https://www.accuweather.com/zh/tw/taipei" in urls
        assert any("中央氣象" in r["title"] for r in results)
        assert any("每小時天氣" in r["title"] for r in results)

    def test_internal_and_short_dropped(self, monkeypatch):
        tool = self._tool_with_html(monkeypatch, self.HTML)
        results = tool._ddg_search("台北天氣", 5)
        urls = [r["url"] for r in results]
        assert not any("duckduckgo.com" in u for u in urls)
        assert not any(u.startswith("/") for u in urls)
        assert all(len(r["title"]) >= 2 for r in results)
