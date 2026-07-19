#!/usr/bin/env python3
"""
企業級監控系統 - 全面的系統監控和告警
Enterprise monitoring system - comprehensive system monitoring and alerting
"""

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# =============================================================================
# ANGELA-MATRIX: [L4] [δ] [A] [L6+]
# Max-size bound for unbounded alerts collection
# =============================================================================
_MAX_ALERTS = 500


class EnterpriseMonitor:
    """Enterprise-grade system monitoring and alerting."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._running = False
        self._metrics: Dict[str, Any] = {}
        self._alerts: List[Dict[str, Any]] = []

    async def start(self) -> None:
        self._running = True
        logger.info("EnterpriseMonitor started")

    async def stop(self) -> None:
        self._running = False
        logger.info("EnterpriseMonitor stopped")

    def is_running(self) -> bool:
        return self._running

    def record_metric(self, name: str, value: Any, tags: Optional[Dict[str, str]] = None) -> None:
        self._metrics[name] = {"value": value, "tags": tags or {}, "timestamp": time.time()}

    def get_metric(self, name: str) -> Optional[Any]:
        entry = self._metrics.get(name)
        return entry["value"] if entry else None

    def get_all_metrics(self) -> Dict[str, Any]:
        return dict(self._metrics)

    def raise_alert(self, severity: str, message: str, source: str = "") -> None:
        alert = {
            "severity": severity,
            "message": message,
            "source": source,
            "timestamp": time.time(),
        }
        self._alerts.append(alert)
        if len(self._alerts) > _MAX_ALERTS:
            self._alerts = self._alerts[-_MAX_ALERTS:]
        logger.warning(f"ALERT [{severity}]: {message} (source={source})")

    def get_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        if severity:
            return [a for a in self._alerts if a["severity"] == severity]
        return list(self._alerts)

    def clear_alerts(self) -> None:
        self._alerts.clear()


enterprise_monitor = EnterpriseMonitor()


__all__ = ["EnterpriseMonitor", "enterprise_monitor"]
