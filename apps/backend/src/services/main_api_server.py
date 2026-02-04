"""
Angela AI Backend API Server v6.0.4
FastAPI-based backend with chat, health, and basic endpoints

Usage:
    python -m uvicorn src.services.main_api_server:app --host 0.0.0.0 --port 8000
"""

import os
import sys
import uuid
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, APIRouter, Body
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Angela AI API",
    description="Backend API for Angela AI Desktop Companion",
    version="6.0.4",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

sessions: Dict[str, Dict] = {}


@router.get("/")
async def root():
    return {"message": "Angela AI API", "version": "6.0.4"}


@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@router.get("/api/v1/status")
async def api_status():
    return {"status": "running", "version": "6.0.4", "services": ["chat", "health"]}


@router.post("/session/start")
async def start_session(request: Dict[str, Any] = Body(default={})):
    session_id = f"sess-{uuid.uuid4().hex[:8]}"
    sessions[session_id] = {
        "created_at": datetime.now().isoformat(),
        "messages": [],
        "user_name": request.get("user_name", "User"),
    }
    return {"session_id": session_id, "message": "Welcome to Angela AI!"}


@router.post("/session/{session_id}/send")
async def send_message(session_id: str, request: Dict[str, Any] = Body(...)):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    user_message = request.get("text", request.get("message", ""))
    sessions[session_id]["messages"].append(
        {
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat(),
        }
    )

    responses = [
        "我明白了！让我帮你想想...",
        "这是个很有趣的想法！",
        "我可以帮你处理这个。",
        "让我分析一下...",
        "没问题，我这就帮你做！",
    ]
    ai_response = random.choice(responses)

    sessions[session_id]["messages"].append(
        {
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.now().isoformat(),
        }
    )

    return {"session_id": session_id, "response_text": ai_response}


@router.post("/angela/chat")
async def angela_chat(request: Dict[str, Any] = Body(...)):
    user_message = request.get("message", request.get("text", ""))
    session_id = request.get("session_id", f"angela-{uuid.uuid4().hex[:8]}")
    user_name = request.get("user_name", "朋友")

    message_lower = user_message.lower()

    greetings = ["你好", "嗨", "hello", "hi", "在吗"]
    if any(greet in message_lower for greet in greetings):
        responses = [
            f"嗨，{user_name}！今天过得怎么样？",
            f"你好呀，{user_name}！见到你真高兴~",
            f"欢迎回来，{user_name}！有什么我可以帮你的吗？",
        ]
    elif any(word in message_lower for word in ["开心", "高兴", "棒", "太好了"]):
        responses = ["太棒了！听起来是个好消息！", "真替你高兴！", "哇，太好了！"]
    elif any(word in message_lower for word in ["难过", "伤心", "不爽"]):
        responses = [
            "我理解你的感受...",
            "别难过，一切都会好起来的。",
            "需要我陪你聊聊吗？",
        ]
    elif "?" in user_message or "？" in user_message:
        responses = [
            "这是个很有意思的问题！让我想想...",
            "好问题！我来帮你分析一下。",
            "让我查查资料再回答你~",
        ]
    else:
        responses = [
            "我明白了！让我帮你想想...",
            "这是个很有趣的想法！",
            "我可以帮你处理这个。",
            "让我分析一下...",
            "没问题，我这就帮你做！",
        ]

    return {
        "session_id": session_id,
        "response_text": random.choice(responses),
        "angela_mood": "happy",
    }


app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
