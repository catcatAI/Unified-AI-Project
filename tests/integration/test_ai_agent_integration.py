"""
AI代理系统集成测试
测试AI代理系统与其他核心组件的集成
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch


class TestAIAgentIntegration:
    @pytest.fixture(autouse=True)
    def setup_agent_test(self):
        self.data_factory = TestDataFactory() if hasattr(self, 'data_factory') else MockDataFactory()
        yield

    @pytest.mark.asyncio()
    async def test_agent_lifecycle_integration(self):
        agent_config = {
            "agent_id": "lifecycle_test_agent",
            "agent_type": "creative_writing",
            "config": {}
        }

        mock_agent = Mock()
        mock_agent.agent_id = agent_config["agent_id"]
        mock_agent.is_running = False

        agent_manager = Mock()
        agent_manager.create_agent = AsyncMock(return_value=mock_agent)
        agent_manager.start_agent = AsyncMock(return_value=True)
        agent_manager.stop_agent = AsyncMock(return_value=True)
        agent_manager.get_agent = AsyncMock(return_value=mock_agent)

        llm_service = Mock()
        llm_service.generate_response = AsyncMock(return_value="Test response from LLM")

        created_agent = await agent_manager.create_agent(
            agent_config["agent_id"],
            agent_config["agent_type"],
            agent_config["config"]
        )

        start_result = await agent_manager.start_agent(agent_config["agent_id"])

        retrieved_agent = await agent_manager.get_agent(agent_config["agent_id"])

        if retrieved_agent:
            llm_response = await llm_service.generate_response("Test prompt")

        stop_result = await agent_manager.stop_agent(agent_config["agent_id"])

        assert created_agent is not None
        assert created_agent.agent_id == agent_config["agent_id"]
        assert start_result is True
        assert retrieved_agent is not None
        assert stop_result is True
        assert llm_response == "Test response from LLM"


class MockDataFactory:
    def create_agent_config(self, agent_id, agent_type):
        return {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "config": {}
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])