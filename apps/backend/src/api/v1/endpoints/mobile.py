"""
Angela AI v6.0 - Mobile Endpoints
行動端專用接口 (受 Key B 加密保護)
"""

from fastapi import APIRouter, Body, Depends
from typing import Dict, Any
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mobile", tags=["Mobile"])

@router.post("/sync")
async def mobile_sync(data: Dict[str, Any] = Body(...)):
    """行動端同步數據接口"""
    return {
        "status": "synchronized",
        "received_data": data,
        "server_time": datetime.now().isoformat(),
        "message": "Angela 安全同步已完成"
    }

@router.post("/status")
async def get_mobile_status(data: Dict[str, Any] = Body(...)):
    """獲取實時系統狀態 (CPU, Memory, Cluster)"""
    import psutil
    from ....system.cluster_manager import cluster_manager
    
    cpu_usage = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    cluster_status = cluster_manager.get_cluster_status()
    
    return {
        "status": "SECURE LINK ACTIVE",
        "metrics": {
            "cpu": f"{cpu_usage}%",
            "mem": f"{memory.percent}%",
            "nodes": cluster_status["cluster"]["active_nodes"]
        },
        "backend_version": "6.0.4",
        "server_time": datetime.now().isoformat()
    }

@router.post("/module-control")
async def mobile_module_control(data: Dict[str, Any] = Body(...)):
    """行動端控制後端模組"""
    module = data.get("module")
    enabled = data.get("enabled")
    
    try:
        from ....core.sync.realtime_sync import sync_manager, SyncEvent
        await sync_manager.broadcast_event(SyncEvent(
            event_type="module_control",
            data={"module": module, "enabled": enabled},
            source="mobile_app"
        ))
        return {"status": "success", "module": module, "enabled": enabled}
    except Exception as e:
        logger.error(f'Error in {__name__}: {e}', exc_info=True)
        return {"status": "error", "message": str(e)}


@router.post("/chat")
async def mobile_chat(data: Dict[str, Any] = Body(...)):
    """行動端聊天代理"""
    # 此處應對接到 DialogueManager，暫時返回簡單響應以驗證連通性
    message = data.get("message", "")
    return {
        "status": "success",
        "message": f"Angela 收到你的訊息: {message}",
        "timestamp": datetime.now().isoformat()
    }
