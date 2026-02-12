"""
Angela AI Backend API Server v6.0.4
FastAPI-based backend with chat, health, and basic endpoints

Usage:
    python -m uvicorn src.services.main_api_server:app --host 127.0.0.1 --port 8000
"""

# =============================================================================
# ANGELA-MATRIX: L6[执行层] 全层级 [A] L2+
# =============================================================================
#
# 职责: 提供 Angela AI 的后端 API 服务，处理所有层级的数据传输
# 维度: 涉及所有维度 (αβγδ)，管理完整的状态矩阵
# 安全: 使用 Key A (后端控制) 进行安全通信和权限管理
# 成熟度: L2+ 等级可以理解 API 的功能和用途
#
# 主要端点:
# - GET /health - 健康检查
# - POST /dialogue - 对话接口
# - POST /angela/chat - Angela 聊天接口 (集成 LLM)
# - WebSocket /ws - 实时双向通信
# - POST /vision - 视觉分析
# - POST /audio - 音频处理
# - POST /tactile - 触觉输入处理
# - GET /pet - 宠物信息
# - GET /economy - 经济系统
#
# 集成服务:
# - VisionService: 视觉处理
# - AudioService: 音频处理
# - TactileService: 触觉处理
# - ChatService: 对话生成
# - AngelaLLMService: LLM 服务 (Ollama/GPT/Gemini)
# - DigitalLifeIntegrator: 数字生命集成
# - EconomyManager: 经济系统
# - BrainBridgeService: 大脑桥接服务
#
# =============================================================================

import os
import sys
import uuid
import random
import asyncio
import httpx
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
logger = logging.getLogger(__name__)

# 確保 src 目錄在 Python 路徑中
# 必須添加 src 目錄本身，這樣 Python 才能找到 src.core 等模塊
_backend_dir = Path(__file__).parent.parent.parent  # /apps/backend
_src_path = str(_backend_dir / "src")  # /apps/backend/src
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from fastapi import FastAPI, HTTPException, APIRouter, Body, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from core.autonomous.desktop_interaction import DesktopInteraction, FileCategory
from core.autonomous.action_executor import ActionExecutor, Action, ActionCategory, ActionPriority
from services.vision_service import VisionService
from services.audio_service import AudioService
from services.tactile_service import TactileService
from services.chat_service import generate_angela_response
from services.angela_llm_service import get_llm_service, angela_llm_response
from system.security_monitor import ABCKeyManager

# Initialize _llm_service as None to prevent NameError before startup
_llm_service = None

from api.router import router as api_v1_router
from api.v1.endpoints import pet, economy
from core.autonomous.digital_life_integrator import DigitalLifeIntegrator
from economy.economy_manager import EconomyManager
from core.cognitive_economy_bridge import initialize_cognitive_bridge
from services.brain_bridge_service import BrainBridgeService

app = FastAPI(
    title="Angela AI API",
    description="Backend API for Angela AI Desktop Companion",
    version="6.0.4",
)

# Initialize Core Services
desktop_interaction = DesktopInteraction()
action_executor = ActionExecutor()
vision_service = VisionService()
audio_service = AudioService()
tactile_service = TactileService()
abc_key_manager = ABCKeyManager()
digital_life = DigitalLifeIntegrator()
economy_manager = EconomyManager({})
brain_bridge = BrainBridgeService(digital_life)

# Link components
pet.set_biological_integrator(digital_life.biological_integrator)
economy.set_economy_manager(economy_manager)

@app.on_event("startup")
async def startup_event():
    await desktop_interaction.initialize()
    await action_executor.initialize()
    await digital_life.initialize()

    # Initialize Logic Bridge
    if digital_life.autonomous_lifecycle:
        initialize_cognitive_bridge(digital_life.autonomous_lifecycle.cdm, economy_manager)

    await brain_bridge.start()
    # vision_service doesn't have an async initialize yet

    # Initialize LLM Service (Angela's brain)
    global _llm_service
    try:
        _llm_service = await get_llm_service()
        print(f"[STARTUP] LLM Service initialized: available={_llm_service.is_available}")
    except Exception as e:
        print(f"[STARTUP] LLM Service initialization failed: {e}")

    # Start background task to broadcast state updates
    asyncio.create_task(broadcast_state_updates())


@app.on_event("shutdown")
async def shutdown_event():
    await desktop_interaction.shutdown()
    await action_executor.shutdown()
    await brain_bridge.stop()
    await digital_life.shutdown()

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


@router.get("/api/v1/security/sync-key-c")
async def sync_key_c():
    """Get Key C for desktop app synchronization"""
    key_c = abc_key_manager.get_key("KeyC")
    if not key_c:
        raise HTTPException(status_code=500, detail="Security keys not initialized")
    return {"key_c": key_c}


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
    """
    Angela 智能對話接口
    ==================
    這是 Angela 與用戶對話的核心接口。

    處理流程：
    1. 接收用戶消息
    2. 通過 Angela LLM 服務生成回應
    3. 返回經過 Angela 個性化處理的回應

    用戶不是直接與 LLM 對話，而是透過 Angela。
    """
    user_message = request.get("message", request.get("text", ""))
    session_id = request.get("session_id", f"angela-{uuid.uuid4().hex[:8]}")
    user_name = request.get("user_name", "朋友")
    history = request.get("history", [])

    # 調用 LLM 服務生成回應
    try:
        service = await get_llm_service()
        response_text = await angela_llm_response(
            user_message=user_message,
            history=history,
            user_name=user_name
        )
        source = "llm" if service and service.is_available else "fallback"
    except Exception as e:
       logger.error(f'Error in {__name__}: {e}', exc_info=True)
       
# 如果 LLM 服務不可用，使用備份回應
        print(f"[WARNING] LLM service error: {e}")
        response_text = generate_angela_response(user_message, user_name)
        source = "fallback"

    # 統一響應格式
    return {
        "session_id": session_id,
        "response": response_text,
        "response_text": response_text,  # 保留此字段以向後兼容
        "emotion": "happy",
        "angela_mood": "happy",  # 保留此字段以向後兼容
        "source": source,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/dialogue")
async def dialogue(request: Dict[str, Any] = Body(...)):
    """
    对話接口 - 與 /angela/chat 相同，為前端兼容性提供
    """
    user_message = request.get("message", request.get("text", ""))
    session_id = request.get("session_id", f"angela-{uuid.uuid4().hex[:8]}")
    user_name = request.get("user_name", "朋友")
    history = request.get("history", [])

    # 调用 LLM 服务生成回应
    try:
        service = await get_llm_service()
        response_text = await angela_llm_response(
            user_message=user_message,
            history=history,
            user_name=user_name
        )
        source = "llm" if service and service.is_available else "fallback"
    except Exception as e:
        print(f"[WARNING] LLM service error: {e}")
        response_text = generate_angela_response(user_message, user_name)
        source = "fallback"

    # 統一響應格式（與 /angela/chat 相同）
    return {
        "session_id": session_id,
        "response": response_text,
        "response_text": response_text,  # 保留此字段以向後兼容
        "emotion": "happy",
        "angela_mood": "happy",  # 保留此字段以向後兼容
        "source": source,
        "timestamp": datetime.now().isoformat()
    }


# --- Desktop Interaction API ---

@router.get("/api/v1/desktop/state")
async def get_desktop_state():
    """Get current desktop state"""
    state = desktop_interaction.get_desktop_state()
    return {
        "total_files": state.total_files,
        "total_size": state.total_size,
        "clutter_level": state.clutter_level,
        "files_by_category": {cat.name: count for cat, count in state.files_by_category.items()},
        "last_organized": state.last_organized.isoformat() if state.last_organized else None
    }

@router.post("/api/v1/desktop/organize")
async def organize_desktop(background_tasks: BackgroundTasks):
    """Trigger desktop organization"""
    # Background task for long running operation
    operations = await desktop_interaction.organize_desktop()
    return {"status": "success", "operations_count": len(operations)}

@router.post("/api/v1/desktop/cleanup")
async def cleanup_desktop(days_old: int = 30):
    """Trigger desktop cleanup"""
    operations = await desktop_interaction.cleanup_desktop(days_old=days_old)
    return {"status": "success", "operations_count": len(operations)}


# --- Action Executor API ---

@router.get("/api/v1/actions/status")
async def get_actions_status():
    """Get action executor status"""
    return action_executor.queue.get_queue_status()

@router.post("/api/v1/actions/execute")
async def execute_action(action_data: Dict[str, Any]):
    """Execute a custom action"""
    # This is a simplified implementation. In a real scenario,
    # we would map the request to specific registered functions.
    
    # Example action creation
    try:
        category = ActionCategory[action_data.get("category", "SYSTEM")]
        priority = ActionPriority[action_data.get("priority", "NORMAL")]
        
        # For now, we only support a "dummy" function via API for safety
        async def dummy_func(**kwargs):
            return {"result": "Action executed successfully", "params": kwargs}
            
        action = Action.create(
            name=action_data.get("name", "api_action"),
            category=category,
            priority=priority,
            function=dummy_func,
            parameters=action_data.get("parameters", {})
        )
        
        result = await action_executor.submit_and_execute(action)
        return {
            "success": result.success,
            "action_id": result.action_id,
            "output": result.output,
            "error": result.error
        }
    except Exception as e:
        logger.error(f'Error in {__name__}: {e}', exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))



# --- Vision API ---

@router.post("/api/v1/vision/sampling")
async def get_vision_sampling(params: Dict[str, Any] = Body(...)):
    """
    Get visual sampling analysis with particle cloud
    """
    center = params.get("center", [0.5, 0.5])
    scale = params.get("scale", 1.0)
    deformation = params.get("deformation", 0.0)
    distribution = params.get("distribution", "GAUSSIAN")
    
    try:
        result = await vision_service.get_sampling_analysis(
            center=(center[0], center[1]),
            scale=scale,
            deformation=deformation,
            distribution=distribution
        )
        return result
    except Exception as e:
        logger.error(f'Error in {__name__}: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/api/v1/vision/perceive")
async def vision_perceive(image_data: bytes = Body(...)):
    """
    Simulate Discover-Focus-Memory cycle
    """
    try:
        result = await vision_service.perceive_and_focus(image_data)
        return result
    except Exception as e:
        logger.error(f'Error in {__name__}: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/api/v1/audio/scan")
async def audio_scan(audio_data: bytes = Body(...), duration: float = 1.0):
    """
    Simulate cocktail party effect: listen, identify, and focus
    """
    try:
        result = await audio_service.scan_and_identify(audio_data, duration)
        return result
    except Exception as e:
        logger.error(f'Error in {__name__}: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/api/v1/audio/register_user")
async def audio_register_user(audio_data: bytes = Body(...)):
    """
    Register user voiceprint
    """
    try:
        result = await audio_service.register_user_voice(audio_data)
        return result
    except Exception as e:
        logger.error(f'Error in {__name__}: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/api/v1/tactile/model")
async def tactile_model(visual_data: Dict[str, Any] = Body(...)):
    """
    Model tactile properties from visual data (texture, light, etc.)
    """
    try:
        result = await tactile_service.model_object_tactile(visual_data)
        return result
    except Exception as e:
        logger.error(f'Error in {__name__}: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/api/v1/tactile/touch")
async def tactile_touch(request: Dict[str, Any] = Body(...)):
    """
    Simulate touch interaction with a specific object
    """
    try:
        object_id = request.get("object_id")
        contact_point = request.get("contact_point", {})
        result = await tactile_service.simulate_touch(object_id, contact_point)
        return result
    except Exception as e:
        logger.error(f'Error in {__name__}: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/api/v1/brain/metrics")
async def get_brain_metrics():
    """Get theoretical AGI metrics (L_s, A_c, etc.)"""
    return brain_bridge.get_current_status()

@router.post("/api/v1/brain/dividend")
async def get_brain_dividend():
    """Get CDM Economic Model data"""
    summary = digital_life.get_formula_metrics()
    if summary and "formula_status" in summary:
        return summary["formula_status"].get("cdm", {})
    return {"message": "Dividend data not available"}


# --- WebSocket Endpoint for Desktop App ---

import asyncio
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except (ConnectionError, RuntimeError, Exception) as e:
                # 連接失敗，從活動連接中移除
                logger.debug(f"廣播消息失敗（可忽略）: {e}")
                try:
                    self.active_connections.remove(connection)
                except ValueError:
                    pass

manager = ConnectionManager()

# Background task to broadcast state updates
async def broadcast_state_updates():
    """Periodically broadcast state updates to all connected clients"""
    while True:
        try:
            # Get current state from brain bridge
            state_data = {
                "alpha": {
                    "energy": brain_bridge.get_energy_level() if hasattr(brain_bridge, 'get_energy_level') else 0.5,
                    "comfort": 0.5,
                    "arousal": 0.5
                },
                "beta": {
                    "curiosity": 0.5,
                    "focus": 0.5,
                    "learning": 0.5
                },
                "gamma": {
                    "happiness": 0.5,
                    "calm": 0.5
                },
                "delta": {
                    "attention": 0.5,
                    "engagement": 0.5
                },
                "timestamp": datetime.now().isoformat()
            }
            
            await manager.broadcast({
                "type": "state_update",
                "data": state_data,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error broadcasting state update: {e}")
        
        # Broadcast every 5 seconds
        await asyncio.sleep(5)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication with desktop app
    """
    await manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_json()
            
            # Handle different message types
            if data.get("type") == "heartbeat":
                await websocket.send_json({
                    "type": "heartbeat_ack",
                    "timestamp": datetime.now().isoformat()
                })
            elif data.get("type") == "state_update":
                # Broadcast state updates to all connected clients
                await manager.broadcast({
                    "type": "state_update",
                    "data": data.get("data", {}),
                    "timestamp": datetime.now().isoformat()
                })
            elif data.get("type") == "chat_message":
                # Handle chat messages from desktop app - use shared service
                user_message = data.get("data", {}).get("content", "")
                message_id = data.get("data", {}).get("message_id", "")
                user_name = data.get("data", {}).get("user_name", "朋友")
                
                # Use shared chat service
                response_text = generate_angela_response(user_message, user_name)
                
                # Send response back to the client
                await websocket.send_json({
                    "type": "chat_response",
                    "data": {
                        "message_id": message_id,
                        "content": response_text,
                        "sender": "angela"
                    },
                    "timestamp": datetime.now().isoformat()
                })
            else:
                # Echo back other messages for now
                await websocket.send_json({
                    "type": "echo",
                    "original": data,
                    "timestamp": datetime.now().isoformat()
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


app.include_router(api_v1_router)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
