"""
系统级集成测试
测试整个Unified AI系统的端到端集成
"""

import pytest
from apps.backend.tests.integration.base_test import SystemIntegrationTest
from apps.backend.tests.integration.test_data_factory import TestDataFactory, TestDataSet


class TestSystemLevelIntegration(SystemIntegrationTest):
    """系统级集成测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self, setup_test, mock_external_services) -> None:
        """设置测试数据"""
        self.data_factory = TestDataFactory()
        self.test_data_set = TestDataSet()
        self.mock_services = mock_external_services
        yield
    
    def get_mock_service(self, service_name: str) -> Mock:
        """
        获取mock服务实例
        
        Args:
            service_name: 服务名称
            
        Returns:
            Mock: mock服务实例
        """
        return self.mock_services.get(service_name)
    
    @pytest.mark.system_integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_end_to_end_user_interaction_integration(self) -> None:
        """测试端到端用户交互集成"""
        # 创建测试数据
        user_id = "test_user_123"
        session_id = "session_456"
        
        # 使用标准测试数据集
        test_data = self.test_data_set.get_data_set("standard")
        
        # 获取所有mock服务
        agent_manager = self.get_mock_service("agent_manager")
        hsp_connector = self.get_mock_service("hsp_connector")
        memory_manager = self.get_mock_service("memory_manager")
        dialogue_manager = self.get_mock_service("dialogue_manager")
        learning_manager = self.get_mock_service("learning_manager")
        llm_service = self.get_mock_service("llm_service")
        
        # 设置mock行为
        # 代理管理器
        mock_agents = [Mock() for _ in test_data["agents"]]
        agent_manager.return_value.create_agent = AsyncMock(side_effect=mock_agents)
        agent_manager.return_value.get_agent = AsyncMock(side_effect=mock_agents)
        agent_manager.return_value.start_agent = AsyncMock(return_value=True)
        
        # HSP连接器
        hsp_connector.return_value.connect = AsyncMock(return_value=True)
        hsp_connector.return_value.publish = AsyncMock(return_value=True)
        hsp_connector.return_value.subscribe = AsyncMock(return_value=True)
        
        # 记忆管理器
        memory_manager.return_value.initialize = AsyncMock(return_value=True)
        memory_manager.return_value.store_memory = AsyncMock(return_value=True)
        memory_manager.return_value.retrieve_memory = AsyncMock(return_value=test_data["memories"])
        
        # 对话管理器
        dialogue_manager.return_value.initialize = AsyncMock(return_value=True)
        dialogue_manager.return_value.process_dialogue = AsyncMock(
            return_value={
                "status": "success",
                "response": "Hello! I'm your AI assistant. How can I help you today?",
                "session_id": session_id,
                "agent_used": test_data["agents"][0]["agent_id"]
            }
        )
        
        # 学习管理器
        learning_manager.return_value.initialize = AsyncMock(return_value=True)
        learning_manager.return_value.process_feedback = AsyncMock(return_value=True)
        
        # LLM服务
        llm_service.return_value.initialize = AsyncMock(return_value=True)
        llm_service.return_value.generate_response = AsyncMock(
            return_value="Generated response from the unified AI system"
        )
        
        # 执行端到端用户交互测试
        # 1. 系统初始化
        system_services = [memory_manager, dialogue_manager, learning_manager, llm_service]
        init_results = []
        for service in system_services:
            result = await service.return_value.initialize()
            init_results.append(result)
        
        # 2. 连接HSP
        hsp_connect_result = await hsp_connector.return_value.connect()
        
        # 3. 创建代理
        created_agents = []
        for agent_config in test_data["agents"]:
            agent = await agent_manager.return_value.create_agent(
                agent_config["agent_id"],
                agent_config["agent_type"],
                agent_config["config"]
            )
            # 启动代理
            _ = await agent_manager.return_value.start_agent(agent_config["agent_id"])
            created_agents.append(agent)
        
        # 4. 用户发起对话
        user_message = "Hello, I need help with data analysis."
        dialogue_context = self.data_factory.create_dialogue_context(
            user_id=user_id,
            session_id=session_id,
            history=[
                {
                    "role": "user",
                    "content": user_message,
                    "timestamp": "2023-01-01T00:00:00Z"
                }
            ]
        )
        
        # 5. 检索用户历史记忆
        user_memories = await memory_manager.return_value.retrieve_memory(
            f"user:{user_id}"
        )
        
        # 6. 处理对话
        dialogue_response = await dialogue_manager.return_value.process_dialogue(
            dialogue_context,
            user_memories
        )
        
        # 7. 生成详细响应
        detailed_response = await llm_service.return_value.generate_response(
            f"Respond to: {user_message}"
        )
        
        # 8. 存储交互记忆
        interaction_memory = self.data_factory.create_memory_item(
            content=f"User: {user_message} | AI: {detailed_response}",
            memory_type="interaction",
            importance_score=0.7,
            tags=["user_interaction", "dialogue", user_id]
        )
        store_memory_result = await memory_manager.return_value.store_memory(
            interaction_memory
        )
        
        # 9. 处理用户反馈
        user_feedback = {
            "rating": 4,
            "comment": "Good response, but could be more detailed",
            "interaction_id": interaction_memory["id"]
        }
        feedback_result = await learning_manager.return_value.process_feedback(
            user_feedback
        )
        
        # 验证结果
        assert all(result is True for result in init_results)
        assert hsp_connect_result is True
        assert len(created_agents) == len(test_data["agents"])
        assert dialogue_response is not None
        assert dialogue_response["status"] == "success"
        assert "response" in dialogue_response
        assert detailed_response is not None
        assert store_memory_result is True
        assert feedback_result is True
        
        # 验证mock调用
        for service in system_services:
            service.return_value.initialize.assert_called_once()
        
        hsp_connector.return_value.connect.assert_called_once()
        
        assert agent_manager.return_value.create_agent.call_count == len(test_data["agents"])
        assert agent_manager.return_value.start_agent.call_count == len(test_data["agents"])
        
        memory_manager.return_value.retrieve_memory.assert_called_once_with(
            f"user:{user_id}"
        )
        
        dialogue_manager.return_value.process_dialogue.assert_called_once_with(
            dialogue_context,
            user_memories
        )
        
        llm_service.return_value.generate_response.assert_called_once_with(
            f"Respond to: {user_message}"
        )
        
        memory_manager.return_value.store_memory.assert_called_once_with(
            interaction_memory
        )
        
        learning_manager.return_value.process_feedback.assert_called_once_with(
            user_feedback
        )
    
    @pytest.mark.system_integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_multi_agent_collaborative_task_integration(self) -> None:
        """测试多代理协作任务集成"""
        # 创建测试数据
        task_request = {
            "type": "collaborative_analysis",
            "content": "Analyze market trends and generate a comprehensive report",
            "deadline": "2023-12-31T23:59:59Z",
            "priority": "high"
        }
        
        # 创建专业代理配置
        specialist_configs = [
            self.data_factory.create_agent_config(
                agent_id="data_analyst_001",
                agent_type="data_analysis",
                capabilities=["data_processing", "statistical_analysis"]
            ),
            self.data_factory.create_agent_config(
                agent_id="market_researcher_001",
                agent_type="research",
                capabilities=["market_analysis", "trend_identification"]
            ),
            self.data_factory.create_agent_config(
                agent_id="report_writer_001",
                agent_type="creative_writing",
                capabilities=["report_writing", "data_visualization"]
            ),
            self.data_factory.create_agent_config(
                agent_id="quality_reviewer_001",
                agent_type="review",
                capabilities=["quality_assurance", "fact_checking"]
            )
        ]
        
        # 获取mock服务
        agent_manager = self.get_mock_service("agent_manager")
        hsp_connector = self.get_mock_service("hsp_connector")
        memory_manager = self.get_mock_service("memory_manager")
        dialogue_manager = self.get_mock_service("dialogue_manager")
        llm_service = self.get_mock_service("llm_service")
        
        # 设置mock行为
        # 代理管理器
        mock_specialists = [Mock() for _ in specialist_configs]
        agent_manager.return_value.create_agent = AsyncMock(side_effect=mock_specialists)
        agent_manager.return_value.assign_collaborative_task = AsyncMock(return_value=True)
        agent_manager.return_value.monitor_task_progress = AsyncMock(
            return_value={"status": "completed", "progress": 100}
        )
        
        # HSP连接器
        hsp_connector.return_value.publish = AsyncMock(return_value=True)
        hsp_connector.return_value.subscribe = AsyncMock(return_value=True)
        
        # 记忆管理器
        memory_manager.return_value.store_memory = AsyncMock(return_value=True)
        memory_manager.return_value.retrieve_memory = AsyncMock(return_value=[])
        
        # 对话管理器
        dialogue_manager.return_value.coordinate_collaborative_task = AsyncMock(
            return_value={
                "task_id": "collab_task_789",
                "assigned_agents": [config["agent_id"] for config in specialist_configs],
                "coordination_channel": "hsp/collaboration/tasks/collab_task_789"
            }
        )
        
        # LLM服务
        llm_service.return_value.generate_response = AsyncMock(
            return_value="Comprehensive market analysis report"
        )
        
        # 执行多代理协作任务测试
        # 1. 创建专业代理
        created_specialists = []
        for config in specialist_configs:
            specialist = await agent_manager.return_value.create_agent(
                config["agent_id"],
                config["agent_type"],
                config["config"]
            )
            created_specialists.append(specialist)
        
        # 2. 协调协作任务
        coordination_result = await dialogue_manager.return_value.coordinate_collaborative_task(
            task_request
        )
        
        # 3. 分配任务给代理
        task_assignments = []
        for agent_id in coordination_result["assigned_agents"]:
            assignment_result = await agent_manager.return_value.assign_collaborative_task(
                agent_id,
                task_request
            )
            task_assignments.append(assignment_result)
        
        # 4. 代理间通信协作
        collaboration_messages = [
            self.data_factory.create_hsp_message(
                message_type="task_update",
                content=f"Agent {agent_id} completed analysis phase",
                source=agent_id,
                target="coordination_system"
            )
            for agent_id in coordination_result["assigned_agents"]
        ]
        
        message_results = []
        for message in collaboration_messages:
            result = await hsp_connector.return_value.publish(
                message,
                coordination_result["coordination_channel"]
            )
            message_results.append(result)
        
        # 5. 监控任务进度
        progress_result = await agent_manager.return_value.monitor_task_progress(
            coordination_result["task_id"]
        )
        
        # 6. 生成最终报告
        final_report = await llm_service.return_value.generate_response(
            f"Generate comprehensive report for task: {task_request['content']}"
        )
        
        # 7. 存储任务结果
        task_result_memory = self.data_factory.create_memory_item(
            content=f"Collaborative task result: {final_report}",
            memory_type="collaborative_task_result",
            importance_score=0.9,
            tags=["collaborative_task", "market_analysis", "report"]
        )
        store_result = await memory_manager.return_value.store_memory(
            task_result_memory
        )
        
        # 验证结果
        assert len(created_specialists) == len(specialist_configs)
        assert coordination_result is not None
        assert "task_id" in coordination_result
        assert "assigned_agents" in coordination_result
        assert all(assignment_result is True for assignment_result in task_assignments)
        assert all(result is True for result in message_results)
        assert progress_result is not None
        assert progress_result["status"] == "completed"
        assert final_report is not None
        assert store_result is True
        
        # 验证mock调用
        assert agent_manager.return_value.create_agent.call_count == len(specialist_configs)
        dialogue_manager.return_value.coordinate_collaborative_task.assert_called_once_with(
            task_request
        )
        assert agent_manager.return_value.assign_collaborative_task.call_count == len(specialist_configs)
        assert hsp_connector.return_value.publish.call_count == len(collaboration_messages)
        agent_manager.return_value.monitor_task_progress.assert_called_once_with(
            coordination_result["task_id"]
        )
        llm_service.return_value.generate_response.assert_called_once()
        memory_manager.return_value.store_memory.assert_called_once_with(
            task_result_memory
        )


class TestSystemIntegrationWithExternalServices(SystemIntegrationTest):
    """与外部服务集成的系统测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_external_services_test(self, setup_test, mock_external_services):
        """设置外部服务测试"""
        self.data_factory = TestDataFactory()
        self.mock_services = mock_external_services
        yield
    
    def get_mock_service(self, service_name: str) -> Mock:
        """
        获取mock服务实例
        
        Args:
            service_name: 服务名称
            
        Returns:
            Mock: mock服务实例
        """
        return self.mock_services.get(service_name)
    
    @pytest.mark.system_integration
    @pytest.mark.asyncio
    async def test_external_api_integration(self) -> None:
        """测试外部API集成"""
        # 创建测试数据
        external_api_request = {
            "service": "weather_api",
            "endpoint": "/current_weather",
            "params": {"location": "New York", "units": "metric"}
        }
        
        # 获取mock服务
        agent_manager = self.get_mock_service("agent_manager")
        llm_service = self.get_mock_service("llm_service")
        
        # 设置mock行为
        mock_agent = Mock()
        agent_manager.return_value.create_agent = AsyncMock(return_value=mock_agent)
        agent_manager.return_value.execute_external_task = AsyncMock(
            return_value={
                "status": "success",
                "data": {
                    "temperature": 22,
                    "condition": "sunny",
                    "humidity": 65
                }
            }
        )
        
        llm_service.return_value.process_external_data = AsyncMock(
            return_value="The current weather in New York is sunny with a temperature of 22°C."
        )
        
        # 执行外部API集成测试
        # 1. 创建专门处理外部API的代理
        api_agent = await agent_manager.return_value.create_agent(
            "external_api_agent",
            "api_handler",
            {"capabilities": ["external_api_integration"]}
        )
        
        # 2. 执行外部任务
        external_result = await agent_manager.return_value.execute_external_task(
            "external_api_agent",
            external_api_request
        )
        
        # 3. 处理外部数据
        processed_data = await llm_service.return_value.process_external_data(
            external_result["data"]
        )
        
        # 验证结果
        assert api_agent is not None
        assert external_result is not None
        assert external_result["status"] == "success"
        assert "data" in external_result
        assert processed_data is not None
        
        # 验证mock调用
        agent_manager.return_value.create_agent.assert_called_once_with(
            "external_api_agent",
            "api_handler",
            {"capabilities": ["external_api_integration"]}
        )
        
        agent_manager.return_value.execute_external_task.assert_called_once_with(
            "external_api_agent",
            external_api_request
        )
        
        llm_service.return_value.process_external_data.assert_called_once_with(
            external_result["data"]
        )
    
    @pytest.mark.system_integration
    @pytest.mark.asyncio
    async def test_database_integration(self) -> None:
        """测试数据库集成"""
        # 创建测试数据
        db_operations = [
            {
                "operation": "insert",
                "table": "user_interactions",
                "data": {
                    "user_id": "user_123",
                    "interaction_type": "query",
                    "content": "What's the weather today?",
                    "timestamp": "2023-01-01T12:00:00Z"
                }
            },
            {
                "operation": "select",
                "table": "user_interactions",
                "conditions": {"user_id": "user_123"}
            }
        ]
        
        # 获取mock服务
        memory_manager = self.get_mock_service("memory_manager")
        
        # 设置mock行为
        memory_manager.return_value.execute_database_operation = AsyncMock(
            side_effect=[
                {"status": "success", "inserted_id": "record_789"},
                {
                    "status": "success",
                    "results": [
                        {
                            "id": "record_789",
                            "user_id": "user_123",
                            "interaction_type": "query",
                            "content": "What's the weather today?",
                            "timestamp": "2023-01-01T12:00:00Z"
                        }
                    ]
                }
            ]
        )
        
        # 执行数据库集成测试
        # 1. 执行数据库插入操作
        insert_result = await memory_manager.return_value.execute_database_operation(
            db_operations[0]
        )
        
        # 2. 执行数据库查询操作
        select_result = await memory_manager.return_value.execute_database_operation(
            db_operations[1]
        )
        
        # 验证结果
        assert insert_result is not None
        assert insert_result["status"] == "success"
        assert "inserted_id" in insert_result
        assert select_result is not None
        assert select_result["status"] == "success"
        assert "results" in select_result
        assert len(select_result["results"]) > 0
        
        # 验证mock调用
        assert memory_manager.return_value.execute_database_operation.call_count == 2
        memory_manager.return_value.execute_database_operation.assert_any_call(
            db_operations[0]
        )
        memory_manager.return_value.execute_database_operation.assert_any_call(
            db_operations[1]
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])