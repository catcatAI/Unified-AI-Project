"""Tests for core/tools/web_search_tool.py"""
import pytest


class TestWebSearchTool:
    """Tests for WebSearchTool"""

    def test_import(self):
        from core.tools.web_search_tool import WebSearchTool
        assert WebSearchTool is not None

    def test_instantiation_defaults(self):
        from core.tools.web_search_tool import WebSearchTool
        instance = WebSearchTool()
        assert instance.search_url_template is not None
        assert instance.user_agent is not None

    def test_search_url_template(self):
        from core.tools.web_search_tool import WebSearchTool
        instance = WebSearchTool()
        url = instance.search_url_template.format(query="test")
        assert "test" in url

    def test_search_no_requests_returns_error_list(self):
        from core.tools.web_search_tool import WebSearchTool
        import core.tools.web_search_tool as wst
        original = wst.REQUESTS_AVAILABLE
        wst.REQUESTS_AVAILABLE = False
        try:
            instance = WebSearchTool()
            result = instance.search("test")
            assert isinstance(result, list)
            assert "error" in result[0]
            assert "requests" in result[0]["error"]
        finally:
            wst.REQUESTS_AVAILABLE = original
