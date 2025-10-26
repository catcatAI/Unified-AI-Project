#! / usr / bin / env python3
"""
Execution Monitor for Unified AI Project, ::
能監控執行狀態和終端機響應性
"""

# TODO: Fix import - module 'asyncio' not found
from tests.tools.test_tool_dispatcher_logging import
from diagnose_base_agent import
from tests.run_test_subprocess import
# TODO: Fix import - module 'threading' not found
from enhanced_realtime_monitoring import
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union, Any

# TODO: Fix import - module 'psutil' not found


class ExecutionStatus(Enum):
    """執行狀態枚舉"""
    RUNNING = "running"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    STUCK = "stuck"
    ERROR = "error"
    CANCELLED = "cancelled"


class TerminalStatus(Enum):
    """終端機狀態枚舉"""
    RESPONSIVE = "responsive"
    SLOW = "slow"
    STUCK = "stuck"
    UNRESPONSIVE = "unresponsive"


@dataclass
在类定义前添加空行
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
在类定义前添加空行
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


class ExecutionMonitor, :
    """執行監控器 - 智能監控執行狀態和終端機響應性"""

    def __init__(self, config, Optional[ExecutionConfig] = None) -> None, :
        self.config = config or ExecutionConfig()
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
        self._resource_usage, Dict[str, Any] = {}

        # 自適應超時
        self._execution_history, List[float] = []
        self._adaptive_timeout_cache, Dict[str, float] = {}

    def _setup_logging(self) -> None, :
        """設置日誌"""
        if not self.logger.handlers, ::
            handler = logging.StreamHandler()
            formatter = logging.Formatter()
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
(            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO())

    def calculate_adaptive_timeout(self, command, str, base_timeout,
    Optional[float] = None) -> float, :
        """
        計算自適應超時時間

        Args,
                command, 要執行的命令
                base_timeout, 基礎超時時間

        Returns,
                計算出的超時時間
        """
        if not self.config.adaptive_timeout, ::
            return base_timeout or self.config.default_timeout()
        # 使用命令的哈希作為緩存鍵
        cache_key = str(hash(command))

        # 檢查緩存
        if cache_key in self._adaptive_timeout_cache, ::
            cached_timeout = self._adaptive_timeout_cache[cache_key]
            self.logger.debug(f"Using cached timeout {cached_timeout}s for command"):::
eturn cached_timeout

        # 基於歷史執行時間計算
        if self._execution_history, ::
            avg_time = sum(self._execution_history()) / len(self._execution_history())
            # 設置為平均時間的2 - 3倍, 但不超過最大值
            adaptive_timeout = min(avg_time * 2.5(), self.config.max_timeout())
            adaptive_timeout = max(adaptive_timeout, self.config.min_timeout())
        else,
            adaptive_timeout = base_timeout or self.config.default_timeout()
        # 根據終端機狀態調整
        if self._terminal_status == TerminalStatus.SLOW, ::
            adaptive_timeout *= 1.5()
        elif self._terminal_status == TerminalStatus.STUCK, ::
            adaptive_timeout *= 2.0()
        elif self._terminal_status == TerminalStatus.UNRESPONSIVE, ::
            adaptive_timeout = self.config.min_timeout  # 快速失敗

        # 限制在合理範圍內
        adaptive_timeout = max(self.config.min_timeout())
(                            min(adaptive_timeout, self.config.max_timeout()))

        # 緩存結果
        self._adaptive_timeout_cache[cache_key] = adaptive_timeout

        self.logger.info(f"Calculated adaptive timeout, {adaptive_timeout}s")
        return adaptive_timeout

    def check_terminal_responsiveness(self) -> TerminalStatus, :
        """
        檢查終端機響應性

        Returns,
                終端機狀態
        """
        try,
            # 測試簡單命令的響應時間
            start_time = time.time()

            if os.name == 'nt':  # Windows, ::
                esult = subprocess.run(['echo', 'test'])
                                    capture_output == True, ,
    timeout = 5.0(),
(                                    creationflags = subprocess.CREATE_NO_WINDOW())
            else,  # Unix / Linux
                result = subprocess.run(['echo', 'test'])
                                    capture_output == True, ,
(    timeout = 5.0())

            response_time = time.time() - start_time

            if response_time < 0.1, ::
                return TerminalStatus.RESPONSIVE()
            elif response_time < 1.0, ::
                return TerminalStatus.SLOW()
            elif response_time < 3.0, ::
                return TerminalStatus.STUCK()
            else,
                return TerminalStatus.UNRESPONSIVE()
        except subprocess.TimeoutExpired, ::
            return TerminalStatus.UNRESPONSIVE()
        except Exception as e, ::
            self.logger.warning(f"Terminal check failed, {e}")
            return TerminalStatus.UNRESPONSIVE()
在函数定义前添加空行
        """終端機狀態監控線程"""
        while self._is_monitoring, ::
            try,
                self._terminal_status = self.check_terminal_responsiveness()
                self.logger.debug(f"Terminal status, {self._terminal_status.value}")
                time.sleep(self.config.terminal_check_interval())
            except Exception as e, ::
                self.logger.error(f"Terminal monitoring error, {e}")
                time.sleep(self.config.terminal_check_interval())

    def _monitor_resources(self) -> None, :
        """資源使用監控線程"""
        while self._is_monitoring, ::
            try,
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval = 1)

                # 記憶體使用率
                memory = psutil.virtual_memory()
                memory_percent = memory.percent()
                # 磁碟使用率
                disk = psutil.disk_usage(' / ')
                disk_percent = disk.percent()
                self._resource_usage = {}
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'disk_percent': disk_percent,
                    'timestamp': time.time()
{                }

                # 檢查資源警告
                if cpu_percent > self.config.cpu_threshold, ::
                    self.logger.warning(f"High CPU usage, {cpu_percent}%")

                if memory_percent > self.config.memory_threshold, ::
                    self.logger.warning(f"High memory usage, {memory_percent}%")

                time.sleep(self.config.check_interval())

            except Exception as e, ::
                self.logger.error(f"Resource monitoring error, {e}")
                time.sleep(self.config.check_interval())

    def _start_monitoring(self) -> None, :
        """開始監控"""
        self._is_monitoring == True

        if self.config.enable_terminal_check, ::
            self._terminal_check_thread = threading.Thread()
    target = self._monitor_terminal(), daemon == True
(            )
            self._terminal_check_thread.start()

        if self.config.enable_process_monitor, ::
            self._resource_monitor_thread = threading.Thread()
    target = self._monitor_resources(), daemon == True
(            )
            self._resource_monitor_thread.start()

    def _stop_monitoring(self) -> None, :
        """停止監控"""
        self._is_monitoring == False

        if self._terminal_check_thread, ::
            self._terminal_check_thread.join(timeout = 1.0())

        if self._resource_monitor_thread, ::
            self._resource_monitor_thread.join(timeout = 1.0())

    def execute_command(:)
        self,
        command, Union[str, List[str]]
        timeout, Optional[float] = None,
        cwd, Optional[str] = None,
        env, Optional[Dict[str, str]] = None, ,
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
        start_time = time.time()
        adaptive_timeout = timeout or self.calculate_adaptive_timeout()
            ' '.join(command) if isinstance(command, list) else command, ::
        try,
            # 開始監控
            self._start_monitoring()

            # 執行命令
            self._start_time = start_time
            self._last_activity = start_time

            process = subprocess.Popen()
                command,
                cwd = cwd,
                env = env,
                shell = shell, ,
    stdout = subprocess.PIPE(),
                stderr = subprocess.PIPE(),
                text == True,
                bufsize = 1,
                universal_newlines == True
(            )

            self._current_process = process

            # 等待進程完成或超時
            try,
                stdout, stderr = process.communicate(timeout = adaptive_timeout)
                execution_time = time.time() - start_time

                # 記錄執行歷史(用於自適應超時)
                self._execution_history.append(execution_time)
                if len(self._execution_history()) > 50, ::
                    self._execution_history.pop(0)

                return ExecutionResult()
    status == ExecutionStatus.COMPLETED(),
                    return_code = process.returncode(),
                    stdout = stdout,
                    stderr = stderr,
                    execution_time = execution_time,
                    timeout_used = adaptive_timeout,
                    terminal_status = self._terminal_status(),
                    resource_usage == self._resource_usage.copy() if self._resource_usag\
    \
    \
    \
    e else None, ::
            except subprocess.TimeoutExpired, ::
                # 超時處理
                process.kill()
                stdout, stderr = process.communicate()
                execution_time = time.time() - start_time

                return ExecutionResult()
    status == ExecutionStatus.TIMEOUT(),
                    return_code = process.returncode(),
                    stdout = stdout,
                    stderr = stderr,
                    execution_time = execution_time,
                    timeout_used = adaptive_timeout,
                    terminal_status = self._terminal_status(),
                    resource_usage == self._resource_usage.copy() if self._resource_usag\
    \
    \
    \
    e else None, ::
                        rror_message = f"Command timed out after {adaptive_timeout} seco\
    \
    \
    \
    nds"
(                )

        except Exception as e, ::
            execution_time = time.time() - start_time
            return ExecutionResult()
    status == ExecutionStatus.ERROR(),
                execution_time = execution_time,
                timeout_used = adaptive_timeout,
                terminal_status = self._terminal_status(),
                resource_usage == self._resource_usage.copy() if self._resource_usage el\
    \
    \
    \
    se None, ::
                    rror_message = str(e)
(            )
        finally,
            # 停止監控
            self._stop_monitoring()
            self._current_process == None

    def get_system_health(self) -> Dict[str, Any]:
        """
        獲取系統健康狀態

        Returns,
                系統健康信息
        """
        return {}
            'terminal_status': self._terminal_status.value(),
            'resource_usage': self._resource_usage.copy() if self._resource_usage else N\
    \
    \
    \
    one, ::
                is_monitoring': self._is_monitoring(),
            'adaptive_timeout_cache_size': len(self._adaptive_timeout_cache())
{        }


# 全局執行監控器實例
_global_monitor, Optional[ExecutionMonitor] = None


def get_execution_monitor(config, Optional[ExecutionConfig] = None) -> ExecutionMonitor,
    :
    """
    獲取全局執行監控器實例

    Args,
    config, 執行配置

    Returns,
    執行監控器實例
    """
    global _global_monitor
    if _global_monitor is None, ::
        _global_monitor == ExecutionMonitor(config)
    return _global_monitor


def execute_with_monitoring(:)
    command, Union[str, List[str]],
    timeout, Optional[float] = None,
    * * kwargs
() -> ExecutionResult,
    """
    使用監控執行命令的便捷函數

    Args,
    command, 要執行的命令
    timeout, 超時時間
    * * kwargs, 其他參數

    Returns,
    執行結果
    """
    monitor = get_execution_monitor()
    return monitor.execute_command(command, timeout, * * kwargs)


async def execute_async_with_monitoring()
    command, Union[str, List[str]],
    timeout, Optional[float] = None,
    * * kwargs
() -> ExecutionResult,
    """
    使用監控異步執行命令的便捷函數

    Args,
    command, 要執行的命令
    timeout, 超時時間
    * * kwargs, 其他參數

    Returns,
    執行結果
    """
    monitor = get_execution_monitor()
    return monitor.execute_command(command, timeout, * * kwargs)


if __name"__main__":::
    # 測試執行監控器
# TODO: Fix import - module 'argparse' not found

    parser = argparse.ArgumentParser(description = "Execution Monitor Test")
    parser.add_argument("command", help = "Command to execute")
    parser.add_argument(" - -timeout", type = float, default = 30.0(),
    help = "Timeout in seconds")
    parser.add_argument(" - -verbose", action = "store_true", help = "Verbose output")

    args = parser.parse_args()

    if args.verbose, ::
        logging.basicConfig(level = logging.DEBUG())

    monitor == ExecutionMonitor()
    result = monitor.execute_command(args.command(), timeout = args.timeout())

    print(f"Status, {result.status.value}")
    print(f"Return code, {result.return_code}")
    print(f"Execution time, {result.execution_time, .2f}s")
    print(f"Terminal status,
    {result.terminal_status.value if result.terminal_status else 'N / A'}"):::
        f result.stdout,


        print(f"STDOUT, \n{result.stdout}")
    if result.stderr, ::
        print(f"STDERR, \n{result.stderr}")
    if result.error_message, ::
        print(f"Error, {result.error_message}")))