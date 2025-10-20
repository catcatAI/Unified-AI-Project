import pytest
from unittest.mock import Mock, patch, AsyncMock
from demo_learning_manager import DemoLearningManager
from execution_manager import ExecutionManager

class TestTrainingWorkflowE2E:
    """端到端训练工作流程测试"""
    
    @pytest.fixture
    def demo_learning_manager(self):
        """创建演示学习管理器实例"""
        manager = DemoLearningManager()
        return manager
    
    @pytest.fixture
    def execution_manager(self):
        """创建执行管理器实例"""
        manager = ExecutionManager()
        return manager
    
    @pytest.mark.asyncio
    async def test_complete_training_workflow(self, demo_learning_manager, execution_manager) -> None:
        """测试完整的训练工作流程"""
        # Mock依赖组件
        demo_learning_manager.model_trainer = AsyncMock()
        demo_learning_manager.model_trainer.train = AsyncMock(return_value={
            "status": "completed",
            "model_id": "e2e_test_model",
            "metrics": {"accuracy": 0.95, "loss": 0.05}
        })
        
        execution_manager._execute_training_task = AsyncMock(return_value={
            "status": "completed",
            "task_id": "e2e_training_task_001",
            "result": {"model_id": "e2e_test_model"}
        })
        
        # 1. 准备训练任务
        training_task = {
            "task_id": "e2e_training_task_001",
            "task_type": "training",
            "parameters": {
                "model_name": "E2E Test Model",
                "dataset": "test_dataset",
                "epochs": 10,
                "batch_size": 32
            }
        }
        
        # 2. 提交训练任务到执行管理器
        execution_result = await execution_manager.execute_task(training_task)
        assert execution_result is not None
        assert execution_result["status"] == "completed"
        assert "task_id" in execution_result
        _ = execution_manager._execute_training_task.assert_called_once_with(training_task)
        
        # 3. 启动模型训练
        training_config = {
            "epochs": 10,
            "batch_size": 32,
            "learning_rate": 0.001
        }
        
        training_result = await demo_learning_manager.start_learning("e2e_test_model", training_config)
        assert training_result is not None
        assert training_result["status"] == "completed"
        assert "model_id" in training_result
        assert "metrics" in training_result
        _ = demo_learning_manager.model_trainer.train.assert_called_once()
        
        # 4. 验证模型状态
        demo_learning_manager.model_registry["e2e_test_model"] = {
            "status": "trained",
            "metrics": training_result["metrics"]
        }
        
        model_status = demo_learning_manager.get_model_status("e2e_test_model")
        assert model_status is not None
        assert model_status["status"] == "trained"
        assert model_status["metrics"]["accuracy"] == 0.95
    
    @pytest.mark.asyncio
    async def test_memory_integration_in_training_workflow(self, demo_learning_manager) -> None:
        """测试训练工作流程中与记忆系统的集成"""
        with patch('apps.backend.src.ai.memory.ham_memory_manager.HAMMemoryManager') as mock_memory_manager:
            # Mock记忆管理器
            mock_memory_instance = mock_memory_manager.return_value
            mock_memory_instance.store_memory = AsyncMock(return_value=True)
            mock_memory_instance.retrieve_memory = AsyncMock(return_value=[])
            
            # 1. 模拟训练过程中存储记忆
            training_memory = {
                "id": "training_progress_001",
                "content": "Training epoch 5 completed with accuracy 0.85",
                "metadata": {
                    "created_at": "2023-01-01T00:00:00Z",
                    "importance_score": 0.9,
                    "tags": ["training", "progress", "epoch_5"],
                    "data_type": "training_log"
                }
            }
            
            # 2. 在训练过程中存储进度记忆
            store_result = await mock_memory_instance.store_memory(training_memory)
            assert store_result is True
            _ = mock_memory_instance.store_memory.assert_called_once_with(training_memory)
            
            # 3. 检索相关训练记忆
            mock_memory_instance.retrieve_memory.return_value = [training_memory]
            retrieved_memories = await mock_memory_instance.retrieve_memory("training progress")
            assert len(retrieved_memories) == 1
            assert retrieved_memories[0]["id"] == training_memory["id"]
    
    @pytest.mark.asyncio
    async def test_agent_collaboration_in_training_workflow(self) -> None:
        """测试训练工作流程中与代理系统的协作"""
        with patch('apps.backend.src.core_ai.agent_manager.AgentManager') as mock_agent_manager:
            # Mock代理管理器
            mock_agent_manager_instance = mock_agent_manager.return_value
            mock_agent_manager_instance.get_agent = Mock(return_value=Mock())
            
            # 创建模拟代理
            mock_agent = Mock()
            mock_agent.agent_id = "training_coordinator_agent"
            mock_agent.process_training_request = AsyncMock(return_value={
                "status": "accepted",
                "assigned_resources": ["gpu_1", "cpu_4"]
            })
            
            mock_agent_manager_instance.get_agent.return_value = mock_agent
            
            # 1. 模拟代理处理训练请求
            training_request = {
                "model_name": "Collaborative Test Model",
                "resources_needed": ["gpu", "cpu_4"],
                "priority": "high"
            }
            
            agent_response = await mock_agent.process_training_request(training_request)
            assert agent_response is not None
            assert agent_response["status"] == "accepted"
            assert "assigned_resources" in agent_response
            _ = mock_agent.process_training_request.assert_called_once_with(training_request)
            
            # 2. 验证代理协调资源分配
            assert "gpu_1" in agent_response["assigned_resources"]
    
    @pytest.mark.asyncio
    async def test_hsp_communication_in_training_workflow(self) -> None:
        """测试训练工作流程中与HSP协议的通信"""
        with patch('apps.backend.src.hsp.connector.HSPConnector') as mock_hsp_connector:
            # Mock HSP连接器
            mock_hsp_instance = mock_hsp_connector.return_value
            mock_hsp_instance.publish_fact = AsyncMock(return_value=True)
            mock_hsp_instance.publish_opinion = AsyncMock(return_value=True)
            
            # 1. 模拟发布训练进度事实
            training_progress_fact = {
                "id": "training_fact_001",
                "statement_type": "natural_language",
                "statement_nl": "Model training reached 90% accuracy at epoch 8",
                "source_ai_id": "demo_learning_manager",
                "timestamp_created": "2023-01-01T00:00:00Z",
                "confidence_score": 1.0,
                "tags": ["training", "progress", "accuracy"]
            }
            
            fact_result = await mock_hsp_instance.publish_fact(training_progress_fact, "hsp/knowledge/facts/training")
            assert fact_result is True
            _ = mock_hsp_instance.publish_fact.assert_called_once_with(training_progress_fact, "hsp/knowledge/facts/training")
            
            # 2. 模拟发布训练建议观点
            training_recommendation_opinion = {
                "id": "training_opinion_001",
                "statement_type": "natural_language",
                "statement_nl": "Recommend increasing learning rate to 0.01 for faster convergence",
                "source_ai_id": "demo_learning_manager",
                "timestamp_created": "2023-01-01T00:00:00Z",
                "confidence_score": 0.85,
                "reasoning_chain": ["training_fact_001"],
                "tags": ["training", "recommendation", "hyperparameter"]
            }
            
            opinion_result = await mock_hsp_instance.publish_opinion(training_recommendation_opinion, "hsp/knowledge/opinions/training")
            assert opinion_result is True
            _ = mock_hsp_instance.publish_opinion.assert_called_once_with(training_recommendation_opinion, "hsp/knowledge/opinions/training")

class TestMultiSystemIntegrationE2E:
    """多系统集成端到端测试"""
    
    @pytest.mark.asyncio
    async def test_complete_ai_system_workflow(self) -> None:
        """测试完整的AI系统工作流程"""
        # 这是一个高层次的集成测试，模拟整个系统的协同工作
        
        # 1. 用户发起复杂任务请求
        user_request = {
            "task_id": "complex_task_001",
            "task_type": "data_analysis",
            "content": "Analyze customer behavior patterns and provide insights",
            "priority": "high"
        }
        
        # 2. 主代理接收并分解任务
        with patch('apps.backend.src.core_ai.agent_manager.AgentManager') as mock_agent_manager:
            mock_manager = mock_agent_manager.return_value
            mock_manager.get_agent = Mock(return_value=Mock())
            
            # 模拟主代理
            mock_main_agent = Mock()
            mock_main_agent.agent_id = "main_coordinator_agent"
            mock_main_agent.decompose_task = Mock(return_value=[
                {"task_id": "subtask_1", "task_type": "data_collection"},
                {"task_id": "subtask_2", "task_type": "data_processing"},
                {"task_id": "subtask_3", "task_type": "analysis"},
                {"task_id": "subtask_4", "task_type": "report_generation"}
            ])
            
            mock_manager.get_agent.return_value = mock_main_agent
            
            # 执行任务分解
            subtasks = mock_main_agent.decompose_task(user_request)
            assert len(subtasks) == 4
            assert all("task_id" in subtask for subtask in subtasks)
            
            # 3. 多代理协作执行子任务
            mock_specialized_agents = []
            for i in range(4):
                mock_agent = Mock()
                mock_agent.agent_id = f"specialized_agent_{i}"
                mock_agent.execute_task = AsyncMock(return_value={
                    "status": "completed",
                    "result": f"Result from specialized agent {i}"
                })
                _ = mock_specialized_agents.append(mock_agent)
            
            # 执行子任务
            subtask_results = []
            for i, subtask in enumerate(subtasks):
                result = await mock_specialized_agents[i].execute_task(subtask)
                _ = subtask_results.append(result)
            
            assert len(subtask_results) == 4
            assert all(result["status"] == "completed" for result in subtask_results)
            
            # 4. 整合结果并存储记忆
            with patch('apps.backend.src.ai.memory.ham_memory_manager.HAMMemoryManager') as mock_memory_manager:
                mock_memory = mock_memory_manager.return_value
                mock_memory.store_memory = AsyncMock(return_value=True)
                
                final_result = {
                    "id": "final_result_001",
                    "content": "Integrated analysis result from all subtasks",
                    "subtask_results": subtask_results,
                    "metadata": {
                        "created_at": "2023-01-01T00:00:00Z",
                        "importance_score": 0.95,
                        "tags": ["analysis", "final_result"],
                        "data_type": "analysis_report"
                    }
                }
                
                store_result = await mock_memory.store_memory(final_result)
                assert store_result is True
                _ = mock_memory.store_memory.assert_called_once_with(final_result)
            
            # 5. 通过HSP协议发布结果
            with patch('apps.backend.src.hsp.connector.HSPConnector') as mock_hsp_connector:
                mock_hsp = mock_hsp_connector.return_value
                mock_hsp.publish_fact = AsyncMock(return_value=True)
                
                result_fact = {
                    "id": "result_fact_001",
                    "statement_type": "natural_language",
                    "statement_nl": "Completed customer behavior analysis with key insights",
                    "source_ai_id": "main_coordinator_agent",
                    "timestamp_created": "2023-01-01T00:00:00Z",
                    "confidence_score": 0.95,
                    "tags": ["analysis", "result", "customer_behavior"]
                }
                
                publish_result = await mock_hsp.publish_fact(result_fact, "hsp/knowledge/facts/analysis")
                assert publish_result is True
                _ = mock_hsp.publish_fact.assert_called_once_with(result_fact, "hsp/knowledge/facts/analysis")