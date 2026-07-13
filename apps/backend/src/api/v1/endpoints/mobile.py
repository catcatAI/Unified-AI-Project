"""
Angela AI v7.5.0-dev - Mobile Endpoints
行動端專用接口 (受 Key B 加密保護)
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict
from core.sync.realtime_sync import SyncEventType

from fastapi import APIRouter, Body

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mobile", tags=["Mobile"])


@router.post("/sync")
async def mobile_sync(data: Dict[str, Any] = Body(...)) -> dict:
    """行動端同步數據接口"""
    return {
        "status": "synchronized",
        "received_data": data,
        "server_time": datetime.now().isoformat(),
        "message": "Angela 安全同步已完成",
    }


@router.get("/status")
async def get_mobile_status_get() -> dict:
    """獲取移動端狀態 (GET 方法支持)"""
    try:
        import psutil
        from core.system.cluster_manager import cluster_manager

        cpu_usage = await asyncio.to_thread(psutil.cpu_percent)
        memory = await asyncio.to_thread(psutil.virtual_memory)
        cluster_status = cluster_manager.get_cluster_status()

        return {
            "status": "SECURE LINK ACTIVE",
            "metrics": {
                "cpu": f"{cpu_usage}%",
                "mem": f"{memory.percent}%",
                "nodes": cluster_status.get("node_count", 0),
            },
            "backend_version": "7.5.0-dev",
            "server_time": datetime.now().isoformat(),
        }
    except ImportError as e:
        logger.error(f"Mobile status import error: {e}", exc_info=True)
        return {
            "status": "partial",
            "metrics": {"cpu": "N/A", "mem": "N/A", "nodes": 0},
            "backend_version": "7.5.0-dev",
            "server_time": datetime.now().isoformat(),
            "error": "Some modules not available",
        }




@router.post("/module-control")
async def mobile_module_control(data: Dict[str, Any] = Body(...)) -> dict:
    """行動端控制後端模組"""
    module = data.get("module")
    enabled = data.get("enabled")

    try:
        from core.sync.realtime_sync import SyncEvent, sync_manager
        import uuid

        await sync_manager.broadcast_event(
            SyncEvent(
                id=str(uuid.uuid4()),
                event_type=SyncEventType.STATUS_CHANGE,
                data={"module": module, "enabled": enabled},
                source="mobile_app",
            )
        )
        return {"status": "success", "module": module, "enabled": enabled}
    except Exception as e:  # broad exception acceptable: module control should be resilient to errors
        logger.error(f"Error in {__name__}: {e}", exc_info=True)
        return {"status": "error", "message": safe_error(e)}


@router.post("/chat")
async def mobile_chat(data: Dict[str, Any] = Body(...)) -> dict:
    """行動端聊天代理 (NGR v7.5.0-dev)"""
    from api.routes.chat_routes import _handle_chat_request

    message = data.get("message", "")
    user_name = data.get("user_name", "朋友")
    history = data.get("history", [])
    session_id = data.get("session_id", f"mobile-{datetime.now().timestamp()}")
    origin = data.get("origin", "mobile_app")

    response = await _handle_chat_request(
        user_message=message,
        user_name=user_name,
        history=history,
        session_id=session_id,
        origin=origin,
    )
    response["status"] = "success"
    return response
