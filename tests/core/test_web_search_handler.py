"""P8-1b — WebSearchHandler unit tests"""

import asyncio


class TestWebSearchHandler:

    def setup_method(self):
        from services.handlers.web_search_handler import WebSearchHandler

        self.handler = WebSearchHandler()

    def test_handler_instantiated(self):
        assert self.handler is not None
        assert hasattr(self.handler, "handle")

    def test_extract_query_simple(self):
        q = self.handler._extract_query("搜尋 Python 教學")
        assert q == "Python 教學"

    def test_extract_query_google_prefix(self):
        q = self.handler._extract_query("google 天氣")
        assert q == "天氣"

    def test_extract_query_lookup(self):
        q = self.handler._extract_query("lookup AI news")
        assert q == "AI news"

    def test_extract_query_empty(self):
        q = self.handler._extract_query("搜尋")
        assert q is None

    def test_extract_query_chinese_prefix(self):
        q = self.handler._extract_query("幫我查台北天氣")
        assert q == "台北天氣"

    def test_extract_query_about_prefix(self):
        q = self.handler._extract_query("關於 Python 的歷史")
        assert q == "Python 的歷史"

    def test_handle_no_query(self):
        result = asyncio.run(self.handler.handle("搜尋", "web_search"))
        assert "搜尋" in result


class TestExtractQueryCorruptionRegression:
    """audit 2026-10-18：舊 re.sub 未錨定——中段「查/找/Search」被摳掉。

    「幫我調查 X Search API」曾變「幫我調 X  API」，搜尋拿殘缺查詢跑。
    """

    def setup_method(self):
        from services.handlers.web_search_handler import WebSearchHandler

        self.handler = WebSearchHandler()

    def test_investigate_preserves_body(self):
        q = self.handler._extract_query("幫我調查 DuckDuckGo vs Brave Search API 差異")
        assert q == "DuckDuckGo vs Brave Search API 差異"

    def test_mid_string_search_untouched(self):
        q = self.handler._extract_query("DuckDuckGo Search API怎麼申請")
        assert q == "DuckDuckGo Search API怎麼申請"

    def test_mid_string_cha_untouched(self):
        q = self.handler._extract_query("比較查號台與搜尋引擎的差異")
        assert q == "比較查號台與搜尋引擎的差異"

    def test_investigate_single_char_verb_body_intact(self):
        q = self.handler._extract_query("幫我調查氣象局網站")
        assert q == "氣象局網站"


class TestHandleResponseClean:
    """#4：回應字串不再自帶裝飾性「（網路搜尋）」前綴（detail 已由
    _gate_execution_response 的「（）」包裹，會變「（（網路搜尋））」）。"""

    class FakeTool:
        def __init__(self, results):
            self._results = results
            self.queries = []

        def search(self, query, num_results=5):
            self.queries.append(query)
            return self._results

    @staticmethod
    def _no_fetch(monkeypatch):
        import core.tools.research_pipeline as rp

        monkeypatch.setattr(rp, "fetch_page_text", lambda *a, **k: None)

    def _handle_with(self, monkeypatch, results, text="搜尋 python tutorial"):
        from services.handlers.web_search_handler import WebSearchHandler

        self._no_fetch(monkeypatch)
        h = WebSearchHandler()
        fake = self.FakeTool(results)
        h._tool = fake
        return asyncio.run(h.handle(text, "web_search"))

    def test_success_no_double_paren(self, monkeypatch):
        out = self._handle_with(
            monkeypatch,
            [
                {"title": "T1", "url": "https://a.example/1"},
                {"title": "T2", "url": "https://b.example/2"},
            ],
        )
        assert "（網路搜尋）" not in out
        assert "搜尋結果" in out
        assert "https://a.example/1" in out

    def test_error_message_clean(self, monkeypatch):
        out = self._handle_with(monkeypatch, [{"error": "boom"}])
        assert "（" not in out
        assert "搜尋時發生錯誤" in out

    def test_empty_message_clean(self, monkeypatch):
        out = self._handle_with(monkeypatch, [])
        assert "沒有找到" in out
        assert "（" not in out

    def test_research_answer_has_facts_when_fetch_succeeds(self, monkeypatch):
        """抓到內文 → 答案含【關鍵事實】與抓取數（非連結清單）。"""
        import core.tools.research_pipeline as rp
        from services.handlers.web_search_handler import WebSearchHandler

        page = (
            "The Brave Search API free tier allows 2,000 queries per month for "
            "developers. After that the paid plan starts at 3 USD per thousand queries. "
            "DuckDuckGo does not offer a public search API."
        )
        monkeypatch.setattr(rp, "fetch_page_text", lambda *a, **k: page)
        h = WebSearchHandler()
        h._tool = self.FakeTool(
            [{"title": "Brave pricing", "url": "https://brave.com/pricing", "snippet": ""}]
        )
        out = asyncio.run(h.handle("搜尋 Brave Search API 免費額度", "web_search"))
        assert "【關鍵事實】" in out
        assert "2,000 queries" in out
        assert "【來源（按可信度）】" in out
        assert "（研究摘要：1/1 頁內文）" in out
