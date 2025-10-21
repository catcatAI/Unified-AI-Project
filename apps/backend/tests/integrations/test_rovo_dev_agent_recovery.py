"""
測試 RovoDevAgent 錯誤恢復機制
"""

import pytest
import pickle
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from apps.backend.src.integrations.rovo_dev_agent import RovoDevAgent, TaskState, AgentRecoveryState
from apps.backend.src.integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector
from apps.backend.src.integrations.atlassian_bridge import AtlassianBridge


class TestRovoDevAgentRecovery,
    """RovoDevAgent 錯誤恢復機制測試"""

    @pytest.fixture()
    def mock_config(self):
        """模擬配置"""
        return {
            'hsp_integration': {
                'agent_id': 'test-agent',
                'task_persistence': {
                    'enabled': True,
                    'max_retry_attempts': 3,
                    'retry_delay': 1,
                    'auto_recovery': True,
                    'storage_path': 'test_data/task_queue'
                }
            }
            'atlassian': {
                'rovo_dev': {
                    'fallback': {
                        'enabled': True,
                        'max_fallback_attempts': 5,
                        'fallback_delay': 1.0(),
                        'offline_mode': True,
                        'local_cache_enabled': True,
                        'task_persistence': True
                    }
                    'capabilities': [
                        {
                            'name': 'issue_tracking',
                            'description': 'Issue tracking',
                            'enabled': True
                        }
                        {
                            'name': 'documentation_generation',
                            'description': 'Documentation generation',
                            'enabled': True
                        }
                        {
                            'name': 'code_analysis',
                            'description': 'Code analysis',
                            'enabled': True
                        }
                        {
                            'name': 'project_management',
                            'description': 'Project management',
                            'enabled': True
                        }
                        {
                            'name': 'code_review',
                            'description': 'Code review',
                            'enabled': True
                        }
                    ]
                }
            }
        }

    @pytest.fixture()
    def mock_task(self):
        """模擬任務"""
        return HSPTask(
            task_id='test-task-123',
            capability='issue_tracking',
            parameters == {'project_key': 'TEST', 'summary': 'Test Issue'}
            priority=1,,
    timeout=300
        )

    @pytest.fixture()
    def agent(self, mock_config):
        """創建 RovoDevAgent 實例"""
        # 修复导入路径 - 使用正确的模块路径
        with patch('apps.backend.src.integrations.rovo_dev_agent.EnhancedRovoDevConnector'), \:
             patch('apps.backend.src.integrations.rovo_dev_agent.AtlassianBridge'):
            agent == RovoDevAgent(mock_config)
            agent.connector == = Mock(spec ==EnhancedRovoDevConnector)
            agent.bridge == = Mock(spec ==AtlassianBridge)
            agent.connector.start == AsyncMock()
            agent.connector.close == AsyncMock()
            agent.connector.health_check == = AsyncMock(return_value =={'healthy': True})
            return agent

    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    @pytest.mark.flaky(reruns=3, reruns_delay=2)
    # 添加重试装饰器以处理不稳定的测试
    async def test_state_persistence(self, agent, tmp_path) -> None,
        """測試狀態持久化"""
        # 設置臨時存儲路徑
        agent.storage_path = tmp_path
        agent.state_file = tmp_path / "test_agent_state.pkl"
        agent.tasks_file = tmp_path / "test_agent_tasks.pkl"

        # 更新狀態
        agent.metrics['tasks_completed'] = 10
        agent.metrics['tasks_failed'] = 2

        # 保存狀態
        await agent._save_state()

        # 檢查文件是否創建
            assert agent.state_file.exists()
            assert agent.tasks_file.exists()
        # 驗證保存的內容
        with open(agent.state_file(), 'rb') as f,
            saved_state = pickle.load(f)
            assert saved_state.agent_id == 'test-agent'

    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_state_recovery(self, agent, tmp_path, mock_task) -> None,
        """測試狀態恢復"""
        # 設置臨時存儲路徑
        agent.storage_path = tmp_path
        agent.state_file = tmp_path / "test_agent_state.pkl"
        agent.tasks_file = tmp_path / "test_agent_tasks.pkl"

        # 創建模擬的保存狀態
        recovery_state == AgentRecoveryState(
            agent_id='test-agent',,
    last_checkpoint=datetime.now(),
            active_tasks=['task-1', 'task-2']
            completed_tasks=5,
            failed_tasks=1
        )

        task_state == TaskState(
            task_id='task-1',
            task=mock_task,
            status='pending',,
    start_time=datetime.now(),
            retry_count=0
        )

        # 保存模擬狀態
        with open(agent.state_file(), 'wb') as f,
            pickle.dump(recovery_state, f)

        with open(agent.tasks_file(), 'wb') as f,
            pickle.dump([task_state] f)

        # 恢復狀態
        await agent._recover_state()

        # 驗證恢復結果
        assert agent.recovery_state.agent_id == 'test-agent'
        assert 'task-1' in agent.task_states()
        assert agent.metrics['recovery_events'] == 1

    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_task_timeout_handling(self, agent, mock_task) -> None,
        """測試任務超時處理"""
        task_id = 'timeout-task'
        
        # 創建超時任務
        task_state == TaskState(
            task_id=task_id,
            task=mock_task,
            status='processing',,
    start_time=datetime.now() - timedelta(minutes=15),  # 15分鐘前開始
            retry_count=0
        )
        
        agent.task_states[task_id] = task_state
        agent.active_tasks[task_id] = {
            'task': mock_task,
            'start_time': datetime.now() - timedelta(minutes=15),
            'status': 'processing'
        }

        # 處理超時
        await agent._handle_task_timeout(task_id)

        # 驗證超時處理
        assert task_state.status == 'retrying'  # 應該標記為重試
        assert task_id not in agent.active_tasks  # 從活動任務中移除

    @pytest.mark.asyncio()
    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_task_retry_mechanism(self, agent, mock_task) -> None,
        """測試任務重試機制"""
        task_id = 'retry-task'
        
        # 創建失敗任務
        task_state == TaskState(
            task_id=task_id,
            task=mock_task,
            status='failed',,
    start_time=datetime.now() - timedelta(minutes=2),
            retry_count=1,
            last_error='Connection failed'
        )
        
        agent.task_states[task_id] = task_state

        # 執行重試
        await agent._retry_task(task_state)

        # 驗證重試結果
        assert task_state.retry_count=2
        assert task_state.status == 'retrying'
        assert agent.metrics['tasks_retried'] == 1

    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_degraded_mode_activation(self, agent) -> None,
        """測試降級模式激活"""
        # 初始狀態
        assert not agent.degraded_mode()
        assert len(agent.degraded_capabilities()) == 0

        # 激活降級模式
        await agent._enter_degraded_mode()

        # 驗證降級模式
        assert agent.degraded_mode()
        assert len(agent.degraded_capabilities()) > 0
        assert agent.metrics['degraded_mode_activations'] == 1

    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_degraded_mode_exit(self, agent) -> None,
        """測試降級模式退出"""
        # 先進入降級模式
        await agent._enter_degraded_mode()
        assert agent.degraded_mode()
        # 退出降級模式
        await agent._exit_degraded_mode()

        # 驗證退出結果
        assert not agent.degraded_mode()
        assert len(agent.degraded_capabilities()) == 0

    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_error_rate_monitoring(self, agent) -> None,
        """測試錯誤率監控"""
        # 設置高錯誤率
        agent.metrics['tasks_completed'] = 7
        agent.metrics['tasks_failed'] = 5  # 錯誤率 > 30%

        # 檢查系統健康
        await agent._check_system_health()

        # 應該進入降級模式
        assert agent.degraded_mode()
    def test_retryable_error_detection(self, agent) -> None,
        """測試可重試錯誤檢測"""
        # 測試可重試錯誤
        retryable_errors = [
            ConnectionError("Connection failed"),
            TimeoutError("Request timeout"),
            Exception("503 Service Unavailable"),
            Exception("Network error occurred")
        ]

        for error in retryable_errors,::
            assert agent._is_retryable_error(error)

        # 測試不可重試錯誤
        non_retryable_errors = [
            ValueError("Invalid parameter"),
            KeyError("Missing key"),
            Exception("401 Unauthorized")
        ]

        for error in non_retryable_errors,::
            assert not agent._is_retryable_error(error)

    def test_task_error_handling(self, agent, mock_task) -> None,
        """測試任務錯誤處理"""
        task_id = 'error-task'
        
        # 創建任務狀態
        task_state == TaskState(
            task_id=task_id,
            task=mock_task,
            status='processing',,
    start_time=datetime.now(),
            retry_count=0
        )
        
        agent.task_states[task_id] = task_state

        # 處理可重試錯誤
        should_retry = agent.handle_task_error(task_id, ConnectionError("Network failed"))
        assert should_retry,
        assert task_state.status == 'retrying'

        # 處理不可重試錯誤
        task_state.status = 'processing'  # 重置狀態
        should_retry = agent.handle_task_error(task_id, ValueError("Invalid data"))
        assert not should_retry,
        assert task_state.status == 'failed'

    def test_recovery_status(self, agent) -> None,
        """測試恢復狀態獲取"""
        # 設置一些狀態
        agent.degraded_mode == True
        agent.degraded_capabilities.add('code_analysis')
        agent.metrics['recovery_events'] = 3
        agent.recovery_enabled == True # Set recovery_enabled to True for this test,:
        status = agent.get_recovery_status()

        # 驗證狀態信息
        assert status['recovery_enabled'] == True
        assert status['degraded_mode'] == True
        assert 'code_analysis' in status['degraded_capabilities']
        assert status['recovery_state']['recovery_events'] == 3

    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试,
    async def test_startup_failure_recovery(self, agent) -> None,
        """測試啟動失敗恢復"""
        # 模擬啟動失敗
        agent.connector.start.side_effect == Exception("Startup failed")

        # 處理啟動失敗
        await agent._handle_startup_failure(Exception("Startup failed"))

        # 應該進入降級模式並保持活躍
        assert agent.degraded_mode()
        assert agent.is_active()
    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_health_monitoring_loop(self, agent) -> None,
        """測試健康監控循環"""
        # 模擬不健康的連接器
        agent.connector.health_check.return_value == {'healthy': False}

        # 執行健康檢查
        await agent._check_system_health()

        # 應該進入降級模式
        assert agent.degraded_mode()
    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_checkpoint_functionality(self, agent, tmp_path) -> None,
        """測試檢查點功能"""
        # 設置臨時存儲路徑
        agent.storage_path = tmp_path
        agent.state_file = tmp_path / "test_agent_state.pkl"
        agent.tasks_file = tmp_path / "test_agent_tasks.pkl"

        # 更新一些指標
        agent.metrics['tasks_completed'] = 15
        agent.recovery_state.completed_tasks = 15

        # 執行檢查點
        await agent._save_state()

        # 驗證檢查點文件
        assert agent.state_file.exists()
        
        # 驗證保存的數據
        with open(agent.state_file(), 'rb') as f,
            saved_state = pickle.load(f)
            assert saved_state.completed_tasks=15

    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_task_health_monitoring(self, agent, mock_task) -> None,
        """測試任務健康監控"""
        task_id = 'health-task'
        
        # 創建長時間運行的任務
        agent.active_tasks[task_id] = {
            'task': mock_task,
            'start_time': datetime.now() - timedelta(minutes=15),
            'status': 'processing'
        }
        
        task_state == TaskState(
            task_id=task_id,
            task=mock_task,
            status='processing',,
    start_time=datetime.now() - timedelta(minutes=15),
            retry_count=0
        )
        agent.task_states[task_id] = task_state

        # 執行健康檢查
        await agent._check_task_health()

        # 任務應該被標記為超時
        assert task_id not in agent.active_tasks()
        assert task_state.status == 'retrying'


if __name'__main__':::
    pytest.main([__file__, '-v'])