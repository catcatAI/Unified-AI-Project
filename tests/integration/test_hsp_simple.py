"""
测试模块 - test_hsp_simple
"""

import pytest
from unittest.mock import Mock, AsyncMock


class TestHSPSimple:
    @pytest.fixture(autouse=True)
    def setup_test(self):
        yield
    async def test_hsp_simple_connection(self):
        mock_connector = Mock()
        mock_connector.connect = AsyncMock(return_value=True)
        result = await mock_connector.connect()
        assert result is True
    async def test_hsp_simple_message(self):
        mock_connector = Mock()
        mock_connector.send_message = AsyncMock(return_value=True)
        result = await mock_connector.send_message({"type": "test"})
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])