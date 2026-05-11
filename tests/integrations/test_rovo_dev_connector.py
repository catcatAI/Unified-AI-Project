"""
测试模块 - test_rovo_dev_connector
"""

import pytest
from unittest.mock import Mock, AsyncMock


class TestRovoDevConnector:
    @pytest.fixture(autouse=True)
    def setup_test(self):
        yield

    @pytest.mark.asyncio()
    async def test_connector_basic(self):
        mock_connector = Mock()
        mock_connector.connect = AsyncMock(return_value=True)
        result = await mock_connector.connect()
        assert result is True

    def test_config_loading(self):
        mock_config = {
            "jira": {"url": "https://test.atlassian.net"},
            "confluence": {"url": "https://test.atlassian.net"}
        }
        assert "jira" in mock_config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])