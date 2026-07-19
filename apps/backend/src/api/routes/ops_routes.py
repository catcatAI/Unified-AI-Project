#!/usr/bin/env python3
"""
AI 運維系統 API 路由
提供 AI 運維功能的 REST API 接口

端點：
  GET  /ops/status       — 系統狀態總覽
  GET  /ops/health       — 健康檢查
  POST /ops/maintenance  — 觸發維護
  GET  /ops/metrics      — Prometheus 風格系統指標
"""

import logging
import time
from datetime import datetime

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ops", tags=["Operations"])


# Local psutil wrapper (avoids circular import with services.main_api_server)
def _get_cpu_percent() -> float:
    try:
        import psutil

        return psutil.cpu_percent(interval=0.1)
    except Exception as err:
        logger.debug("CPU metric unavailable: %s", err)
        return 0.0


def _get_memory_percent() -> float:
    try:
        import psutil

        return psutil.virtual_memory().percent
    except Exception as err:
        logger.debug("Memory metric unavailable: %s", err)
        return 0.0


def _get_disk_percent() -> float:
    try:
        import psutil

        return psutil.disk_usage("/").percent
    except Exception as err:
        logger.debug("Disk metric unavailable: %s", err)
        return 0.0


def _get_all_metrics() -> dict:
    return {
        "cpu_percent": _get_cpu_percent(),
        "memory_percent": _get_memory_percent(),
        "disk_percent": _get_disk_percent(),
    }


@router.get("/status")
async def get_ops_status() -> dict:
    """Get system status overview with real metrics."""
    return {
        "status": "ok",
        "service": "ops",
        "timestamp": datetime.now().isoformat(),
        "metrics": _get_all_metrics(),
    }


@router.get("/health")
async def health_check() -> dict:
    """Health check with component status."""
    cpu = _get_cpu_percent()
    mem = _get_memory_percent()
    disk = _get_disk_percent()
    stressed = cpu > 80 or mem > 90
    return {
        "status": "degraded" if stressed else "healthy",
        "service": "ops",
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": cpu,
        "memory_percent": mem,
        "disk_percent": disk,
    }


@router.post("/maintenance")
async def trigger_maintenance() -> dict:
    """Trigger maintenance mode (logging + placeholder)."""
    logger.info("Maintenance triggered via ops_routes at %s", datetime.now().isoformat())
    return {
        "status": "started",
        "task": "maintenance",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/metrics")
async def get_prometheus_metrics() -> dict:
    """Get Prometheus-style system metrics."""
    return {
        **_get_all_metrics(),
        "timestamp": datetime.now().isoformat(),
    }
