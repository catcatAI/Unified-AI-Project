"""
测试模块 - test_example_integration
"""

import pytest
from unittest.mock import Mock, AsyncMock


class TestExampleIntegration:
    @pytest.fixture(autouse=True)
    def setup_test(self):
        yield

    @pytest.mark.asyncio()
    async def test_example_integration(self):
        mock_result = await AsyncMock(return_value={"status": "success"})()
        assert mock_result["status"] == "success"

    @pytest.mark.asyncio()
    async def test_example_async_operation(self):
        async def mock_async_op():
            return {"data": "test"}
        result = await mock_async_op()
        assert result["data"] == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])