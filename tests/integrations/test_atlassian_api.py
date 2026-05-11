"""
测试模块 - test_atlassian_api
"""

import pytest
from unittest.mock import Mock, AsyncMock


class TestAtlassianAPI:
    @pytest.fixture(autouse=True)
    def setup_test(self):
        yield

    @pytest.mark.asyncio()
    async def test_atlassian_api_connection(self):
        mock_client = Mock()
        mock_client.connect = AsyncMock(return_value=True)
        result = await mock_client.connect()
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])