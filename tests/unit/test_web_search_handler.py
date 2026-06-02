"""Tests for WebSearchHandler"""
import pytest


class TestWebSearchHandler:
    """Tests for WebSearchHandler"""

    def test_import(self):
        from services.handlers.web_search_handler import WebSearchHandler
        assert WebSearchHandler is not None

    def test_instantiation(self):
        from services.handlers.web_search_handler import WebSearchHandler
        instance = WebSearchHandler()
        assert instance is not None
        assert instance._tool is None

    def test_extract_query(self):
        from services.handlers.web_search_handler import WebSearchHandler
        instance = WebSearchHandler()
        q = instance._extract_query("搜尋 Python 教學")
        assert q == "Python 教學"

    def test_extract_query_english(self):
        from services.handlers.web_search_handler import WebSearchHandler
        instance = WebSearchHandler()
        q = instance._extract_query("search quantum computing")
        assert q == "quantum computing"

    def test_extract_query_no_query(self):
        from services.handlers.web_search_handler import WebSearchHandler
        instance = WebSearchHandler()
        q = instance._extract_query("搜尋")
        assert q == "" or q is None

    def test_handle_no_query(self):
        from services.handlers.web_search_handler import WebSearchHandler
        import asyncio
        instance = WebSearchHandler()
        result = asyncio.run(instance.handle("搜尋", "web_search"))
        assert "搜尋" in result
