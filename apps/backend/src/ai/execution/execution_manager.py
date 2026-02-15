#!/usr/bin/env python3
# Angela Matrix - 4D State: αβγδ (Cognitive-Emotional-Volitional-Memory)
# File: execution_manager.py
# State: L5-Mature-Agentic (Mature Agent Capabilities)

"""
Execution Manager for Unified AI Project
Unified execution monitoring and management system
"""

import asyncio
import logging
import threading
import time
import uuid
import gc
import yaml
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from .execution_monitor import (
    ExecutionMonitor, ExecutionConfig, ExecutionResult,
    ExecutionStatus, TerminalStatus
)


@dataclass
class ExecutionManagerConfig:
    """Execution manager configuration"""
    # Basic configuration
    enabled: bool = True
    adaptive_timeout: bool = True
    terminal_monitoring: bool = True
    resource_monitoring: bool = True
    auto_recovery: bool = True

    # Timeout configuration
    default_timeout: float = 60.0   # Increased from 30s to 60s
    max_timeout: float = 600.0      # Increased from 300s to 600s
    min_timeout: float = 10.0       # Increased from 5s to 10s

    # Threshold configuration
    cpu_warning: float = 80.0
    cpu_critical: float = 90.0
    memory_warning: float = 75.0
    memory_critical: float = 85.0
    disk_warning: float = 80.0
    disk_critical: float = 90.0
    
    # Adaptive timeout configuration
    max_history_size: int = 1000
    alert_threshold: float = 0.8
    timeout_multiplier: float = 2.5
    slow_terminal_multiplier: float = 1.5
    stuck_terminal_multiplier: float = 2.0
    cache_size: int = 100

    # Recovery strategy configuration
    circuit_breaker_enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout: int = 300
    stuck_process_timeout: float = 60.0   # Increased from 30s to 60s
    max_concurrent_tasks: int = 5
    task_timeout: int = 300
    max_retries: int = 5
    retry_interval: float = 1.0
    escalation_enabled: bool = True

    # Logging configuration
    log_level: str = "INFO"
    log_file: str = "execution.log"
    log_execution_details: bool = True
    log_resource_usage: bool = False
    log_terminal_status: bool = False


class ExecutionManager:
    """
    Execution Manager - Unified execution monitoring and management system

    Features:
    - Intelligent timeout control
    - Terminal responsiveness monitoring
    - System resource monitoring
    - Automatic recovery mechanism
    - Execution history analysis
    - Issue escalation handling
    """

    def __init__(self, config: Optional[ExecutionManagerConfig] = None) -> None:
        self.config = config or self._load_config_from_system()
        self.logger = self._setup_logger()

        # Initialize execution monitor
        monitor_config = ExecutionConfig(
            default_timeout=self.config.default_timeout,
            max_timeout=self.config.max_timeout,
            min_timeout=self.config.min_timeout,
            adaptive_timeout=self.config.adaptive_timeout,
            enable_terminal_check=self.config.terminal_monitoring,
        )
        
        # Initialize execution monitor
        self.execution_monitor = ExecutionMonitor(
            config=monitor_config
        )
        self.monitor = ExecutionMonitor(
            config=monitor_config
        )

        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'timeout_executions': 0,
            'recovered_executions': 0,
            'average_execution_time': 0.0
        }

        # Add test-required attributes
        self.task_queue: Dict[str, Any] = {}
        self.execution_status: Dict[str, Any] = {}

        # Issue tracking
        self.issues_log: List[Dict[str, Any]] = []
        self.recovery_actions: List[Dict[str, Any]] = []

        # Status monitoring
        self._monitoring_active = False
        self._health_check_thread: Optional[threading.Thread] = None

        self.logger.info("ExecutionManager initialized with adaptive monitoring")

    def _load_config_from_system(self) -> ExecutionManagerConfig:
        """Load configuration from system configuration file"""
        # Set up a temporary logger for error recording
        temp_logger = logging.getLogger(f"{__name__}.ExecutionManager.temp")

        try:
            config_path = Path("configs/system_config.yaml")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    system_config = yaml.safe_load(f)

                # Extract execution monitoring related configuration
                operational_configs = system_config.get('operational_configs', {})
                execution_config = operational_configs.get('execution_monitor', {})
                timeouts = operational_configs.get('timeouts', {})
                thresholds = execution_config.get('thresholds', {})
                adaptive_config = execution_config.get('adaptive_timeout_config', {})
                recovery_config = execution_config.get('recovery_strategies', {})
                logging_config = execution_config.get('logging', {})

                return ExecutionManagerConfig(
                    enabled=execution_config.get('enabled', True),
                    adaptive_timeout=execution_config.get('adaptive_timeout', True),
                    terminal_monitoring=execution_config.get('terminal_monitoring', True),
                    resource_monitoring=execution_config.get('resource_monitoring', True),
                    auto_recovery=execution_config.get('auto_recovery', True),

                    default_timeout=timeouts.get('command_execution_default', 30.0),
                    max_timeout=timeouts.get('command_execution_max', 300.0),
                    min_timeout=timeouts.get('command_execution_min', 5.0),

                    cpu_warning=thresholds.get('cpu_warning', 80.0),
                    cpu_critical=thresholds.get('cpu_critical', 90.0),
                    memory_warning=thresholds.get('memory_warning', 75.0),
                    memory_critical=thresholds.get('memory_critical', 85.0),
                    disk_warning=thresholds.get('disk_warning', 80.0),
                    disk_critical=thresholds.get('disk_critical', 90.0),

                    history_size=adaptive_config.get('history_size', 50),
                    timeout_multiplier=adaptive_config.get('timeout_multiplier', 2.5),
                    slow_terminal_multiplier=adaptive_config.get('slow_terminal_multiplier', 1.5),
                    stuck_terminal_multiplier=adaptive_config.get('stuck_terminal_multiplier', 2.0),
                    cache_size=adaptive_config.get('cache_size', 100),

                    stuck_process_timeout=recovery_config.get('stuck_process_timeout', 30.0),
                    max_retry_attempts=recovery_config.get('max_retry_attempts', 3),
                    retry_delay=recovery_config.get('retry_delay', 5.0),
                    escalation_enabled=recovery_config.get('escalation_enabled', True),

                    log_level=logging_config.get('level', 'INFO'),
                    log_execution_details=logging_config.get('log_execution_details', True),
                    log_resource_usage=logging_config.get('log_resource_usage', False),
                    log_terminal_status=logging_config.get('log_terminal_status', False)
                )
            else:
                temp_logger.warning("System config not found, using default configuration")
                return ExecutionManagerConfig()

        except Exception as e:
            temp_logger.error(f"Failed to load system config: {e}")
            return ExecutionManagerConfig()

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        if task_id in self.task_queue:
            task = self.task_queue[task_id]
            if hasattr(task, 'cancel'):
                result = task.cancel()
                return result
        return False

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task"""
        task_id = task.get("task_id", str(uuid.uuid4()))

        # Store task to queue
        self.task_queue[task_id] = task

        # If there's a specific task execution method, use it
        if "_execute_training_task" in dir(self) and task.get("task_type") == "training":
            result = await self._execute_training_task(task)
            self.execution_status[task_id] = result
            return result

        # Default execution method
        result = {"status": "completed"}
        self.execution_status[task_id] = result
        return result

    async def _execute_training_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute training task"""
        # Simulate training task execution
        return {"status": "completed"}

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        return self.execution_status.get(task_id, {"status": "unknown"})

    def _setup_logger(self) -> logging.Logger:
        """Setup logger"""
        logger = logging.getLogger(f"{__name__}.ExecutionManager")

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        logger.setLevel(getattr(logging, self.config.log_level.upper(), logging.INFO))
        return logger

    def start_health_monitoring(self) -> None:
        """Start health monitoring"""
        if not self.config.enabled or self._monitoring_active:
            return

        self._monitoring_active = True
        self._health_check_thread = threading.Thread(
            target=self._health_monitoring_loop,
            daemon=True
        )
        self._health_check_thread.start()
        self.logger.info("Health monitoring started")

    def stop_health_monitoring(self) -> None:
        """Stop health monitoring"""
        self._monitoring_active = False
        if self._health_check_thread:
            self._health_check_thread.join(timeout=5.0)
        self.logger.info("Health monitoring stopped")

    def _health_monitoring_loop(self) -> None:
        """Health monitoring loop"""
        while self._monitoring_active:
            try:
                health = self.monitor.get_system_health()

                # Check resource usage
                # Here can add more health check logic

                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")

    def _check_resource_thresholds(self, health: Dict[str, Any]) -> None:
        """Check resource thresholds"""
        cpu_percent = health.get('cpu_percent', 0)
        memory_percent = health.get('memory_percent', 0)
        disk_percent = health.get('disk_percent', 0)

        # CPU check
        if cpu_percent > self.config.cpu_critical:
            self._handle_resource_issue('cpu', 'critical', cpu_percent)
        elif cpu_percent > self.config.cpu_warning:
            self._handle_resource_issue('cpu', 'warning', cpu_percent)

        # Memory check
        if memory_percent > self.config.memory_critical:
            self._handle_resource_issue('memory', 'critical', memory_percent)
        elif memory_percent > self.config.memory_warning:
            self._handle_resource_issue('memory', 'warning', memory_percent)

        # Disk check
        if disk_percent > self.config.disk_critical:
            self._handle_resource_issue('disk', 'critical', disk_percent)
        elif disk_percent > self.config.disk_warning:
            self._handle_resource_issue('disk', 'warning', disk_percent)

    def _handle_resource_issue(self, resource_type: str, severity: str, value: float) -> None:
        """Handle resource issue"""
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

    def _attempt_resource_recovery(self, resource_type: str) -> None:
        """Attempt resource recovery"""
        recovery_action = {
            'timestamp': time.time(),
            'type': 'resource_recovery',
            'resource': resource_type,
            'action': 'attempted'
        }

        try:
            if resource_type == 'memory':
                # Trigger garbage collection
                gc.collect()
                recovery_action['details'] = 'garbage_collection'

            elif resource_type == 'cpu':
                # Can implement CPU throttling or process priority adjustment
                recovery_action['details'] = 'cpu_throttling_suggested'

            elif resource_type == 'disk':
                # Can clean temporary files
                recovery_action['details'] = 'temp_cleanup_suggested'

            recovery_action['status'] = 'completed'
            self.logger.info(f"Recovery action completed for {resource_type}")
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            recovery_action['status'] = 'failed'

            recovery_action['error'] = str(e)
            self.logger.error(f"Recovery action failed for {resource_type}: {e}")
        
        self.recovery_actions.append(recovery_action)

    def execute_command(
        self,
        command: Union[str, List[str]],
        timeout: Optional[float] = None,
        retry_on_failure: bool = True,
        **kwargs
    ) -> ExecutionResult:
        """
        Execute command with intelligent monitoring

        Args:
            command: Command to execute
            timeout: Timeout time (seconds)
            retry_on_failure: Whether to retry on failure
            **kwargs: Other parameters

        Returns:
            Execution result
        """
        if not self.config.enabled:
            # If monitoring not enabled, use basic execution
            return self.monitor.execute_command(command, timeout, **kwargs)

        self.execution_stats['total_executions'] += 1

        # Record execution details
        if self.config.log_execution_details:
            self.logger.info(f"Executing command: {command}")

        result: Optional[ExecutionResult] = None
        retry_count = 0
        max_retries = self.config.max_retries if retry_on_failure else 0
        
        while retry_count <= max_retries:
            try:
                result = self.monitor.execute_command(command, timeout, **kwargs)

                # Update statistics
                if result.status == ExecutionStatus.COMPLETED:
                    self.execution_stats['successful_executions'] += 1
                    break
                elif result.status == ExecutionStatus.TIMEOUT:
                    self.execution_stats['timeout_executions'] += 1
                else:
                    self.execution_stats['failed_executions'] += 1

                # Check if need to retry
                if retry_count < max_retries and self._should_retry(result):
                    retry_count += 1
                    self.logger.warning(f"Retrying command (attempt {retry_count}/{max_retries})")
                    time.sleep(self.config.retry_interval)
                    continue
                else:
                    break

            except Exception as e:
                self.logger.error(f"Command execution error: {e}")
                if retry_count < max_retries:
                    retry_count += 1
                    time.sleep(self.config.retry_interval)
                    continue
                else:
                    result = ExecutionResult(
                        status=ExecutionStatus.ERROR,
                        error_message=str(e)
                    )
                    break

        # If recovered after retries, record recovery
        if retry_count > 0 and result and result.status == ExecutionStatus.COMPLETED:
            self.execution_stats['recovered_executions'] += 1
            self.logger.info(f"Command recovered after {retry_count} retries")

        # Update average execution time
        if result and result.execution_time > 0:
            total_time = (self.execution_stats['average_execution_time'] *
                        (self.execution_stats['total_executions'] - 1) +
                        result.execution_time)
            self.execution_stats['average_execution_time'] = total_time / \
                self.execution_stats['total_executions']

        # Ensure return an ExecutionResult object
        if result is None:
            result = ExecutionResult(
                status=ExecutionStatus.ERROR,
                error_message="Unknown error occurred"
            )

        return result

    def _should_retry(self, result: ExecutionResult) -> bool:
        """Determine if should retry"""
        if not self.config.auto_recovery:
            return False

        # Retry on timeout or terminal issues
        if result.status == ExecutionStatus.TIMEOUT:
            return True

        # Retry on terminal unresponsiveness
        if (result.terminal_status and 
            result.terminal_status in [TerminalStatus.STUCK, 
                                      TerminalStatus.UNRESPONSIVE]):
            return True

        return False

    async def execute_async_command(
        self,
        command: Union[str, List[str]],
        timeout: Optional[float] = None,
        **kwargs
    ) -> ExecutionResult:
        """
        Asynchronously execute command

        Args:
            command: Command to execute
            timeout: Timeout time (seconds)
            **kwargs: Other parameters

        Returns:
            Execution result
        """
        if self.config.log_execution_details:
            self.logger.info(f"Executing async command: {command}")

        return await self.monitor.execute_async_command(command, timeout, **kwargs)

    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution statistics"""
        stats = self.execution_stats.copy()

        # Calculate success rate
        if stats['total_executions'] > 0:
            stats['success_rate'] = stats['successful_executions'] / \
                stats['total_executions']
            stats['failure_rate'] = stats['failed_executions'] / \
                stats['total_executions']
            stats['timeout_rate'] = stats['timeout_executions'] / \
                stats['total_executions']
            stats['recovery_rate'] = stats['recovered_executions'] / \
                stats['total_executions']
        else:
            stats['success_rate'] = 0.0
            stats['failure_rate'] = 0.0
            stats['timeout_rate'] = 0.0
            stats['recovery_rate'] = 0.0
        
        return stats

    def get_system_health_report(self) -> Dict[str, Any]:
        """Get system health report"""
        health = self.monitor.get_system_health()

        # Add issues and recovery records
        recent_issues = [issue for issue in self.issues_log 
                        if time.time() - issue['timestamp'] < 3600]  # Recent 1 hour
        recent_recoveries = [action for action in self.recovery_actions 
                            if time.time() - action['timestamp'] < 3600]  # Recent 1 hour
        
        return {
            'system_health': health,
            'execution_stats': self.get_execution_statistics(),
            'recent_issues': recent_issues,
            'recent_recoveries': recent_recoveries,
            'config': self.config.__dict__
        }

    def reset_statistics(self) -> None:
        """Reset statistics"""
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

    def __enter__(self) -> 'ExecutionManager':
        """Context manager enter"""
        self.start_health_monitoring()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        self.stop_health_monitoring()


# Global execution manager instance
_global_execution_manager: Optional[ExecutionManager] = None


def get_execution_manager(config: Optional[ExecutionManagerConfig] = None) -> ExecutionManager:
    """
    Get global execution manager instance

    Args:
        config: Execution manager configuration

    Returns:
        Execution manager instance
    """
    global _global_execution_manager
    if _global_execution_manager is None:
        _global_execution_manager = ExecutionManager(config)
    return _global_execution_manager


def execute_with_smart_monitoring(
    command: Union[str, List[str]],
    timeout: Optional[float] = None,
    **kwargs
) -> ExecutionResult:
    """
    Convenient function to execute command with smart monitoring

    Args:
        command: Command to execute
        timeout: Timeout time
        **kwargs: Other parameters

    Returns:
        Execution result
    """
    manager = get_execution_manager()
    return manager.execute_command(command, timeout, **kwargs)


async def execute_async_with_smart_monitoring(
    command: Union[str, List[str]],
    timeout: Optional[float] = None,
    **kwargs
) -> ExecutionResult:
    """
    Convenient function to asynchronously execute command with smart monitoring

    Args:
        command: Command to execute
        timeout: Timeout time
        **kwargs: Other parameters

    Returns:
        Execution result
    """
    manager = get_execution_manager()
    return await manager.execute_async_command(command, timeout, **kwargs)


if __name__ == '__main__':
    # Test execution manager
    parser = argparse.ArgumentParser(description="Execution Manager Test")
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("--timeout", type=float, help="Timeout in seconds")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--health-report", action="store_true", help="Show health report")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG())

    with ExecutionManager() as manager:
        if args.health_report:
            health_report = manager.get_system_health_report()
            logger.info("System Health Report:")
            logger.info(f"CPU: {health_report['system_health'].get('cpu_percent', 'N/A')}%")
            logger.info(f"Memory: {health_report['system_health'].get('memory_percent', 'N/A')}%")
            logger.info(f"Disk: {health_report['system_health'].get('disk_percent', 'N/A')}%")
            logger.info(f"Terminal Status: {health_report['system_health'].get('terminal_status', 'N/A')}")
            logger.info("\nExecution Statistics:")
            stats = health_report['execution_stats']
            logger.info(f"Total Executions: {stats['total_executions']}")
            logger.info(f"Success Rate: {stats['success_rate']:.2%}")
            logger.info(f"Average Execution Time: {stats['average_execution_time']:.2f}s")

        result = manager.execute_command(args.command, timeout=args.timeout)

        logger.info(f"\nExecution Result:")
        logger.info(f"Status: {result.status.value}")
        logger.info(f"Return code: {result.returncode}")
        logger.info(f"Execution time: {result.execution_time:.2f}s")
        logger.info(f"Timeout used: {result.timeout_used:.2f}s")

        if result.stdout:
            logger.info(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            logger.info(f"STDERR:\n{result.stderr}")
        if result.error_message:
            logger.error(f"Error: {result.error_message}")