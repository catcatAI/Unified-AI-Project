"""WebSearchAgent 重寫（#5）— 委託 WebSearchTool 消雙實裝、真文字摘要、刪假趨勢。

audit 2026-10-18：舊自帶 DDG HTML regex（rel="nofollow" class="result__a"）
對真實 DDG 0 命中（R29 同源缺陷）；get_search_trends 回傳 dummy_value =
len(topic)*10 假數據；fetch_content 摘要為裸 HTML 前 500 字元。
"""

from types import SimpleNamespace


class TestDelegateToWebSearchTool:
    def test_search_delegates_with_normalized_shape(self, monkeypatch):
        from ai.agents.specialized.web_search_agent import WebSearchAgent

        agent = WebSearchAgent()
        seen = {}

        class FakeTool:
            def search(self, query, num_results=5):
                seen["query"] = query
                seen["num_results"] = num_results
                return [
                    {"title": "T1", "url": "https://a.example/1", "snippet": "s1"},
                    {"error": "one failed"},
                    {"title": "T2", "url": "https://b.example/2", "snippet": "s2"},
                ]

        monkeypatch.setattr(agent, "_tool", lambda: FakeTool())
        out = agent.search("python tutorial", num_results=3)
        assert seen["query"] == "python tutorial"
        assert seen["num_results"] == 3
        assert out["status"] == "success"
        assert out["result_count"] == 2
        assert [r["url"] for r in out["results"]] == ["https://a.example/1", "https://b.example/2"]

    def test_search_all_errors_is_error(self, monkeypatch):
        from ai.agents.specialized.web_search_agent import WebSearchAgent

        agent = WebSearchAgent()

        class FakeTool:
            def search(self, query, num_results=5):
                return [{"error": "network down"}]

        monkeypatch.setattr(agent, "_tool", lambda: FakeTool())
        out = agent.search("x")
        assert out["status"] == "error"
        assert "network down" in out["message"]

    def test_empty_query_error(self):
        from ai.agents.specialized.web_search_agent import WebSearchAgent

        out = WebSearchAgent().search("")
        assert out["status"] == "error"

    def test_fake_trends_method_removed(self):
        from ai.agents.specialized.web_search_agent import WebSearchAgent

        assert not hasattr(WebSearchAgent(), "get_search_trends")


class TestFetchContentTextSummary:
    def _fetch_with(self, monkeypatch, html):
        from ai.agents.specialized import web_search_agent as wsa

        class FakeResp:
            def __init__(self, data, content_type="text/html; charset=utf-8"):
                self._data = data.encode("utf-8")
                self.headers = {"Content-Type": content_type}

            def read(self):
                return self._data

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        monkeypatch.setattr(wsa.urllib.request, "urlopen", lambda req, timeout=15: FakeResp(html))
        return wsa.WebSearchAgent().fetch_content("https://example.com/page")

    def test_script_style_and_tags_stripped(self, monkeypatch):
        html = (
            "<html><head><script>var x='secret-token';</script>"
            "<style>.a{color:red}</style></head>"
            "<body><h1>Brave Search API</h1><p>Free tier 2,000 queries/month.</p></body></html>"
        )
        out = self._fetch_with(monkeypatch, html)
        assert out["status"] == "success"
        summary = out["content_summary"]
        assert "Brave Search API" in summary
        assert "2,000 queries" in summary
        assert "<" not in summary
        assert "secret-token" not in summary
        assert "color:red" not in summary

    def test_whitespace_collapsed(self, monkeypatch):
        out = self._fetch_with(monkeypatch, "<body>a\n\n  b\tc</body>")
        assert out["content_summary"] == "a b c"

    def test_fetch_error_status(self, monkeypatch):
        from ai.agents.specialized import web_search_agent as wsa

        def _boom(req, timeout=15):
            raise OSError("refused")

        monkeypatch.setattr(wsa.urllib.request, "urlopen", _boom)
        out = wsa.WebSearchAgent().fetch_content("https://example.com/x")
        assert out["status"] == "error"


class TestHandleRequestDispatch:
    def test_url_routes_to_fetch(self, monkeypatch):
        from ai.agents.specialized.web_search_agent import WebSearchAgent

        agent = WebSearchAgent()
        monkeypatch.setattr(
            agent,
            "fetch_content",
            lambda url: {"status": "success", "url": url},
        )
        monkeypatch.setattr(
            agent, "search", lambda q, num_results=5: {"status": "success", "query": q}
        )
        out = agent.handle_request("看看 https://example.com/doc 的內容")
        assert out["url"] == "https://example.com/doc"

    def test_plain_text_routes_to_search(self, monkeypatch):
        from ai.agents.specialized.web_search_agent import WebSearchAgent

        agent = WebSearchAgent()
        monkeypatch.setattr(
            agent,
            "fetch_content",
            lambda url: {"status": "success", "url": url},
        )
        monkeypatch.setattr(
            agent, "search", lambda q, num_results=5: {"status": "success", "query": q}
        )
        out = agent.handle_request("free tier pricing of Brave Search API")
        assert out["query"] == "free tier pricing of Brave Search API"

    def test_empty_request_error(self):
        from ai.agents.specialized.web_search_agent import WebSearchAgent

        assert WebSearchAgent().handle_request("  ")["status"] == "error"


class TestWiredContractUnchanged:
    """tests/ai/agents/test_unreachable_agents_wired.py 依賴的簽名不可破。"""

    def test_fetch_content_accepts_url_kwarg_and_returns_dict(self):
        from ai.agents.specialized.web_search_agent import WebSearchAgent

        agent = WebSearchAgent()
        out = agent.fetch_content(url="https://127.0.0.1:9/never")  # monkeypatched in wired test
        assert isinstance(out, dict)
        assert "status" in out

    def test_search_signature_has_num_results(self):
        import inspect

        from ai.agents.specialized.web_search_agent import WebSearchAgent

        sig = inspect.signature(WebSearchAgent.search)
        assert "query" in sig.parameters
        assert "num_results" in sig.parameters

    def test_is_available_true(self):
        from ai.agents.specialized.web_search_agent import WebSearchAgent

        assert WebSearchAgent().is_available() is True
