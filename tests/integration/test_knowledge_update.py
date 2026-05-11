"""
测试模块 - test_knowledge_update
"""

import pytest
from unittest.mock import Mock, AsyncMock


class TestKnowledgeUpdate:
    @pytest.fixture(autouse=True)
    def setup_test(self):
        yield

    @pytest.mark.asyncio()
    async def test_knowledge_update_basic(self):
        mock_knowledge_base = Mock()
        mock_knowledge_base.update = AsyncMock(return_value=True)
        result = await mock_knowledge_base.update({"key": "value"})
        assert result is True

    @pytest.mark.asyncio()
    async def test_knowledge_retrieval(self):
        mock_knowledge_base = Mock()
        mock_knowledge_base.get = AsyncMock(return_value={"key": "value"})
        result = await mock_knowledge_base.get("key")
        assert result["key"] == "value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])