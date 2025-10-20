"""
AI代理系统集成测试
测试AI代理系统与其他核心组件的集成
"""

import pytest
from apps.backend.tests.integration.base_test import SystemIntegrationTest
from apps.backend.tests.integration.test_data_factory import TestDataFactory


class TestAIAgentIntegration(SystemIntegrationTest):
    """AI代理系统集成测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_agent_test(self, setup_system_test):
        """设置代理测试"""
        self.data_factory = TestDataFactory()
        yield
    
    @pytest.mark.system_integration
    @pytest.mark.asyncio
    async def test_agent_lifecycle_integration(self) -> None:
        """测试代理生命周期管理集成"""
        # 创建测试数据
        agent_config = self.data_factory.create_agent_config(
            agent_id="lifecycle_test_agent",
            agent_type="creative_writing"
        )
        
        # 获取mock服务
        agent_manager = self.get_mock_service("agent_manager")
        llm_service = self.get_mock_service("llm_service")
        
        # 设置mock行为
        mock_agent = Mock()
        mock_agent.agent_id = agent_config["agent_id"]
        mock_agent.is_running = False
        
        agent_manager.return_value.create_agent = AsyncMock(return_value=mock_agent)
        agent_manager.return_value.start_agent = AsyncMock(return_value=True)
        agent_manager.return_value.stop_agent = AsyncMock(return_value=True)
        agent_manager.return_value.get_agent = AsyncMock(return_value=mock_agent)
        
        llm_service.return_value.generate_response = AsyncMock(
            return_value="Test response from LLM"
        )
        
        # 执行代理生命周期测试
        # 1. 创建代理
        created_agent = await agent_manager.return_value.create_agent(
            agent_config["agent_id"],
            agent_config["agent_type"],
            agent_config["config"]
        )
        
        # 2. 启动代理
        start_result = await agent_manager.return_value.start_agent(
            agent_config["agent_id"]
        )
        
        # 3. 验证代理状态
        retrieved_agent = await agent_manager.return_value.get_agent(
            agent_config["agent_id"]
        )
        
        # 4. 使用代理执行任务
        if retrieved_agent:
            llm_response = await llm_service.return_value.generate_response(
                "Test prompt for agent"
            )
        
        # 5. 停止代理
        stop_result = await agent_manager.return_value.stop_agent(
            agent_config["agent_id"]
        )
        
        # 验证结果
        assert created_agent is not None
        assert created_agent.agent_id == agent_config["agent_id"]
        assert start_result is True
        assert retrieved_agent is not None
        assert stop_result is True
        assert llm_response == "Test response from LLM"
        
        # 验证mock调用
        agent_manager.return_value.create_agent.assert_called_once_with(
            agent_config["agent_id"],
            agent_config["agent_type"],
            agent_config["config"]
        )
        
        agent_manager.return_value.start_agent.assert_called_once_with(
            agent_config["agent_id"]
        )
        
        agent_manager.return_value.get_agent.assert_called_with(
            agent_config["agent_id"]
        )
        
        agent_manager.return_value.stop_agent.assert_called_once_with(
            agent_config["agent_id"]
        )
        
        llm_service.return_value.generate_response.assert_called_once_with(
            "Test prompt for agent"
        )
    
    @pytest.mark.system_integration
    @pytest.mark.asyncio
    async def test_agent_hsp_communication_integration(self) -> None:
        """测试代理与HSP通信集成"""
        # 创建测试数据
        sender_config = self.data_factory.create_agent_config(
            agent_id="sender_agent",
            agent_type="creative_writing"
        )
        
        receiver_config = self.data_factory.create_agent_config(
            agent_id="receiver_agent",
            agent_type="data_analysis"
        )
        
        hsp_message = self.data_factory.create_hsp_message(
            message_type="request",
            content="Please analyze this data",
            source=sender_config["agent_id"],
            target=receiver_config["agent_id"]
        )
        
        # 获取mock服务
        agent_manager = self.get_mock_service("agent_manager")
        hsp_connector = self.get_mock_service("hsp_connector")
        
        # 设置mock行为
        mock_sender_agent = Mock()
        mock_receiver_agent = Mock()
        
        agent_manager.return_value.create_agent = AsyncMock(side_effect=[
            mock_sender_agent,
            mock_receiver_agent
        ])
        
        hsp_connector.return_value.connect = AsyncMock(return_value=True)
        hsp_connector.return_value.publish = AsyncMock(return_value=True)
        hsp_connector.return_value.subscribe = AsyncMock(return_value=True)
        
        # 执行代理间通信测试
        # 1. 创建代理
        sender_agent = await agent_manager.return_value.create_agent(
            sender_config["agent_id"],
            sender_config["agent_type"]
        )
        
        receiver_agent = await agent_manager.return_value.create_agent(
            receiver_config["agent_id"],
            receiver_config["agent_type"]
        )
        
        # 2. 连接HSP
        connect_result = await hsp_connector.return_value.connect()
        
        # 3. 发送消息
        publish_result = await hsp_connector.return_value.publish(
            hsp_message,
            f"hsp/agents/{receiver_config['agent_id']}/requests"
        )
        
        # 4. 接收消息
        subscribe_result = await hsp_connector.return_value.subscribe(
            f"hsp/agents/{receiver_config['agent_id']}/requests"
        )
        
        # 验证结果
        assert sender_agent is not None
        assert receiver_agent is not None
        assert connect_result is True
        assert publish_result is True
        assert subscribe_result is True
        
        # 验证mock调用
        assert agent_manager.return_value.create_agent.call_count == 2
        
        _ = hsp_connector.return_value.connect.assert_called_once()
        hsp_connector.return_value.publish.assert_called_once_with(
            hsp_message,
            f"hsp/agents/{receiver_config['agent_id']}/requests"
        )
        hsp_connector.return_value.subscribe.assert_called_once_with(
            f"hsp/agents/{receiver_config['agent_id']}/requests"
        )
    
    @pytest.mark.system_integration
    @pytest.mark.asyncio
    async def test_agent_memory_integration(self) -> None:
        """测试代理与记忆系统集成"""
        # 创建测试数据
        agent_config = self.data_factory.create_agent_config(
            agent_id="memory_test_agent",
            agent_type="creative_writing"
        )
        
        memory_item = self.data_factory.create_memory_item(
            content="This is a test memory for agent integration",
            memory_type="fact",
            importance_score=0.8
        )
        
        # 获取mock服务
        agent_manager = self.get_mock_service("agent_manager")
        memory_manager = self.get_mock_service("memory_manager")
        
        # 设置mock行为
        mock_agent = Mock()
        mock_agent.agent_id = agent_config["agent_id"]
        
        agent_manager.return_value.create_agent = AsyncMock(return_value=mock_agent)
        agent_manager.return_value.get_agent = AsyncMock(return_value=mock_agent)
        
        memory_manager.return_value.store_memory = AsyncMock(return_value=True)
        memory_manager.return_value.retrieve_memory = AsyncMock(
            return_value=[memory_item]
        )
        
        # 执行代理与记忆系统集成测试
        # 1. 创建代理
        agent = await agent_manager.return_value.create_agent(
            agent_config["agent_id"],
            agent_config["agent_type"]
        )
        
        # 2. 存储记忆
        store_result = await memory_manager.return_value.store_memory(
            memory_item
        )
        
        # 3. 代理检索记忆
        retrieved_memories = await memory_manager.return_value.retrieve_memory(
            "test query from agent"
        )
        
        # 验证结果
        assert agent is not None
        assert store_result is True
        assert len(retrieved_memories) == 1
        assert retrieved_memories[0]["content"] == memory_item["content"]
        
        # 验证mock调用
        agent_manager.return_value.create_agent.assert_called_once_with(
            agent_config["agent_id"],
            agent_config["agent_type"]
        )
        
        memory_manager.return_value.store_memory.assert_called_once_with(
            memory_item
        )
        
        memory_manager.return_value.retrieve_memory.assert_called_once_with(
            "test query from agent"
        )
    
    @pytest.mark.system_integration
    @pytest.mark.asyncio
    async def test_agent_learning_integration(self) -> None:
        """测试代理与学习系统集成"""
        # 创建测试数据
        agent_config = self.data_factory.create_agent_config(
            agent_id="learning_test_agent",
            agent_type="creative_writing"
        )
        
        training_data = self.data_factory.create_training_data(
            input_data="Write a story about technology",
            expected_output="A story exploring the impact of technology"
        )
        
        # 获取mock服务
        agent_manager = self.get_mock_service("agent_manager")
        learning_manager = self.get_mock_service("learning_manager")
        llm_service = self.get_mock_service("llm_service")
        
        # 设置mock行为
        mock_agent = Mock()
        mock_agent.agent_id = agent_config["agent_id"]
        
        agent_manager.return_value.create_agent = AsyncMock(return_value=mock_agent)
        agent_manager.return_value.get_agent = AsyncMock(return_value=mock_agent)
        
        learning_manager.return_value.start_learning = AsyncMock(return_value=True)
        learning_manager.return_value.process_feedback = AsyncMock(return_value=True)
        
        llm_service.return_value.generate_response = AsyncMock(
            return_value="Generated story about technology"
        )
        
        # 执行代理与学习系统集成测试
        # 1. 创建代理
        agent = await agent_manager.return_value.create_agent(
            agent_config["agent_id"],
            agent_config["agent_type"]
        )
        
        # 2. 启动学习
        learning_result = await learning_manager.return_value.start_learning()
        
        # 3. 代理使用LLM生成内容
        generated_content = await llm_service.return_value.generate_response(
            training_data["input"]
        )
        
        # 4. 处理反馈
        feedback_result = await learning_manager.return_value.process_feedback(
            {
                "input": training_data["input"],
                "output": generated_content,
                "expected": training_data["expected_output"],
                "score": 0.8
            }
        )
        
        # 验证结果
        assert agent is not None
        assert learning_result is True
        assert generated_content == "Generated story about technology"
        assert feedback_result is True
        
        # 验证mock调用
        agent_manager.return_value.create_agent.assert_called_once_with(
            agent_config["agent_id"],
            agent_config["agent_type"]
        )
        
        _ = learning_manager.return_value.start_learning.assert_called_once()
        llm_service.return_value.generate_response.assert_called_once_with(
            training_data["input"]
        )
        _ = learning_manager.return_value.process_feedback.assert_called_once()


class TestAgentCollaborationIntegration(SystemIntegrationTest):
    """代理协作集成测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_collaboration_test(self, setup_system_test):
        """设置协作测试"""
        self.data_factory = TestDataFactory()
        yield
    
    @pytest.mark.system_integration
    @pytest.mark.asyncio
    async def test_multi_agent_collaboration(self) -> None:
        """测试多代理协作"""
        # 创建测试数据
        writer_config = self.data_factory.create_agent_config(
            agent_id="collab_writer",
            agent_type="creative_writing",
            capabilities=["text_generation", "story_creation"]
        )
        
        analyst_config = self.data_factory.create_agent_config(
            agent_id="collab_analyst",
            agent_type="data_analysis",
            capabilities=["data_processing", "insight_extraction"]
        )
        
        editor_config = self.data_factory.create_agent_config(
            agent_id="collab_editor",
            agent_type="text_editing",
            capabilities=["text_review", "grammar_check"]
        )
        
        collaboration_request = self.data_factory.create_hsp_message(
            message_type="request",
            content="Create and analyze a story about AI development",
            source=writer_config["agent_id"]
        )
        
        # 获取mock服务
        agent_manager = self.get_mock_service("agent_manager")
        hsp_connector = self.get_mock_service("hsp_connector")
        memory_manager = self.get_mock_service("memory_manager")
        
        # 设置mock行为
        mock_writer = Mock()
        mock_analyst = Mock()
        mock_editor = Mock()
        
        agent_manager.return_value.create_agent = AsyncMock(side_effect=[
            mock_writer,
            mock_analyst,
            mock_editor
        ])
        
        hsp_connector.return_value.publish = AsyncMock(return_value=True)
        hsp_connector.return_value.subscribe = AsyncMock(return_value=True)
        
        memory_manager.return_value.store_memory = AsyncMock(return_value=True)
        
        # 执行多代理协作测试
        # 1. 创建所有代理
        writer_agent = await agent_manager.return_value.create_agent(
            writer_config["agent_id"],
            writer_config["agent_type"]
        )
        
        analyst_agent = await agent_manager.return_value.create_agent(
            analyst_config["agent_id"],
            analyst_config["agent_type"]
        )
        
        editor_agent = await agent_manager.return_value.create_agent(
            editor_config["agent_id"],
            editor_config["agent_type"]
        )
        
        # 2. 发起协作请求
        publish_result = await hsp_connector.return_value.publish(
            collaboration_request,
            "hsp/agents/collaboration/requests"
        )
        
        # 3. 各代理处理请求
        # 作家代理生成故事
        story_content = "Once upon a time, in a world of artificial intelligence..."
        
        # 分析师代理分析故事
        analysis_result = {
            "themes": ["technology", "future"],
            "sentiment": "positive",
            "complexity_score": 0.7
        }
        
        # 编辑代理审查内容
        edited_content = story_content + " (edited version)"
        
        # 4. 存储协作结果到记忆系统
        collaboration_memory = self.data_factory.create_memory_item(
            content=f"Collaboration result: {edited_content}",
            memory_type="collaboration_result",
            importance_score=0.9
        )
        
        store_result = await memory_manager.return_value.store_memory(
            collaboration_memory
        )
        
        # 验证结果
        assert writer_agent is not None
        assert analyst_agent is not None
        assert editor_agent is not None
        assert publish_result is True
        assert store_result is True
        
        # 验证mock调用
        assert agent_manager.return_value.create_agent.call_count == 3
        
        hsp_connector.return_value.publish.assert_called_once_with(
            collaboration_request,
            "hsp/agents/collaboration/requests"
        )
        
        memory_manager.return_value.store_memory.assert_called_once_with(
            collaboration_memory
        )


if __name__ == "__main__":
    _ = pytest.main([__file__, "-v"])