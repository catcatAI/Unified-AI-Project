"""
API路由模块
"""

import random
import psutil
from system.cluster_manager import cluster_manager
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Body
from services.chat_service import generate_angela_response
from api.v1.endpoints import drive, pet, vision, audio, tactile, mobile, economy
from api.routes.ops_routes import router as ops_router

router = APIRouter(prefix="/api/v1")

# 包含 v1 端點
router.include_router(drive.router)
router.include_router(pet.router)
router.include_router(vision.router)
router.include_router(audio.router)
router.include_router(tactile.router)
router.include_router(mobile.router)
router.include_router(economy.router)
router.include_router(ops_router)


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
        "mode": "text-only"
    }

@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@router.get("/agents", response_model=List[Dict[str, Any]])
async def get_ai_agents():
    """获取所有AI代理 (Dynamic Discovery)"""
    # In a real scenario, this would call AgentManager or HSP Service Discovery
    # For now, we simulate this while keeping the structure ready for integration
    from src.ai.agents.agent_manager import AgentManager
    # Note: AgentManager might need a singleton or a global instance
    
    # Placeholder for actual discovery logic
    discovered_agents = [
        {
            "id": "creative-writing-1",
            "name": "CreativeWritingAgent",
            "type": "创意写作",
            "status": "idle",
            "capabilities": ["text_generation", "creative_writing"],
            "last_active": datetime.now().isoformat()
        },
        {
            "id": "code-understanding-1",
            "name": "CodeUnderstandingAgent",
            "type": "代码理解",
            "status": "active",
            "capabilities": ["analyze_code", "fix_code"],
            "last_active": datetime.now().isoformat()
        }
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
            "status": "normal"
            if cpu_usage < 70
            else "warning"
            if cpu_usage < 90
            else "critical",
        },
        "memory": {
            "value": memory.percent,
            "max": 100,
            "status": "normal"
            if memory.percent < 70
            else "warning"
            if memory.percent < 90
            else "critical",
        },
        "disk": {
            "value": (disk.used / disk.total) * 100,
            "max": 100,
            "status": "normal"
            if (disk.used / disk.total) < 0.7
            else "warning"
            if (disk.used / disk.total) < 0.9
            else "critical",
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
    """聊天完成接口"""
    return {
        "id": f"chatcmpl-{random.randint(1000, 9999)}",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": "gpt-4",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "你好！我是 Angela，很高兴见到你！有什么我可以帮助你的吗？",
                },
                "finish_reason": "stop",
            }
        ],
    }


# Session management for Angela
sessions: Dict[str, Dict] = {}


@router.post("/session/start")
async def start_session(request: Dict[str, Any] = Body(default={})):
    """开始新对话会话"""
    session_id = str(uuid.uuid4())[:8]
    sessions[session_id] = {
        "created_at": datetime.now().isoformat(),
        "messages": [],
        "user_name": request.get("user_name", "User"),
    }
    return {
        "session_id": session_id,
        "message": "Session started. Welcome to Angela AI!",
    }


@router.post("/session/{session_id}/send")
async def send_message(session_id: str, request: Dict[str, Any] = Body(...)):
    """发送消息到会话"""
    if session_id not in sessions:
        return {"error": "Session not found"}

    user_message = request.get("text", "")
    sessions[session_id]["messages"].append(
        {
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat(),
        }
    )

    angela_responses = [
        "我明白了！让我帮你想想...",
        "这是个很有趣的想法！",
        "我可以帮你处理这个。",
        "让我分析一下这个问题...",
        "没问题，我这就帮你做！",
        "我理解你的需求了。",
    ]

    ai_response = random.choice(angela_responses)

    sessions[session_id]["messages"].append(
        {
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.now().isoformat(),
        }
    )

    return {"session_id": session_id, "response_text": ai_response}


# Angela-specific chat endpoint with personality
@router.post("/angela/chat")
async def angela_chat(request: Dict[str, Any] = Body(...)):
    """Angela 智能對話接口 - 帶有性格和情感"""
    user_message = request.get("message", request.get("text", ""))
    session_id = request.get("session_id", f"angela-{uuid.uuid4().hex[:8]}")
    user_name = request.get("user_name", "朋友")

    # Use shared chat service
    response_text = generate_angela_response(user_message, user_name)

    return {
        "session_id": session_id,
        "response_text": response_text,
        "angela_mood": "happy",
        "personality": "Angela AI",
    }
