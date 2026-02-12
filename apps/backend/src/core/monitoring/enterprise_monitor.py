#!/usr/bin/env python3
"""
企業級監控系統 - 全面的系統監控和告警
Enterprise monitoring system - comprehensive system monitoring and alerting
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """告警級別 / Alert levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Alert:
    """告警 / Alert"""
    def __init__(
        self,
        level: AlertLevel,
        message: str,
        source: str = "system"
    ):
        self.id = f"alert_{datetime.now().timestamp()}"
        self.level = level
        self.message = message
        self.source = source
        self.timestamp = datetime.now()
        self.acknowledged = False
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典 / Convert to dictionary"""
        return {
            "id": self.id,
            "level": self.level.value if hasattr(self.level, 'value') else str(self.level),
            "message": self.message,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged
        }


class MetricsCollector:
    """指標收集器 / Metrics collector"""
    def __init__(self):
        self._metrics: Dict[str, List] = {}
    
    def record(self, metric_name: str, value: float):
        """記錄指標 / Record metric"""
        if metric_name not in self._metrics:
            self._metrics[metric_name] = []
        self._metrics[metric_name].append({
            "value": value,
            "timestamp": datetime.now()
        })
    
    def get(self, metric_name: str) -> List[Dict[str, Any]]:
        """獲取指標 / Get metric"""
        return self._metrics.get(metric_name, [])
    
    def get_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """獲取所有指標 / Get all metrics"""
        return self._metrics.copy()


class EnterpriseMonitor:
    """企業級監控器 / Enterprise monitor"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._running = False
        self._alerts: List[Alert] = []
        self._metrics = MetricsCollector()
        self._alert_callbacks: List[Callable] = []
    
    async def start(self) -> bool:
        """啟動監控 / Start monitoring"""
        self._running = True
        logger.info("企業級監控系統已啟動")
        return True
    
    async def stop(self) -> bool:
        """停止監控 / Stop monitoring"""
        self._running = False
        self._alerts.clear()
        logger.info("企業級監控系統已停止")
        return True
    
    def is_running(self) -> bool:
        """檢查是否運行中 / Check if running"""
        return self._running
    
    def record_metric(self, name: str, value: float):
        """記錄指標 / Record metric"""
        self._metrics.record(name, value)
    
    def get_metrics(self, name: str = None) -> Dict[str, Any]:
        """獲取指標 / Get metrics"""
        if name:
            return {"name": name, "data": self._metrics.get(name)}
        return self._metrics.get_all()
    
    def raise_alert(
        self,
        level: AlertLevel,
        message: str,
        source: str = "system"
    ) -> Alert:
        """發起告警 / Raise alert"""
        alert = Alert(level, message, source)
        self._alerts.append(alert)
        
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                pass

        
        logger.warning(f"告警 [{level.value}]: {message}")
        return alert
    
    def get_alerts(self, acknowledged: bool = None) -> List[Alert]:
        """獲取告警列表 / Get alerts"""
        if acknowledged is None:
            return self._alerts
        return [a for a in self._alerts if a.acknowledged == acknowledged]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """確認告警 / Acknowledge alert"""
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False
    
    def on_alert(self, callback: Callable[[Alert], None]):
        """註冊告警回調 / Register alert callback"""
        self._alert_callbacks.append(callback)
    
    def get_status(self) -> Dict[str, Any]:
        """獲取狀態 / Get status"""
        return {
            "running": self._running,
            "alert_count": len(self._alerts),
            "unacknowledged_count": len([a for a in self._alerts if not a.acknowledged]),
            "metrics_count": len(self._metrics.get_all()),
            "timestamp": datetime.now().isoformat()
        }


# 全局監控器實例
enterprise_monitor = EnterpriseMonitor()
