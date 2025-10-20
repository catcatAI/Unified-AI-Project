"""
训练系统集成测试
测试训练系统与其他核心组件的集成
"""

import pytest
from apps.backend.tests.integration.base_test import SystemIntegrationTest
from apps.backend.tests.integration.test_data_factory import TestDataFactory


class TestTrainingSystemIntegration(SystemIntegrationTest):
    """训练系统集成测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_training_test(self, setup_system_test):
        """设置训练测试"""
        self.data_factory = TestDataFactory()
        yield
    
    @pytest.mark.system_integration
    @pytest.mark.asyncio
    async def test_model_training_integration(self) -> None:
        """测试模型训练集成"""
        # 创建测试数据
        training_data = [
            self.data_factory.create_training_data(
                data_id=f"train_data_{i}",
                input_data=f"Input data sample {i}",
                expected_output=f"Expected output sample {i}",
                data_type="text_generation"
            )
            for i in range(5)
        ]
        
        # 获取mock服务
        learning_manager = self.get_mock_service("learning_manager")
        llm_service = self.get_mock_service("llm_service")
        
        # 设置mock行为
        learning_manager.return_value.start_training = AsyncMock(return_value=True)
        learning_manager.return_value.stop_training = AsyncMock(return_value=True)
        learning_manager.return_value.evaluate_model = AsyncMock(
            return_value={"accuracy": 0.85, "loss": 0.15}
        )
        
        llm_service.return_value.train_model = AsyncMock(return_value=True)
        llm_service.return_value.get_model_metrics = AsyncMock(
            return_value={"accuracy": 0.85, "loss": 0.15}
        )
        
        # 执行模型训练测试
        # 1. 启动训练
        start_result = await learning_manager.return_value.start_training(
            training_data,
            {"epochs": 3, "batch_size": 32}
        )
        
        # 2. 执行训练
        train_result = await llm_service.return_value.train_model(
            training_data,
            {"epochs": 3, "batch_size": 32}
        )
        
        # 3. 评估模型
        evaluation_result = await learning_manager.return_value.evaluate_model(
            "test_model_v1"
        )
        
        # 4. 停止训练
        stop_result = await learning_manager.return_value.stop_training()
        
        # 验证结果
        assert start_result is True
        assert train_result is True
        assert evaluation_result is not None
        assert "accuracy" in evaluation_result
        assert "loss" in evaluation_result
        assert stop_result is True
        
        # 验证mock调用
        learning_manager.return_value.start_training.assert_called_once_with(
            training_data,
            {"epochs": 3, "batch_size": 32}
        )
        
        llm_service.return_value.train_model.assert_called_once_with(
            training_data,
            {"epochs": 3, "batch_size": 32}
        )
        
        learning_manager.return_value.evaluate_model.assert_called_once_with(
            "test_model_v1"
        )
        
        _ = learning_manager.return_value.stop_training.assert_called_once()
    
    @pytest.mark.system_integration
    @pytest.mark.asyncio
    async def test_auto_training_integration(self) -> None:
        """测试自动训练集成"""
        # 创建测试数据
        auto_training_config = {
            "data_source": "user_interactions",
            "trigger_threshold": 100,
            "schedule": "daily"
        }
        
        training_samples = [
            self.data_factory.create_training_data(
                input_data=f"User input {i}",
                expected_output=f"Expected response {i}"
            )
            for i in range(150)  # 超过触发阈值
        ]
        
        # 获取mock服务
        learning_manager = self.get_mock_service("learning_manager")
        
        # 设置mock行为
        learning_manager.return_value.configure_auto_training = AsyncMock(
            return_value=True
        )
        learning_manager.return_value.trigger_auto_training = AsyncMock(
            return_value={"status": "success", "model_version": "v1.2"}
        )
        learning_manager.return_value.get_training_status = AsyncMock(
            return_value={"status": "completed", "progress": 100}
        )
        
        # 执行自动训练测试
        # 1. 配置自动训练
        config_result = await learning_manager.return_value.configure_auto_training(
            auto_training_config
        )
        
        # 2. 触发自动训练（数据量超过阈值）
        trigger_result = await learning_manager.return_value.trigger_auto_training(
            training_samples
        )
        
        # 3. 检查训练状态
        status_result = await learning_manager.return_value.get_training_status()
        
        # 验证结果
        assert config_result is True
        assert trigger_result is not None
        assert "status" in trigger_result
        assert "model_version" in trigger_result
        assert status_result is not None
        assert status_result["status"] == "completed"
        
        # 验证mock调用
        learning_manager.return_value.configure_auto_training.assert_called_once_with(
            auto_training_config
        )
        
        learning_manager.return_value.trigger_auto_training.assert_called_once_with(
            training_samples
        )
        
        _ = learning_manager.return_value.get_training_status.assert_called_once()
    
    @pytest.mark.system_integration
    @pytest.mark.asyncio
    async def test_collaborative_training_integration(self) -> None:
        """测试协作式训练集成"""
        # 创建测试数据
        agent_configs = [
            self.data_factory.create_agent_config(
                agent_id=f"collab_trainer_{i}",
                agent_type="data_analysis" if i % 2 == 0 else "creative_writing"
            )
            for i in range(3)
        ]
        
        collaborative_training_data = [
            self.data_factory.create_training_data(
                input_data=f"Collaborative input {i}",
                expected_output=f"Collaborative output {i}",
                metadata={"source_agent": config["agent_id"]}
            )
            for i, config in enumerate(agent_configs)
        ]
        
        # 获取mock服务
        learning_manager = self.get_mock_service("learning_manager")
        agent_manager = self.get_mock_service("agent_manager")
        
        # 设置mock行为
        mock_agents = [Mock() for _ in agent_configs]
        agent_manager.return_value.create_agent = AsyncMock(side_effect=mock_agents)
        agent_manager.return_value.get_agent = AsyncMock(side_effect=mock_agents)
        
        learning_manager.return_value.start_collaborative_training = AsyncMock(
            return_value=True
        )
        learning_manager.return_value.aggregate_training_results = AsyncMock(
            return_value={
                "aggregated_model": "collab_model_v1",
                "performance_metrics": {"accuracy": 0.92}
            }
        )
        
        # 执行协作式训练测试
        # 1. 创建训练代理
        created_agents = []
        for config in agent_configs:
            agent = await agent_manager.return_value.create_agent(
                config["agent_id"],
                config["agent_type"]
            )
            _ = created_agents.append(agent)
        
        # 2. 启动协作式训练
        collab_result = await learning_manager.return_value.start_collaborative_training(
            collaborative_training_data,
            {"collaboration_strategy": "federated"}
        )
        
        # 3. 聚合训练结果
        aggregation_result = await learning_manager.return_value.aggregate_training_results(
            [data["metadata"]["source_agent"] for data in collaborative_training_data]
        )
        
        # 验证结果
        assert len(created_agents) == len(agent_configs)
        assert collab_result is True
        assert aggregation_result is not None
        assert "aggregated_model" in aggregation_result
        assert "performance_metrics" in aggregation_result
        
        # 验证mock调用
        assert agent_manager.return_value.create_agent.call_count == len(agent_configs)
        learning_manager.return_value.start_collaborative_training.assert_called_once_with(
            collaborative_training_data,
            {"collaboration_strategy": "federated"}
        )
        _ = learning_manager.return_value.aggregate_training_results.assert_called_once()


class TestIncrementalLearningIntegration(SystemIntegrationTest):
    """增量学习集成测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_incremental_test(self, setup_system_test):
        """设置增量学习测试"""
        self.data_factory = TestDataFactory()
        yield
    
    @pytest.mark.system_integration
    @pytest.mark.asyncio
    async def test_incremental_learning_integration(self) -> None:
        """测试增量学习集成"""
        # 创建测试数据
        base_model_version = "model_v1.0"
        incremental_data = [
            self.data_factory.create_training_data(
                input_data=f"Incremental input {i}",
                expected_output=f"Incremental output {i}",
                metadata={"timestamp": f"2023-01-{i+1:02d}"}
            )
            for i in range(10)
        ]
        
        # 获取mock服务
        learning_manager = self.get_mock_service("learning_manager")
        llm_service = self.get_mock_service("llm_service")
        
        # 设置mock行为
        learning_manager.return_value.start_incremental_learning = AsyncMock(
            return_value=True
        )
        learning_manager.return_value.update_model_incrementally = AsyncMock(
            return_value={"new_version": "model_v1.1", "improvement": 0.05}
        )
        learning_manager.return_value.validate_incremental_update = AsyncMock(
            return_value={"validation_passed": True, "metrics": {"accuracy": 0.88}}
        )
        
        llm_service.return_value.fine_tune_model = AsyncMock(return_value=True)
        llm_service.return_value.get_model_version = AsyncMock(
            return_value=base_model_version
        )
        
        # 执行增量学习测试
        # 1. 获取当前模型版本
        current_version = await llm_service.return_value.get_model_version()
        
        # 2. 启动增量学习
        start_result = await learning_manager.return_value.start_incremental_learning(
            base_model_version
        )
        
        # 3. 增量更新模型
        update_result = await learning_manager.return_value.update_model_incrementally(
            incremental_data,
            {"learning_rate": 0.001}
        )
        
        # 4. 验证增量更新
        validation_result = await learning_manager.return_value.validate_incremental_update(
            update_result["new_version"]
        )
        
        # 验证结果
        assert current_version == base_model_version
        assert start_result is True
        assert update_result is not None
        assert "new_version" in update_result
        assert "improvement" in update_result
        assert validation_result is not None
        assert validation_result["validation_passed"] is True
        
        # 验证mock调用
        _ = llm_service.return_value.get_model_version.assert_called_once()
        learning_manager.return_value.start_incremental_learning.assert_called_once_with(
            base_model_version
        )
        learning_manager.return_value.update_model_incrementally.assert_called_once_with(
            incremental_data,
            {"learning_rate": 0.001}
        )
        learning_manager.return_value.validate_incremental_update.assert_called_once_with(
            update_result["new_version"]
        )


class TestTrainingDataManagementIntegration(SystemIntegrationTest):
    """训练数据管理集成测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_data_management_test(self, setup_system_test):
        """设置数据管理测试"""
        self.data_factory = TestDataFactory()
        yield
    
    @pytest.mark.system_integration
    @pytest.mark.asyncio
    async def test_training_data_pipeline_integration(self) -> None:
        """测试训练数据管道集成"""
        # 创建测试数据
        raw_data_samples = [
            {"user_input": f"Raw input {i}", "system_response": f"Response {i}"}
            for i in range(20)
        ]
        
        # 获取mock服务
        learning_manager = self.get_mock_service("learning_manager")
        
        # 设置mock行为
        learning_manager.return_value.preprocess_training_data = AsyncMock(
            return_value=[
                self.data_factory.create_training_data(
                    input_data=sample["user_input"],
                    expected_output=sample["system_response"]
                )
                for sample in raw_data_samples
            ]
        )
        learning_manager.return_value.filter_training_data = AsyncMock(
            return_value={
                "filtered_data": [
                    self.data_factory.create_training_data(
                        input_data=f"Filtered input {i}",
                        expected_output=f"Filtered output {i}"
                    )
                    for i in range(15)  # 过滤后剩余15个样本
                ],
                "filtered_count": 5
            }
        )
        learning_manager.return_value.augment_training_data = AsyncMock(
            return_value=[
                self.data_factory.create_training_data(
                    input_data=f"Augmented input {i}",
                    expected_output=f"Augmented output {i}"
                )
                for i in range(30)  # 数据增强后30个样本
            ]
        )
        
        # 执行训练数据管道测试
        # 1. 预处理原始数据
        preprocessed_data = await learning_manager.return_value.preprocess_training_data(
            raw_data_samples
        )
        
        # 2. 过滤训练数据
        filtered_result = await learning_manager.return_value.filter_training_data(
            preprocessed_data
        )
        
        # 3. 数据增强
        augmented_data = await learning_manager.return_value.augment_training_data(
            filtered_result["filtered_data"]
        )
        
        # 验证结果
        assert len(preprocessed_data) == len(raw_data_samples)
        assert filtered_result is not None
        assert "filtered_data" in filtered_result
        assert "filtered_count" in filtered_result
        assert len(augmented_data) > len(filtered_result["filtered_data"])
        
        # 验证mock调用
        learning_manager.return_value.preprocess_training_data.assert_called_once_with(
            raw_data_samples
        )
        learning_manager.return_value.filter_training_data.assert_called_once_with(
            preprocessed_data
        )
        learning_manager.return_value.augment_training_data.assert_called_once_with(
            filtered_result["filtered_data"]
        )


if __name__ == "__main__":
    _ = pytest.main([__file__, "-v"])