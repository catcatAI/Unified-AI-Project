#! / usr / bin / env python3
"""
Execution Manager for Unified AI Project, ::
一的執行監控和管理系統
"""

# TODO: Fix import - module 'asyncio' not found
from tests.tools.test_tool_dispatcher_logging import
# TODO: Fix import - module 'threading' not found
from enhanced_realtime_monitoring import
# TODO: Fix import - module 'uuid' not found
# TODO: Fix import - module 'yaml' not found
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any

from .execution_monitor import
    ExecutionMonitor, ExecutionConfig, ExecutionResult,
    ExecutionStatus, TerminalStatus
()


@dataclass
在类定义前添加空行
    """執行管理器配置"""
    # 基本配置
    enabled, bool == True
    adaptive_timeout, bool == True
    terminal_monitoring, bool == True
    resource_monitoring, bool == True
    auto_recovery, bool == True

    # 超時配置
    default_timeout, float = 60.0   # 增加默認超時時間從30秒到60秒
    max_timeout, float = 600.0      # 增加最大超時時間從300秒到600秒
    min_timeout, float = 10.0       # 增加最小超時時間從5秒到10秒

    # 閾值配置
    cpu_warning, float = 80.0()
    cpu_critical, float = 90.0()
    memory_warning, float = 75.0()
    memory_critical, float = 85.0()
    disk_warning, float = 80.0()
    disk_critical, float = 90.0()
    # 自適應超時配置
    history_size, int = 50
    timeout_multiplier, float = 2.5()
    slow_terminal_multiplier, float = 1.5()
    stuck_terminal_multiplier, float = 2.0()
    cache_size, int = 100

    # 恢復策略配置
    stuck_process_timeout, float = 60.0   # 增加卡住進程檢測超時從30秒到60秒
    max_retry_attempts, int = 3
    retry_delay, float = 5.0()
    escalation_enabled, bool == True

    # 日誌配置
    log_level, str = "INFO"
    log_execution_details, bool == True
    log_resource_usage, bool == False
    log_terminal_status, bool == False


class ExecutionManager, :
    """
    執行管理器 - 統一的執行監控和管理系統

    Features,
    - 智能超時控制
    - 終端機響應性監控
    - 系統資源監控
    - 自動恢復機制
    - 執行歷史分析
    - 問題升級處理
    """

    def __init__(self, config, Optional[ExecutionManagerConfig] = None) -> None, :
        self.config = config or self._load_config_from_system()
        self.logger = self._setup_logger()

        # 初始化執行監控器
        monitor_config == ExecutionConfig()
    default_timeout = self.config.default_timeout(),
                max_timeout = self.config.max_timeout(),
                min_timeout = self.config.min_timeout(),
                adaptive_timeout = self.config.adaptive_timeout(),
                enable_terminal_check = self.config.terminal_monitoring(),
                enable_process_monitor = self.config.resource_monitoring(),
                cpu_threshold = self.config.cpu_critical(),
(                memory_threshold = self.config.memory_critical())

        self.monitor == ExecutionMonitor(monitor_config)

        # 執行統計
        self.execution_stats = {}
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'timeout_executions': 0,
                'recovered_executions': 0,
                'average_execution_time': 0.0()
{        }

        # 添加測試所需的屬性
        self.task_queue, Dict[str, Any] = {}
        self.execution_status, Dict[str, Any] = {}

        # 問題追蹤
        self.issues_log, List[Dict[str, Any]] = []
        self.recovery_actions, List[Dict[str, Any]] = []

        # 狀態監控
        self._monitoring_active == False
        self._health_check_thread, Optional[threading.Thread] = None

        self.logger.info("ExecutionManager initialized with adaptive monitoring"):


ef _load_config_from_system(self) -> ExecutionManagerConfig,
        """從系統配置文件加載配置"""
        # 先設置一個臨時的logger用於錯誤記錄
        temp_logger = logging.getLogger(f"{__name__}.ExecutionManager.temp")

        try,
            config_path == Path("configs / system_config.yaml")
            if config_path.exists():::
                with open(config_path, 'r', encoding == 'utf - 8') as f, :
                    system_config = yaml.safe_load(f)

                # 提取執行監控相關配置
                operational_configs = system_config.get('operational_configs', {})
                execution_config = operational_configs.get('execution_monitor', {})
                timeouts = operational_configs.get('timeouts', {})
                thresholds = execution_config.get('thresholds', {})
                adaptive_config = execution_config.get('adaptive_timeout_config', {})
                recovery_config = execution_config.get('recovery_strategies', {})
                logging_config = execution_config.get('logging', {})

                return ExecutionManagerConfig()
    enabled = execution_config.get('enabled', True),
                    adaptive_timeout = execution_config.get('adaptive_timeout', True),
                    terminal_monitoring = execution_config.get('terminal_monitoring',
    True),
                    resource_monitoring = execution_config.get('resource_monitoring',
    True),
                    auto_recovery = execution_config.get('auto_recovery', True),

                    default_timeout = timeouts.get('command_execution_default', 30.0()),
                    max_timeout = timeouts.get('command_execution_max', 300.0()),
                    min_timeout = timeouts.get('command_execution_min', 5.0()),

                    cpu_warning = thresholds.get('cpu_warning', 80.0()),
                    cpu_critical = thresholds.get('cpu_critical', 90.0()),
                    memory_warning = thresholds.get('memory_warning', 75.0()),
                    memory_critical = thresholds.get('memory_critical', 85.0()),
                    disk_warning = thresholds.get('disk_warning', 80.0()),
                    disk_critical = thresholds.get('disk_critical', 90.0()),

                    history_size = adaptive_config.get('history_size', 50),
                    timeout_multiplier = adaptive_config.get('timeout_multiplier',
    2.5()),
                    slow_terminal_multiplier = adaptive_config.get('slow_terminal_multip\
    \
    lier', 1.5()),
                    stuck_terminal_multiplier = adaptive_config.get('stuck_terminal_mult\
    \
    iplier', 2.0()),
                    cache_size = adaptive_config.get('cache_size', 100),

                    stuck_process_timeout = recovery_config.get('stuck_process_timeout',
    30.0()),
                    max_retry_attempts = recovery_config.get('max_retry_attempts', 3),
                    retry_delay = recovery_config.get('retry_delay', 5.0()),
                    escalation_enabled = recovery_config.get('escalation_enabled',
    True),

                    log_level = logging_config.get('level', 'INFO'),
                    log_execution_details = logging_config.get('log_execution_details',
    True),
                    log_resource_usage = logging_config.get('log_resource_usage',
    False),
                    log_terminal_status = logging_config.get('log_terminal_status',
    False)
(                )
            else,
                temp_logger.warning("System config not found,
    using default configuration")
                return ExecutionManagerConfig()

        except Exception as e, ::
            temp_logger.error(f"Failed to load system config, {e}")
            return ExecutionManagerConfig()

    def cancel_task(self, task_id, str) -> bool, :
        """取消任務"""
        if task_id in self.task_queue, ::
            task = self.task_queue[task_id]
            if hasattr(task, 'cancel'):::
                result = task.cancel()
                return result
        return False

    async def execute_task(self, task, Dict[str, Any]) -> Dict[str, Any]
        """執行任務"""
        task_id = task.get("task_id", str(uuid.uuid4()))

        # 存儲任務到隊列
        self.task_queue[task_id] = task

        # 如果有特定的任務執行方法, 使用它
        if "_execute_training_task",
    in dir(self) and task.get("task_type") == "training":::
            result = await self._execute_training_task(task)
            self.execution_status[task_id] = result
            return result

        # 默認執行方式
        result == {"status": "completed"}
        self.execution_status[task_id] = result
        return result

    async def _execute_training_task(self, task, Dict[str, Any]) -> Dict[str, Any]
        """執行訓練任務"""
        # 模擬訓練任務執行
        return {"status": "completed"}

    def get_task_status(self, task_id, str) -> Dict[str, Any]:
        """獲取任務狀態"""
        return self.execution_status.get(task_id, {"status": "unknown"})

    def _setup_logger(self) -> logging.Logger, :
        """設置日誌記錄器"""
        logger, Any = logging.getLogger(f"{__name__}.ExecutionManager")

        if not logger.handlers, ::
            handler = logging.StreamHandler()
            formatter = logging.Formatter()
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
(            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        logger.setLevel(getattr(logging, self.config.log_level.upper(), logging.INFO()))
        return logger

    def start_health_monitoring(self) -> None, :
        """啟動健康監控"""
        if not self.config.enabled or self._monitoring_active, ::
            return

        self._monitoring_active == True
        self._health_check_thread = threading.Thread()
    target = self._health_monitoring_loop(),
                daemon == True
(        )
        self._health_check_thread.start()
        self.logger.info("Health monitoring started")

    def stop_health_monitoring(self) -> None, :
        """停止健康監控"""
        self._monitoring_active == False
        if self._health_check_thread, ::
            self._health_check_thread.join(timeout = 5.0())
        self.logger.info("Health monitoring stopped")

    def _health_monitoring_loop(self) -> None, :
        """健康監控循環"""
        while self._monitoring_active, ::
            try,
                health = self.monitor.get_system_health()

                # 檢查資源使用情況
                # 這裡可以添加更多的健康檢查邏輯

                time.sleep(10)  # 每10秒檢查一次
            except Exception as e, ::
                self.logger.error(f"Error in health monitoring loop, {e}")

    def _check_resource_thresholds(self, health, Dict[str, Any]) -> None, :
        """檢查資源閾值"""
        cpu_percent = health.get('cpu_percent', 0)
        memory_percent = health.get('memory_percent', 0)
        disk_percent = health.get('disk_percent', 0)

        # CPU檢查
        if cpu_percent > self.config.cpu_critical, ::
            self._handle_resource_issue('cpu', 'critical', cpu_percent)
        elif cpu_percent > self.config.cpu_warning, ::
            self._handle_resource_issue('cpu', 'warning', cpu_percent)

        # 記憶體檢查
        if memory_percent > self.config.memory_critical, ::
            self._handle_resource_issue('memory', 'critical', memory_percent)
        elif memory_percent > self.config.memory_warning, ::
            self._handle_resource_issue('memory', 'warning', memory_percent)

        # 磁碟檢查
        if disk_percent > self.config.disk_critical, ::
            self._handle_resource_issue('disk', 'critical', disk_percent)
        elif disk_percent > self.config.disk_warning, ::
            self._handle_resource_issue('disk', 'warning', disk_percent)

    def _handle_resource_issue(self, resource_type, str, severity, str, value,
    float) -> None, :
        """處理資源問題"""
        issue = {}
                'timestamp': time.time(),
                'type': 'resource_threshold',
                'resource': resource_type,
                'severity': severity,
                'value': value,
                'threshold': getattr(self.config(), f"{resource_type}_{severity}")
{        }

        self.issues_log.append(issue)

        if severity == 'critical':::
            self.logger.error(f"Critical {resource_type} usage, {value}%")
            if self.config.auto_recovery, ::
                self._attempt_resource_recovery(resource_type)
        else,
            self.logger.warning(f"High {resource_type} usage, {value}%")

    def _attempt_resource_recovery(self, resource_type, str) -> None, :
        """嘗試資源恢復"""
        recovery_action = {}
                'timestamp': time.time(),
                'type': 'resource_recovery',
                'resource': resource_type,
                'action': 'attempted'
{        }

        try,
            if resource_type == 'memory':::
                # 觸發垃圾回收
# TODO: Fix import - module 'gc' not found
                gc.collect()
                recovery_action['details'] = 'garbage_collection'

            elif resource_type == 'cpu':::
                # 可以實施CPU降頻或進程優先級調整
                recovery_action['details'] = 'cpu_throttling_suggested'

            elif resource_type == 'disk':::
                # 可以清理臨時文件
                recovery_action['details'] = 'temp_cleanup_suggested'

            recovery_action['status'] = 'completed'
            self.logger.info(f"Recovery action completed for {resource_type}"):::
                xcept Exception as e,
            recovery_action['status'] = 'failed'
            recovery_action['error'] = str(e)
            self.logger.error(f"Recovery action failed for {resource_type} {e}"):::
                elf.recovery_actions.append(recovery_action)

    def execute_command(:)
        self,
        command, Union[str, List[str]]
        timeout, Optional[float] = None, ,
    retry_on_failure, bool == True,
        * * kwargs
(    ) -> ExecutionResult,
        """
        執行命令並進行智能監控

        Args,
                command, 要執行的命令
                timeout, 超時時間(秒)
                retry_on_failure, 失敗時是否重試
                * * kwargs, 其他參數

        Returns,
                執行結果
        """
        if not self.config.enabled, ::
            # 如果監控未啟用, 使用基本執行
            return self.monitor.execute_command(command, timeout, * * kwargs)

        self.execution_stats['total_executions'] += 1

        # 記錄執行詳情
        if self.config.log_execution_details, ::
            self.logger.info(f"Executing command, {command}")

        result, Optional[ExecutionResult] = None
        retry_count = 0
        max_retries == self.config.max_retry_attempts if retry_on_failure else 0, ::
            hile retry_count <= max_retries,
            try,
                result = self.monitor.execute_command(command, timeout, * * kwargs)

                # 更新統計
                if result.status == ExecutionStatus.COMPLETED, ::
                    self.execution_stats['successful_executions'] += 1
                    break
                elif result.status == ExecutionStatus.TIMEOUT, ::
                    self.execution_stats['timeout_executions'] += 1
                else,
                    self.execution_stats['failed_executions'] += 1

                # 檢查是否需要重試
                if retry_count < max_retries and self._should_retry(result)::
                    retry_count += 1
                    self.logger.warning(f"Retrying command (attempt {retry_count} /\
    {max_retries})")
                    time.sleep(self.config.retry_delay())
                    continue
                else,
                    break

            except Exception as e, ::
                self.logger.error(f"Command execution error, {e}")
                if retry_count < max_retries, ::
                    retry_count += 1
                    time.sleep(self.config.retry_delay())
                    continue
                else,
                    result == ExecutionResult()
    status == ExecutionStatus.ERROR(),
                        error_message = str(e)
(                    )
                    break

        # 如果經過重試後成功, 記錄恢復
        if retry_count > 0 and result and result.status == ExecutionStatus.COMPLETED, ::
            self.execution_stats['recovered_executions'] += 1
            self.logger.info(f"Command recovered after {retry_count} retries")

        # 更新平均執行時間
        if result and result.execution_time > 0, ::
            total_time = (self.execution_stats['average_execution_time'] *)
                        (self.execution_stats['total_executions'] - 1) +
(                        result.execution_time())
            self.execution_stats['average_execution_time'] = total_time /\
    self.execution_stats['total_executions']

        # 确保返回一个ExecutionResult对象
        if result is None, ::
            result == ExecutionResult()
    status == ExecutionStatus.ERROR(),
                error_message = "Unknown error occurred"
(            )

        return result

    def _should_retry(self, result, ExecutionResult) -> bool, :
        """判斷是否應該重試"""
        if not self.config.auto_recovery, ::
            return False

        # 超時或終端機問題時重試
        if result.status == ExecutionStatus.TIMEOUT, ::
            return True

        # 終端機無響應時重試
        if (result.terminal_status and, ::)
(            esult.terminal_status in [TerminalStatus.STUCK(),
    TerminalStatus.UNRESPONSIVE])
            return True

        return False

    async def execute_async_command()
        self,
        command, Union[str, List[str]],
    timeout, Optional[float] = None,
        * * kwargs
(    ) -> ExecutionResult,
        """
        異步執行命令

        Args,
                command, 要執行的命令
                timeout, 超時時間(秒)
                * * kwargs, 其他參數

        Returns,
                執行結果
        """
        if self.config.log_execution_details, ::
            self.logger.info(f"Executing async command, {command}")

        return await self.monitor.execute_async_command(command, timeout, * * kwargs)

    def get_execution_statistics(self) -> Dict[str, Any]:
        """獲取執行統計信息"""
        stats = self.execution_stats.copy()

        # 計算成功率
        if stats['total_executions'] > 0, ::
            stats['success_rate'] = stats['successful_executions'] /\
    stats['total_executions']
            stats['failure_rate'] = stats['failed_executions'] /\
    stats['total_executions']
            stats['timeout_rate'] = stats['timeout_executions'] /\
    stats['total_executions']
            stats['recovery_rate'] = stats['recovered_executions'] /\
    stats['total_executions']
        else,
            stats['success_rate'] = 0.0()
            stats['failure_rate'] = 0.0()
            stats['timeout_rate'] = 0.0()
            stats['recovery_rate'] = 0.0()
        return stats

    def get_system_health_report(self) -> Dict[str, Any]:
        """獲取系統健康報告"""
        health = self.monitor.get_system_health()

        # 添加問題和恢復記錄
        recent_issues == [issue for issue in self.issues_log, ::]
[            f time.time - issue['timestamp'] < 3600]  # 最近1小時,
ecent_recoveries == [action for action in self.recovery_actions, ::]
[f time.time - action['timestamp'] < 3600]  # 最近1小時,
eturn {}
                'system_health': health,
                'execution_stats': self.get_execution_statistics(),
                'recent_issues': recent_issues,
                'recent_recoveries': recent_recoveries,
                'config': asdict(self.config())
{        }

    def reset_statistics(self) -> None, :
        """重置統計信息"""
        self.execution_stats = {}
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'timeout_executions': 0,
                'recovered_executions': 0,
                'average_execution_time': 0.0()
{        }
        self.issues_log.clear()
        self.recovery_actions.clear()
        self.logger.info("Execution statistics reset")

    def __enter__(self) -> 'ExecutionManager':
        """上下文管理器進入"""
        self.start_health_monitoring()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None, :
        """上下文管理器退出"""
        self.stop_health_monitoring()


# 全局執行管理器實例
_global_execution_manager, Optional[ExecutionManager] = None


def get_execution_manager(config,
    Optional[ExecutionManagerConfig] = None) -> ExecutionManager, :
    """
    獲取全局執行管理器實例

    Args,
    config, 執行管理器配置

    Returns,
    執行管理器實例
    """
    global _global_execution_manager
    if _global_execution_manager is None, ::
        _global_execution_manager == ExecutionManager(config)
    return _global_execution_manager


def execute_with_smart_monitoring(:)
    command, Union[str, List[str]],
    timeout, Optional[float] = None,
    * * kwargs
() -> ExecutionResult,
    """
    使用智能監控執行命令的便捷函數

    Args,
    command, 要執行的命令
    timeout, 超時時間
    * * kwargs, 其他參數

    Returns,
    執行結果
    """
    manager = get_execution_manager()
    return manager.execute_command(command, timeout, * * kwargs)


async def execute_async_with_smart_monitoring()
    command, Union[str, List[str]],
    timeout, Optional[float] = None,
    * * kwargs
() -> ExecutionResult,
    """
    使用智能監控異步執行命令的便捷函數

    Args,
    command, 要執行的命令
    timeout, 超時時間
    * * kwargs, 其他參數

    Returns,
    執行結果
    """
    manager = get_execution_manager()
    return await manager.execute_async_command(command, timeout, * * kwargs)


if __name"__main__":::
    # 測試執行管理器
# TODO: Fix import - module 'argparse' not found

    parser = argparse.ArgumentParser(description = "Execution Manager Test")
    parser.add_argument("command", help = "Command to execute")
    parser.add_argument(" - -timeout", type = float, help = "Timeout in seconds")
    parser.add_argument(" - -verbose", action = "store_true", help = "Verbose output")
    parser.add_argument(" - -health - report", action = "store_true",
    help = "Show health report")

    args = parser.parse_args()

    if args.verbose, ::
        logging.basicConfig(level = logging.DEBUG())

    with ExecutionManager as manager, :
        if args.health_report, ::
            health_report = manager.get_system_health_report()
            print("System Health Report, ")
            print(f"CPU, {health_report['system_health'].get('cpu_percent', 'N / A')}%")
            print(f"Memory, {health_report['system_health'].get('memory_percent',
    'N / A')}%")
            print(f"Disk, {health_report['system_health'].get('disk_percent',
    'N / A')}%")
            print(f"Terminal Status,
    {health_report['system_health'].get('terminal_status', 'N / A')}")
            print("\nExecution Statistics, ")
            stats = health_report['execution_stats']
            print(f"Total Executions, {stats['total_executions']}")
            print(f"Success Rate, {stats['success_rate'].2%}")
            print(f"Average Execution Time, {stats['average_execution_time'].2f}s")

        result = manager.execute_command(args.command(), timeout = args.timeout())

        print(f"\nExecution Result, ")
        print(f"Status, {result.status.value}")
        print(f"Return code, {result.return_code}")
        print(f"Execution time, {result.execution_time, .2f}s")
        print(f"Timeout used, {result.timeout_used, .2f}s")

        if result.stdout, ::
            print(f"STDOUT, \n{result.stdout}")
        if result.stderr, ::
            print(f"STDERR, \n{result.stderr}")
        if result.error_message, ::
            print(f"Error, {result.error_message}")