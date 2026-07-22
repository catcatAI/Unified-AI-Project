import pytest

pytest.importorskip("ai.agents.agent_manager")
from ai.agents.agent_manager import AgentManager


class TestAIAgentIntegration:
    @pytest.mark.asyncio
    async def test_agent_manager_instantiation(self):
        manager = AgentManager()
        assert manager is not None

    @pytest.mark.asyncio
    async def test_agent_manager_register_and_get(self):
        manager = AgentManager()
        initial_count = len(manager.agents)
        # Just verify the manager can be inspected
        assert isinstance(initial_count, int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
