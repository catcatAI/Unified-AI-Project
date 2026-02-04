"""
API路由模块
"""

import random
import psutil
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Body
from src.api.v1.endpoints import drive, pet
from src.api.routes.ops_routes import router as ops_router

router = APIRouter()

# 包含 v1 端點
router.include_router(drive.router)
router.include_router(pet.router)
router.include_router(ops_router)


@router.get("/")
async def root():
    """根路径"""
    return {"message": "Unified AI Project API"}


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@router.get("/agents", response_model=List[Dict[str, Any]])
async def get_ai_agents():
    """获取所有AI代理"""
    agents = [
        {
            "id": "1",
            "name": "CreativeWritingAgent",
            "type": "创意写作",
            "status": "idle",
            "capabilities": ["文本生成", "创意写作", "内容创作"],
            "current_task": None,
            "last_active": datetime.now().isoformat(),
            "performance": {
                "tasks_completed": 1247,
                "success_rate": 0.95,
                "avg_response_time": 1.2,
            },
        },
        {
            "id": "2",
            "name": "ImageGenerationAgent",
            "type": "图像生成",
            "status": "busy",
            "capabilities": ["图像生成", "风格转换", "图像编辑"],
            "current_task": "生成风景图像",
            "last_active": datetime.now().isoformat(),
            "performance": {
                "tasks_completed": 856,
                "success_rate": 0.92,
                "avg_response_time": 3.5,
            },
        },
    ]
    return agents


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
    """获取详细系统指标"""
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
    """Angela 智能对话接口 - 带有性格和情感"""
    user_message = request.get("message", request.get("text", ""))
    session_id = request.get("session_id", f"angela-{uuid.uuid4().hex[:8]}")
    user_name = request.get("user_name", "朋友")

    angela_responses = {
        "greeting": [
            f"嗨，{user_name}！今天过得怎么样？",
            f"你好呀，{user_name}！见到你真高兴~",
            f"欢迎回来，{user_name}！有什么我可以帮你的吗？",
        ],
        "happy": ["太棒了！听起来是个好消息！", "真替你高兴！", "哇，太好了！"],
        "sad": [
            "我理解你的感受...",
            "别难过，一切都会好起来的。",
            "需要我陪你聊聊吗？",
        ],
        "question": [
            "这是个很有意思的问题！让我想想...",
            "好问题！我来帮你分析一下。",
            "让我查查资料再回答你~",
        ],
        "default": [
            "我明白了！让我帮你想想...",
            "这是个很有趣的想法！",
            "我可以帮你处理这个。",
            "让我分析一下这个问题...",
            "没问题，我这就帮你做！",
            "我理解你的需求了。",
        ],
    }

    message_lower = user_message.lower()
    response_text = ""

    greetings = ["你好", "嗨", "hello", "hi", "早安", "晚安", "在吗"]
    if any(greet in message_lower for greet in greetings):
        response_text = random.choice(angela_responses["greeting"])
    elif any(
        word in message_lower
        for word in ["开心", "高兴", "棒", "太好了", "good", "great", "万岁"]
    ):
        response_text = random.choice(angela_responses["happy"])
    elif any(
        word in message_lower
        for word in ["难过", "伤心", "不爽", "sad", "坏", "糟糕", "郁闷"]
    ):
        response_text = random.choice(angela_responses["sad"])
    elif (
        "?" in user_message
        or "？" in user_message
        or any(
            word in message_lower
            for word in [
                "什么",
                "为什么",
                "如何",
                "怎么",
                "who",
                "what",
                "why",
                "how",
                "能否",
                "可以",
            ]
        )
    ):
        response_text = random.choice(angela_responses["question"])
    else:
        response_text = random.choice(angela_responses["default"])

    return {
        "session_id": session_id,
        "response_text": response_text,
        "angela_mood": "happy",
        "personality": "Angela AI",
    }
