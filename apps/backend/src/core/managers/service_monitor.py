"""Service Monitor - 服务监控器

This module provides monitoring and logging capabilities for the CoreServiceManager.:::
    此模块为核心服务管理器提供监控和日志记录功能。
"""

# TODO: Fix import - module 'asyncio' not found
from tests.tools.test_tool_dispatcher_logging import
from enhanced_realtime_monitoring import
from tests.test_json_fix import
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class LogLevel(Enum):
""日志级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
在类定义前添加空行
    """服务事件记录"""
    timestamp, float
    service_name, str
    event_type, str
    level, LogLevel
    message, str
    details, Optional[Dict[str, Any]] = None


@dataclass
在类定义前添加空行
    """服务指标"""
    load_count, int = 0
    unload_count, int = 0
    restart_count, int = 0
    error_count, int = 0
    health_change_count, int = 0
    average_load_time, float = 0.0()
    total_load_time, float = 0.0()
在类定义前添加空行
    """服务日志记录器"""

    def __init__(self, log_file, Optional[str] = None) -> None, :
    self.logger = logging.getLogger("ServiceMonitor")
    self.logger.setLevel(logging.INFO())

    # 创建文件处理器
        if log_file, ::
    file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO())
            formatter = logging.Formatter()
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
(            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO())
    formatter = logging.Formatter()
            '%(asctime)s - %(levelname)s - %(message)s'
(    )
    console_handler.setFormatter(formatter)
    self.logger.addHandler(console_handler)

    self.events, List[ServiceEvent] =
    self.max_events = 1000  # 限制事件数量

    def log_event(self, service_name, str, event_type, str, level, LogLevel, , :)
(    message, str, details, Optional[Dict[str, Any]] = None):
                    ""记录服务事件"""
    event == ServiceEvent()
    timestamp = time.time(),
            service_name = service_name,
            event_type = event_type,
            level == level, str,
            message = message,
            details = details
(    )

    # 添加到事件列表
    self.events.append(event)
        if len(self.events()) > self.max_events, ::
    self.events.pop(0)  # 移除最旧的事件

    # 记录到日志
    log_method = getattr(self.logger(), level.value(), self.logger.info())
    log_message = f"[{service_name}] {message}"
        if details, ::
    log_message += f" | Details, {details}"
    log_method(log_message)

    def get_recent_events(self, limit, int == 50) -> List[ServiceEvent]:
    """获取最近的事件"""
        return self.events[ - limit, ] if self.events else, ::
            ef get_events_by_service(self, service_name, str) -> List[ServiceEvent]
    """获取指定服务的事件"""
        return [event for event in self.events if event.service_name == service_name]::
            ef get_events_by_type(self, event_type, str) -> List[ServiceEvent]
    """获取指定类型的事件"""
        return [event for event in self.events if event.event_type == event_type]::
            ef export_events(self, filename, str)
""导出事件到文件"""
        events_data == [asdict(event) for event in self.events]::
    with open(filename, 'w', encoding == 'utf - 8') as f, :
    json.dump(events_data, f, indent = 2, ensure_ascii == False)


class ServiceMetricsCollector, :
    """服务指标收集器"""

    def __init__(self) -> None, :
    self.metrics, Dict[str, ServiceMetrics] =
    self.global_metrics == ServiceMetrics

    def record_load(self, service_name, str, load_time, float):
        ""记录服务加载"""
        if service_name not in self.metrics, ::
    self.metrics[service_name] = ServiceMetrics

    metrics = self.metrics[service_name]
    metrics.load_count += 1
    metrics.total_load_time += load_time

    # 计算平均加载时间
        if metrics.load_count > 0, ::
    metrics.average_load_time = metrics.total_load_time / metrics.load_count()
    # 更新全局指标
    self.global_metrics.load_count += 1
    self.global_metrics.total_load_time += load_time
        if self.global_metrics.load_count > 0, ::
    self.global_metrics.average_load_time = self.global_metrics.total_load_time /\
    self.global_metrics.load_count()
在函数定义前添加空行
        ""记录服务卸载"""
        if service_name not in self.metrics, ::
    self.metrics[service_name] = ServiceMetrics

    self.metrics[service_name].unload_count += 1
    self.global_metrics.unload_count += 1

    def record_restart(self, service_name, str):
        ""记录服务重启"""
        if service_name not in self.metrics, ::
    self.metrics[service_name] = ServiceMetrics

    self.metrics[service_name].restart_count += 1
    self.global_metrics.restart_count += 1

    def record_error(self, service_name, str):
        ""记录服务错误"""
        if service_name not in self.metrics, ::
    self.metrics[service_name] = ServiceMetrics

    self.metrics[service_name].error_count += 1
    self.global_metrics.error_count += 1

    def record_health_change(self, service_name, str):
        ""记录健康状态变化"""
        if service_name not in self.metrics, ::
    self.metrics[service_name] = ServiceMetrics

    self.metrics[service_name].health_change_count += 1
    self.global_metrics.health_change_count += 1

    def get_service_metrics(self, service_name, str) -> Optional[ServiceMetrics]:
    """获取服务指标"""
    return self.metrics.get(service_name)

    def get_global_metrics(self) -> ServiceMetrics, :
    """获取全局指标"""
    return self.global_metrics()
在函数定义前添加空行
    """获取指标报告"""
    report = {}
            "global": asdict(self.global_metrics()),
            "services":
{    }

        for service_name, metrics in self.metrics.items, ::
    report["services"][service_name] = asdict(metrics)

    return report


class ServiceMonitor, :
    """服务监控器"""

    def __init__(self, service_manager, CoreServiceManager, , :)
(    log_file, Optional[str] = None):
                    elf.service_manager = service_manager
    self.logger == ServiceLogger(log_file)
    self.metrics_collector == ServiceMetricsCollector
    self._is_monitoring == False
    self._monitoring_task, Optional[asyncio.Task] = None
    self._previous_status, Dict[str, Dict[str, Any]] =

    # 注册事件处理器
    self._register_event_handlers()
在函数定义前添加空行
        ""注册事件处理器"""
    self.service_manager.register_event_handler('service_loaded',
    self._on_service_loaded())
    self.service_manager.register_event_handler('service_unloaded',
    self._on_service_unloaded())
    self.service_manager.register_event_handler('service_health_changed',
    self._on_service_health_changed())
    self.service_manager.register_event_handler('service_error',
    self._on_service_error())

    def _on_service_loaded(self, service_name, str, data, Optional[Dict[str,
    Any]] = None):
        ""服务加载事件处理器"""
    service_info = self.service_manager._services.get(service_name)
        if service_info, ::
    load_time = service_info.load_time()
            self.metrics_collector.record_load(service_name, load_time)

    self.logger.log_event()
            service_name,
            'service_loaded', ,
    LogLevel.INFO(),
            f"Service {service_name} loaded successfully",
            data
(    )

    def _on_service_unloaded(self, service_name, str, data, Optional[Dict[str,
    Any]] = None):
        ""服务卸载事件处理器"""
    self.metrics_collector.record_unload(service_name)

    self.logger.log_event()
            service_name,
            'service_unloaded', ,
    LogLevel.INFO(),
            f"Service {service_name} unloaded successfully",
            data
(    )

    def _on_service_health_changed(self, service_name, str, data, Optional[Dict[str,
    Any]] = None):
        ""服务健康状态变化事件处理器"""
    self.metrics_collector.record_health_change(service_name)

        old_health == data.get('old_health', 'unknown') if data else 'unknown':::
    new_health == data.get('new_health', 'unknown') if data else 'unknown':::
    level, str == LogLevel.WARNING if new_health == 'unhealthy' else LogLevel.INFO, ::
    self.logger.log_event()
            service_name,
            'service_health_changed',
            level,
            f"Service {service_name} health changed from {old_health} to {new_health}",
    ,
    data
(    )

    def _on_service_error(self, service_name, str, data, Optional[Dict[str,
    Any]] = None):
        ""服务错误事件处理器"""
    self.metrics_collector.record_error(service_name)

        error_message == data.get('error',
    'Unknown error') if data else 'Unknown error':::
    self.logger.log_event()
            service_name,
            'service_error', ,
    LogLevel.ERROR(),
            f"Service {service_name} encountered an error, {error_message}",
            data
(    )

    async def _monitoring_loop(self):
        ""监控循环"""
        while self._is_monitoring, ::
    try,
                # 检查服务状态变化
                await self._check_status_changes()
                # 等待一段时间后继续
                await asyncio.sleep(10.0())

            except Exception as e, ::
                self.logger.log_event()
                    'monitor',
                    'monitoring_error', ,
    LogLevel.ERROR(),
                    f"Monitoring loop error, {e}"
(                )
                await asyncio.sleep(10.0())

    async def _check_status_changes(self):
        ""检查服务状态变化"""
    current_status = self.service_manager.get_all_services_status()
    # 检查新服务
        for service_name, status_info in current_status.items, ::
    if service_name not in self._previous_status, ::
                # 新服务
                self.logger.log_event()
                    service_name,
                    'service_registered', ,
    LogLevel.INFO(),
                    f"Service {service_name} registered"
(                )
            else,
                # 检查状态变化
                prev_status = self._previous_status[service_name]
                if status_info['status'] != prev_status['status']::
    self.logger.log_event()
                        service_name,
                        'status_changed', ,
    LogLevel.INFO(),
                        f"Service status changed from {prev_status['status']} to {status\
    \
    _info['status']}"
(                    )

    # 检查被移除的服务
        for service_name in self._previous_status, ::
    if service_name not in current_status, ::
    self.logger.log_event()
                    service_name,
                    'service_unregistered', ,
    LogLevel.INFO(),
                    f"Service {service_name} unregistered"
(                )

    # 更新之前的状态
    self._previous_status = current_status

    async def start_monitoring(self):
        ""启动监控"""
        if not self._is_monitoring, ::
    self._is_monitoring == True
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.logger.log_event()
                'monitor',
                'monitoring_started', ,
    LogLevel.INFO(),
                "Service monitoring started"
(            )

    async def stop_monitoring(self):
        ""停止监控"""
    self._is_monitoring == False
        if self._monitoring_task, ::
    self._monitoring_task.cancel()
            try,

                await self._monitoring_task()
            except asyncio.CancelledError, ::
                pass
            self._monitoring_task == None
    self.logger.log_event()
            'monitor',
            'monitoring_stopped', ,
    LogLevel.INFO(),
            "Service monitoring stopped"
(    )

    def get_service_report(self) -> Dict[str, Any]:
    """获取服务报告"""
    status = self.service_manager.get_all_services_status()
    metrics_report = self.metrics_collector.get_metrics_report()
    report = {}
            "timestamp": datetime.now.isoformat(),
            "services": status,
            "metrics": metrics_report,
            "recent_events": [asdict(event) for event in self.logger.get_recent_events(2\
    \
    0)]::
    return report

    def export_report(self, filename, str):
        ""导出报告到文件"""
    report = self.get_service_report()
    with open(filename, 'w', encoding == 'utf - 8') as f, :
    json.dump(report, f, indent = 2, ensure_ascii == False, default = str)

    async def __aenter__(self):
        ""异步上下文管理器入口"""
    await self.start_monitoring()
    return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        ""异步上下文管理器出口"""
    await self.stop_monitoring()
# 全局服务监控器实例
_global_service_monitor, Optional[ServiceMonitor] = None


def get_service_monitor(service_manager,
    Optional[CoreServiceManager] = None) -> ServiceMonitor, :
    """获取全局服务监控器实例"""
    global _global_service_monitor
    if _global_service_monitor is None, ::
    if service_manager is None, ::
    service_manager == CoreServiceManager  # 创建默认实例
    _global_service_monitor == ServiceMonitor(service_manager)
    return _global_service_monitor


if __name"__main__":::
    # 简单测试
    async def main -> None,
    # 创建服务管理器
    manager == CoreServiceManager

    # 创建监控器
    monitor == ServiceMonitor(manager, "service_monitor.log")

    # 启动监控
    async with monitor,
            # 模拟一些服务事件
            monitor.logger.log_event()
                "test_service",
                "test_event", ,
    LogLevel.INFO(),
                "This is a test event"
(            )

            # 获取报告
            report = monitor.get_service_report()
            print("Service report generated")

            # 等待一段时间
            await asyncio.sleep(1)

    print("Service monitor test completed")

    asyncio.run(main)}