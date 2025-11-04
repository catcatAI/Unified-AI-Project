import pytest
from unittest.mock import AsyncMock, MagicMock

# Correct import paths for DemoLearningManager and ExecutionManager
from apps.backend.src.ai.learning.demo_learning_manager import DemoLearningManager
from apps.backend.src.ai.execution.execution_manager import ExecutionManager

class TestTrainingManager:
    """训练系统组件单元测试"""
    
    @pytest.fixture
    def demo_learning_manager(self):
        """创建DemoLearningManager实例"""
        manager = DemoLearningManager()
        return manager
    
    @pytest.fixture
    def execution_manager(self):
        """创建ExecutionManager实例"""
        manager = ExecutionManager()
        return manager
    
    
    def test_demo_learning_manager_init(self, demo_learning_manager) -> None:
        """测试DemoLearningManager初始化"""
        assert demo_learning_manager is not None
        assert hasattr(demo_learning_manager, 'training_configs')
        assert hasattr(demo_learning_manager, 'model_registry')
    
    def test_execution_manager_init(self, execution_manager) -> None:
        """测试ExecutionManager初始化"""
        assert execution_manager is not None
        assert hasattr(execution_manager, 'task_queue')
        assert hasattr(execution_manager, 'execution_status')
    
    @pytest.mark.asyncio
    async def test_demo_learning_manager_start_learning(self, demo_learning_manager) -> None:
        """测试开始学习"""
        # Mock依赖组件
        demo_learning_manager.model_trainer = AsyncMock()
        demo_learning_manager.model_trainer.train = AsyncMock(return_value={"status": "completed"})
        
        result = await demo_learning_manager.start_learning("test_model", {"epochs": 10})
        assert result is not None
        assert "status" in result
        demo_learning_manager.model_trainer.train.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_demo_learning_manager_stop_learning(self, demo_learning_manager) -> None:
        """测试停止学习"""
        # Mock依赖组件
        demo_learning_manager.model_trainer = AsyncMock()
        demo_learning_manager.model_trainer.stop = AsyncMock(return_value=True)
        
        result = await demo_learning_manager.stop_learning("test_model")
        assert result is True
        demo_learning_manager.model_trainer.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execution_manager_execute_task(self, execution_manager) -> None:
        """测试执行任务"""
        task = {
            "task_id": "test_task_001",
            "task_type": "training",
            "parameters": {"model": "test_model", "epochs": 10}
        }
        
        # Mock执行函数
        execution_manager._execute_training_task = AsyncMock(return_value={"status": "completed"})
        
        result = await execution_manager.execute_task(task)
        assert result is not None
        assert "status" in result
        execution_manager._execute_training_task.assert_called_once_with(task)
    
    @pytest.mark.asyncio
    async def test_execution_manager_get_task_status(self, execution_manager) -> None:
        """测试获取任务状态"""
        task_id = "test_task_001"
        execution_manager.execution_status[task_id] = {"status": "running"}
        
        status = execution_manager.get_task_status(task_id)
        assert status is not None
        assert status["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_execution_manager_cancel_task(self, execution_manager) -> None:
        """测试取消任务"""
        task_id = "test_task_001"
        execution_manager.task_queue[task_id] = AsyncMock()
        execution_manager.task_queue[task_id].cancel = MagicMock(return_value=True)
        
        result = execution_manager.cancel_task(task_id)
        assert result is True
        execution_manager.task_queue[task_id].cancel.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_demo_learning_manager_get_model_status(self, demo_learning_manager) -> None:
        """测试获取模型状态"""
        model_id = "test_model"
        demo_learning_manager.model_registry[model_id] = {
            "status": "trained",
            "metrics": {"accuracy": 0.95}
        }
        
        status = demo_learning_manager.get_model_status(model_id)
        assert status is not None
        assert status["status"] == "trained"
        assert "metrics" in status
    
    @pytest.mark.asyncio
    async def test_demo_learning_manager_list_models(self, demo_learning_manager) -> None:
        """测试列出模型"""
        demo_learning_manager.model_registry["model_1"] = {"status": "trained"}
        demo_learning_manager.model_registry["model_2"] = {"status": "training"}
        
        models = demo_learning_manager.list_models()
        assert len(models) == 2
        assert "model_1" in models
        assert "model_2" in models
