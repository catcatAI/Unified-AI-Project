"""
API路由模块
"""

import logging
from typing import Dict, Optional

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()

_hw_caps_cache: Optional[Dict[str, object]] = None


@router.get("/api/v1/")
def root() -> dict:
    """API 根路径信息。"""
    return {"message": "Unified AI Project API"}


@router.get("/api/v1/health")
def health_check() -> dict:
    """API v1 健康检查。"""
    return {"status": "healthy"}


@router.get("/api/v1/system/emergency")
def trigger_emergency_mode() -> dict:
    """強制進入緊急純文字模式，關閉所有重型組件。"""
    return {
        "status": "emergency_active",
        "action": "Visual/Audio components suspended",
        "mode": "text-only",
    }


def _get_hw_caps() -> Dict[str, object]:
    """Get cached hardware capability snapshot (probe once, reuse)."""
    global _hw_caps_cache
    if _hw_caps_cache is not None:
        return _hw_caps_cache
    try:
        from shared.utils.hardware_detector import SystemHardwareProbe

        probe = SystemHardwareProbe().detect()
        _hw_caps_cache = {
            "cpu_brand": probe.cpu_brand,
            "performance_tier": probe.performance_tier,
            "ai_capability_score": probe.ai_capability_score,
        }
    except Exception as err:
        logger.warning("Hardware capability probe failed: %s", err, exc_info=True)
        _hw_caps_cache = {
            "cpu_brand": "Unknown",
            "performance_tier": "Unknown",
            "ai_capability_score": 0.0,
        }
    return _hw_caps_cache


@router.get("/api/v1/system/cluster/status")
def get_cluster_status() -> dict:
    """系統叢集與硬體狀態總覽（供前端監控面板輪詢）。"""
    cpu_usage = 0.0
    mem_percent = 0.0
    mem_total = 0
    try:
        import psutil

        cpu_usage = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        mem_total = mem.total
    except Exception as err:
        logger.warning("Cluster/status metrics unavailable: %s", err, exc_info=True)

    hw = _get_hw_caps()

    try:
        from core.system.cluster_manager import cluster_manager

        cluster = cluster_manager.get_cluster_status()
    except Exception as err:
        logger.warning("Cluster manager unavailable: %s", err, exc_info=True)
        cluster = {"node_count": 0, "nodes": {}}

    nodes = [
        {
            "id": node_id,
            "type": info.get("type", "unknown"),
            "status": "online" if info.get("status") in ("idle", "busy") else "offline",
            "load": 0.0,
        }
        for node_id, info in cluster.get("nodes", {}).items()
    ]

    return {
        "hardware": {
            "cpu": {"usage": cpu_usage, "brand": hw["cpu_brand"]},
            "memory": {"usage_percent": mem_percent, "total": mem_total},
            "performance_tier": hw["performance_tier"],
            "ai_capability_score": hw["ai_capability_score"],
        },
        "cluster": {
            "active_nodes": len(nodes),
            "total_nodes": cluster.get("node_count", len(nodes)),
            "nodes": nodes,
        },
    }


# Import and include sub-routers
try:
    from api.routes.chat_routes import router as chat_router

    router.include_router(chat_router, prefix="/api/v1")
    logger.debug("Included chat_routes")
except ImportError as e:
    logger.warning(f"chat_routes not available: {e}")

try:
    from api.routes.desktop_routes import router as desktop_router

    router.include_router(desktop_router, prefix="/api/v1")
    logger.debug("Included desktop_routes")
except ImportError as e:
    logger.warning(f"desktop_routes not available: {e}")

try:
    from api.routes.ops_routes import router as ops_router

    router.include_router(ops_router, prefix="/api/v1")
    logger.debug("Included ops_routes")
except ImportError as e:
    logger.warning(f"ops_routes not available: {e}")

try:
    from api.v1.endpoints import include_endpoint_routers

    include_endpoint_routers(router, prefix="/api/v1")
    logger.debug("Included v1 endpoint routers")
except ImportError as e:
    logger.warning(f"v1 endpoint routers not available: {e}")

try:
    from api.routes.meta_routes import router as meta_router

    router.include_router(meta_router, prefix="/api/v1")
    logger.debug("Included meta_routes")
except ImportError as e:
    logger.warning(f"meta_routes not available: {e}")

try:
    from api.routes.multimodal_routes import router as multimodal_router

    router.include_router(multimodal_router, prefix="/api/v1")
    logger.debug("Included multimodal_routes")
except ImportError as e:
    logger.warning(f"multimodal_routes not available: {e}")

try:
    from api.routes.image_generation_routes import router as image_gen_router

    router.include_router(image_gen_router, prefix="/api/v1")
    logger.debug("Included image_generation_routes")
except ImportError as e:
    logger.warning(f"image_generation_routes not available: {e}")

try:
    from services.api.state_matrix_api import state_matrix_router

    router.include_router(state_matrix_router, prefix="/api/v1")
    logger.debug("Included state_matrix_routes")
except ImportError as e:
    logger.warning(f"state_matrix_routes not available: {e}")
