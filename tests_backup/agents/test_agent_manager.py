"""
测试模块 - test_agent_manager

自动生成的测试模块,用于验证系统功能。
"""

import pytest
import asyncio
import sys
from pathlib import Path

# 添加源代码路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'apps' / 'backend' / 'src'))

from unittest.mock import Mock, AsyncMock
from ai.agents.agent_manager import AgentManager
from ai.agents.base.base_agent import BaseAgent

@pytest.fixture
def agent_manager():
    """创建AgentManager实例"""
    return AgentManager()

@pytest.fixture
def mock_agent():
    """创建模拟代理"""
    agent = Mock(spec=BaseAgent)
    agent.agent_id = "test_agent_001"
    agent.name = "Test Agent"
    agent.status = "idle"
    agent.start = AsyncMock(return_value=True)
    agent.stop = AsyncMock(return_value=True)
    agent.get_status = Mock(return_value={"status": "idle"})
    return agent

class TestAgentManager:
    """AgentManager单元测试"""

    def test_init(self, agent_manager) -> None:
        """测试初始化"""
        assert agent_manager is not None
        assert hasattr(agent_manager, 'agents')
        assert hasattr(agent_manager, 'agent_factories')
        assert len(agent_manager.agents) == 0

    def test_register_agent_factory(self, agent_manager) -> None:
        """测试注册代理工厂"""
        factory = Mock()
        agent_manager.register_agent_factory("test_agent", factory)
        assert "test_agent" in agent_manager.agent_factories
        assert agent_manager.agent_factories["test_agent"] == factory

    @pytest.mark.asyncio
    async def test_create_agent(self, agent_manager) -> None:
        """测试创建代理"""
        factory = Mock()
        mock_agent_instance = Mock(spec=BaseAgent)
        mock_agent_instance.agent_id = "test_agent_001"
        factory.return_value = mock_agent_instance
        
        agent_manager.register_agent_factory("test_agent", factory)
        agent = await agent_manager.create_agent("test_agent", "Test Agent")
        
        assert agent is not None
        assert agent.agent_id == "test_agent_001"
        factory.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_agent(self, agent_manager, mock_agent) -> None:
        """测试添加代理"""
        result = await agent_manager.add_agent(mock_agent)
        assert result is True
        assert mock_agent.agent_id in agent_manager.agents
        assert agent_manager.agents[mock_agent.agent_id] == mock_agent

    @pytest.mark.asyncio
    async def test_remove_agent(self, agent_manager, mock_agent) -> None:
        """测试移除代理"""
        await agent_manager.add_agent(mock_agent)
        assert mock_agent.agent_id in agent_manager.agents
        
        result = await agent_manager.remove_agent(mock_agent.agent_id)
        assert result is True
        assert mock_agent.agent_id not in agent_manager.agents

    @pytest.mark.asyncio
    async def test_get_agent(self, agent_manager, mock_agent) -> None:
        """测试获取代理"""
        await agent_manager.add_agent(mock_agent)
        
        agent = agent_manager.get_agent(mock_agent.agent_id)
        assert agent is not None
        assert agent.agent_id == mock_agent.agent_id

    def test_get_agent_not_found(self, agent_manager) -> None:
        """测试获取不存在的代理"""
        agent = agent_manager.get_agent("non_existent_agent")
        assert agent is None

    @pytest.mark.asyncio
    async def test_start_agent(self, agent_manager, mock_agent) -> None:
        """测试启动代理"""
        await agent_manager.add_agent(mock_agent)
        
        result = await agent_manager.start_agent(mock_agent.agent_id)
        assert result is True
        mock_agent.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_agent(self, agent_manager, mock_agent) -> None:
        """测试停止代理"""
        await agent_manager.add_agent(mock_agent)
        
        result = await agent_manager.stop_agent(mock_agent.agent_id)
        assert result is True
        mock_agent.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_all_agents(self, agent_manager, mock_agent) -> None:
        """测试启动所有代理"""
        mock_agent2 = Mock(spec=BaseAgent)
        mock_agent2.agent_id = "test_agent_002"
        mock_agent2.start = AsyncMock(return_value=True)
        
        await agent_manager.add_agent(mock_agent)
        await agent_manager.add_agent(mock_agent2)
        
        results = await agent_manager.start_all_agents()
        assert len(results) == 2
        mock_agent.start.assert_called_once()
        mock_agent2.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_all_agents(self, agent_manager, mock_agent) -> None:
        """测试停止所有代理"""
        mock_agent2 = Mock(spec=BaseAgent)
        mock_agent2.agent_id = "test_agent_002"
        mock_agent2.stop = AsyncMock(return_value=True)
        
        await agent_manager.add_agent(mock_agent)
        await agent_manager.add_agent(mock_agent2)
        
        results = await agent_manager.stop_all_agents()
        assert len(results) == 2
        mock_agent.stop.assert_called_once()
        mock_agent2.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_agents(self, agent_manager, mock_agent) -> None:
        """测试列出所有代理"""
        await agent_manager.add_agent(mock_agent)
        
        agents = agent_manager.list_agents()
        assert len(agents) == 1
        assert mock_agent.agent_id in agents

    @pytest.mark.asyncio
    async def test_get_agent_status(self, agent_manager, mock_agent) -> None:
        """测试获取代理状态"""
        await agent_manager.add_agent(mock_agent)
        
        status = agent_manager.get_agent_status(mock_agent.agent_id)
        assert status is not None
        assert "status" in status
        mock_agent.get_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_lifecycle(self, agent_manager) -> None:
        """测试代理生命周期"""
        factory = Mock()
        mock_agent_instance = Mock(spec=BaseAgent)
        mock_agent_instance.agent_id = "lifecycle_test_agent"
        mock_agent_instance.start = AsyncMock(return_value=True)
        mock_agent_instance.stop = AsyncMock(return_value=True)
        mock_agent_instance.get_status = Mock(return_value={"status": "running"})
        factory.return_value = mock_agent_instance
        
        agent_manager.register_agent_factory("lifecycle_test", factory)
        
        # 创建代理
        agent = await agent_manager.create_agent("lifecycle_test", "Lifecycle Test Agent")
        assert agent is not None
        
        # 添加代理
        result = await agent_manager.add_agent(agent)
        assert result is True
        
        # 启动代理
        result = await agent_manager.start_agent(agent.agent_id)
        assert result is True
        
        # 检查状态
        status = agent_manager.get_agent_status(agent.agent_id)
        assert status is not None
        assert status["status"] == "running"
        
        # 停止代理
        result = await agent_manager.stop_agent(agent.agent_id)
        assert result is True
        
        # 移除代理
        result = await agent_manager.remove_agent(agent.agent_id)
        assert result is True
        assert agent.agent_id not in agent_manager.agents
