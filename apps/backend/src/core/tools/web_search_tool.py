"""
网络搜索工具
"""

import logging

logger = logging.getLogger(__name__)

REQUESTS_AVAILABLE = False
DEFAULT_SEARCH_URL = "https://api.duckduckgo.com/?q={query}&format=json"
DEFAULT_USER_AGENT = "AngelaAI/7.5.0"


class WebSearchTool:
    """Simple web search tool with configurable search URL and user agent."""

    def __init__(self):
        self.search_url_template = DEFAULT_SEARCH_URL
        self.user_agent = DEFAULT_USER_AGENT

    def search(self, query: str) -> list:
        """Execute a web search and return results as a list."""
        if not REQUESTS_AVAILABLE:
            return [{"error": "requests library not available"}]
        return [{"error": "requests library not available"}]
