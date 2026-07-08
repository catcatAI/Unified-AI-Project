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
