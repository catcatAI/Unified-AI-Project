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
