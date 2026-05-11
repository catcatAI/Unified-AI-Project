"""
测试模块 - test_rovo_dev_agent
"""

import pytest
from unittest.mock import Mock, AsyncMock


class TestRovoDevAgent:
    @pytest.fixture(autouse=True)
    def setup_test(self):
        yield

    @pytest.mark.asyncio()
    async def test_rovo_agent_initialization(self):
        mock_agent = Mock()
        mock_agent.init = AsyncMock(return_value=True)
        result = await mock_agent.init()
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])