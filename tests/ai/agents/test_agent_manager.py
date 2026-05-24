"""Tests for AgentManager."""

import pytest
from unittest.mock import Mock, AsyncMock

from ai.agents.agent_manager import AgentManager


@pytest.fixture
def agent_manager():
    """Create an AgentManager instance with router disabled for testing."""
    return AgentManager(enable_router=False, enable_process_agents=False)


@pytest.fixture
def mock_agent():
    """Create a mock agent with async methods."""
    agent = Mock()
    agent.agent_id = "test_agent_001"
    agent.start = AsyncMock(return_value=True)
    agent.stop = AsyncMock(return_value=True)
    agent.get_status = Mock(return_value={"status": "active"})
    return agent


class TestAgentManagerInit:
    """Tests for AgentManager initialization."""

    def test_init_defaults(self):
        """Test default initialization creates expected data structures."""
        manager = AgentManager(enable_router=False, enable_process_agents=False)
        assert manager.agents == {}
        assert manager.agent_factories == {}
        assert manager.active_agents == {}
        assert manager.enable_router is False
        assert manager.enable_process_agents is False

    def test_init_with_custom_python(self):
        """Test initialization with custom python executable path."""
        manager = AgentManager(
            python_executable="/custom/python/bin",
            enable_router=False,
            enable_process_agents=False,
        )
        assert manager.python_executable == "/custom/python/bin"

    def test_init_with_state_manager(self):
        """Test initialization with a state manager."""
        state_manager = Mock()
        manager = AgentManager(
            enable_router=False,
            enable_process_agents=False,
            state_manager=state_manager,
        )
        assert manager.state_manager is state_manager


class TestAgentManagerRegister:
    """Tests for agent registration (add, remove, list, get)."""

    @pytest.mark.asyncio
    async def test_add_agent(self, agent_manager, mock_agent):
        """Test adding a single agent to the manager."""
        result = await agent_manager.add_agent(mock_agent)
        assert result is True
        assert mock_agent.agent_id in agent_manager.agents
        assert agent_manager.agents[mock_agent.agent_id] is mock_agent

    @pytest.mark.asyncio
    async def test_add_duplicate_agent_overwrites(self, agent_manager, mock_agent):
        """Test adding a duplicate agent_id overwrites the previous entry."""
        await agent_manager.add_agent(mock_agent)
        replacement = Mock()
        replacement.agent_id = "test_agent_001"
        result = await agent_manager.add_agent(replacement)
        assert result is True
        assert agent_manager.agents["test_agent_001"] is replacement
        assert len(agent_manager.agents) == 1

    @pytest.mark.asyncio
    async def test_remove_agent(self, agent_manager, mock_agent):
        """Test removing a registered agent returns True and removes it."""
        await agent_manager.add_agent(mock_agent)
        result = await agent_manager.remove_agent(mock_agent.agent_id)
        assert result is True
        assert mock_agent.agent_id not in agent_manager.agents

    @pytest.mark.asyncio
    async def test_remove_nonexistent_agent(self, agent_manager):
        """Test removing an unregistered agent returns False."""
        result = await agent_manager.remove_agent("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_agents(self, agent_manager, mock_agent):
        """Test list_agents returns all registered agent IDs."""
        await agent_manager.add_agent(mock_agent)
        agents = agent_manager.list_agents()
        assert len(agents) == 1
        assert mock_agent.agent_id in agents

    @pytest.mark.asyncio
    async def test_list_agents_empty(self, agent_manager):
        """Test list_agents returns empty list when no agents registered."""
        assert agent_manager.list_agents() == []

    def test_get_agent(self, agent_manager):
        """Test get_agent returns the agent object by ID."""
        agent = Mock()
        agent.agent_id = "direct_001"
        agent_manager.agents["direct_001"] = agent
        assert agent_manager.get_agent("direct_001") is agent

    def test_get_agent_not_found(self, agent_manager):
        """Test get_agent returns None for non-existent agent ID."""
        assert agent_manager.get_agent("nonexistent") is None

    def test_register_agent_factory(self, agent_manager):
        """Test registering an agent factory by type."""
        factory = Mock()
        agent_manager.register_agent_factory("test_type", factory)
        assert "test_type" in agent_manager.agent_factories
        assert agent_manager.agent_factories["test_type"] is factory

    @pytest.mark.asyncio
    async def test_create_agent_from_factory(self, agent_manager):
        """Test creating an agent from a registered factory."""
        factory = Mock()
        created = Mock()
        created.agent_id = "created_001"
        factory.return_value = created
        agent_manager.register_agent_factory("test_type", factory)
        agent = await agent_manager.create_agent("test_type", "TestAgent")
        assert agent is created
        factory.assert_called_once_with("TestAgent")

    @pytest.mark.asyncio
    async def test_create_agent_unregistered_type(self, agent_manager):
        """Test create_agent returns None for unregistered type."""
        agent = await agent_manager.create_agent("unknown_type", "Test")
        assert agent is None


class TestAgentManagerLifecycle:
    """Tests for agent lifecycle management (start, stop, status)."""

    @pytest.mark.asyncio
    async def test_start_agent(self, agent_manager, mock_agent):
        """Test start_agent calls agent.start() and returns True."""
        await agent_manager.add_agent(mock_agent)
        result = await agent_manager.start_agent(mock_agent.agent_id)
        assert result is True
        mock_agent.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_nonexistent_agent(self, agent_manager):
        """Test start_agent returns False for non-existent agent."""
        result = await agent_manager.start_agent("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_stop_agent(self, agent_manager, mock_agent):
        """Test stop_agent calls agent.stop() and returns True."""
        await agent_manager.add_agent(mock_agent)
        result = await agent_manager.stop_agent(mock_agent.agent_id)
        assert result is True
        mock_agent.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_nonexistent_agent(self, agent_manager):
        """Test stop_agent returns False for non-existent agent."""
        result = await agent_manager.stop_agent("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async     def test_get_agent_status(self, agent_manager, mock_agent):
        """Test get_agent_status returns the agent's status dict."""
        await agent_manager.add_agent(mock_agent)
        status = agent_manager.get_agent_status(mock_agent.agent_id)
        assert status["status"] == "active"
        mock_agent.get_status.assert_called_once()

    def test_get_agent_status_nonexistent(self, agent_manager):
        """Test get_agent_status returns None for non-existent agent."""
        assert agent_manager.get_agent_status("nonexistent") is None

    @pytest.mark.asyncio
    async def test_start_all_agents(self, agent_manager):
        """Test start_all_agents starts every registered agent."""
        a1 = Mock()
        a1.agent_id = "agent_001"
        a1.start = AsyncMock(return_value=True)
        a2 = Mock()
        a2.agent_id = "agent_002"
        a2.start = AsyncMock(return_value=True)
        await agent_manager.add_agent(a1)
        await agent_manager.add_agent(a2)
        results = await agent_manager.start_all_agents()
        assert len(results) == 2
        a1.start.assert_called_once()
        a2.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_all_agents(self, agent_manager, mock_agent):
        """Test stop_all_agents stops every registered agent."""
        await agent_manager.add_agent(mock_agent)
        results = await agent_manager.stop_all_agents()
        assert len(results) == 1
        mock_agent.stop.assert_called_once()

    def test_get_available_agents(self, agent_manager):
        """Test get_available_agents returns discovered agent names."""
        agents = agent_manager.get_available_agents()
        assert isinstance(agents, list)

    def test_check_agent_health_not_active(self, agent_manager):
        """Test check_agent_health returns False when agent not in active_agents."""
        assert agent_manager.check_agent_health("nonexistent") is False
