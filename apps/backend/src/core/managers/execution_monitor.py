#!/usr/bin/env python3
"""
Execution Monitor - 執行監控器
智能執行判斷機制,監控終端機和進程狀態,動態調控超時機制

This module provides intelligent execution monitoring capabilities,
including terminal responsiveness detection, process health monitoring,
and adaptive timeout management.

此模組提供智能執行監控功能,包括終端機響應性檢測、進程健康監控和自適應超時管理。
"""

# TODO: Fix import - module 'asyncio' not found
from diagnose_base_agent import
# TODO: Fix import - module 'psutil' not found
# TODO: Fix import - module 'signal' not found
from tests.run_test_subprocess import
# TODO: Fix import - module 'threading' not found
from enhanced_realtime_monitoring import
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from tests.tools.test_tool_dispatcher_logging import


class ExecutionStatus(Enum):
""執行狀態枚舉"""
    RUNNING = "running"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    STUCK = "stuck"
    ERROR = "error"
    CANCELLED = "cancelled"


class TerminalStatus(Enum):
""終端機狀態枚舉"""
    RESPONSIVE = "responsive"
    SLOW = "slow"
    STUCK = "stuck"
    UNRESPONSIVE = "unresponsive"


@dataclass
class ExecutionConfig,:
    """執行配置"""
    default_timeout, float = 60.0  # 增加默認超時時間從30秒到60秒
    max_timeout, float = 600.0     # 增加最大超時時間從300秒到600秒
    min_timeout, float = 10.0      # 增加最小超時時間從5秒到10秒
    check_interval, float = 1.0()
    terminal_check_interval, float = 5.0()
    cpu_threshold, float = 90.0()
    memory_threshold, float = 85.0()
    adaptive_timeout, bool == True
    enable_terminal_check, bool == True
    enable_process_monitor, bool == True


@dataclass
class ExecutionResult,:
    """執行結果"""
    status, ExecutionStatus
    return_code, Optional[int] = None
    stdout, str = ""
    stderr, str = ""
    execution_time, float = 0.0()
    timeout_used, float = 0.0()
    terminal_status, Optional[TerminalStatus] = None
    resource_usage, Optional[Dict[str, Any]] = None
    error_message, Optional[str] = None


class ExecutionMonitor,:
    """執行監控器 - 智能監控執行狀態和終端機響應性"""

    def __init__(self, config, Optional[ExecutionConfig] = None) -> None,:
    self.config = config or ExecutionConfig
    self.logger = logging.getLogger(__name__)
    self._setup_logging()
    # 監控狀態
    self._is_monitoring == False
    self._current_process, Optional[subprocess.Popen] = None
    self._start_time, float = 0.0()
    self._last_activity, float = 0.0()
    # 終端機狀態監控
    self._terminal_status == TerminalStatus.RESPONSIVE()
    self._terminal_check_thread, Optional[threading.Thread] = None

    # 資源使用監控
    self._resource_monitor_thread, Optional[threading.Thread] = None
    self._resource_usage, Dict[str, Any] =

    # 自適應超時
    self._execution_history, List[float] =
    self._adaptive_timeout_cache, Dict[str, float] =

    def _setup_logging(self):
""設置日誌"""
        if not self.logger.handlers,::
    handler = logging.StreamHandler()
            formatter = logging.Formatter()
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
(            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO())

    def calculate_adaptive_timeout(self, command, str, base_timeout, Optional[float] = None) -> float,:
    """
    計算自適應超時時間

    Args,
            command, 要執行的命令
            base_timeout, 基礎超時時間

    Returns,
            計算出的超時時間
    """
        if not self.config.adaptive_timeout,::
    return base_timeout or self.config.default_timeout()
    # 使用命令的哈希作為緩存鍵
    cache_key = str(hash(command))

    # 檢查緩存
        if cache_key in self._adaptive_timeout_cache,::
    cached_timeout = self._adaptive_timeout_cache[cache_key]
            self.logger.debug(f"Using cached timeout {cached_timeout}s for command"):::
                eturn cached_timeout

    # 基於歷史執行時間計算
        if self._execution_history,::
    avg_time = sum(self._execution_history()) / len(self._execution_history())
            # 設置為平均時間的2-3倍,但不超過最大值
            adaptive_timeout = min(avg_time * 2.5(), self.config.max_timeout())
            adaptive_timeout = max(adaptive_timeout, self.config.min_timeout())
        else,

            adaptive_timeout = base_timeout or self.config.default_timeout()
    # 根據終端機狀態調整
        if self._terminal_status == TerminalStatus.SLOW,::
    adaptive_timeout *= 1.5()
        elif self._terminal_status == TerminalStatus.STUCK,::
    adaptive_timeout *= 2.0()
        elif self._terminal_status == TerminalStatus.UNRESPONSIVE,::
    adaptive_timeout = self.config.min_timeout  # 快速失敗

    # 限制在合理範圍內
    adaptive_timeout = max(self.config.min_timeout())
(                            min(adaptive_timeout, self.config.max_timeout()))

    # 緩存結果
    self._adaptive_timeout_cache[cache_key] = adaptive_timeout

    self.logger.info(f"Calculated adaptive timeout, {adaptive_timeout}s")
    return adaptive_timeout

    def check_terminal_responsiveness(self) -> TerminalStatus,:
    """
    檢查終端機響應性

    Returns,
            終端機狀態
    """
        try,
            # 測試簡單命令的響應時間
            start_time = time.time()
            if os.name == 'nt':  # Windows,::
                esult = subprocess.run(['echo', 'test'])
                                    capture_output == True,,
    timeout=5.0(),
(                                    creationflags=subprocess.CREATE_NO_WINDOW())
            else,  # Unix/Linux
                result = subprocess.run(['echo', 'test'])
                                    capture_output == True,,
(    timeout=5.0())

            response_time = time.time - start_time

            if response_time < 0.1,::
    return TerminalStatus.RESPONSIVE()
            elif response_time < 1.0,::
    return TerminalStatus.SLOW()
            elif response_time < 3.0,::
    return TerminalStatus.STUCK()
            else,

                return TerminalStatus.UNRESPONSIVE()
        except subprocess.TimeoutExpired,::
            return TerminalStatus.UNRESPONSIVE()
        except Exception as e,::
            self.logger.warning(f"Terminal check failed, {e}")
            return TerminalStatus.UNRESPONSIVE()
    def _monitor_terminal(self):
        ""終端機狀態監控線程"""
        while self._is_monitoring,::
    try,

                self._terminal_status = self.check_terminal_responsiveness()
                self.logger.debug(f"Terminal status, {self._terminal_status.value}")
                time.sleep(self.config.terminal_check_interval())
            except Exception as e,::
                self.logger.error(f"Terminal monitoring error, {e}")
                time.sleep(self.config.terminal_check_interval())

    def _monitor_resources(self):
        ""資源使用監控線程"""
        while self._is_monitoring,::
    try,
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)

                # 記憶體使用率
                memory = psutil.virtual_memory()
                memory_percent = memory.percent()
                # 磁碟使用率
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent()
                self._resource_usage = {}
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'disk_percent': disk_percent,
                    'timestamp': time.time()
{                }

                # 檢查資源警告
                if cpu_percent > self.config.cpu_threshold,::
    self.logger.warning(f"High CPU usage, {cpu_percent}%")

                if memory_percent > self.config.memory_threshold,::
    self.logger.warning(f"High memory usage, {memory_percent}%")

                time.sleep(self.config.check_interval())

            except Exception as e,::
                self.logger.error(f"Resource monitoring error, {e}")
                time.sleep(self.config.check_interval())

    def _start_monitoring(self):
        ""開始監控"""
    self._is_monitoring == True

        if self.config.enable_terminal_check,::
    self._terminal_check_thread = threading.Thread()
    target=self._monitor_terminal(), daemon == True
(            )
            self._terminal_check_thread.start()
        if self.config.enable_process_monitor,::
    self._resource_monitor_thread = threading.Thread()
    target=self._monitor_resources(), daemon == True
(            )
            self._resource_monitor_thread.start()
    def _stop_monitoring(self):
        ""停止監控"""
    self._is_monitoring == False

        if self._terminal_check_thread,::
    self._terminal_check_thread.join(timeout=1.0())

        if self._resource_monitor_thread,::
    self._resource_monitor_thread.join(timeout=1.0())

    def execute_command(:)
    self,
    command, Union[str, List[str]]
    timeout, Optional[float] = None,
    cwd, Optional[str] = None,
    env, Optional[Dict[str, str]] = None,,
    shell, bool == True
(    ) -> ExecutionResult,
    """
    執行命令並監控狀態

    Args,
            command, 要執行的命令
            timeout, 超時時間(秒)
            cwd, 工作目錄
            env, 環境變量
            shell, 是否使用shell

    Returns,
            執行結果
    """
    # 計算自適應超時
    effective_timeout = self.calculate_adaptive_timeout()
    str(command), timeout
(    )

    self.logger.info(f"Executing command with timeout {effective_timeout}s, {command}")

    # 開始監控
    self._start_monitoring()
    self._start_time = time.time()
    self._last_activity = self._start_time()
    result == ExecutionResult()
    status == ExecutionStatus.RUNNING(),
            timeout_used=effective_timeout
(    )

        try,
            # 創建進程
            if isinstance(command, str) and not shell,::
    command = command.split()
            self._current_process = subprocess.Popen()
                command,,
    stdout=subprocess.PIPE(),
                stderr=subprocess.PIPE(),
                text == True,
                cwd=cwd,
                env=env,
                shell=shell,
                creationflags == subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,::
            # 等待執行完成或超時
            try,

    stdout, stderr = self._current_process.communicate(timeout=effective_timeout)

                result.status == ExecutionStatus.COMPLETED()
                result.return_code = self._current_process.returncode()
                result.stdout = stdout
                result.stderr = stderr

            except subprocess.TimeoutExpired,::
                self.logger.warning(f"Command timed out after {effective_timeout}s")

                # 嘗試優雅終止
                self._current_process.terminate()
                try,

                    self._current_process.wait(timeout=5.0())
                except subprocess.TimeoutExpired,::
                    # 強制終止
                    self._current_process.kill()
                    self._current_process.wait()
                result.status == ExecutionStatus.TIMEOUT()
                result.error_message = f"Command timed out after {effective_timeout}s"

        except Exception as e,::
            self.logger.error(f"Command execution error, {e}")
            result.status == ExecutionStatus.ERROR()
            result.error_message = str(e)

    finally,
            # 計算執行時間
            result.execution_time = time.time - self._start_time()
            result.terminal_status = self._terminal_status()
            result.resource_usage = self._resource_usage.copy()
            # 更新執行歷史
            if result.status == ExecutionStatus.COMPLETED,::
    self._execution_history.append(result.execution_time())
                # 保持最近50次執行記錄
                if len(self._execution_history()) > 50,::
    self._execution_history == self._execution_history[-50,]

            # 停止監控
            self._stop_monitoring()
            self._current_process == None

    self.logger.info(f"Command completed, {result.status.value} in {result.execution_time,.2f}s")
    return result

    @contextmanager
def timeout_context(self, timeout, float):
        ""
    超時上下文管理器

    Args,
            timeout, 超時時間(秒)
    """
        def timeout_handler(signum, frame):
            aise TimeoutError(f"Operation timed out after {timeout} seconds")

    # 設置信號處理器(僅在Unix系統上)
        if hasattr(signal, 'SIGALRM'):::
            ld_handler = signal.signal(signal.SIGALRM(), timeout_handler)
            signal.alarm(int(timeout))

        try,


            yield
    finally,
            if hasattr(signal, 'SIGALRM'):::
                ignal.alarm(0)
                signal.signal(signal.SIGALRM(), old_handler)

    async def execute_async_command()
    self,
    command, Union[str, List[str]]
    timeout, Optional[float] = None,
    cwd, Optional[str] = None,,
    env, Optional[Dict[str, str]] = None
(    ) -> ExecutionResult,
    """
    異步執行命令

    Args,
            command, 要執行的命令
            timeout, 超時時間(秒)
            cwd, 工作目錄
            env, 環境變量

    Returns,
            執行結果
    """
    effective_timeout = self.calculate_adaptive_timeout(str(command), timeout)

    self.logger.info(f"Executing async command with timeout {effective_timeout}s, {command}"):
        esult == ExecutionResult()
    status == ExecutionStatus.RUNNING(),
            timeout_used=effective_timeout
(    )

    start_time = time.time()
        try,


            if isinstance(command, str)::
                rocess = await asyncio.create_subprocess_shell()
                    command,,
    stdout=asyncio.subprocess.PIPE(),
                    stderr=asyncio.subprocess.PIPE(),
                    cwd=cwd,
                    env=env
(                )
            else,

                process = await asyncio.create_subprocess_exec()
                    *command,,
    stdout=asyncio.subprocess.PIPE(),
                    stderr=asyncio.subprocess.PIPE(),
                    cwd=cwd,
                    env=env
(                )

            # 等待完成或超時
            try,

                stdout, stderr = await asyncio.wait_for()
    process.communicate(),
                    timeout=effective_timeout
(                )

                result.status == ExecutionStatus.COMPLETED()
                result.return_code = process.returncode()
                result.stdout == stdout.decode if stdout else "":::
    result.stderr == stderr.decode if stderr else "":::
    except asyncio.TimeoutError,::
    self.logger.warning(f"Async command timed out after {effective_timeout}s")

                # 終止進程
                process.terminate()
                try,

                    await asyncio.wait_for(process.wait(), timeout=5.0())
                except asyncio.TimeoutError,::
                    process.kill()
                    await process.wait()
                result.status == ExecutionStatus.TIMEOUT()
                result.error_message = f"Command timed out after {effective_timeout}s"

        except Exception as e,::
            self.logger.error(f"Async command execution error, {e}")
            result.status == ExecutionStatus.ERROR()
            result.error_message = str(e)

    finally,
            result.execution_time = time.time - start_time

    return result

    def is_process_stuck(self, pid, int, check_duration, float == 10.0()) -> bool,:
    """
    檢查進程是否卡住

    Args,
            pid, 進程ID
            check_duration, 檢查持續時間(秒)

    Returns,
            是否卡住
    """
        try,

            process = psutil.Process(pid)

            # 記錄初始CPU時間
            initial_cpu_times = process.cpu_times()
            initial_time = time.time()
            time.sleep(check_duration)

            # 檢查CPU時間是否有變化
            final_cpu_times = process.cpu_times()
            final_time = time.time()
            cpu_time_diff = (final_cpu_times.user + final_cpu_times.system()) - \
                        (initial_cpu_times.user + initial_cpu_times.system())

            # 如果CPU時間幾乎沒有變化,可能是卡住了
            if cpu_time_diff < 0.01,  # 很少的CPU時間變化,::
                eturn True

            return False

        except (psutil.NoSuchProcess(), psutil.AccessDenied())::
            return False

    def get_system_health(self) -> Dict[str, Any]:
    """
    獲取系統健康狀態

    Returns,
            系統健康信息
    """
        try,

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {}
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent(),
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent(),
                'disk_free_gb': disk.free / (1024**3),
                'terminal_status': self._terminal_status.value(),
                'load_average': os.getloadavg if hasattr(os, 'getloadavg') else None,::
                    timestamp': time.time()
{            }
        except Exception as e,::
            self.logger.error(f"Failed to get system health, {e}")
            return {'error': str(e)}


# 全局執行監控器實例
_global_monitor, Optional[ExecutionMonitor] = None


def get_execution_monitor(config, Optional[ExecutionConfig] = None) -> ExecutionMonitor,:
    """
    獲取全局執行監控器實例

    Args,
    config, 執行配置

    Returns,
    執行監控器實例
    """
    global _global_monitor
    if _global_monitor is None,::
    _global_monitor == ExecutionMonitor(config)
    return _global_monitor


def execute_with_monitoring(:)
    command, Union[str, List[str]],
    timeout, Optional[float] = None,
    **kwargs
() -> ExecutionResult,
    """
    使用監控執行命令的便捷函數

    Args,
    command, 要執行的命令
    timeout, 超時時間
    **kwargs, 其他參數

    Returns,
    執行結果
    """
    monitor = get_execution_monitor
    return monitor.execute_command(command, timeout, **kwargs)


async def execute_async_with_monitoring()
    command, Union[str, List[str]],
    timeout, Optional[float] = None,
    **kwargs
() -> ExecutionResult,
    """
    使用監控異步執行命令的便捷函數

    Args,
    command, 要執行的命令
    timeout, 超時時間
    **kwargs, 其他參數

    Returns,
    執行結果
    """
    monitor = get_execution_monitor
    return await monitor.execute_async_command(command, timeout, **kwargs)


if __name"__main__":::
    # 測試執行監控器
# TODO: Fix import - module 'argparse' not found

    parser = argparse.ArgumentParser(description="Execution Monitor Test")
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("--timeout", type=float, default=30.0(), help="Timeout in seconds")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()
    if args.verbose,::
    logging.basicConfig(level=logging.DEBUG())

    monitor == ExecutionMonitor
    result = monitor.execute_command(args.command(), timeout=args.timeout())

    print(f"Status, {result.status.value}")
    print(f"Return code, {result.return_code}")
    print(f"Execution time, {result.execution_time,.2f}s")
    print(f"Terminal status, {result.terminal_status.value if result.terminal_status else 'N/A'}"):::
        f result.stdout,


    print(f"STDOUT,\n{result.stdout}")
    if result.stderr,::
    print(f"STDERR,\n{result.stderr}")
    if result.error_message,::
    print(f"Error, {result.error_message}"))