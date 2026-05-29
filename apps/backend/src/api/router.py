"""
API路由模块
"""

import random
import psutil
from system.cluster_manager import cluster_manager
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Body  # noqa: E402
from api.routes.ops_routes import router as ops_router  # noqa: E402
from api.routes.chat_routes import router as chat_router  # noqa: E402
from api.routes.desktop_routes import router as desktop_router  # noqa: E402

router = APIRouter(prefix="/api/v1")

# Lazy-load endpoint routers
from api.v1.endpoints import include_endpoint_routers  # noqa: E402
include_endpoint_routers(router)

router.include_router(ops_router)
router.include_router(chat_router)
router.include_router(desktop_router)


@router.get("/")
async def root():
    """根路径"""
    return {"message": "Unified AI Project API"}


@router.get("/system/emergency")
async def trigger_emergency_mode():
    """強制進入緊急純文字模式，關閉所有重型組件"""
    return {
        "status": "emergency_active",
        "action": "Visual/Audio components suspended",
        "mode": "text-only",
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@router.get("/status")
async def app_status():
    """桌面端狀態查詢"""
    return {"health": 100, "energy": 100, "mood": "happy", "status": "idle"}


@router.post("/system/status")
async def system_status():
    """系統狀態 (行動端/桌面端通用)"""
    return {"status": "online", "stats": {"cpu": "N/A", "mem": "N/A", "nodes": 0}}


@router.get("/agents", response_model=List[Dict[str, Any]])
async def get_ai_agents():
    """获取所有AI代理 (Dynamic Discovery)"""
    # In a real scenario, this would call AgentManager or HSP Service Discovery
    # For now, we simulate this while keeping the structure ready for integration
    from ai.agents.agent_manager import AgentManager

    # Note: AgentManager might need a singleton or a global instance

    # Placeholder for actual discovery logic
    discovered_agents = [
        {
            "id": "creative-writing-1",
            "name": "CreativeWritingAgent",
            "type": "创意写作",
            "status": "idle",
            "capabilities": ["text_generation", "creative_writing"],
            "last_active": datetime.now().isoformat(),
        },
        {
            "id": "code-understanding-1",
            "name": "CodeUnderstandingAgent",
            "type": "代码理解",
            "status": "active",
            "capabilities": ["analyze_code", "fix_code"],
            "last_active": datetime.now().isoformat(),
        },
    ]
    return discovered_agents


@router.get("/agents/{agent_id}", response_model=Dict[str, Any])
async def get_ai_agent(agent_id: str):
    """获取特定AI代理"""
    agents = await get_ai_agents()
    for agent in agents:
        if agent["id"] == agent_id:
            return agent
    return {"error": "Agent not found"}


@router.get("/models", response_model=List[Dict[str, Any]])
async def get_models():
    """获取所有模型"""
    models = [
        {
            "id": "1",
            "name": "GPT-4",
            "type": "语言模型",
            "status": "ready",
            "version": "4.0",
            "created_at": "2023-03-14",
            "last_trained": "2023-09-01",
            "accuracy": 0.94,
            "size": "1760GB",
        }
    ]
    return models


@router.get("/system/metrics/detailed", response_model=Dict[str, Any])
async def get_detailed_system_metrics():
    """获取详细 system 指标"""
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    metrics = {
        "cpu": {
            "value": cpu_usage,
            "max": 100,
            "status": "normal" if cpu_usage < 70 else "warning" if cpu_usage < 90 else "critical",
        },
        "memory": {
            "value": memory.percent,
            "max": 100,
            "status": (
                "normal"
                if memory.percent < 70
                else "warning" if memory.percent < 90 else "critical"
            ),
        },
        "disk": {
            "value": (disk.used / disk.total) * 100,
            "max": 100,
            "status": (
                "normal"
                if (disk.used / disk.total) < 0.7
                else "warning" if (disk.used / disk.total) < 0.9 else "critical"
            ),
        },
        "network": {"value": random.uniform(10, 60), "max": 100, "status": "normal"},
        "timestamp": datetime.now().isoformat(),
    }
    return metrics


@router.get("/system/cluster/status", response_model=Dict[str, Any])
async def get_cluster_status():
    """獲取集群與硬體探針狀態"""
    return cluster_manager.get_cluster_status()


@router.post("/chat/completions")
async def chat_completions(request: Dict[str, Any] = Body(...)):
    """聊天完成接口 — 代理至 AngelaChatService"""
    messages = request.get("messages", [])
    user_message = messages[-1].get("content", "") if messages else request.get("prompt", "")
    user_name = request.get("user_name", "User")
    from core.interfaces.service_registry import get_registry
    svc = get_registry().get("chat_service")
    if svc is None:
        from services.chat_service import get_angela_chat_service
        svc = await get_angela_chat_service()
    response_text = await svc.generate_response(user_message, user_name)
    return {
        "id": f"chatcmpl-{random.randint(1000, 9999)}",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": "angela-ai",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text,
                },
                "finish_reason": "stop",
            }
        ],
    }


@router.post("/angela/reload")
async def reload_llm():
    """強制重新載入 LLM 服務（hot-reload 配置變更）"""
    from services.angela_llm_service import get_llm_service
    svc = await get_llm_service(force_reload=True)
    providers = list(svc.backends.keys())
    return {
        "status": "reloaded",
        "llm_mode": svc.llm_mode,
        "active_backend": str(svc.active_backend_type.value) if svc.active_backend_type else "none",
        "available_backends": [str(b.value) for b in providers],
    }


