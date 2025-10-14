"""
企業級監控和指標系統
提供實時監控、指標收集、性能分析和警報系統
"""

import asyncio
import time
import psutil
import json
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid
import statistics

from ..logging.enterprise_logger import get_logger, LogCategory, LogLevel
from ..error.error_handler import error_handler, ErrorCategory, ErrorSeverity

class MetricType(Enum):
    """指標類型"""
    COUNTER = "counter"      # 計數器（只增不減）
    GAUGE = "gauge"          # 儀表（可增可減）
    HISTOGRAM = "histogram"  # 直方圖
    SUMMARY = "summary"      # 摘要（統計分位數）

class AlertSeverity(Enum):
    """警報嚴重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MonitoringCategory(Enum):
    """監控分類"""
    SYSTEM = "system"
    APPLICATION = "application"
    DATABASE = "database"
    NETWORK = "network"
    AI_MODELS = "ai_models"
    BUSINESS = "business"
    SECURITY = "security"

@dataclass
class Metric:
    """指標數據"""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    category: MonitoringCategory
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None
    description: Optional[str] = None

@dataclass
class Alert:
    """警報"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    severity: AlertSeverity = AlertSeverity.WARNING
    category: MonitoringCategory = MonitoringCategory.SYSTEM
    message: str = ""
    condition: str = ""
    triggered_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class MetricCollector:
    """指標收集器"""
    
    def __init__(self, name: str):
        self.name = name
        self.metrics: Dict[str, Metric] = {}
        self.logger = get_logger(f"metric_collector.{name}")
    
    def increment(self, metric_name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """增加計數器"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = Metric(
                name=metric_name,
                value=0,
                metric_type=MetricType.COUNTER,
                category=MonitoringCategory.APPLICATION
            )
        
        metric = self.metrics[metric_name]
        if metric.metric_type == MetricType.COUNTER:
            metric.value += value
            metric.labels.update(labels or {})
            metric.timestamp = datetime.now()
        else:
            self.logger.warning(f"嘗試對非計數器指標執行增量操作: {metric_name}")
    
    def set_gauge(self, metric_name: str, value: Union[int, float], 
                  labels: Optional[Dict[str, str]] = None):
        """設置儀表值"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = Metric(
                name=metric_name,
                value=value,
                metric_type=MetricType.GAUGE,
                category=MonitoringCategory.APPLICATION
            )
        
        metric = self.metrics[metric_name]
        if metric.metric_type == MetricType.GAUGE:
            metric.value = value
            metric.labels.update(labels or {})
            metric.timestamp = datetime.now()
        else:
            self.logger.warning(f"嘗試對非儀表指標執行設置操作: {metric_name}")
    
    def record_histogram(self, metric_name: str, value: float, 
                        labels: Optional[Dict[str, str]] = None):
        """記錄直方圖數據"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = Metric(
                name=metric_name,
                value=[],
                metric_type=MetricType.HISTOGRAM,
                category=MonitoringCategory.APPLICATION
            )
        
        metric = self.metrics[metric_name]
        if metric.metric_type == MetricType.HISTOGRAM:
            if not isinstance(metric.value, list):
                metric.value = []
            metric.value.append(value)
            metric.labels.update(labels or {})
            metric.timestamp = datetime.now()
        else:
            self.logger.warning(f"嘗試對非直方圖指標執行記錄操作: {metric_name}")
    
    def get_metric(self, metric_name: str) -> Optional[Metric]:
        """獲取指標"""
        return self.metrics.get(metric_name)
    
    def get_all_metrics(self) -> Dict[str, Metric]:
        """獲取所有指標"""
        return self.metrics.copy()

class SystemMonitor:
    """系統監控器"""
    
    def __init__(self):
        self.collector = MetricCollector("system")
        self.logger = get_logger("system_monitor")
        self.monitoring = False
        self.interval = 5  # 秒
    
    async def start(self):
        """啟動系統監控"""
        self.monitoring = True
        asyncio.create_task(self._monitoring_loop())
        self.logger.info("系統監控已啟動")
    
    async def stop(self):
        """停止系統監控"""
        self.monitoring = False
        self.logger.info("系統監控已停止")
    
    async def _monitoring_loop(self):
        """監控循環"""
        while self.monitoring:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self.interval)
            except Exception as e:
                self.logger.error("系統監控錯誤", LogCategory.SYSTEM, exc_info=e)
                await asyncio.sleep(self.interval)
    
    async def _collect_system_metrics(self):
        """收集系統指標"""
        # CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        self.collector.set_gauge("system_cpu_usage", cpu_percent, 
                                {"unit": "percent"})
        
        # 內存使用情況
        memory = psutil.virtual_memory()
        self.collector.set_gauge("system_memory_usage", memory.percent, 
                                {"unit": "percent"})
        self.collector.set_gauge("system_memory_total", memory.total, 
                                {"unit": "bytes"})
        self.collector.set_gauge("system_memory_available", memory.available, 
                                {"unit": "bytes"})
        
        # 磁盤使用情況
        disk = psutil.disk_usage('/')
        self.collector.set_gauge("system_disk_usage", 
                                (disk.used / disk.total) * 100, 
                                {"unit": "percent", "mount": "/"})
        self.collector.set_gauge("system_disk_total", disk.total, 
                                {"unit": "bytes", "mount": "/"})
        
        # 網絡統計
        network = psutil.net_io_counters()
        self.collector.increment("system_network_bytes_sent", network.bytes_sent)
        self.collector.increment("system_network_bytes_recv", network.bytes_recv)
        
        # 進程數量
        process_count = len(psutil.pids())
        self.collector.set_gauge("system_process_count", process_count)
        
        # 系統負載（僅限 Unix）
        if hasattr(psutil, 'getloadavg'):
            load_avg = psutil.getloadavg()
            self.collector.set_gauge("system_load_1m", load_avg[0])
            self.collector.set_gauge("system_load_5m", load_avg[1])
            self.collector.set_gauge("system_load_15m", load_avg[2])

class ApplicationMonitor:
    """應用程序監控器"""
    
    def __init__(self):
        self.collector = MetricCollector("application")
        self.logger = get_logger("application_monitor")
        self.request_times = []
        self.max_request_times = 1000
    
    def record_request(self, endpoint: str, method: str, status_code: int, 
                      duration: float):
        """記錄請求"""
        # 請求計數
        self.collector.increment("http_requests_total", 1, 
                               {"method": method, "endpoint": endpoint, "status": str(status_code)})
        
        # 請求持續時間
        self.collector.record_histogram("http_request_duration_seconds", duration,
                                       {"method": method, "endpoint": endpoint})
        
        # 保存請求時間用於計算統計
        self.request_times.append(duration)
        if len(self.request_times) > self.max_request_times:
            self.request_times.pop(0)
        
        # 錯誤計數
        if status_code >= 400:
            self.collector.increment("http_errors_total", 1,
                                   {"method": method, "endpoint": endpoint, "status": str(status_code)})
    
    def get_request_stats(self) -> Dict[str, Any]:
        """獲取請求統計"""
        if not self.request_times:
            return {}
        
        return {
            "count": len(self.request_times),
            "avg": statistics.mean(self.request_times),
            "min": min(self.request_times),
            "max": max(self.request_times),
            "p50": statistics.median(self.request_times),
            "p95": self._percentile(self.request_times, 0.95),
            "p99": self._percentile(self.request_times, 0.99)
        }
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """計算百分位數"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]

class AlertManager:
    """警報管理器"""
    
    def __init__(self):
        self.logger = get_logger("alert_manager")
        self.alerts: Dict[str, Alert] = []
        self.alert_rules: List[Dict[str, Any]] = []
        self.notification_channels: List[Callable] = []
        self.running = False
        self.check_interval = 30  # 秒
    
    def add_alert_rule(self, name: str, condition: str, severity: AlertSeverity,
                      category: MonitoringCategory, message: str,
                      metadata: Optional[Dict[str, Any]] = None):
        """添加警報規則"""
        rule = {
            "name": name,
            "condition": condition,
            "severity": severity,
            "category": category,
            "message": message,
            "metadata": metadata or {},
            "enabled": True
        }
        self.alert_rules.append(rule)
        self.logger.info(f"添加警報規則: {name}")
    
    def add_notification_channel(self, channel: Callable):
        """添加通知渠道"""
        self.notification_channels.append(channel)
        self.logger.info("添加通知渠道")
    
    async def start(self):
        """啟動警報管理器"""
        self.running = True
        asyncio.create_task(self._alert_loop())
        self.logger.info("警報管理器已啟動")
    
    async def stop(self):
        """停止警報管理器"""
        self.running = False
        self.logger.info("警報管理器已停止")
    
    async def _alert_loop(self):
        """警報檢查循環"""
        while self.running:
            try:
                await self._check_alert_rules()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error("警報檢查錯誤", LogCategory.SYSTEM, exc_info=e)
                await asyncio.sleep(self.check_interval)
    
    async def _check_alert_rules(self):
        """檢查警報規則"""
        for rule in self.alert_rules:
            if not rule["enabled"]:
                continue
            
            try:
                # 評估警報條件
                triggered = await self._evaluate_condition(rule["condition"])
                
                # 檢查是否已存在相同的警報
                existing_alert = next((a for a in self.alerts 
                                     if a.name == rule["name"] and not a.resolved), None)
                
                if triggered and not existing_alert:
                    # 創建新警報
                    alert = Alert(
                        name=rule["name"],
                        severity=rule["severity"],
                        category=rule["category"],
                        message=rule["message"],
                        condition=rule["condition"],
                        metadata=rule["metadata"]
                    )
                    self.alerts.append(alert)
                    
                    # 發送通知
                    await self._send_notification(alert)
                    
                    self.logger.warning(f"觸發警報: {rule['name']}", 
                                       LogCategory.SYSTEM,
                                       extra={'alert_id': alert.id})
                
                elif not triggered and existing_alert:
                    # 解決警報
                    existing_alert.resolved = True
                    existing_alert.resolved_at = datetime.now()
                    
                    self.logger.info(f"警報已解決: {rule['name']}", 
                                    LogCategory.SYSTEM,
                                    extra={'alert_id': existing_alert.id})
                
            except Exception as e:
                self.logger.error(f"評估警報規則失敗: {rule['name']}", 
                                LogCategory.SYSTEM, exc_info=e)
    
    async def _evaluate_condition(self, condition: str) -> bool:
        """評估警報條件"""
        # 這裡應該實現實際的條件評估邏輯
        # 簡化示例：檢查 CPU 使用率
        if "cpu_usage" in condition:
            cpu_percent = psutil.cpu_percent(interval=1)
            return cpu_percent > 80
        
        # 檢查錯誤率
        if "error_rate" in condition:
            # 獲取錯誤統計
            error_stats = error_handler.get_error_stats()
            return error_stats['error_rate'] > 0.1
        
        return False
    
    async def _send_notification(self, alert: Alert):
        """發送警報通知"""
        notification_data = {
            "alert_id": alert.id,
            "name": alert.name,
            "severity": alert.severity.value,
            "category": alert.category.value,
            "message": alert.message,
            "triggered_at": alert.triggered_at.isoformat(),
            "metadata": alert.metadata
        }
        
        for channel in self.notification_channels:
            try:
                await channel(notification_data)
            except Exception as e:
                self.logger.error("發送通知失敗", LogCategory.SYSTEM, exc_info=e)
    
    def acknowledge_alert(self, alert_id: str, user: str):
        """確認警報"""
        alert = next((a for a in self.alerts if a.id == alert_id), None)
        if alert:
            alert.acknowledged = True
            alert.acknowledged_by = user
            self.logger.info(f"警報已確認: {alert_id} by {user}")
    
    def get_active_alerts(self) -> List[Alert]:
        """獲取活躍警報"""
        return [a for a in self.alerts if not a.resolved]

class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.logger = get_logger("performance_analyzer")
        self.performance_data: Dict[str, List[Dict[str, Any]]] = {}
        self.max_data_points = 1000
    
    def record_performance(self, operation: str, duration: float, 
                          metadata: Optional[Dict[str, Any]] = None):
        """記錄性能數據"""
        if operation not in self.performance_data:
            self.performance_data[operation] = []
        
        data_point = {
            "timestamp": datetime.now(),
            "duration": duration,
            "metadata": metadata or {}
        }
        
        self.performance_data[operation].append(data_point)
        
        # 限制數據點數量
        if len(self.performance_data[operation]) > self.max_data_points:
            self.performance_data[operation].pop(0)
    
    def analyze_performance(self, operation: str, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """分析性能"""
        if operation not in self.performance_data:
            return {}
        
        data = self.performance_data[operation]
        
        # 時間窗口過濾
        if time_window:
            cutoff = datetime.now() - time_window
            data = [d for d in data if d["timestamp"] >= cutoff]
        
        if not data:
            return {}
        
        durations = [d["duration"] for d in data]
        
        return {
            "operation": operation,
            "count": len(durations),
            "avg_duration": statistics.mean(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "p50_duration": statistics.median(durations),
            "p95_duration": self._percentile(durations, 0.95),
            "p99_duration": self._percentile(durations, 0.99),
            "time_window": str(time_window) if time_window else "all"
        }
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """計算百分位數"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def get_slow_operations(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """獲取慢操作"""
        slow_ops = []
        
        for operation, data in self.performance_data.items():
            if data:
                avg_duration = statistics.mean(d["duration"] for d in data)
                if avg_duration > threshold:
                    slow_ops.append({
                        "operation": operation,
                        "avg_duration": avg_duration,
                        "count": len(data)
                    })
        
        return sorted(slow_ops, key=lambda x: x["avg_duration"], reverse=True)

class EnterpriseMonitoringSystem:
    """企業級監控系統"""
    
    def __init__(self):
        self.logger = get_logger("enterprise_monitoring")
        self.system_monitor = SystemMonitor()
        self.application_monitor = ApplicationMonitor()
        self.alert_manager = AlertManager()
        self.performance_analyzer = PerformanceAnalyzer()
        self.running = False
        
        # 設置默認警報規則
        self._setup_default_alerts()
    
    def _setup_default_alerts(self):
        """設置默認警報規則"""
        # CPU 使用率警報
        self.alert_manager.add_alert_rule(
            "high_cpu_usage",
            "cpu_usage > 90",
            AlertSeverity.WARNING,
            MonitoringCategory.SYSTEM,
            "CPU 使用率超過 90%"
        )
        
        # 內存使用率警報
        self.alert_manager.add_alert_rule(
            "high_memory_usage",
            "memory_usage > 85",
            AlertSeverity.WARNING,
            MonitoringCategory.SYSTEM,
            "內存使用率超過 85%"
        )
        
        # 錯誤率警報
        self.alert_manager.add_alert_rule(
            "high_error_rate",
            "error_rate > 0.05",
            AlertSeverity.ERROR,
            MonitoringCategory.APPLICATION,
            "錯誤率超過 5%"
        )
    
    async def start(self):
        """啟動監控系統"""
        self.running = True
        
        # 啟動各個監控組件
        await self.system_monitor.start()
        await self.alert_manager.start()
        
        self.logger.info("企業級監控系統已啟動")
    
    async def stop(self):
        """停止監控系統"""
        self.running = False
        
        # 停止各個監控組件
        await self.system_monitor.stop()
        await self.alert_manager.stop()
        
        self.logger.info("企業級監控系統已停止")
    
    def record_request(self, endpoint: str, method: str, status_code: int, 
                      duration: float):
        """記錄請求"""
        self.application_monitor.record_request(endpoint, method, status_code, duration)
        self.performance_analyzer.record_performance(f"{method} {endpoint}", duration)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """獲取儀表板數據"""
        return {
            "system_metrics": self.system_monitor.collector.get_all_metrics(),
            "application_metrics": self.application_monitor.collector.get_all_metrics(),
            "request_stats": self.application_monitor.get_request_stats(),
            "active_alerts": [
                {
                    "id": a.id,
                    "name": a.name,
                    "severity": a.severity.value,
                    "message": a.message,
                    "triggered_at": a.triggered_at.isoformat()
                }
                for a in self.alert_manager.get_active_alerts()
            ],
            "slow_operations": self.performance_analyzer.get_slow_operations(),
            "performance_summary": {
                op: self.performance_analyzer.analyze_performance(op)
                for op in list(self.performance_analyzer.performance_data.keys())[:5]
            }
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """獲取健康狀態"""
        active_alerts = self.alert_manager.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
        
        status = "healthy"
        if critical_alerts:
            status = "critical"
        elif active_alerts:
            status = "warning"
        
        return {
            "status": status,
            "active_alerts": len(active_alerts),
            "critical_alerts": len(critical_alerts),
            "uptime": "N/A",  # 應該從系統啟動時間計算
            "last_check": datetime.now().isoformat()
        }

# 全局監控系統實例
enterprise_monitor = EnterpriseMonitoringSystem()

# 裝飾器用於自動性能監控
def monitor_performance(operation_name: Optional[str] = None):
    """裝飾器：自動監控函數性能"""
    def decorator(func):
        name = operation_name or f"{func.__module__}.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                enterprise_monitor.performance_analyzer.record_performance(name, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                enterprise_monitor.performance_analyzer.record_performance(name, duration, 
                                                                          {"error": str(e)})
                raise
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                enterprise_monitor.performance_analyzer.record_performance(name, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                enterprise_monitor.performance_analyzer.record_performance(name, duration, 
                                                                          {"error": str(e)})
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# 通知渠道示例
async def email_notification(alert_data: Dict[str, Any]):
    """郵件通知（示例）"""
    logger = get_logger("email_notification")
    logger.info(f"發送郵件警報: {alert_data['name']}", LogCategory.SYSTEM)

async def slack_notification(alert_data: Dict[str, Any]):
    """Slack 通知（示例）"""
    logger = get_logger("slack_notification")
    logger.info(f"發送 Slack 警報: {alert_data['name']}", LogCategory.SYSTEM)

# 註冊通知渠道
enterprise_monitor.alert_manager.add_notification_channel(email_notification)
enterprise_monitor.alert_manager.add_notification_channel(slack_notification)