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

# 加载环境变量
env_path = None
try:
    from dotenv import load_dotenv

    # 从项目根目录加载 .env 文件
    # main_api_server.py 在 apps/backend/src/services/
    # 项目根目录是 apps/backend/src/services 的向上5级 (services -> src -> backend -> apps -> Unified-AI-Project)
    env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)
except ImportError:
    pass
except Exception:
    pass

logger = logging.getLogger(__name__)

# 现在可以安全地记录环境变量加载状态
try:
    from dotenv import load_dotenv

    if env_path and env_path.exists():
        logger.info(f"Environment variables loaded from: {env_path}")
    else:
        if env_path:
            logger.warning(f".env file not found at: {env_path}")
except ImportError:
    logger.warning(
        "python-dotenv not installed, environment variables will not be loaded from .env file"
    )

# ========== 修复：系统指标管理器 ==========
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available, system metrics will use fallback values")


class SystemMetricsManager:
    """系统指标管理器

    修复版本：统一的系统指标管理
    - 统一数据源（使用 psutil）
    - 统一计算方法
    - 添加缓存机制
    """

    def __init__(self, cache_ttl: float = 5.0):
        self.cache_ttl = cache_ttl  # 缓存生存时间（秒）
        self._cache = {}
        self._cache_timestamp = {}

    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self._cache_timestamp:
            return False
        return (
            datetime.now() - self._cache_timestamp[key]
        ).total_seconds() < self.cache_ttl

    def _get_cached_or_compute(self, key: str, compute_func) -> Any:
        """获取缓存值或计算新值"""
        if self._is_cache_valid(key):
            return self._cache[key]

        value = compute_func()
        self._cache[key] = value
        self._cache_timestamp[key] = datetime.now()
        return value

    def get_cpu_percent(self) -> float:
        """获取 CPU 使用率（统一数据源）"""
        if not PSUTIL_AVAILABLE:
            return 0.0

        def compute():
            return psutil.cpu_percent(interval=0.1)

        return self._get_cached_or_compute("cpu_percent", compute)

    def get_memory_percent(self) -> float:
        """获取内存使用率（统一数据源）"""
        if not PSUTIL_AVAILABLE:
            return 0.0

        def compute():
            return psutil.virtual_memory().percent

        return self._get_cached_or_compute("memory_percent", compute)

    def get_disk_percent(self) -> float:
        """获取磁盘使用率（统一数据源）"""
        if not PSUTIL_AVAILABLE:
            return 0.0

        def compute():
            return psutil.disk_usage("/").percent

        return self._get_cached_or_compute("disk_percent", compute)

    def get_all_metrics(self) -> Dict[str, float]:
        """获取所有系统指标"""
        return {
            "cpu_percent": self.get_cpu_percent(),
            "memory_percent": self.get_memory_percent(),
            "disk_percent": self.get_disk_percent(),
        }

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        self._cache_timestamp.clear()


# 创建全局系统指标管理器实例
system_metrics_manager = SystemMetricsManager()


# ========== 修复：消息管理器 ==========
class MessageManager:
    """消息管理器

    修复版本：添加消息序列号、状态合并和去重机制
    - 消息序列号
    - 状态合并
    - 消息去重
    """

    def __init__(self):
        self.message_counter = 0  # 消息序列号计数器
        self.message_cache = {}  # 消息缓存（用于去重）
        self.max_cache_size = 1000  # 最大缓存大小
        self.state_history = {}  # 状态历史
        self.max_state_history = 100  # 最大状态历史记录数

    def get_next_message_id(self) -> str:
        """获取下一个消息序列号"""
        self.message_counter += 1
        return (
            f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.message_counter:06d}"
        )

    def is_duplicate_message(self, message_id: str) -> bool:
        """检查消息是否重复"""
        return message_id in self.message_cache

    def cache_message(self, message_id: str, message_data: Dict[str, Any]):
        """缓存消息"""
        self.message_cache[message_id] = {
            "data": message_data,
            "timestamp": datetime.now().isoformat(),
        }

        # 限制缓存大小
        if len(self.message_cache) > self.max_cache_size:
            # 删除最旧的 10% 的消息
            items_to_remove = int(self.max_cache_size * 0.1)
            for _ in range(items_to_remove):
                if self.message_cache:
                    self.message_cache.pop(next(iter(self.message_cache)))

    def merge_state(
        self, current_state: Dict[str, Any], new_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并状态"""
        merged = current_state.copy()

        for key, value in new_state.items():
            if (
                isinstance(value, dict)
                and key in merged
                and isinstance(merged[key], dict)
            ):
                # 递归合并嵌套字典
                merged[key] = self.merge_state(merged[key], value)
            else:
                # 直接替换
                merged[key] = value

        return merged

    def record_state(self, state_id: str, state_data: Dict[str, Any]):
        """记录状态历史"""
        if state_id not in self.state_history:
            self.state_history[state_id] = []

        self.state_history[state_id].append(
            {"data": state_data, "timestamp": datetime.now().isoformat()}
        )

        # 限制历史记录大小
        if len(self.state_history[state_id]) > self.max_state_history:
            self.state_history[state_id] = self.state_history[state_id][
                -self.max_state_history :
            ]

    def get_state_history(self, state_id: str) -> List[Dict[str, Any]]:
        """获取状态历史"""
        return self.state_history.get(state_id, [])


# 创建全局消息管理器实例
message_manager = MessageManager()

# 確保 src 目錄在 Python 路徑中
# 必須添加 src 目錄本身，這樣 Python 才能找到 src.core 等模塊
_backend_dir = Path(__file__).parent.parent.parent  # /apps/backend
_src_path = str(_backend_dir / "src")  # /apps/backend/src
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from fastapi import (
    FastAPI,
    HTTPException,
    APIRouter,
    Body,
    BackgroundTasks,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware

from core.autonomous.desktop_interaction import DesktopInteraction, FileCategory
from core.autonomous.action_executor import (
    ActionExecutor,
    Action,
    ActionCategory,
    ActionPriority,
)
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
pet.set_economy_manager(economy_manager)
economy.set_economy_manager(economy_manager)


def _validate_environment_variables():
    """
    驗證啟動時必需的環境變量

    檢查 ANGELA_KEY_A, ANGELA_KEY_B, ANGELA_KEY_C 是否存在
    如有缺失，記錄警告但不阻止啟動（允許演示模式）
    """
    required_keys = ["ANGELA_KEY_A", "ANGELA_KEY_B", "ANGELA_KEY_C"]
    missing_keys = []

    for key in required_keys:
        value = os.environ.get(key)
        if not value:
            missing_keys.append(key)

    if missing_keys:
        logger.warning(
            f"[STARTUP] Missing environment variables: {', '.join(missing_keys)}. "
            "Using demo keys for development mode. "
            "Set these variables for production deployment."
        )
    else:
        logger.info("[STARTUP] All required environment variables are set")

    return len(missing_keys) == 0


async def _handle_chat_request(
    user_message: str, user_name: str, history: List[Dict[str, Any]], session_id: str
) -> Dict[str, Any]:
    """
    處理聊天請求的共用函數

    統一處理 /angela/chat 和 /dialogue 端點的聊天邏輯
    包含 LLM 調用、情感分析和錯誤處理

    Args:
        user_message: 用戶輸入的消息
        user_name: 用戶名稱
        history: 對話歷史
        session_id: 會話 ID

    Returns:
        包含回應、情感分析和元數據的字典
    """
    # 輸入驗證
    if not user_message or not user_message.strip():
        raise HTTPException(status_code=400, detail="消息不能為空")

    # 調用 LLM 服務生成回應，添加超時控制
    try:
        service = await get_llm_service()
        # 使用 asyncio.wait_for 添加 30 秒超時（增加以適應慢速模型）
        response_text = await asyncio.wait_for(
            angela_llm_response(
                user_message=user_message, history=history, user_name=user_name
            ),
            timeout=30.0,  # 30 秒超時
        )
        source = "llm" if service and service.is_available else "fallback"

        # 使用情感识别系统分析情感
        if service and hasattr(service, "analyze_emotion"):
            emotion_analysis = service.analyze_emotion(user_message, response_text)
            emotion = emotion_analysis.get("emotion", "happy")
            emotion_confidence = emotion_analysis.get("confidence", 0.5)
            emotion_intensity = emotion_analysis.get("intensity", 0.5)
        else:
            emotion = "happy"
            emotion_confidence = 0.5
            emotion_intensity = 0.5

    except asyncio.TimeoutError:
        logger.warning(f"LLM response timeout for message: {user_message[:50]}...")
        # 超時時使用備份回應
        response_text = generate_angela_response(user_message, user_name)
        source = "fallback-timeout"
        emotion = "neutral"
        emotion_confidence = 0.5
        emotion_intensity = 0.5
    except Exception as e:
        logger.error(f"Error in {__name__}: {e}", exc_info=True)

        # 如果 LLM 服務不可用，使用備份回應
        logger.warning(f"LLM service error: {e}")
        response_text = generate_angela_response(user_message, user_name)
        source = "fallback-error"
        emotion = "neutral"
        emotion_confidence = 0.5
        emotion_intensity = 0.5

    # 統一響應格式
    return {
        "session_id": session_id,
        "response": response_text,
        "response_text": response_text,  # 保留此字段以向後兼容
        "emotion": emotion,
        "angela_mood": emotion,  # 保留此字段以向後兼容
        "emotion_confidence": emotion_confidence,
        "emotion_intensity": emotion_intensity,
        "source": source,
        "timestamp": datetime.now().isoformat(),
    }


@app.on_event("startup")
async def startup_event():
    # 驗證環境變量
    _validate_environment_variables()

    # 自動創建日誌目錄
    log_dir = Path("logs")
    try:
        os.makedirs(log_dir, exist_ok=True)
        logger.info(f"[STARTUP] Log directory created/verified: {log_dir.absolute()}")
    except Exception as e:
        logger.warning(f"[STARTUP] Failed to create log directory: {e}")

    await desktop_interaction.initialize()
    await action_executor.initialize()
    await digital_life.initialize()

    # Initialize Logic Bridge
    if digital_life.autonomous_lifecycle:
        initialize_cognitive_bridge(
            digital_life.autonomous_lifecycle.cdm, economy_manager
        )

    await brain_bridge.start()
    # vision_service doesn't have an async initialize yet

    # Initialize LLM Service (Angela's brain)
    global _llm_service
    try:
        _llm_service = await get_llm_service()
        logger.info(
            f"[STARTUP] LLM Service initialized: available={_llm_service.is_available}"
        )
    except Exception as e:
        logger.error(f"[STARTUP] LLM Service initialization failed: {e}")

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


@router.get("/api/v1/system/status")
async def system_status():
    """
    獲取系統狀態信息

    修复版本：使用统一的系统指标管理器
    - 统一数据源
    - 统一计算方法
    - 添加缓存机制
    """
    try:
        # 獲取服務狀態
        services_status = {
            "llm_service": _llm_service.is_available if _llm_service else False,
            "digital_life": digital_life.is_initialized
            if hasattr(digital_life, "is_initialized")
            else False,
            "brain_bridge": brain_bridge.is_running
            if hasattr(brain_bridge, "is_running")
            else False,
            "economy": economy_manager is not None
            if "economy_manager" in globals()
            else False,
        }

        # ========== 修复：使用统一的系统指标管理器 ==========
        system_resources = system_metrics_manager.get_all_metrics()

        return {
            "status": "running",
            "version": "6.0.4",
            "timestamp": datetime.now().isoformat(),
            "services": services_status,
            "system_resources": system_resources,
            "active_sessions": len(sessions),
            "message": "System operational",
        }
    except Exception as e:
        logger.error(f"Error in {__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
    3. 分析用戶情感
    4. 返回經過 Angela 個性化處理的回應

    用戶不是直接與 LLM 對話，而是透過 Angela。
    """
    user_message = request.get("message", request.get("text", ""))
    session_id = request.get("session_id", f"angela-{uuid.uuid4().hex[:8]}")
    user_name = request.get("user_name", "朋友")
    history = request.get("history", [])

    return await _handle_chat_request(user_message, user_name, history, session_id)


@router.post("/dialogue")
async def dialogue(request: Dict[str, Any] = Body(...)):
    """
    对話接口 - 與 /angela/chat 相同，為前端兼容性提供
    """
    user_message = request.get("message", request.get("text", ""))
    session_id = request.get("session_id", f"angela-{uuid.uuid4().hex[:8]}")
    user_name = request.get("user_name", "朋友")
    history = request.get("history", [])

    return await _handle_chat_request(user_message, user_name, history, session_id)


# --- Desktop Interaction API ---


@router.get("/api/v1/desktop/state")
async def get_desktop_state():
    """Get current desktop state"""
    state = desktop_interaction.get_desktop_state()
    return {
        "total_files": state.total_files,
        "total_size": state.total_size,
        "clutter_level": state.clutter_level,
        "files_by_category": {
            cat.name: count for cat, count in state.files_by_category.items()
        },
        "last_organized": state.last_organized.isoformat()
        if state.last_organized
        else None,
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
            parameters=action_data.get("parameters", {}),
        )

        result = await action_executor.submit_and_execute(action)
        return {
            "success": result.success,
            "action_id": result.action_id,
            "output": result.output,
            "error": result.error,
        }
    except Exception as e:
        logger.error(f"Error in {__name__}: {e}", exc_info=True)
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
            distribution=distribution,
        )
        return result
    except Exception as e:
        logger.error(f"Error in {__name__}: {e}", exc_info=True)
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
        logger.error(f"Error in {__name__}: {e}", exc_info=True)
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
        logger.error(f"Error in {__name__}: {e}", exc_info=True)
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
        logger.error(f"Error in {__name__}: {e}", exc_info=True)
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
        logger.error(f"Error in {__name__}: {e}", exc_info=True)
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
        logger.error(f"Error in {__name__}: {e}", exc_info=True)
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
    """连接管理器

    修复版本：改进的 WebSocket 连接管理
    - 添加心跳机制
    - 改进重连逻辑
    - 添加连接状态监控
    - 实现状态缓冲和重发
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}  # 连接信息
        self.message_buffer: Dict[WebSocket, List[Dict[str, Any]]] = {}  # 消息缓冲
        self.max_buffer_size = 10  # 最大缓冲消息数
        self.heartbeat_interval = 30  # 心跳间隔（秒）
        self.heartbeat_timeout = 120  # 心跳超时（秒） - 增加到120秒以提高稳定性

    async def connect(self, websocket: WebSocket):
        """接受新连接"""
        await websocket.accept()
        self.active_connections.append(websocket)

        # 记录连接信息
        self.connection_info[websocket] = {
            "connected_at": datetime.now().isoformat(),
            "last_heartbeat": datetime.now(),
            "heartbeat_missed": 0,
            "client_id": str(uuid.uuid4()),
        }

        # 初始化消息缓冲
        self.message_buffer[websocket] = []

        logger.info(
            f"WebSocket 连接已建立 (ID: {self.connection_info[websocket]['client_id']})"
        )

        # 启动心跳检测
        asyncio.create_task(self._heartbeat_monitor(websocket))

    def disconnect(self, websocket: WebSocket):
        """断开连接"""
        if websocket in self.active_connections:
            client_id = self.connection_info.get(websocket, {}).get(
                "client_id", "unknown"
            )
            self.active_connections.remove(websocket)
            self.connection_info.pop(websocket, None)
            self.message_buffer.pop(websocket, None)
            logger.info(f"WebSocket 连接已断开 (ID: {client_id})")

    async def _heartbeat_monitor(self, websocket: WebSocket):
        """心跳监控"""
        while websocket in self.active_connections:
            try:
                # 检查心跳超时
                info = self.connection_info.get(websocket)
                if info:
                    time_since_last_heartbeat = (
                        datetime.now() - info["last_heartbeat"]
                    ).total_seconds()

                    if time_since_last_heartbeat > self.heartbeat_timeout:
                        logger.warning(f"心跳超时，断开连接 (ID: {info['client_id']})")
                        self.disconnect(websocket)
                        break

                # 等待心跳间隔
                await asyncio.sleep(self.heartbeat_interval)

            except Exception as e:
                logger.error(f"心跳监控错误: {e}")
                break

    async def broadcast(self, message: dict):
        """广播消息到所有连接"""
        for connection in self.active_connections[:]:  # 使用副本遍历
            try:
                await connection.send_json(message)

                # 清除该连接的消息缓冲（成功发送）
                if connection in self.message_buffer:
                    self.message_buffer[connection].clear()

            except (ConnectionError, RuntimeError, Exception) as e:
                # 连接失败，添加到消息缓冲
                logger.warning(
                    f"广播消息失败，添加到缓冲 (ID: {self.connection_info.get(connection, {}).get('client_id', 'unknown')}): {e}"
                )

                if connection in self.message_buffer:
                    self.message_buffer[connection].append(message)
                    # 限制缓冲大小
                    if len(self.message_buffer[connection]) > self.max_buffer_size:
                        self.message_buffer[connection].pop(0)

                # 尝试重发缓冲的消息
                await self._retry_buffered_messages(connection)

                # 如果仍然失败，断开连接
                try:
                    await connection.close()
                except Exception:
                    pass
                finally:
                    self.disconnect(connection)

    async def _retry_buffered_messages(self, websocket: WebSocket):
        """重发缓冲的消息"""
        if websocket not in self.message_buffer:
            return

        buffered_messages = self.message_buffer[websocket].copy()
        self.message_buffer[websocket].clear()

        for message in buffered_messages:
            try:
                await websocket.send_json(message)
                logger.debug(f"成功重发缓冲消息")
            except Exception as e:
                # 重发失败，重新添加到缓冲
                self.message_buffer[websocket].append(message)
                logger.warning(f"重发消息失败: {e}")
                break

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_json(message)
            # 清除该连接的消息缓冲（成功发送）
            if websocket in self.message_buffer:
                self.message_buffer[websocket].clear()
        except Exception as e:
            # 发送失败，添加到缓冲
            logger.warning(f"发送个人消息失败，添加到缓冲: {e}")
            if websocket in self.message_buffer:
                self.message_buffer[websocket].append(message)
                # 限制缓冲大小
                if len(self.message_buffer[websocket]) > self.max_buffer_size:
                    self.message_buffer[websocket].pop(0)

    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        return {
            "active_connections": len(self.active_connections),
            "connections": [
                {
                    "client_id": info.get("client_id", "unknown"),
                    "connected_at": info.get("connected_at", "unknown"),
                    "last_heartbeat": info.get("last_heartbeat").isoformat()
                    if info.get("last_heartbeat")
                    else "unknown",
                    "heartbeat_missed": info.get("heartbeat_missed", 0),
                }
                for info in self.connection_info.values()
            ],
        }


manager = ConnectionManager()


# Background task to broadcast state updates
async def broadcast_state_updates():
    """Periodically broadcast state updates to all connected clients"""
    while True:
        try:
            # Get current state from brain bridge
            state_data = {
                "alpha": {
                    "energy": brain_bridge.get_energy_level()
                    if hasattr(brain_bridge, "get_energy_level")
                    else 0.5,
                    "comfort": 0.5,
                    "arousal": 0.5,
                },
                "beta": {"curiosity": 0.5, "focus": 0.5, "learning": 0.5},
                "gamma": {"happiness": 0.5, "calm": 0.5},
                "delta": {"attention": 0.5, "engagement": 0.5},
                "timestamp": datetime.now().isoformat(),
            }

            await manager.broadcast(
                {
                    "type": "state_update",
                    "data": state_data,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting state update: {e}")

        # Broadcast every 5 seconds
        await asyncio.sleep(5)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication with desktop app

    修复版本：改进的 WebSocket 端点
    - 改进心跳处理
    - 添加错误处理
    - 支持消息重发
    """
    await manager.connect(websocket)
    client_id = manager.connection_info.get(websocket, {}).get("client_id", "unknown")

    try:
        # Send initial connection confirmation
        await websocket.send_json(
            {
                "type": "connected",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "server_version": "6.0.4",
            }
        )

        # ========== 修复：改进的消息处理循环 ==========
        while True:
            try:
                # 接收消息（带超时）
                data = await asyncio.wait_for(
                    websocket.receive_json(), timeout=manager.heartbeat_timeout
                )

                # 更新心跳时间
                if websocket in manager.connection_info:
                    manager.connection_info[websocket]["last_heartbeat"] = (
                        datetime.now()
                    )
                    manager.connection_info[websocket]["heartbeat_missed"] = 0

                # Handle different message types
                if data.get("type") in ["heartbeat", "ping"]:
                    # 心跳响应
                    await websocket.send_json(
                        {
                            "type": "heartbeat_ack"
                            if data.get("type") == "heartbeat"
                            else "echo",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                elif data.get("type") == "state_update":
                    # Broadcast state updates to all connected clients
                    await manager.broadcast(
                        {
                            "type": "state_update",
                            "data": data.get("data", {}),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                elif data.get("type") == "chat_message":
                    # Handle chat messages from desktop app - use shared service
                    user_message = data.get("data", {}).get("content", "")
                    message_id = data.get("data", {}).get("message_id", "")
                    user_name = data.get("data", {}).get("user_name", "朋友")

                    # Use shared chat service
                    response_text = generate_angela_response(user_message, user_name)

                    # Send response back to the client
                    await manager.send_personal_message(
                        {
                            "type": "chat_response",
                            "data": {
                                "message_id": message_id,
                                "content": response_text,
                                "sender": "angela",
                            },
                            "timestamp": datetime.now().isoformat(),
                        },
                        websocket,
                    )

                else:
                    # Echo back other messages for now
                    await websocket.send_json(
                        {
                            "type": "echo",
                            "original": data,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

            except asyncio.TimeoutError:
                # 超时，检查是否需要断开连接
                if websocket in manager.connection_info:
                    manager.connection_info[websocket]["heartbeat_missed"] += 1
                    logger.warning(
                        f"心跳超时 ({manager.connection_info[websocket]['heartbeat_missed']}次): {client_id}"
                    )

                    # 如果连续错过多次心跳，断开连接
                    if manager.connection_info[websocket]["heartbeat_missed"] >= 2:
                        logger.warning(f"连续心跳超时，断开连接: {client_id}")
                        break
                else:
                    break

            except WebSocketDisconnect:
                logger.info(f"WebSocket 客户端主动断开: {client_id}")
                break

            except Exception as e:
                logger.error(f"WebSocket 处理错误: {e}")
                break

    finally:
        # 确保连接被清理
        manager.disconnect(websocket)


app.include_router(api_v1_router)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
