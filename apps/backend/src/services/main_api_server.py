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
    # broad exception acceptable: env file may not exist, non-critical setup
    pass

logger = logging.getLogger(__name__)

# ========== 修复：日志目录自动创建 ==========
try:
    log_dir = Path("logs")
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created logs directory at: {log_dir.absolute()}")
except Exception as e:
    # broad exception acceptable: log directory creation is non-critical, fallback to default
    print(f"Warning: Failed to create logs directory: {e}")

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
        return (datetime.now() - self._cache_timestamp[key]).total_seconds() < self.cache_ttl

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
        return f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.message_counter:06d}"

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
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
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
            self.state_history[state_id] = self.state_history[state_id][-self.max_state_history :]

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
    Request,
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
from services.chat_service import generate_angela_response, get_angela_chat_service
from services.angela_llm_service import get_llm_service, angela_llm_response
from system.security_monitor import ABCKeyManager

# Initialize _llm_service as None to prevent NameError before startup
_llm_service = None

from api.router import router as api_v1_router
from api.v1.endpoints import pet, economy
from core.autonomous.digital_life_integrator import DigitalLifeIntegrator
from economy.economy_manager import EconomyManager
from core.cognitive_economy_bridge import initialize_cognitive_bridge
from core.autonomous.heartbeat import MetabolicHeartbeat

app = FastAPI(
    title="Angela AI API",
    description="Backend API for Angela AI Desktop Companion",
    version="6.0.4",
)

# ========== Lazy Loading: Service Initialization ==========
# Services are initialized on first access to avoid blocking imports
_desktop_interaction = None
_action_executor = None
_vision_service = None
_audio_service = None
_tactile_service = None
_abc_key_manager = None
_digital_life = None
_economy_manager = None
_metabolic_heartbeat = None

# Session management
sessions: Dict[str, Any] = {}


def get_metabolic_heartbeat() -> MetabolicHeartbeat:
    global _metabolic_heartbeat
    if _metabolic_heartbeat is None:
        from core.autonomous.heartbeat import MetabolicHeartbeat
        _metabolic_heartbeat = MetabolicHeartbeat(update_interval=30.0)
    return _metabolic_heartbeat

def get_desktop_interaction() -> DesktopInteraction:
    global _desktop_interaction
    if _desktop_interaction is None:
        _desktop_interaction = DesktopInteraction()
    return _desktop_interaction


def get_action_executor() -> ActionExecutor:
    global _action_executor
    if _action_executor is None:
        _action_executor = ActionExecutor()
    return _action_executor


def get_vision_service() -> VisionService:
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
    return _vision_service


def get_audio_service() -> AudioService:
    global _audio_service
    if _audio_service is None:
        _audio_service = AudioService()
    return _audio_service


def get_tactile_service() -> TactileService:
    global _tactile_service
    if _tactile_service is None:
        _tactile_service = TactileService()
    return _tactile_service


def get_abc_key_manager() -> ABCKeyManager:
    global _abc_key_manager
    if _abc_key_manager is None:
        _abc_key_manager = ABCKeyManager()
    return _abc_key_manager


def get_digital_life() -> DigitalLifeIntegrator:
    global _digital_life
    if _digital_life is None:
        _digital_life = DigitalLifeIntegrator()
    return _digital_life


def get_economy_manager() -> EconomyManager:
    global _economy_manager
    if _economy_manager is None:
        _economy_manager = EconomyManager({})
    return _economy_manager


# Initialize services and link components during startup
def _initialize_all_services():
    global manager
    desktop_interaction = get_desktop_interaction()
    action_executor = get_action_executor()
    vision_service = get_vision_service()
    audio_service = get_audio_service()
    tactile_service = get_tactile_service()
    abc_key_manager = get_abc_key_manager()
    digital_life = get_digital_life()
    economy_manager = get_economy_manager()

    # Link components
    pet_manager = pet.get_pet_manager()
    digital_life.broadcast_callback = manager.broadcast
    pet.set_biological_integrator(digital_life.biological_integrator)
    pet.set_economy_manager(economy_manager)
    economy.set_economy_manager(economy_manager)

    # ========== WebSocket hooks for real-time digital life ==========

    # 1. Hook PetManager to broadcast state changes
    async def pet_broadcast_wrapper(event_type, data):
        await manager.broadcast(
            {
                "type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat(),
            }
        )

    pet_manager.broadcast_callback = pet_broadcast_wrapper

    # 2. Hook BiologicalIntegrator to broadcast discrete events (emotions, etc.)
    def bio_event_callback(event_name, event_data):
        # We need to bridge from sync callback to async broadcast
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast(
                        {
                            "type": "biological_event",
                            "data": {"event": event_name, "data": event_data},
                            "timestamp": datetime.now().isoformat(),
                        }
                    ),
                    loop,
                )
        except Exception as e:
            # broad exception acceptable: callback errors should not break the loop
            logger.error(f"Failed to bridge biological event: {e}")

    # Registered with the underlying integrator if supported
    if hasattr(digital_life.biological_integrator, "register_event_callback"):
        digital_life.biological_integrator.register_event_callback(bio_event_callback)

    return (
        desktop_interaction,
        action_executor,
        vision_service,
        audio_service,
        tactile_service,
        abc_key_manager,
        digital_life,
        economy_manager,
        
    )


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
            "[STARTUP] Required security keys missing. "
            "Using demo keys for development mode. "
            "Set required environment variables for production deployment."
        )
    else:
        logger.info("[STARTUP] All required environment variables are set")

    return len(missing_keys) == 0


async def _handle_chat_request(
    user_message: str, user_name: str, history: List[Dict[str, Any]], session_id: str, origin: str = "Human"
) -> Dict[str, Any]:
    """
    處理聊天請求的共用函數 (GSI-4 / 2030 Standard)
    雙軌數學驗證：LLM 提取 + 引擎驗證 + 狀態觸發
    """
    from services.math_verifier import MathVerifier  # noqa: E402

    logger.info(f"📩 [LIS] Raw message received: '{user_message}' from {origin} (Session: {session_id})")

    if not user_message or not user_message.strip():
        raise HTTPException(status_code=400, detail="訊號遺失：消息不能為空")

    if len(user_message) > 4000:
        logger.warning(f"🛡️ [LIS] Intercepted oversized input from {origin}")
        user_message = user_message[:1000]

    if session_id not in sessions:
        sessions[session_id] = {
            "created_at": datetime.now().isoformat(),
            "origin": origin,
            "user_name": user_name
        }

    try:
        service = None

        # ============================================================
        # [Task N.22-DUAL-RAIL] 雙軌數學驗證
        # ============================================================
        is_math = False
        verifier = None

        try:
            digital_life = get_digital_life()
            matrix = None
            if digital_life and hasattr(digital_life, "state_matrix"):
                matrix = digital_life.state_matrix

            verifier = MathVerifier(state_matrix=matrix)
            is_math = verifier.is_math_message(user_message)

            if is_math:
                logger.info(f"🧮 [DualRail] Math task detected from {origin}")
                verification = await verifier.verify(user_message, user_name)

                if verification.response_text:
                    response_text = verification.response_text
                    source = "dual_rail"

                    if verification.needs_clarification:
                        emotion = "confused"
                        emotion_confidence = 0.7
                        emotion_intensity = 0.6
                    elif not verification.matches:
                        emotion = "surprised"
                        emotion_confidence = 0.8
                        emotion_intensity = 0.7
                    elif verification.extraction and verification.extraction.confidence >= 0.8:
                        emotion = "happy"
                        emotion_confidence = 0.9
                        emotion_intensity = 0.6
                    else:
                        emotion = "calm"
                        emotion_confidence = 0.6
                        emotion_intensity = 0.4

                    is_math = True

                    if matrix and verification.final_answer is not None:
                        epsilon_conf = verification.extraction.confidence if verification.extraction else 0.5
                        matrix.epsilon.values["certainty"] = min(1.0, 0.5 + epsilon_conf * 0.5)
                        matrix.epsilon.values["complexity"] = min(
                            1.0, len(user_message) / 50.0
                        )
                        if not verification.matches:
                            matrix.epsilon.values["certainty"] *= 0.5
                            matrix.gamma.values["surprise"] = min(
                                1.0, matrix.gamma.values.get("surprise", 0.0) + 0.3
                            )
                        elif verification.needs_clarification:
                            matrix.beta.values["confusion"] = min(
                                1.0, matrix.beta.values.get("confusion", 0.0) + 0.4
                            )
                        matrix.apply_epsilon_influence()
                else:
                    is_math = False

        except Exception as math_err:  # broad exception acceptable: math verification is optional
            logger.warning(f"⚠️ [DualRail] Math verification failed, falling back to LLM: {math_err}")
            is_math = False

        if not is_math:
            service = await get_llm_service()
            response_text = await asyncio.wait_for(
                angela_llm_response(user_message=user_message, history=history, user_name=user_name, origin=origin),
                timeout=30.0,
            )
            source = "llm" if service and service.is_available else "fallback"

        # ============================================================
        # 情感分析
        # ============================================================
        if service and hasattr(service, "analyze_emotion"):
            emotion_analysis = service.analyze_emotion(user_message, response_text)
            emotion = emotion_analysis.get("emotion", "happy")
            emotion_confidence = emotion_analysis.get("confidence", 0.5)
            emotion_intensity = emotion_analysis.get("intensity", 0.5)
        else:
            emotion = emotion if is_math else "happy"
            emotion_confidence = emotion_confidence if is_math else 0.5
            emotion_intensity = emotion_intensity if is_math else 0.5

        return {
            "response_text": response_text,
            "source": source,
            "emotion": emotion,
            "emotion_confidence": emotion_confidence,
            "emotion_intensity": emotion_intensity,
            "session_id": session_id,
        }

    except asyncio.TimeoutError:
        logger.warning(f"LLM response timeout for message: {user_message[:50]}...")
        response_text = await generate_angela_response(user_message, user_name)
        source = "fallback-timeout"
        emotion = "neutral"
        emotion_confidence = 0.5
        emotion_intensity = 0.5
        return {
            "response_text": response_text,
            "source": source,
            "emotion": emotion,
            "emotion_confidence": emotion_confidence,
            "emotion_intensity": emotion_intensity,
            "session_id": session_id,
        }
    except Exception as e:
        logger.error(f"Error in _handle_chat_request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="internal server error")


@api_v1_router.get("/security/sync-key-c")
async def sync_key_c(request: Request):
    """Get Key C for desktop app synchronization (Localhost restricted)"""
    client_host = request.client.host
    if client_host not in ["127.0.0.1", "::1", "localhost"]:
        logger.warning(f"Unauthorized access attempt to sync-key-c from {client_host}")
        raise HTTPException(status_code=403, detail="Access restricted to localhost")
    
    abc_key_manager = get_abc_key_manager()
    key_c = abc_key_manager.get_key("KeyC")
    if not key_c:
        raise HTTPException(status_code=500, detail="Security keys not initialized")
    return {"key_c": key_c}


@api_v1_router.post("/session/start")
async def start_session(request: Dict[str, Any] = Body(default={})):
    session_id = f"sess-{uuid.uuid4().hex[:8]}"
    sessions[session_id] = {
        "created_at": datetime.now().isoformat(),
        "messages": [],
        "user_name": request.get("user_name", "User"),
    }
    return {"session_id": session_id, "message": "Welcome to Angela AI!"}


@api_v1_router.post("/session/{session_id}/send")
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


@api_v1_router.post("/angela/chat")
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
    origin = request.get("origin", "Human")

    return await _handle_chat_request(user_message, user_name, history, session_id, origin=origin)


@api_v1_router.post("/dialogue")
async def dialogue(request: Dict[str, Any] = Body(...)):
    """
    对話接口 - 與 /angela/chat 相同，為前端兼容性提供
    """
    user_message = request.get("message", request.get("text", ""))
    session_id = request.get("session_id", f"angela-{uuid.uuid4().hex[:8]}")
    user_name = request.get("user_name", "朋友")
    history = request.get("history", [])
    origin = request.get("origin", "Human")

    return await _handle_chat_request(user_message, user_name, history, session_id, origin=origin)


@api_v1_router.post("/chat/unified")
async def unified_chat(request: Dict[str, Any] = Body(...)):
    """
    Unified chat endpoint for multi-frontend/persona migration.

    Migration notes:
    - New clients should prefer this endpoint.
    - Legacy endpoints (/dialogue, /angela/chat) remain available during migration.
    """
    user_message = request.get("message", request.get("text", ""))
    context = {
        "user_id": request.get("user_name", request.get("user_id", "User")),
        "tenant_id": request.get("tenant_id", "default"),
        "persona_id": request.get("persona_id", "angela"),
        "client_id": request.get("origin", request.get("client_id", "desktop")),
    }
    user_name = request.get("user_name", context["user_id"])
    history = request.get("history", [])

    # Default session id is now namespace-aware to reduce cross-client confusion
    session_id = request.get(
        "session_id",
        f"{context['tenant_id']}::{context['persona_id']}::{uuid.uuid4().hex[:8]}",
    )
    origin = request.get("origin", context["client_id"])

    response = await _handle_chat_request(
        user_message=user_message,
        user_name=user_name,
        history=history,
        session_id=session_id,
        origin=origin,
    )
    response["context"] = context
    response["migration_note"] = (
        "Use /api/v1/chat/unified for multi-persona isolation; "
        "legacy /dialogue and /angela/chat remain temporarily supported."
    )
    return response


# --- Desktop Interaction API ---


@api_v1_router.get("/desktop/state")
@api_v1_router.post("/desktop/organize")
@api_v1_router.post("/desktop/cleanup")
@api_v1_router.get("/actions/status")
@api_v1_router.post("/actions/execute")
@api_v1_router.post("/vision/sampling")
@api_v1_router.post("/vision/perceive")
@api_v1_router.post("/audio/scan")
@api_v1_router.post("/audio/register_user")
@api_v1_router.post("/tactile/model")
@api_v1_router.post("/tactile/touch")
@api_v1_router.post("/brain/metrics")
@api_v1_router.post("/brain/dividend")
async def get_brain_dividend():
    """Get CDM Economic Model data"""
    digital_life = get_digital_life()
    summary = digital_life.get_formula_metrics()
    if summary and "formula_status" in summary:
        return summary["formula_status"].get("cdm", {})
    return {"message": "Dividend data not available"}


# --- WebSocket Endpoint for Desktop App ---

import asyncio
import json
from services.connection_session import get_session_manager, SessionState


class ConnectionManager:
    """
    WebSocket connection manager - now uses SessionManager internally.
    
    This class provides backward-compatible API while delegating to SessionManager.
    """

    def __init__(self):
        self._sm = get_session_manager()
    
    @property
    def active_connections(self):
        return [s.websocket for s in self._sm._sessions.values()]
    
    @property
    def connection_info(self):
        return {
            s.websocket: {
                "client_id": s.client_id,
                "session_id": s.session_id,
                "connected_at": s.created_at.isoformat(),
                "last_heartbeat": s.last_heartbeat,
                "heartbeat_missed": 0,
                "metadata": s.metadata,
            }
            for s in self._sm._sessions.values()
        }
    
    @property
    def message_buffer(self):
        return self._sm._message_buffers
    
    @property
    def heartbeat_interval(self):
        return self._sm.heartbeat_interval
    
    @property
    def heartbeat_timeout(self):
        return self._sm.heartbeat_timeout
    
    async def connect(self, websocket: WebSocket, session_id: str = None, metadata: dict = None):
        """Accept new connection with optional session_id"""
        await websocket.accept()
        session = await self._sm.register(websocket, session_id, metadata, single_device_mode=True)
        return session
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket"""
        for client_id, session in list(self._sm._sessions.items()):
            if session.websocket == websocket:
                asyncio.create_task(self._sm.unregister(client_id, "Normal close"))
                break
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connections"""
        return await self._sm.broadcast(message)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket"""
        for client_id, session in self._sm._sessions.items():
            if session.websocket == websocket:
                return await self._sm.send_to_client(client_id, message)
        return False
    
    def get_connection_stats(self):
        return self._sm.get_stats()
    
    # Legacy compatibility: direct access to SessionManager methods
    async def send_to_session(self, session_id: str, message: dict):
        return await self._sm.send_to_session(session_id, message)
    
    async def unregister(self, client_id: str):
        return await self._sm.unregister(client_id)
    
    def get_all_connections_info(self):
        return self._sm.get_all_connections_info()
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息 - uses SessionManager"""
        stats = self._sm.get_stats()
        connections = self._sm.get_all_connections_info()
        return {
            "active_connections": stats.active_sessions,
            "total_sessions": stats.total_sessions,
            "connections": [
                {
                    "client_id": info.get("client_id", "unknown"),
                    "session_id": info.get("session_id", "unknown"),
                    "state": info.get("state", "unknown"),
                    "connected_at": info.get("created_at", "unknown"),
                    "last_heartbeat": info.get("last_heartbeat", "unknown"),
                    "metadata": info.get("metadata", {}),
                }
                for info in connections
            ],
        }


manager = ConnectionManager()


# Background task to broadcast state updates
async def broadcast_state_updates():
    """Periodically broadcast state updates to all connected clients"""
    while True:
        try:
            # 2030 Standard: Get current state from real life systems
            heartbeat = get_metabolic_heartbeat()
            digital_life = get_digital_life()
            bio_state = heartbeat.bio_integrator.get_biological_state()
            
            # Map the GSI-4 / Bio status to UI dimensions (alpha, beta, gamma, delta)
            state_data = {
                "alpha": {
                    "energy": (100.0 - bio_state.get("fatigue", 0.0)) / 100.0,
                    "stress": bio_state.get("stress_level", 0.0),
                    "hormones": bio_state.get("hormones", {}),
                },
                "beta": {
                    "learning_rate": 0.01,
                    "cognitive_load": 0.0,
                },
                "gamma": {
                    "happiness": bio_state.get("mood", 0.5),
                    "emotion": bio_state.get("dominant_emotion", "calm"),
                },
                "delta": {
                    "intensity": bio_state.get("arousal", 50.0) / 100.0,
                },
                "spatial": {
                    "x": heartbeat.x,
                    "y": heartbeat.y,
                    "posture": heartbeat.posture, # [Task N.16.1.3] Cerebellum data

                },
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
            # broad exception acceptable: broadcast loop should not crash on errors
            logger.error(f"Error broadcasting state update: {e}")

        # Broadcast every 0.2 seconds
        await asyncio.sleep(0.2)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication with desktop app

    修复版本：改进的 WebSocket 端点 - 支持 session_id
    - 使用 SessionManager 进行会话管理
    - 支持单 session 生命周期
    - 支持多客户端注册
    """
    # Wait for initial handshake message with session_id
    try:
        handshake = await asyncio.wait_for(websocket.receive_json(), timeout=10)
    except asyncio.TimeoutError:
        logger.warning("[WebSocket] Handshake timeout, closing connection")
        await websocket.close(code=4001, reason="Handshake timeout")
        return
    
    # Extract session info from handshake
    session_id = handshake.get("session_id") or str(uuid.uuid4())
    client_type = handshake.get("client_type", "desktop")
    client_version = handshake.get("client_version", "unknown")
    
    metadata = {
        "client_type": client_type,
        "client_version": client_version,
    }
    
    # Register session with SessionManager
    session = await manager.connect(websocket, session_id, metadata)
    client_id = session.client_id
    
    logger.info(f"[WebSocket] Incoming connection - client_id: {client_id}, session_id: {session_id}, remote: {websocket.client}")

    try:
        # Send initial connection confirmation with session info
        await websocket.send_json(
            {
                "type": "connected",
                "client_id": client_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "server_version": "6.0.4",
            }
        )

        # ========== Session-based message processing loop ==========
        while True:
            try:
                # 接收消息（带超时）
                data = await asyncio.wait_for(
                    websocket.receive_json(), timeout=manager.heartbeat_timeout
                )

                # Update heartbeat and sequence
                await manager._sm.update_heartbeat(client_id)
                sequence = manager._sm.increment_sequence(client_id)
                
                # Handle different message types
                if data.get("type") in ["heartbeat", "ping"]:
                    # 心跳响应
                    await websocket.send_json(
                        {
                            "type": (
                                "heartbeat_ack" if data.get("type") == "heartbeat" else "echo"
                            ),
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

                elif data.get("type") == "tactile_event":
                    # 2030 Standard: Identity-aware Reflex Loop
                    tactile_data = data.get("data", {})
                    tactile_service = get_tactile_service()
                    res = await tactile_service.simulate_touch("user_hand", tactile_data, origin="Human")
                    
                    # Direct reflex response for 2030 responsiveness
                    await manager.send_personal_message({
                        "type": "biological_feedback",
                        "status": res.get("status"),
                        "reflex": res.get("reflex"),
                        "intensity": res.get("feedback", {}).get("intensity")
                    }, websocket)

                elif data.get("type") == "chat_message":
                    # 2030 Standard: Use Realized Chat Service with Origin Tracking
                    user_message = data.get("data", {}).get("content", "")
                    message_id = data.get("data", {}).get("message_id", "")
                    user_name = data.get("data", {}).get("user_name", "朋友")

                    chat_service = get_angela_chat_service()
                    response_text = await chat_service.generate_response(user_message, user_name, origin="Human")

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
                # Heartbeat timeout - SessionManager handles this, but we close here
                logger.warning(f"[WebSocket] Heartbeat timeout for client: {client_id}")
                break

            except WebSocketDisconnect:
                logger.info(f"[WebSocket] Client disconnected: {client_id}")
                break

            except Exception as e:
                # broad exception acceptable: WebSocket message handling should be resilient
                logger.error(f"[WebSocket] Message error for {client_id}: {e}")
                continue

    finally:
        # Clean up session via SessionManager
        asyncio.create_task(manager.unregister(client_id))


from services.atlassian_api import atlassian_router
from services.api.state_matrix_api import state_matrix_router

# Include existing routers
app.include_router(api_v1_router)
app.include_router(atlassian_router)
app.include_router(state_matrix_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
