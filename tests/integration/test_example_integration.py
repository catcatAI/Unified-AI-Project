"""
测试模块 - test_example_integration
"""

from unittest.mock import AsyncMock, Mock

import pytest


class TestExampleIntegration:
    @pytest.fixture(autouse=True)
    def setup_test(self):
        yield
    async def test_example_integration(self):
        mock_result = await AsyncMock(return_value={"status": "success"})()
        assert mock_result["status"] == "success"
    async def test_example_async_operation(self):
        async def mock_async_op():
            return {"data": "test"}
        result = await mock_async_op()
        assert result["data"] == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])