"""
Angela AI Backend API Server v6.0.4
FastAPI-based backend with chat, health, and basic endpoints

Usage:
    python -m uvicorn src.services.main_api_server:app --host 127.0.0.1 --port 8000
"""

import os
import sys
import uuid
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, APIRouter, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from ..core.autonomous.desktop_interaction import DesktopInteraction, FileCategory
from ..core.autonomous.action_executor import ActionExecutor, Action, ActionCategory, ActionPriority
from .vision_service import VisionService
from .audio_service import AudioService
from .tactile_service import TactileService
from ..system.security_monitor import ABCKeyManager
from ..api.router import router as api_v1_router
from ..api.v1.endpoints import pet, economy
from ..core.autonomous.digital_life_integrator import DigitalLifeIntegrator
from ..economy.economy_manager import EconomyManager
from ..core.cognitive_economy_bridge import initialize_cognitive_bridge
from .brain_bridge_service import BrainBridgeService

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

app.include_router(api_v1_router)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
