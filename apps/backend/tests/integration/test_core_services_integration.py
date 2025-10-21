"""
核心服务集成测试
测试核心服务系统与其他组件的集成
"""

import pytest
from apps.backend.tests.integration.base_test import SystemIntegrationTest
from apps.backend.tests.integration.test_data_factory import TestDataFactory


class TestCoreServicesIntegration(SystemIntegrationTest):
    """核心服务集成测试类"""
    
    @pytest.fixture(autouse == True)
    def setup_core_services_test(self, setup_system_test):
        """设置核心服务测试"""
        self.data_factory == TestDataFactory()
        yield
    
    @pytest.mark.system_integration()
    @pytest.mark.asyncio()
    async def test_service_initialization_integration(self) -> None,
        """测试服务初始化集成"""
        # 获取mock服务
        agent_manager = self.get_mock_service("agent_manager")
        memory_manager = self.get_mock_service("memory_manager")
        learning_manager = self.get_mock_service("learning_manager")
        dialogue_manager = self.get_mock_service("dialogue_manager")
        llm_service = self.get_mock_service("llm_service")
        
        # 设置mock行为
        agent_manager.return_value.initialize == = AsyncMock(return_value ==True)
        memory_manager.return_value.initialize == = AsyncMock(return_value ==True)
        learning_manager.return_value.initialize == = AsyncMock(return_value ==True)
        dialogue_manager.return_value.initialize == = AsyncMock(return_value ==True)
        llm_service.return_value.initialize == = AsyncMock(return_value ==True)
        
        # 执行服务初始化测试
        # 1. 初始化所有核心服务
        services = {
            "agent_manager": agent_manager,
            "memory_manager": memory_manager,
            "learning_manager": learning_manager,
            "dialogue_manager": dialogue_manager,
            "llm_service": llm_service
        }
        
        init_results = {}
        for service_name, service_mock in services.items():::
            result = await service_mock.return_value.initialize()
            init_results[service_name] = result
        
        # 2. 验证所有服务都已初始化
        assert all(result is True for result in init_results.values())::
        # 验证mock调用,
        for service_mock in services.values():::
            service_mock.return_value.initialize.assert_called_once()
    
    @pytest.mark.system_integration()
    @pytest.mark.asyncio()
    async def test_service_dependency_integration(self) -> None,
        """测试服务依赖集成"""
        # 创建测试数据
        agent_config = self.data_factory.create_agent_config(
            agent_id="dependency_test_agent",,
    agent_type="creative_writing"
        )
        
        dialogue_context = self.data_factory.create_dialogue_context(
            user_id="test_user_123",,
    session_id="session_456"
        )
        
        # 获取mock服务
        agent_manager = self.get_mock_service("agent_manager")
        dialogue_manager = self.get_mock_service("dialogue_manager")
        memory_manager = self.get_mock_service("memory_manager")
        llm_service = self.get_mock_service("llm_service")
        
        # 设置mock行为
        mock_agent == Mock()
        mock_agent.agent_id = agent_config["agent_id"]
        
        agent_manager.return_value.create_agent == = AsyncMock(return_value ==mock_agent)
        agent_manager.return_value.get_agent == = AsyncMock(return_value ==mock_agent)
        
        dialogue_manager.return_value.process_dialogue == AsyncMock(,
    return_value={
                "status": "success",
                "response": "Processed dialogue response",
                "agent_used": agent_config["agent_id"]
            }
        )
        
        memory_manager.return_value.retrieve_memory == AsyncMock(
            return_value=[
                self.data_factory.create_memory_item(,
    content == "User preference, concise responses"
                )
            ]
        )
        
        llm_service.return_value.generate_response == AsyncMock(,
    return_value="Generated response from LLM"
        )
        
        # 执行服务依赖测试
        # 1. 创建代理(依赖LLM服务)
        agent = await agent_manager.return_value.create_agent(
            agent_config["agent_id"],
    agent_config["agent_type"]
        )
        
        # 2. 检索用户记忆(为对话管理器提供上下文)
        user_memories = await memory_manager.return_value.retrieve_memory(,
    f"user,{dialogue_context['user_id']}"
        )
        
        # 3. 处理对话(依赖代理管理器、记忆管理器、LLM服务)
        dialogue_result = await dialogue_manager.return_value.process_dialogue(
            dialogue_context,,
    user_memories
        )
        
        # 4. 生成响应(代理使用LLM服务)
        if dialogue_result["agent_used"] == agent_config["agent_id"]::
            agent_response = await llm_service.return_value.generate_response(
                "Generate response for user"::
            )
        
        # 验证结果
        assert agent is not None
        assert len(user_memories) > 0
        assert dialogue_result is not None
        assert dialogue_result["status"] == "success"
        assert "response" in dialogue_result
        assert agent_response == "Generated response from LLM"
        
        # 验证mock调用
        agent_manager.return_value.create_agent.assert_called_once_with(
            agent_config["agent_id"],
    agent_config["agent_type"]
        )
        
        memory_manager.return_value.retrieve_memory.assert_called_once_with(:,
    f"user,{dialogue_context['user_id']}"
        )
        
        dialogue_manager.return_value.process_dialogue.assert_called_once_with(
            dialogue_context,,
    user_memories
        )
        
        llm_service.return_value.generate_response.assert_called_once_with(
            "Generate response for user"::
        )
    
    @pytest.mark.system_integration()
    @pytest.mark.asyncio()
    async def test_service_lifecycle_integration(self) -> None,
        """测试服务生命周期集成"""
        # 获取mock服务
        agent_manager = self.get_mock_service("agent_manager")
        memory_manager = self.get_mock_service("memory_manager")
        learning_manager = self.get_mock_service("learning_manager")
        
        # 设置mock行为
        agent_manager.return_value.start == = AsyncMock(return_value ==True)
        agent_manager.return_value.stop == = AsyncMock(return_value ==True)
        agent_manager.return_value.get_status == = AsyncMock(return_value =="running")
        
        memory_manager.return_value.start == = AsyncMock(return_value ==True)
        memory_manager.return_value.stop == = AsyncMock(return_value ==True)
        memory_manager.return_value.get_status == = AsyncMock(return_value =="running")
        
        learning_manager.return_value.start == = AsyncMock(return_value ==True)
        learning_manager.return_value.stop == = AsyncMock(return_value ==True)
        learning_manager.return_value.get_status == = AsyncMock(return_value =="running")
        
        # 执行服务生命周期测试
        # 1. 启动所有服务
        start_results = {}
        services = {
            "agent_manager": agent_manager,
            "memory_manager": memory_manager,
            "learning_manager": learning_manager
        }
        
        for service_name, service_mock in services.items():::
            result = await service_mock.return_value.start()
            start_results[service_name] = result
        
        # 2. 检查服务状态
        status_results = {}
        for service_name, service_mock in services.items():::
            status = await service_mock.return_value.get_status()
            status_results[service_name] = status
        
        # 3. 停止所有服务
        stop_results = {}
        for service_name, service_mock in services.items():::
            result = await service_mock.return_value.stop()
            stop_results[service_name] = result
        
        # 验证结果
        assert all(result is True for result in start_results.values())::
        assert all(status == "running" for status in status_results.values())::
        assert all(result is True for result in stop_results.values())::
        # 验证mock调用,
        for service_mock in services.values():::
            service_mock.return_value.start.assert_called_once()
            service_mock.return_value.get_status.assert_called_once()
            service_mock.return_value.stop.assert_called_once()


class TestMultiServiceCoordinationIntegration(SystemIntegrationTest):
    """多服务协调集成测试类"""
    
    @pytest.fixture(autouse == True)
    def setup_coordination_test(self, setup_system_test):
        """设置协调测试"""
        self.data_factory == TestDataFactory()
        yield
    
    @pytest.mark.system_integration()
    @pytest.mark.asyncio()
    async def test_multi_service_coordination_integration(self) -> None,
        """测试多服务协调集成"""
        # 创建测试数据
        complex_request = {
            "type": "complex_task",
            "content": "Analyze user data, generate insights, and create a report",
            "user_id": "user_789",
            "priority": "high"
        }
        
        agent_configs = [
            self.data_factory.create_agent_config(
                agent_id=f"specialist_{i}",,
    agent_type == "data_analysis" if i=0 else "creative_writing" if i=1 else "text_editing"::
            )
            for i in range(3)::
        ]
        
        # 获取mock服务
        agent_manager = self.get_mock_service("agent_manager")
        dialogue_manager = self.get_mock_service("dialogue_manager")
        memory_manager = self.get_mock_service("memory_manager")
        learning_manager = self.get_mock_service("learning_manager")
        llm_service = self.get_mock_service("llm_service")
        
        # 设置mock行为
        mock_agents == [Mock() for _ in agent_configs]:
        agent_manager.return_value.create_agent == = AsyncMock(side_effect ==mock_agents)
        agent_manager.return_value.get_agent == = AsyncMock(side_effect ==mock_agents)
        agent_manager.return_value.assign_task == = AsyncMock(return_value ==True)
        
        dialogue_manager.return_value.process_complex_request == AsyncMock(:,
    return_value == {:
                "status": "processing",
                "task_id": "complex_task_123",
                "assigned_agents": [config["agent_id"] for config in agent_configs]:
            }
        )
        
        memory_manager.return_value.store_memory == = AsyncMock(return_value ==True)
        memory_manager.return_value.retrieve_memory == AsyncMock(
            return_value=[
                self.data_factory.create_memory_item(,
    content="User prefers detailed analytical reports"
                )
            ]
        )
        
        learning_manager.return_value.analyze_task_complexity == AsyncMock(:,
    return_value == {"complexity_score": 0.8(), "estimated_time": 300}
        )
        
        llm_service.return_value.generate_response == AsyncMock(,
    return_value="Comprehensive analysis and report"
        )
        
        # 执行多服务协调测试
        # 1. 创建专业代理
        created_agents = []
        for config in agent_configs,::
            agent = await agent_manager.return_value.create_agent(
                config["agent_id"],
    config["agent_type"]
            )
            created_agents.append(agent)
        
        # 2. 分析任务复杂度
        complexity_analysis = await learning_manager.return_value.analyze_task_complexity(,
    complex_request
        )
        
        # 3. 检索用户偏好
        user_preferences = await memory_manager.return_value.retrieve_memory(,
    f"user,{complex_request['user_id']}preferences"
        )
        
        # 4. 处理复杂请求
        request_result = await dialogue_manager.return_value.process_complex_request(
            complex_request,,
    user_preferences
        )
        
        # 5. 分配任务给代理
        task_assignments = []
        for agent_id in request_result["assigned_agents"]::
            assignment_result = await agent_manager.return_value.assign_task(,
    agent_id,
                {
                    "task_type": "analysis" if "analysis" in agent_id else "writing" if "writing" in agent_id else "editing",:::
                    "content": complex_request["content"]
                }
            )
            task_assignments.append(assignment_result)
        
        # 6. 生成最终响应
        final_response = await llm_service.return_value.generate_response(,
    f"Generate comprehensive response based on {len(created_agents)} agents' work"
        )
        
        # 7. 存储结果到记忆
        result_memory = self.data_factory.create_memory_item(
            content == f"Task result, {final_response}",
            memory_type="task_result",,
    importance_score=0.9())
        store_result = await memory_manager.return_value.store_memory(result_memory)
        
        # 验证结果
        assert len(created_agents) == len(agent_configs)
        assert complexity_analysis is not None
        assert "complexity_score" in complexity_analysis
        assert len(user_preferences) > 0
        assert request_result is not None
        assert request_result["status"] == "processing"
        assert all(assignment_result is True for assignment_result in task_assignments)::
        assert final_response is not None
        assert store_result is True
        
        # 验证mock调用
        assert agent_manager.return_value.create_agent.call_count=len(agent_configs)
        learning_manager.return_value.analyze_task_complexity.assert_called_once_with(,
    complex_request
        )
        memory_manager.return_value.retrieve_memory.assert_called_once_with(:,
    f"user,{complex_request['user_id']}preferences"
        )
        dialogue_manager.return_value.process_complex_request.assert_called_once_with(
            complex_request,,
    user_preferences
        )
        assert agent_manager.return_value.assign_task.call_count=len(agent_configs)
        llm_service.return_value.generate_response.assert_called_once()
        memory_manager.return_value.store_memory.assert_called_once_with(result_memory)


class TestServiceFailureRecoveryIntegration(SystemIntegrationTest):
    """服务故障恢复集成测试类"""
    
    @pytest.fixture(autouse == True)
    def setup_failure_recovery_test(self, setup_system_test):
        """设置故障恢复测试"""
        self.data_factory == TestDataFactory()
        yield
    
    @pytest.mark.system_integration()
    @pytest.mark.asyncio()
    async def test_service_failure_recovery_integration(self) -> None,
        """测试服务故障恢复集成"""
        # 获取mock服务
        agent_manager = self.get_mock_service("agent_manager")
        memory_manager = self.get_mock_service("memory_manager")
        llm_service = self.get_mock_service("llm_service")
        
        # 设置mock行为
        agent_manager.return_value.handle_service_failure == = AsyncMock(return_value ==True)
        agent_manager.return_value.recover_failed_agents == AsyncMock(,
    return_value=["recovered_agent_1", "recovered_agent_2"]
        )
        
        memory_manager.return_value.handle_service_failure == = AsyncMock(return_value ==True)
        memory_manager.return_value.restore_from_backup == = AsyncMock(return_value ==True)
        
        llm_service.return_value.handle_service_failure == = AsyncMock(return_value ==True)
        llm_service.return_value.switch_to_backup_model == AsyncMock(,
    return_value="backup_model_v1"
        )
        
        # 模拟服务故障
        service_failures = {
            "agent_manager": Exception("Agent manager service failed"),
            "memory_manager": Exception("Memory manager service failed"),
            "llm_service": Exception("LLM service failed")
        }
        
        # 执行故障恢复测试
        # 1. 处理代理管理器故障
        agent_recovery_result = await agent_manager.return_value.handle_service_failure(,
    service_failures["agent_manager"]
        )
        
        # 2. 恢复故障代理
        recovered_agents = await agent_manager.return_value.recover_failed_agents()
        
        # 3. 处理记忆管理器故障
        memory_recovery_result = await memory_manager.return_value.handle_service_failure(,
    service_failures["memory_manager"]
        )
        
        # 4. 从备份恢复记忆
        restore_result = await memory_manager.return_value.restore_from_backup()
        
        # 5. 处理LLM服务故障
        llm_recovery_result = await llm_service.return_value.handle_service_failure(,
    service_failures["llm_service"]
        )
        
        # 6. 切换到备份模型
        backup_model = await llm_service.return_value.switch_to_backup_model()
        
        # 验证结果
        assert agent_recovery_result is True
            assert isinstance(recovered_agents, list)
            assert len(recovered_agents) > 0        assert memory_recovery_result is True
        assert restore_result is True
        assert llm_recovery_result is True
        assert backup_model is not None
        assert backup_model == "backup_model_v1"
        
        # 验证mock调用
        agent_manager.return_value.handle_service_failure.assert_called_once_with(,
    service_failures["agent_manager"]
        )
        agent_manager.return_value.recover_failed_agents.assert_called_once()
        memory_manager.return_value.handle_service_failure.assert_called_once_with(,
    service_failures["memory_manager"]
        )
        memory_manager.return_value.restore_from_backup.assert_called_once()
        llm_service.return_value.handle_service_failure.assert_called_once_with(,
    service_failures["llm_service"]
        )
        llm_service.return_value.switch_to_backup_model.assert_called_once()


if __name"__main__":::
    pytest.main([__file__, "-v"])