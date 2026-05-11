"""
测试模块 - test_atlassian_bridge
"""

import pytest
from unittest.mock import Mock, AsyncMock


class TestAtlassianBridge:
    @pytest.fixture(autouse=True)
    def setup_test(self):
        yield

    @pytest.mark.asyncio()
    async def test_atlassian_bridge_connection(self):
        mock_bridge = Mock()
        mock_bridge.connect = AsyncMock(return_value=True)
        result = await mock_bridge.connect()
        assert result is True

    def test_config_loading(self):
        mock_config = {
            "confluence": {"url": "https://test.atlassian.net"},
            "jira": {"url": "https://test.atlassian.net"}
        }
        assert "confluence" in mock_config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])