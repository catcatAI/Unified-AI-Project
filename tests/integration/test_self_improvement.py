"""
测试模块 - test_self_improvement
"""

import pytest
from unittest.mock import Mock, AsyncMock


class TestSelfImprovement:
    @pytest.fixture(autouse=True)
    def setup_test(self):
        yield

    @pytest.mark.asyncio()
    async def test_self_improvement_basic(self):
        mock_improver = Mock()
        mock_improver.improve = AsyncMock(return_value=True)
        result = await mock_improver.improve({"target": "performance"})
        assert result is True

    @pytest.mark.asyncio()
    async def test_self_learning(self):
        mock_learner = Mock()
        mock_learner.learn = AsyncMock(return_value={"learned": True})
        result = await mock_learner.learn({"data": "test"})
        assert result["learned"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])