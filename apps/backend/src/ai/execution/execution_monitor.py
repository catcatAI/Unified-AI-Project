#!/usr/bin/env python3
# Angela Matrix - 4D State: αβγδ (Cognitive-Emotional-Volitional-Memory)
# File: execution_monitor.py
# State: L5-Mature-Agentic (Mature Agent Capabilities)

"""
Execution Monitor for Unified AI Project
Monitors execution status and terminal responsiveness
"""

import asyncio
import logging
import subprocess
import time
import os
import threading
import psutil
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union, Any


class ExecutionStatus(Enum):
    """Execution status enumeration"""
    RUNNING = "running"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    STUCK = "stuck"
    ERROR = "error"
    CANCELLED = "cancelled"


class TerminalStatus(Enum):
    """Terminal status enumeration"""
    RESPONSIVE = "responsive"
    SLOW = "slow"
    STUCK = "stuck"
    UNRESPONSIVE = "unresponsive"


@dataclass
class ExecutionConfig:
    """Execution configuration"""
    default_timeout: float = 60.0  # Increased from 30s to 60s
    max_timeout: float = 600.0     # Increased from 300s to 600s
    min_timeout: float = 10.0      # Increased from 5s to 10s
    check_interval: float = 1.0
    terminal_check_interval: float = 5.0
    cpu_threshold: float = 90.0
    memory_threshold: float = 85.0
    adaptive_timeout: bool = True
    enable_terminal_check: bool = True
    enable_process_monitor: bool = True


@dataclass
class ExecutionResult:
    """Execution result"""
    status: ExecutionStatus
    return_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    execution_time: float = 0.0
    timeout_used: float = 0.0
    terminal_status: Optional[TerminalStatus] = None
    resource_usage: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ExecutionMonitor:
    """Execution Monitor - Intelligent monitoring of execution status and terminal responsiveness"""

    def __init__(self, config: Optional[ExecutionConfig] = None) -> None:
        self.config = config or ExecutionConfig()
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

        # Monitoring status
        self._is_monitoring = False
        self._current_process: Optional[subprocess.Popen] = None
        self._start_time: float = 0.0
        self._last_activity: float = 0.0
        
        # Terminal status monitoring
        self._terminal_status = TerminalStatus.RESPONSIVE
        self._terminal_check_thread: Optional[threading.Thread] = None

        # Resource usage monitoring
        self._resource_monitor_thread: Optional[threading.Thread] = None
        self._resource_usage: Dict[str, Any] = {}

        # Adaptive timeout
        self._execution_history: List[float] = []
        self._adaptive_timeout_cache: Dict[str, float] = {}

    def _setup_logging(self) -> None:
        """Setup logging"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO())

    def calculate_adaptive_timeout(self, command: str, base_timeout: Optional[float] = None) -> float:
        """
        Calculate adaptive timeout time

        Args:
            command: Command to execute
            base_timeout: Base timeout time

        Returns:
            Calculated timeout time
        """
        if not self.config.adaptive_timeout:
            return base_timeout or self.config.default_timeout
        
        # Use command hash as cache key
        cache_key = str(hash(command))

        # Check cache
        if cache_key in self._adaptive_timeout_cache:
            cached_timeout = self._adaptive_timeout_cache[cache_key]
            self.logger.debug(f"Using cached timeout {cached_timeout}s for command")
            return cached_timeout

        # Calculate based on historical execution time
        if self._execution_history:
            avg_time = sum(self._execution_history) / len(self._execution_history)
            # Set to 2-3 times average time, but not exceed max value
            adaptive_timeout = min(avg_time * 2.5, self.config.max_timeout)
            adaptive_timeout = max(adaptive_timeout, self.config.min_timeout)
        else:
            adaptive_timeout = base_timeout or self.config.default_timeout
        
        # Adjust based on terminal status
        if self._terminal_status == TerminalStatus.SLOW:
            adaptive_timeout *= 1.5
        elif self._terminal_status == TerminalStatus.STUCK:
            adaptive_timeout *= 2.0
        elif self._terminal_status == TerminalStatus.UNRESPONSIVE:
            adaptive_timeout = self.config.min_timeout  # Fast fail

        # Limit to reasonable range
        adaptive_timeout = max(self.config.min_timeout, 
                            min(adaptive_timeout, self.config.max_timeout))

        # Cache result
        self._adaptive_timeout_cache[cache_key] = adaptive_timeout

        self.logger.info(f"Calculated adaptive timeout: {adaptive_timeout}s")
        return adaptive_timeout

    def check_terminal_responsiveness(self) -> TerminalStatus:
        """
        Check terminal responsiveness

        Returns:
            Terminal status
        """
        try:
            # Test simple command response time
            start_time = time.time()

            if os.name == 'nt':  # Windows
                result = subprocess.run(['echo', 'test'],
                                    capture_output=True,
                                    timeout=5.0,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            else:  # Unix/Linux
                result = subprocess.run(['echo', 'test'],
                                    capture_output=True,
                                    timeout=5.0)

            response_time = time.time() - start_time

            if response_time < 0.1:
                return TerminalStatus.RESPONSIVE
            elif response_time < 1.0:
                return TerminalStatus.SLOW
            elif response_time < 3.0:
                return TerminalStatus.STUCK
            else:
                return TerminalStatus.UNRESPONSIVE
        except subprocess.TimeoutExpired:
            return TerminalStatus.UNRESPONSIVE
        except Exception as e:
            self.logger.warning(f"Terminal check failed: {e}")
            return TerminalStatus.UNRESPONSIVE

    def _monitor_terminal(self):
        """Terminal status monitoring thread"""
        while self._is_monitoring:
            try:
                self._terminal_status = self.check_terminal_responsiveness()
                self.logger.debug(f"Terminal status: {self._terminal_status.value}")
                time.sleep(self.config.terminal_check_interval)
            except Exception as e:
                self.logger.error(f"Terminal monitoring error: {e}")
                time.sleep(self.config.terminal_check_interval)

    def _monitor_resources(self) -> None:
        """Resource usage monitoring thread"""
        while self._is_monitoring:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)

                # Memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # Disk usage
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
                
                self._resource_usage = {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'disk_percent': disk_percent,
                    'timestamp': time.time()
                }

                # Check resource warnings
                if cpu_percent > self.config.cpu_threshold:
                    self.logger.warning(f"High CPU usage: {cpu_percent}%")

                if memory_percent > self.config.memory_threshold:
                    self.logger.warning(f"High memory usage: {memory_percent}%")

                time.sleep(self.config.check_interval)

            except Exception as e:
                self.logger.error(f"Resource monitoring error: {e}")
                time.sleep(self.config.check_interval)

    def _start_monitoring(self) -> None:
        """Start monitoring"""
        self._is_monitoring = True

        if self.config.enable_terminal_check:
            self._terminal_check_thread = threading.Thread(
                target=self._monitor_terminal, 
                daemon=True
            )
            self._terminal_check_thread.start()

        if self.config.enable_process_monitor:
            self._resource_monitor_thread = threading.Thread(
                target=self._monitor_resources, 
                daemon=True
            )
            self._resource_monitor_thread.start()

    def _stop_monitoring(self) -> None:
        """Stop monitoring"""
        self._is_monitoring = False

        if self._terminal_check_thread:
            self._terminal_check_thread.join(timeout=1.0)

        if self._resource_monitor_thread:
            self._resource_monitor_thread.join(timeout=1.0)

    def execute_command(
        self,
        command: Union[str, List[str]],
        timeout: Optional[float] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        shell: bool = True
    ) -> ExecutionResult:
        """
        Execute command and monitor status

        Args:
            command: Command to execute
            timeout: Timeout time (seconds)
            cwd: Working directory
            env: Environment variables
            shell: Whether to use shell

        Returns:
            Execution result
        """
        start_time = time.time()
        adaptive_timeout = timeout or self.calculate_adaptive_timeout(
            ' '.join(command) if isinstance(command, list) else command
        )
        
        try:
            # Start monitoring
            self._start_monitoring()

            # Execute command
            self._start_time = start_time
            self._last_activity = start_time

            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            self._current_process = process

            # Wait for process to complete or timeout
            try:
                stdout, stderr = process.communicate(timeout=adaptive_timeout)
                execution_time = time.time() - start_time

                # Record execution history (for adaptive timeout)
                self._execution_history.append(execution_time)
                if len(self._execution_history) > 50:
                    self._execution_history.pop(0)

                return ExecutionResult(
                    status=ExecutionStatus.COMPLETED,
                    return_code=process.returncode,
                    stdout=stdout,
                    stderr=stderr,
                    execution_time=execution_time,
                    timeout_used=adaptive_timeout,
                    terminal_status=self._terminal_status,
                    resource_usage=self._resource_usage.copy() if self._resource_usage else None
                )
            except subprocess.TimeoutExpired:
                # Timeout handling
                process.kill()
                stdout, stderr = process.communicate()
                execution_time = time.time() - start_time

                return ExecutionResult(
                    status=ExecutionStatus.TIMEOUT,
                    return_code=process.returncode,
                    stdout=stdout,
                    stderr=stderr,
                    execution_time=execution_time,
                    timeout_used=adaptive_timeout,
                    terminal_status=self._terminal_status,
                    resource_usage=self._resource_usage.copy() if self._resource_usage else None,
                    error_message=f"Command timed out after {adaptive_timeout} seconds"
                )

        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            execution_time = time.time() - start_time

            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                execution_time=execution_time,
                timeout_used=adaptive_timeout,
                terminal_status=self._terminal_status,
                resource_usage=self._resource_usage.copy() if self._resource_usage else None,
                error_message=str(e)
            )
        finally:
            # Stop monitoring
            self._stop_monitoring()
            self._current_process = None

    def get_system_health(self) -> Dict[str, Any]:
        """
        Get system health status

        Returns:
            System health information
        """
        return {
            'terminal_status': self._terminal_status.value,
            'resource_usage': self._resource_usage.copy() if self._resource_usage else None,
            'is_monitoring': self._is_monitoring,
            'adaptive_timeout_cache_size': len(self._adaptive_timeout_cache)
        }


# Global execution monitor instance
_global_monitor: Optional[ExecutionMonitor] = None


def get_execution_monitor(config: Optional[ExecutionConfig] = None) -> ExecutionMonitor:
    """
    Get global execution monitor instance

    Args:
        config: Execution configuration

    Returns:
        Execution monitor instance
    """
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ExecutionMonitor(config)
    return _global_monitor


def execute_with_monitoring(
    command: Union[str, List[str]],
    timeout: Optional[float] = None,
    **kwargs
) -> ExecutionResult:
    """
    Convenient function to execute command with monitoring

    Args:
        command: Command to execute
        timeout: Timeout time
        **kwargs: Other parameters

    Returns:
        Execution result
    """
    monitor = get_execution_monitor()
    return monitor.execute_command(command, timeout, **kwargs)


async def execute_async_with_monitoring(
    command: Union[str, List[str]],
    timeout: Optional[float] = None,
    **kwargs
) -> ExecutionResult:
    """
    Convenient function to asynchronously execute command with monitoring

    Args:
        command: Command to execute
        timeout: Timeout time
        **kwargs: Other parameters

    Returns:
        Execution result
    """
    monitor = get_execution_monitor()
    return monitor.execute_command(command, timeout, **kwargs)


if __name__ == '__main__':
    import argparse
    
    # Test execution monitor
    parser = argparse.ArgumentParser(description="Execution Monitor Test")
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout in seconds")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG())

    monitor = ExecutionMonitor()
    result = monitor.execute_command(args.command, timeout=args.timeout)

    print(f"Status: {result.status.value}")
    print(f"Return code: {result.return_code}")
    print(f"Execution time: {result.execution_time:.2f}s")
    print(f"Terminal status: {result.terminal_status.value if result.terminal_status else 'N/A'}")
    
    if result.stdout:
        print(f"STDOUT:\n{result.stdout}")
    if result.stderr:
        print(f"STDERR:\n{result.stderr}")
    if result.error_message:
        print(f"Error: {result.error_message}")