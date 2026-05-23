"""Tests for apps.backend.src.ai.execution.execution_manager"""
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from unittest.mock import MagicMock, patch, AsyncMock

import pytest


class ExecutionStatus(Enum):
    RUNNING = 'running'
    COMPLETED = 'completed'
    TIMEOUT = 'timeout'
    STUCK = 'stuck'
    ERROR = 'error'
    CANCELLED = 'cancelled'


class TerminalStatus(Enum):
    RESPONSIVE = 'responsive'
    SLOW = 'slow'
    STUCK = 'stuck'
    UNRESPONSIVE = 'unresponsive'


@dataclass
class ExecutionConfig:
    default_timeout: float = 60.0
    max_timeout: float = 600.0
    min_timeout: float = 10.0
    check_interval: float = 1.0
    terminal_check_interval: float = 5.0
    cpu_threshold: float = 90.0
    memory_threshold: float = 85.0
    adaptive_timeout: bool = True
    enable_terminal_check: bool = True
    enable_process_monitor: bool = True


@dataclass
class ExecutionResult:
    status: ExecutionStatus = ExecutionStatus.RUNNING
    return_code: Optional[int] = None
    stdout: str = ''
    stderr: str = ''
    execution_time: float = 0.0
    timeout_used: float = 0.0
    terminal_status: Optional[TerminalStatus] = None
    resource_usage: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


execution_monitor_mock = MagicMock()
execution_monitor_mock.ExecutionStatus = ExecutionStatus
execution_monitor_mock.TerminalStatus = TerminalStatus
execution_monitor_mock.ExecutionConfig = ExecutionConfig
execution_monitor_mock.ExecutionResult = ExecutionResult


def make_mock_monitor(**attrs):
    m = MagicMock()
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


execution_monitor_mock.ExecutionMonitor = MagicMock
sys.modules['apps.backend.src.ai.execution.execution_monitor'] = execution_monitor_mock

from apps.backend.src.ai.execution.execution_manager import ExecutionManager, ExecutionManagerConfig


class TestExecutionManagerConfig:
    def test_default_values(self):
        cfg = ExecutionManagerConfig()
        assert cfg.enabled is True
        assert cfg.adaptive_timeout is True
        assert cfg.default_timeout == 60.0
        assert cfg.max_timeout == 600.0
        assert cfg.min_timeout == 10.0
        assert cfg.cpu_warning == 80.0
        assert cfg.cpu_critical == 90.0
        assert cfg.log_level == 'INFO'

    def test_custom_values(self):
        cfg = ExecutionManagerConfig(enabled=False, default_timeout=30.0, log_level='DEBUG')
        assert cfg.enabled is False
        assert cfg.default_timeout == 30.0
        assert cfg.log_level == 'DEBUG'


class TestExecutionManagerInit:
    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    def test_init_with_config(self, mock_monitor_cls):
        mock_monitor = MagicMock()
        mock_monitor_cls.return_value = mock_monitor

        cfg = ExecutionManagerConfig(enabled=False)
        manager = ExecutionManager(config=cfg)
        assert manager.config is cfg
        assert manager.task_queue == {}
        assert manager.execution_status == {}

    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    @patch.object(ExecutionManager, '_load_config_from_system')
    def test_init_without_config_loads_from_system(self, mock_load, mock_monitor_cls):
        mock_load.return_value = ExecutionManagerConfig()
        mock_monitor_cls.return_value = MagicMock()

        manager = ExecutionManager()
        mock_load.assert_called_once()
        assert isinstance(manager.config, ExecutionManagerConfig)


class TestExecutionManagerTaskExecution:
    @pytest.mark.asyncio
    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    async def test_execute_task_default(self, mock_monitor_cls):
        mock_monitor_cls.return_value = MagicMock()
        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=False))

        result = await manager.execute_task({'task_id': 't1'})
        assert result == {'status': 'completed'}
        assert 't1' in manager.task_queue
        assert manager.task_queue['t1'] == {'task_id': 't1'}

    @pytest.mark.asyncio
    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    async def test_execute_task_auto_id(self, mock_monitor_cls):
        mock_monitor_cls.return_value = MagicMock()
        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=False))

        result = await manager.execute_task({'cmd': 'echo hi'})
        assert result == {'status': 'completed'}
        task_ids = list(manager.task_queue.keys())
        assert len(task_ids) == 1
        assert isinstance(task_ids[0], str)

    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    def test_cancel_task_not_found(self, mock_monitor_cls):
        mock_monitor_cls.return_value = MagicMock()
        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=False))

        assert manager.cancel_task('nonexistent') is False

    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    def test_get_task_status_unknown(self, mock_monitor_cls):
        mock_monitor_cls.return_value = MagicMock()
        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=False))

        assert manager.get_task_status('nonexistent') == {'status': 'unknown'}

    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    def test_get_task_status_known(self, mock_monitor_cls):
        mock_monitor_cls.return_value = MagicMock()
        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=False))

        manager.execution_status['t1'] = {'status': 'running'}
        assert manager.get_task_status('t1') == {'status': 'running'}


class TestExecutionManagerExecuteCommand:
    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    def test_execute_command_disabled(self, mock_monitor_cls):
        mock_exec = MagicMock()
        mock_exec.execute_command.return_value = ExecutionResult(
            status=ExecutionStatus.COMPLETED, return_code=0
        )
        mock_monitor_cls.return_value = mock_exec

        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=False))
        result = manager.execute_command('echo hi')
        assert result.status == ExecutionStatus.COMPLETED
        assert result.return_code == 0

    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    def test_execute_command_enabled_success(self, mock_monitor_cls):
        mock_exec = MagicMock()
        mock_exec.execute_command.return_value = ExecutionResult(
            status=ExecutionStatus.COMPLETED, return_code=0, execution_time=1.0
        )
        mock_monitor_cls.return_value = mock_exec

        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=True))
        result = manager.execute_command('echo hi')
        assert result.status == ExecutionStatus.COMPLETED
        assert manager.execution_stats['total_executions'] == 1
        assert manager.execution_stats['successful_executions'] == 1

    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    def test_execute_command_timeout_retry_then_success(self, mock_monitor_cls):
        mock_exec = MagicMock()
        mock_exec.execute_command.side_effect = [
            ExecutionResult(status=ExecutionStatus.TIMEOUT, execution_time=2.0),
            ExecutionResult(status=ExecutionStatus.COMPLETED, return_code=0, execution_time=3.0),
        ]
        mock_monitor_cls.return_value = mock_exec

        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=True, max_retries=3))
        result = manager.execute_command('echo hi')
        assert result.status == ExecutionStatus.COMPLETED
        assert manager.execution_stats['recovered_executions'] == 1

    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    def test_execute_command_error_returns_execution_result(self, mock_monitor_cls):
        mock_exec = MagicMock()
        mock_exec.execute_command.side_effect = RuntimeError('boom')
        mock_monitor_cls.return_value = mock_exec

        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=True))
        result = manager.execute_command('echo hi')
        assert result.status == ExecutionStatus.ERROR
        assert result.error_message is not None


class TestExecutionManagerStatistics:
    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    def test_get_execution_statistics_empty(self, mock_monitor_cls):
        mock_monitor_cls.return_value = MagicMock()
        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=False))

        stats = manager.get_execution_statistics()
        assert stats['total_executions'] == 0
        assert stats['success_rate'] == 0.0
        assert stats['failure_rate'] == 0.0

    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    def test_get_execution_statistics_with_data(self, mock_monitor_cls):
        mock_exec = MagicMock()
        mock_exec.execute_command.return_value = ExecutionResult(
            status=ExecutionStatus.COMPLETED, return_code=0, execution_time=1.0
        )
        mock_monitor_cls.return_value = mock_exec

        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=True))
        manager.execute_command('echo hi')
        stats = manager.get_execution_statistics()
        assert stats['total_executions'] == 1
        assert stats['success_rate'] == 1.0
        assert stats['average_execution_time'] == 1.0

    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    def test_reset_statistics(self, mock_monitor_cls):
        mock_exec = MagicMock()
        mock_exec.execute_command.return_value = ExecutionResult(
            status=ExecutionStatus.COMPLETED, return_code=0, execution_time=1.0
        )
        mock_monitor_cls.return_value = mock_exec

        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=True))
        manager.execute_command('echo hi')
        manager.reset_statistics()
        stats = manager.get_execution_statistics()
        assert stats['total_executions'] == 0
        assert len(manager.issues_log) == 0
        assert len(manager.recovery_actions) == 0


class TestExecutionManagerHealth:
    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    def test_start_health_monitoring_disabled(self, mock_monitor_cls):
        mock_monitor_cls.return_value = MagicMock()
        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=False))
        manager.start_health_monitoring()
        assert manager._monitoring_active is False

    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    def test_stop_health_monitoring_when_not_started(self, mock_monitor_cls):
        mock_monitor_cls.return_value = MagicMock()
        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=True))
        manager.stop_health_monitoring()
        assert manager._monitoring_active is False

    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    def test_context_manager(self, mock_monitor_cls):
        mock_monitor_cls.return_value = MagicMock()
        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=True))
        with manager as m:
            assert m._monitoring_active is True
        assert m._monitoring_active is False

    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    def test_get_system_health_report(self, mock_monitor_cls):
        mock_exec = MagicMock()
        mock_exec.get_system_health.return_value = {'cpu_percent': 50.0}
        mock_monitor_cls.return_value = mock_exec

        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=False))
        report = manager.get_system_health_report()
        assert 'system_health' in report
        assert 'execution_stats' in report
        assert 'recent_issues' in report
        assert 'config' in report


class TestExecutionManagerResourceThresholds:
    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    def test_check_resource_thresholds_cpu_warning(self, mock_monitor_cls):
        mock_monitor_cls.return_value = MagicMock()
        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=True))
        manager._check_resource_thresholds({'cpu_percent': 85.0, 'memory_percent': 50.0, 'disk_percent': 50.0})
        assert len(manager.issues_log) == 1
        assert manager.issues_log[0]['resource'] == 'cpu'
        assert manager.issues_log[0]['severity'] == 'warning'

    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    def test_check_resource_thresholds_memory_critical(self, mock_monitor_cls):
        mock_monitor_cls.return_value = MagicMock()
        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=True))
        manager._check_resource_thresholds({'cpu_percent': 50.0, 'memory_percent': 90.0, 'disk_percent': 50.0})
        assert len(manager.issues_log) == 1
        assert manager.issues_log[0]['resource'] == 'memory'
        assert manager.issues_log[0]['severity'] == 'critical'

    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    def test_check_resource_thresholds_disk_warning(self, mock_monitor_cls):
        mock_monitor_cls.return_value = MagicMock()
        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=True))
        manager._check_resource_thresholds({'cpu_percent': 50.0, 'memory_percent': 50.0, 'disk_percent': 82.0})
        assert len(manager.issues_log) == 1
        assert manager.issues_log[0]['resource'] == 'disk'
        assert manager.issues_log[0]['severity'] == 'warning'


class TestExecutionManagerAsyncCommand:
    @pytest.mark.asyncio
    @patch('apps.backend.src.ai.execution.execution_manager.ExecutionMonitor')
    async def test_execute_async_command(self, mock_monitor_cls):
        mock_exec = MagicMock()
        mock_exec.execute_async_command = AsyncMock(return_value=ExecutionResult(
            status=ExecutionStatus.COMPLETED, return_code=0
        ))
        mock_monitor_cls.return_value = mock_exec

        manager = ExecutionManager(config=ExecutionManagerConfig(enabled=False))
        result = await manager.execute_async_command('echo hi')
        assert result.status == ExecutionStatus.COMPLETED
