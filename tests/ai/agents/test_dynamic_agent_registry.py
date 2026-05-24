"""Tests for DynamicAgentRegistry."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from ai.agents.dynamic_agent_registry import DynamicAgentRegistry, RegisteredAgent


@pytest.fixture
def mock_hsp_connector():
    """Create a mock HSPConnector that tracks callback registration."""
    connector = Mock()
    connector.register_on_capability_advertisement_callback = Mock()
    return connector


@pytest.fixture
def registry(mock_hsp_connector):
    """Create a DynamicAgentRegistry with mocked HSP connector."""
    return DynamicAgentRegistry(hsp_connector=mock_hsp_connector)
class TestDynamicAgentRegistry:
    """Tests for DynamicAgentRegistry."""

    async def test_init_with_none_connector(self):
        """Test initialization with None connector does not crash."""
        reg = DynamicAgentRegistry(hsp_connector=None)
        assert reg.hsp_connector is None
        assert reg.registered_agents == {}
        assert reg.is_running is False

    async def test_init_registers_capability_callback(self, mock_hsp_connector):
        """Test that init registers the capability advertisement callback."""
        DynamicAgentRegistry(hsp_connector=mock_hsp_connector)
        mock_hsp_connector.register_on_capability_advertisement_callback.assert_called_once()

    async def test_register_agent_manually(self, registry):
        """Test manually registering an agent with capabilities."""
        await registry.register_agent_manually(
            agent_id="agent_001",
            agent_name="TestAgent",
            capabilities=[{"capability_id": "cap_1", "name": "Capability 1"}],
        )
        assert "agent_001" in registry.registered_agents
        agent = registry.registered_agents["agent_001"]
        assert agent.agent_id == "agent_001"
        assert agent.agent_name == "TestAgent"
        assert agent.status == "active"
        assert len(agent.capabilities) == 1

    async def test_register_agent_with_metadata(self, registry):
        """Test registering an agent with custom metadata."""
        await registry.register_agent_manually(
            agent_id="agent_002",
            agent_name="MetaAgent",
            capabilities=[],
            metadata={"version": "2.0", "owner": "test-suite"},
        )
        agent = registry.registered_agents["agent_002"]
        assert agent.metadata["version"] == "2.0"
        assert agent.metadata["owner"] == "test-suite"

    async def test_register_duplicate_overwrites(self, registry):
        """Test registering the same agent_id overwrites the previous entry."""
        await registry.register_agent_manually(
            agent_id="agent_001",
            agent_name="Original",
            capabilities=[],
        )
        await registry.register_agent_manually(
            agent_id="agent_001",
            agent_name="Updated",
            capabilities=[{"capability_id": "cap_new"}],
        )
        agent = registry.registered_agents["agent_001"]
        assert agent.agent_name == "Updated"
        assert len(agent.capabilities) == 1

    async def test_unregister_agent(self, registry):
        """Test unregistering an agent sets its status to offline."""
        await registry.register_agent_manually(
            agent_id="agent_001",
            agent_name="TestAgent",
            capabilities=[],
        )
        await registry.unregister_agent("agent_001")
        assert registry.registered_agents["agent_001"].status == "offline"

    async def test_unregister_nonexistent_agent(self, registry):
        """Test unregistering a non-existent agent does not raise."""
        await registry.unregister_agent("nonexistent")
        # No exception expected

    async def test_get_agent(self, registry):
        """Test get_agent returns the RegisteredAgent by ID."""
        await registry.register_agent_manually(
            agent_id="agent_001",
            agent_name="TestAgent",
            capabilities=[],
        )
        agent = await registry.get_agent("agent_001")
        assert agent.agent_id == "agent_001"
        assert agent.agent_name == "TestAgent"

    async def test_get_agent_not_found(self, registry):
        """Test get_agent returns None for non-existent agent."""
        agent = await registry.get_agent("nonexistent")
        assert agent is None

    async def test_get_all_agents(self, registry):
        """Test get_all_agents returns all registered agents."""
        await registry.register_agent_manually(
            agent_id="agent_001",
            agent_name="Agent1",
            capabilities=[],
        )
        await registry.register_agent_manually(
            agent_id="agent_002",
            agent_name="Agent2",
            capabilities=[],
        )
        agents = await registry.get_all_agents()
        assert len(agents) == 2
        ids = {a.agent_id for a in agents}
        assert ids == {"agent_001", "agent_002"}

    async def test_get_all_agents_empty(self, registry):
        """Test get_all_agents returns empty list when no agents registered."""
        agents = await registry.get_all_agents()
        assert agents == []

    async def test_get_agent_count(self, registry):
        """Test get_agent_count returns correct count."""
        await registry.register_agent_manually(
            agent_id="agent_001",
            agent_name="Agent1",
            capabilities=[],
        )
        count = await registry.get_agent_count()
        assert count == 1

    async def test_get_agent_count_empty(self, registry):
        """Test get_agent_count returns 0 when no agents registered."""
        count = await registry.get_agent_count()
        assert count == 0

    async def test_find_agents_by_capability(self, registry):
        """Test finding agents that have a specific capability."""
        await registry.register_agent_manually(
            agent_id="agent_001",
            agent_name="Agent1",
            capabilities=[{"capability_id": "cap_alpha"}],
        )
        await registry.register_agent_manually(
            agent_id="agent_002",
            agent_name="Agent2",
            capabilities=[{"capability_id": "cap_beta"}],
        )
        matching = await registry.find_agents_by_capability("cap_alpha")
        assert len(matching) == 1
        assert matching[0].agent_id == "agent_001"

    async def test_find_agents_by_capability_no_match(self, registry):
        """Test find_agents_by_capability returns empty list when no match."""
        await registry.register_agent_manually(
            agent_id="agent_001",
            agent_name="Agent1",
            capabilities=[{"capability_id": "cap_alpha"}],
        )
        matching = await registry.find_agents_by_capability("nonexistent")
        assert matching == []

    async def test_register_discovery_callback(self, registry):
        """Test registering a discovery callback adds it to the list."""
        callback = Mock()
        registry.register_discovery_callback(callback)
        assert callback in registry.discovery_callbacks

    async def test_start_registry(self, registry):
        """Test start_registry sets is_running and creates the background task."""
        assert registry.is_running is False
        await registry.start_registry()
        assert registry.is_running is True
        assert registry.registry_task is not None

    async def test_stop_registry(self, registry):
        """Test stop_registry cancels the background task."""
        await registry.start_registry()
        assert registry.is_running is True
        await registry.stop_registry()
        assert registry.is_running is False

    async def test_multiple_agents(self, registry):
        """Test registering multiple agents and retrieving them all."""
        for i in range(5):
            await registry.register_agent_manually(
                agent_id=f"agent_{i:03d}",
                agent_name=f"Agent{i}",
                capabilities=[{"capability_id": f"cap_{i}"}],
            )
        count = await registry.get_agent_count()
        assert count == 5
        all_agents = await registry.get_all_agents()
        assert len(all_agents) == 5
