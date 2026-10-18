"""Tests for core/tools/web_search_tool.py — matches actual WebSearchTool API"""

import json

import pytest


class TestWebSearchTool:
    """Tests for WebSearchTool"""

    @pytest.fixture(autouse=True)
    def _no_repo_history_pollution(self, tmp_path, monkeypatch):
        """真打網路的 search() 現會 append jsonl——導向 tmp，勿污染 repo data/。"""
        from core.tools import web_search_tool as wst

        monkeypatch.setattr(wst, "_HISTORY_PATH", tmp_path / "web_search.jsonl")

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


class TestWikiLanguage:
    """#6：中文查詢走 zh.wikipedia（原一律英語 API，中文備援語種不對）。"""

    def test_cjk_query_selects_zh(self):
        from core.tools.web_search_tool import WebSearchTool

        tool = WebSearchTool()
        api, host = tool._wiki_endpoint("台北天氣政")
        assert api == "https://zh.wikipedia.org/w/api.php"
        assert host == "zh.wikipedia.org"

    def test_english_query_stays_en(self):
        from core.tools.web_search_tool import WebSearchTool

        tool = WebSearchTool()
        api, host = tool._wiki_endpoint("taipei weather")
        assert api == "https://en.wikipedia.org/w/api.php"
        assert host == "en.wikipedia.org"

    def test_config_override_wins_with_derived_host(self):
        from core.tools.web_search_tool import WebSearchTool

        tool = WebSearchTool()
        tool.wiki_api = "https://custom.example/w/api.php"
        api, host = tool._wiki_endpoint("中文查詢")
        assert api == "https://custom.example/w/api.php"
        assert host == "custom.example"


class TestSearchHistoryAudit:
    """#7：TTL RAM session 是研究結果唯一落地處 → append-only jsonl 稽核軌跡。"""

    DDG_HTML = (
        "<html><body>"
        '<a href="https://www.cwa.gov.tw/V8/C/">氣象署</a>'
        '<a href="https://www.accuweather.com/zh/tw/taipei">臺北天氣</a>'
        "</body></html>"
    )

    @pytest.fixture
    def history_path(self, tmp_path, monkeypatch):
        from core.tools import web_search_tool as wst

        path = tmp_path / "research" / "web_search.jsonl"
        monkeypatch.setattr(wst, "_HISTORY_PATH", path)
        return path

    def _tool_with_ddg(self, monkeypatch, html_text=None, fail=False):
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

        if fail:

            def _boom(req, timeout=10):
                raise OSError("network down")

            monkeypatch.setattr(wst.urllib.request, "urlopen", _boom)
        else:
            monkeypatch.setattr(
                wst.urllib.request, "urlopen", lambda req, timeout=10: FakeResp(html_text)
            )
        return wst.WebSearchTool()

    def test_search_appends_record(self, history_path, monkeypatch):
        from core.tools.web_search_tool import read_recent_history

        tool = self._tool_with_ddg(monkeypatch, self.DDG_HTML)
        results = tool.search("台北天氣", 3)
        assert results
        records = read_recent_history(10)
        assert len(records) == 1
        rec = records[0]
        assert rec["query"] == "台北天氣"
        assert rec["provider"] == "duckduckgo"
        assert rec["n_results"] == 2
        assert "https://www.cwa.gov.tw/V8/C/" in rec["urls"]
        assert rec["timestamp"]
        # jsonl 真實落盤、逐行可解析
        raw = history_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(raw) == 1
        assert json.loads(raw[0])["query"] == "台北天氣"

    def test_failed_search_records_error(self, history_path, monkeypatch):
        from core.tools.web_search_tool import read_recent_history

        tool = self._tool_with_ddg(monkeypatch, fail=True)
        results = tool.search("python", 3)
        assert results and results[0].get("error")
        records = read_recent_history(5)
        assert len(records) == 1
        assert records[0]["provider"] == "wikipedia"
        assert records[0]["error"]

    def test_read_recent_missing_file(self, tmp_path, monkeypatch):
        from core.tools import web_search_tool as wst

        monkeypatch.setattr(wst, "_HISTORY_PATH", tmp_path / "nope.jsonl")
        assert wst.read_recent_history(5) == []

    def test_rotation_on_size_cap(self, history_path, monkeypatch):
        from core.tools import web_search_tool as wst

        monkeypatch.setattr(wst, "_HISTORY_ROTATE_BYTES", 10)
        tool = self._tool_with_ddg(monkeypatch, self.DDG_HTML)
        tool.search("台北天氣", 3)  # 第一次寫入即超 cap
        tool.search("台北天氣", 3)  # 第二次觸發 rotate
        assert history_path.with_suffix(".jsonl.old").exists()
        assert history_path.exists()
