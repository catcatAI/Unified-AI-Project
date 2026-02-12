"""
Execution Manager - 執行管理器
整合執行監控、超時控制和自動恢復的統一管理器 (SKELETON)
"""

import logging
import threading
import time
import os
import yaml # type: ignore
import psutil # type: ignore
import gc # type: ignore
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Union

# Mock dependencies for syntax validation
class ExecutionStatus:
    COMPLETED = "COMPLETED"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"

class TerminalStatus:
    STUCK = "STUCK"
    UNRESPONSIVE = "UNRESPONSIVE"

@dataclass
class ExecutionResult:
    status: str = ExecutionStatus.COMPLETED
    output: str = ""
    error_message: Optional[str] = None
    return_code: Optional[int] = None
    execution_time: float = 0.0
    timeout_used: float = 0.0
    terminal_status: Optional[str] = None

@dataclass
class ExecutionConfig:
    default_timeout: float = 30.0
    max_timeout: float = 300.0
    min_timeout: float = 5.0
    adaptive_timeout: bool = True
    enable_terminal_check: bool = True
    enable_process_monitor: bool = True
    cpu_threshold: float = 90.0
    memory_threshold: float = 85.0

class ExecutionMonitor:
    def __init__(self, config: ExecutionConfig): pass
    def execute_command(self, command: Union[str, List[str]], timeout: Optional[float], **kwargs) -> ExecutionResult: return ExecutionResult()
    async def execute_async_command(self, command: Union[str, List[str]], timeout: Optional[float], **kwargs) -> ExecutionResult: return ExecutionResult()
    def get_system_health(self) -> Dict[str, Any]: return {}

logger = logging.getLogger(__name__)

@dataclass
class ExecutionManagerConfig:
    """執行管理器配置"""
    enabled: bool = True
    adaptive_timeout: bool = True
    terminal_monitoring: bool = True
    resource_monitoring: bool = True
    auto_recovery: bool = True

    default_timeout: float = 60.0
    max_timeout: float = 600.0
    min_timeout: float = 10.0

    cpu_warning: float = 80.0
    cpu_critical: float = 90.0
    memory_warning: float = 75.0
    memory_critical: float = 85.0
    disk_warning: float = 80.0
    disk_critical: float = 90.0

    history_size: int = 50
    timeout_multiplier: float = 2.5
    slow_terminal_multiplier: float = 1.5
    stuck_terminal_multiplier: float = 2.0
    cache_size: int = 100

    stuck_process_timeout: float = 60.0
    max_retry_attempts: int = 3
    retry_delay: float = 5.0
    escalation_enabled: bool = True

    log_level: str = "INFO"
    log_execution_details: bool = True
    log_resource_usage: bool = False
    log_terminal_status: bool = False

class ExecutionManager:
    """執行管理器 - 統一的執行監控和管理系統 (SKELETON)"""

    def __init__(self, config: Optional[ExecutionManagerConfig] = None) -> None:
        self.config = config or self._load_config_from_system()
        self.logger = self._setup_logger()
        
        monitor_config = ExecutionConfig(
            default_timeout=self.config.default_timeout,
            max_timeout=self.config.max_timeout,
            min_timeout=self.config.min_timeout,
            adaptive_timeout=self.config.adaptive_timeout,
            enable_terminal_check=self.config.terminal_monitoring,
            enable_process_monitor=self.config.resource_monitoring,
            cpu_threshold=self.config.cpu_critical,
            memory_threshold=self.config.memory_critical
        )
        self.monitor = ExecutionMonitor(monitor_config)

        self.execution_stats: Dict[str, Any] = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'timeout_executions': 0,
            'recovered_executions': 0,
            'average_execution_time': 0.0
        }
        self.issues_log: List[Dict[str, Any]] = []
        self.recovery_actions: List[Dict[str, Any]] = []

        self._monitoring_active = False
        self._health_check_thread: Optional[threading.Thread] = None

        self.logger.info("ExecutionManager Skeleton Initialized")

    def _load_config_from_system(self) -> ExecutionManagerConfig:
        try:
            config_path = Path("configs/system_config.yaml")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    system_config = yaml.safe_load(f)

                operational_configs = system_config.get('operational_configs', {})
                execution_config_data = operational_configs.get('execution_monitor', {})
                timeouts_data = operational_configs.get('timeouts', {})
                recovery_data = execution_config_data.get('recovery_strategies', {})
                logging_data = execution_config_data.get('logging', {})
                adaptive_timeout_data = execution_config_data.get('adaptive_timeout_config', {})
                thresholds_data = execution_config_data.get('thresholds', {})

                return ExecutionManagerConfig(
                    enabled=execution_config_data.get('enabled', True),
                    adaptive_timeout=execution_config_data.get('adaptive_timeout', True),
                    terminal_monitoring=execution_config_data.get('terminal_monitoring', True),
                    resource_monitoring=execution_config_data.get('resource_monitoring', True),
                    auto_recovery=execution_config_data.get('auto_recovery', True),

                    default_timeout=timeouts_data.get('command_execution_default', 30.0),
                    max_timeout=timeouts_data.get('command_execution_max', 300.0),
                    min_timeout=timeouts_data.get('command_execution_min', 5.0),

                    cpu_warning=thresholds_data.get('cpu_warning', 80.0),
                    cpu_critical=thresholds_data.get('cpu_critical', 90.0),
                    memory_warning=thresholds_data.get('memory_warning', 75.0),
                    memory_critical=thresholds_data.get('memory_critical', 85.0),
                    disk_warning=thresholds_data.get('disk_warning', 80.0),
                    disk_critical=thresholds_data.get('disk_critical', 90.0),

                    history_size=adaptive_timeout_data.get('history_size', 50),
                    timeout_multiplier=adaptive_timeout_data.get('timeout_multiplier', 2.5),
                    slow_terminal_multiplier=adaptive_timeout_data.get('slow_terminal_multiplier', 1.5),
                    stuck_terminal_multiplier=adaptive_timeout_data.get('stuck_terminal_multiplier', 2.0),
                    cache_size=adaptive_timeout_data.get('cache_size', 100),

                    stuck_process_timeout=recovery_data.get('stuck_process_timeout', 30.0),
                    max_retry_attempts=recovery_data.get('max_retry_attempts', 3),
                    retry_delay=recovery_data.get('retry_delay', 5.0),
                    escalation_enabled=recovery_data.get('escalation_enabled', True),

                    log_level=logging_data.get('level', 'INFO'),
                    log_execution_details=logging_data.get('log_execution_details', True),
                    log_resource_usage=logging_data.get('log_resource_usage', False),
                    log_terminal_status=logging_data.get('log_terminal_status', False)
                )
            else:
                logger.warning("System config not found, using default configuration")
                return ExecutionManagerConfig()
        except Exception as e:
            logger.error(f"Failed to load system config: {e}", exc_info=True)
            return ExecutionManagerConfig()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"{__name__}.ExecutionManager")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(getattr(logging, self.config.log_level.upper(), logging.INFO))
        return logger

    def start_health_monitoring(self):
        if not self.config.enabled or self._monitoring_active:
            return
        self._monitoring_active = True
        self._health_check_thread = threading.Thread(target=self._health_monitoring_loop, daemon=True)
        self._health_check_thread.start()
        self.logger.info("Health monitoring started")

    def stop_health_monitoring(self):
        self._monitoring_active = False
        if self._health_check_thread:
            self._health_check_thread.join(timeout=5.0)
        self.logger.info("Health monitoring stopped")

    def _health_monitoring_loop(self):
        while self._monitoring_active:
            try:
                health = self.monitor.get_system_health()
                self._check_resource_thresholds(health)
                if self.config.log_resource_usage:
                    self.logger.debug(f"System health: {health}")
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}", exc_info=True)
                time.sleep(10)

    def _check_resource_thresholds(self, health: Dict[str, Any]):
        cpu_percent = health.get('cpu_percent', 0)
        memory_percent = health.get('memory_percent', 0)
        disk_percent = health.get('disk_percent', 0)

        if cpu_percent > self.config.cpu_critical:
            self._handle_resource_issue('cpu', 'critical', cpu_percent)
        elif cpu_percent > self.config.cpu_warning:
            self._handle_resource_issue('cpu', 'warning', cpu_percent)

        if memory_percent > self.config.memory_critical:
            self._handle_resource_issue('memory', 'critical', memory_percent)
        elif memory_percent > self.config.memory_warning:
            self._handle_resource_issue('memory', 'warning', memory_percent)

        if disk_percent > self.config.disk_critical:
            self._handle_resource_issue('disk', 'critical', disk_percent)
        elif disk_percent > self.config.disk_warning:
            self._handle_resource_issue('disk', 'warning', disk_percent)

    def _handle_resource_issue(self, resource_type: str, severity: str, value: float):
        issue = {
            'timestamp': time.time(),
            'type': 'resource_threshold',
            'resource': resource_type,
            'severity': severity,
            'value': value,
            'threshold': getattr(self.config, f"{resource_type}_{severity}")
        }
        self.issues_log.append(issue)

        if severity == 'critical':
            self.logger.error(f"Critical {resource_type} usage: {value}%")
            if self.config.auto_recovery:
                self._attempt_resource_recovery(resource_type)
        else:
            self.logger.warning(f"High {resource_type} usage: {value}%")

    def _attempt_resource_recovery(self, resource_type: str):
        recovery_action = {
            'timestamp': time.time(),
            'type': 'resource_recovery',
            'resource': resource_type,
            'action': 'attempted'
        }
        try:
            if resource_type == 'memory':
                gc.collect()
                recovery_action['details'] = 'garbage_collection'
            elif resource_type == 'cpu':
                recovery_action['details'] = 'cpu_throttling_suggested'
            elif resource_type == 'disk':
                recovery_action['details'] = 'temp_cleanup_suggested'

            recovery_action['status'] = 'completed'
            self.logger.info(f"Recovery action completed for {resource_type}")
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            recovery_action['status'] = 'failed'

            recovery_action['error'] = str(e)
            self.logger.error(f"Recovery action failed for {resource_type}: {e}", exc_info=True)
        finally:
            self.recovery_actions.append(recovery_action)

    def execute_command(self, command: Union[str, List[str]], timeout: Optional[float] = None, retry_on_failure: bool = True, **kwargs) -> ExecutionResult:
        if not self.config.enabled:
            return self.monitor.execute_command(command, timeout, **kwargs)

        self.execution_stats['total_executions'] += 1

        if self.config.log_execution_details:
            self.logger.info(f"Executing command: {command}")

        result: Optional[ExecutionResult] = None
        retry_count = 0
        max_retries = self.config.max_retry_attempts if retry_on_failure else 0

        while retry_count <= max_retries:
            try:
                result = self.monitor.execute_command(command, timeout, **kwargs)

                if result.status == ExecutionStatus.COMPLETED:
                    self.execution_stats['successful_executions'] += 1
                    break
                elif result.status == ExecutionStatus.TIMEOUT:
                    self.execution_stats['timeout_executions'] += 1
                else:
                    self.execution_stats['failed_executions'] += 1

                if retry_count < max_retries and self._should_retry(result):
                    retry_count += 1
                    self.logger.warning(f"Retrying command (attempt {retry_count}/{max_retries})")
                    time.sleep(self.config.retry_delay)
                    continue
                else:
                    break

            except Exception as e:
                self.logger.error(f"Command execution error: {e}", exc_info=True)
                if retry_count < max_retries:
                    retry_count += 1
                    time.sleep(self.config.retry_delay)
                    continue
                else:
                    result = ExecutionResult(
                        status=ExecutionStatus.ERROR,
                        error_message=str(e)
                    )
                    break
        
        return result if result else ExecutionResult(status=ExecutionStatus.ERROR, error_message="Unknown execution error")

    def _should_retry(self, result: ExecutionResult) -> bool:
        if not self.config.auto_recovery:
            return False

        if result.status == ExecutionStatus.TIMEOUT:
            return True

        if result.terminal_status in [TerminalStatus.STUCK, TerminalStatus.UNRESPONSIVE]:
            return True

        return False

    async def execute_async_command(self, command: Union[str, List[str]], timeout: Optional[float] = None, **kwargs) -> ExecutionResult:
        if self.config.log_execution_details:
            self.logger.info(f"Executing async command: {command}")
        return await self.monitor.execute_async_command(command, timeout, **kwargs)

    def get_execution_statistics(self) -> Dict[str, Any]:
        stats = self.execution_stats.copy()
        if stats['total_executions'] > 0:
            stats['success_rate'] = stats['successful_executions'] / stats['total_executions']
            stats['failure_rate'] = stats['failed_executions'] / stats['total_executions']
            stats['timeout_rate'] = stats['timeout_executions'] / stats['total_executions']
            stats['recovery_rate'] = stats['recovered_executions'] / stats['total_executions']
        else:
            stats['success_rate'] = 0.0
            stats['failure_rate'] = 0.0
            stats['timeout_rate'] = 0.0
            stats['recovery_rate'] = 0.0
        return stats

    def get_system_health_report(self) -> Dict[str, Any]:
        health = self.monitor.get_system_health()
        recent_issues = [issue for issue in self.issues_log if (time.time() - issue['timestamp']) < 3600]  # Last 1 hour
        recent_recoveries = [action for action in self.recovery_actions if (time.time() - action['timestamp']) < 3600]  # Last 1 hour
        return {
            'system_health': health,
            'execution_stats': self.get_execution_statistics(),
            'recent_issues': recent_issues,
            'recent_recoveries': recent_recoveries,
            'config': asdict(self.config)
        }

    def reset_statistics(self):
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'timeout_executions': 0,
            'recovered_executions': 0,
            'average_execution_time': 0.0
        }
        self.issues_log.clear()
        self.recovery_actions.clear()
        self.logger.info("Execution statistics reset")

    def __enter__(self):
        self.start_health_monitoring()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_health_monitoring()

_global_execution_manager: Optional[ExecutionManager] = None

def get_execution_manager(config: Optional[ExecutionManagerConfig] = None) -> ExecutionManager:
    global _global_execution_manager
    if _global_execution_manager is None:
        _global_execution_manager = ExecutionManager(config)
    return _global_execution_manager

def execute_with_smart_monitoring(command: Union[str, List[str]], timeout: Optional[float] = None, **kwargs) -> ExecutionResult:
    manager = get_execution_manager()
    return manager.execute_command(command, timeout, **kwargs)

async def execute_async_with_smart_monitoring(command: Union[str, List[str]], timeout: Optional[float] = None, **kwargs) -> ExecutionResult:
    manager = get_execution_manager()
    return await manager.execute_async_command(command, timeout, **kwargs)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Execution Manager Test")
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("--timeout", type=float, help="Timeout in seconds")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--health-report", action="store_true", help="Show health report")

    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    with ExecutionManager() as manager:
        if args.health_report:
            health_report = manager.get_system_health_report()
            print("System Health Report:")
            print(f"CPU: {health_report['system_health'].get('cpu_percent', 'N/A')}% ")
            print(f"Memory: {health_report['system_health'].get('memory_percent', 'N/A')}% ")
            print(f"Disk: {health_report['system_health'].get('disk_percent', 'N/A')}% ")
            print(f"Terminal Status: {health_report['system_health'].get('terminal_status', 'N/A')}")
            print("\nExecution Statistics:")
            stats = health_report['execution_stats']
            print(f"Total Executions: {stats['total_executions']}")
            print(f"Success Rate: {stats['success_rate']:.2%}")
            print(f"Average Execution Time: {stats['average_execution_time']:.2f}s")

        result = manager.execute_command(args.command, timeout=args.timeout)

        print("\nExecution Result:")
        print(f"Status: {result.status}")
        print(f"Return code: {result.return_code}")
        print(f"Execution time: {result.execution_time:.2f}s")
        print(f"Timeout used: {result.timeout_used:.2f}s")

        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        if result.error_message:
            print(f"Error: {result.error_message}")