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
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
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
from core.config_loader import get_angela_config

from core.autonomous.desktop_interaction import DesktopInteraction
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
from services.angela_llm_service import get_llm_service
from system.security_monitor import ABCKeyManager
from shared.security_middleware import EncryptedCommunicationMiddleware

# Initialize _llm_service as None to prevent NameError before startup
_llm_service = None

from api.router import router as api_v1_router
from api.v1.endpoints import pet, economy
from core.autonomous.digital_life_integrator import DigitalLifeIntegrator
from economy.economy_manager import EconomyManager

from core.autonomous.heartbeat import MetabolicHeartbeat

app = FastAPI(
    title="Angela AI API",
    description="Backend API for Angela AI Desktop Companion",
    version="6.0.4",
)

# ========== CORS 中間件（從配置讀取） ==========
try:
    _angela_cfg = get_angela_config()
    _cors_cfg = _angela_cfg.get_authority("angela_core", {}).get("middleware", {}).get("cors", {})
    if _cors_cfg.get("enabled", True):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=_cors_cfg.get("allow_origins", ["*"]),
            allow_credentials=_cors_cfg.get("allow_credentials", True),
            allow_methods=_cors_cfg.get("allow_methods", ["*"]),
            allow_headers=_cors_cfg.get("allow_headers", ["*"]),
        )
        logger.info("[Middleware] CORS enabled from config")
except Exception as e:
    logger.warning(f"[Middleware] CORS setup skipped: {e}")

# ========== 加密通訊中間件（Key B 簽名驗證） ==========
try:
    app.add_middleware(
        EncryptedCommunicationMiddleware,
        key_b=get_abc_key_manager().get_key("KeyB"),
    )
    logger.info("[Middleware] EncryptedCommunication enabled")
except Exception as e:
    logger.warning(f"[Middleware] EncryptedCommunication setup skipped: {e}")

# ========== 生命週期管理 ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: 預初始化核心服務。Shutdown: 清理資源。"""
    logger.info("[Lifecycle] Starting Angela AI API server...")
    try:
        _lc = _angela_cfg.get("lifecycle", {}) if _angela_cfg else {}
        if _lc.get("preinitialize_on_startup", True):
            for svc_name in _lc.get("services_to_preinit", []):
                try:
                    if svc_name == "AngelaChatService":
                        from services.chat_service import get_angela_chat_service
                        svc = get_angela_chat_service()
                        await svc.initialize()
                        logger.info("[Lifecycle] AngelaChatService initialized")
                    elif svc_name == "AngelaLLMService":
                        from services.angela_llm_service import get_llm_service
                        await get_llm_service()
                        logger.info("[Lifecycle] AngelaLLMService initialized")
                    elif svc_name == "BiologicalIntegrator":
                        from core.autonomous.biological_integrator import BiologicalIntegrator
                        bio = BiologicalIntegrator()
                        await bio.initialize()
                        logger.info("[Lifecycle] BiologicalIntegrator initialized")
                except Exception as e:
                    logger.warning(f"[Lifecycle] Failed to pre-init {svc_name}: {e}")
    except Exception as e:
        logger.warning(f"[Lifecycle] Startup config error: {e}")

    logger.info("[Lifecycle] Server startup complete")
    yield

    logger.info("[Lifecycle] Shutting down...")
    _sd_timeout = _lc.get("shutdown_timeout", 10.0) if _angela_cfg else 10.0
    logger.info(f"[Lifecycle] Shutdown complete (timeout={_sd_timeout}s)")


app.router.lifespan_context = lifespan

# ========== DEBUG: Patch websockets Frame.check to log RSV frames ==========
import websockets
import websockets.frames
import sys
_orig_frame_check = websockets.frames.Frame.check

def _patched_frame_check(self):
    if self.rsv1 or self.rsv2 or self.rsv3:
        payload = getattr(self, 'data', b'') if hasattr(self, 'data') else b''
        sys.stderr.write(f"[DEBUG RSV] RSV: rsv3={self.rsv3} opcode={self.opcode} fin={self.fin} payload_len={len(payload)} payload={payload[:50]}\n")
    return _orig_frame_check(self)

websockets.frames.Frame.check = _patched_frame_check

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

# Session management with TTL
class TTLSessionManager:
    """TTL-aware session manager with LRU eviction"""
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._config = _angela_cfg.get_authority("angela_core", {}).get("session_manager", {}) if _angela_cfg else {}
        self._ttl = self._config.get("ttl_seconds", 3600)
        self._max_sessions = self._config.get("max_sessions", 1000)

    def _purge_expired(self):
        now = datetime.now()
        expired = [sid for sid, s in self._sessions.items()
                    if (now - datetime.fromisoformat(s.get("created_at", now.isoformat()))).total_seconds() > self._ttl]
        for sid in expired:
            del self._sessions[sid]
        if len(self._sessions) > self._max_sessions:
            sorted_sessions = sorted(self._sessions.items(), key=lambda x: x[1].get("created_at", ""))
            for sid, _ in sorted_sessions[:len(sorted_sessions) - self._max_sessions]:
                del self._sessions[sid]

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        self._purge_expired()
        return self._sessions.get(session_id)

    def set(self, session_id: str, data: Dict[str, Any]):
        self._purge_expired()
        if len(self._sessions) >= self._max_sessions:
            oldest = min(self._sessions.keys(), key=lambda k: self._sessions[k].get("created_at", ""))
            del self._sessions[oldest]
        self._sessions[session_id] = data

    def __contains__(self, session_id: str) -> bool:
        self._purge_expired()
        return session_id in self._sessions

    def items(self):
        self._purge_expired()
        return self._sessions.items()


sessions = TTLSessionManager()


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
    """處理聊天請求 — 合併 Flow A (AngelaChatService) 完整管線 + Flow B HTTP"""
    logger.info(f"📩 [LIS] Raw message received: '{user_message}' from {origin} (Session: {session_id})")

    if not user_message or not user_message.strip():
        raise HTTPException(status_code=400, detail="訊號遺失：消息不能為空")

    _chat_cfg = _angela_cfg.get_authority("angela_core", {}).get("chat_flow", {}) if _angela_cfg else {}
    _max_len = _chat_cfg.get("max_message_length", 4000)
    _trunc_len = _chat_cfg.get("truncation_length", 1000)
    _http_timeout = _chat_cfg.get("http_timeout", 30.0)
    if len(user_message) > _max_len:
        logger.warning(f"🛡️ [LIS] Intercepted oversized input ({len(user_message)} chars)")
        user_message = user_message[:_trunc_len]

    if session_id not in sessions:
        sessions.set(session_id, {
            "created_at": datetime.now().isoformat(),
            "origin": origin,
            "user_name": user_name
        })

    try:
        from services.math_verifier import MathVerifier
        is_math = False
        try:
            digital_life = get_digital_life()
            matrix = digital_life.state_matrix if digital_life and hasattr(digital_life, "state_matrix") else None
            verifier = MathVerifier(state_matrix=matrix)
            is_math = verifier.is_math_message(user_message)
            if is_math:
                logger.info(f"🧮 [DualRail] Math task detected from {origin}")
                verification = await verifier.verify(user_message, user_name)
                if verification.response_text:
                    return _build_math_response(verification, matrix, user_message, session_id)
                is_math = False
        except Exception as math_err:
            logger.warning(f"⚠️ [DualRail] Math verification failed: {math_err}")
            is_math = False

        from services.chat_service import generate_angela_response
        response_text = await asyncio.wait_for(
            generate_angela_response(user_message, user_name),
            timeout=_http_timeout,
        )
        _flow_source = _chat_cfg.get("default_flow", "angela_chat_service")
        _trunc_msg = _chat_cfg.get("truncation_message", "...（截斷）")
        _schema_ver = _chat_cfg.get("response_schema_version", "2.0")
        return {
            "response_text": response_text,
            "source": _flow_source,
            "schema_version": _schema_ver,
            "truncation_message": _trunc_msg if len(user_message) > _max_len else "",
            "emotion": "happy",
            "emotion_confidence": 0.5,
            "emotion_intensity": 0.5,
            "session_id": session_id,
        }

    except asyncio.TimeoutError:
        logger.warning(f"LLM response timeout for message: {user_message[:50]}...")
        return {
            "response_text": "（我的大腦似乎遇到了一點點小干擾，能再說一次嗎？）",
            "source": "fallback-timeout",
            "emotion": "neutral",
            "emotion_confidence": 0.5,
            "emotion_intensity": 0.5,
            "session_id": session_id,
        }
    except Exception as e:
        logger.error(f"Error in _handle_chat_request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="internal server error")


def _build_math_response(verification, matrix, user_message: str, session_id: str) -> Dict[str, Any]:
    """建構數學驗證回應（抽出為獨立函數）"""
    if verification.needs_clarification:
        emotion, emotion_confidence, emotion_intensity = "confused", 0.7, 0.6
    elif not verification.matches:
        emotion, emotion_confidence, emotion_intensity = "surprised", 0.8, 0.7
    elif verification.extraction and verification.extraction.confidence >= 0.8:
        emotion, emotion_confidence, emotion_intensity = "happy", 0.9, 0.6
    else:
        emotion, emotion_confidence, emotion_intensity = "calm", 0.6, 0.4

    if matrix and verification.final_answer is not None:
        epsilon_conf = verification.extraction.confidence if verification.extraction else 0.5
        matrix.epsilon.values["certainty"] = min(1.0, 0.5 + epsilon_conf * 0.5)
        matrix.epsilon.values["complexity"] = min(1.0, len(user_message) / 50.0)
        if not verification.matches:
            matrix.epsilon.values["certainty"] *= 0.5
            matrix.gamma.values["surprise"] = min(1.0, matrix.gamma.values.get("surprise", 0.0) + 0.3)
        elif verification.needs_clarification:
            matrix.beta.values["confusion"] = min(1.0, matrix.beta.values.get("confusion", 0.0) + 0.4)
        matrix.apply_epsilon_influence()

    return {
        "response_text": verification.response_text,
        "source": "dual_rail",
        "emotion": emotion,
        "emotion_confidence": emotion_confidence,
        "emotion_intensity": emotion_intensity,
        "session_id": session_id,
    }


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
    sessions.set(session_id, {
        "created_at": datetime.now().isoformat(),
        "messages": [],
        "user_name": request.get("user_name", "User"),
    })
    return {"session_id": session_id, "message": "Welcome to Angela AI!"}


@api_v1_router.post("/session/{session_id}/send")
async def send_message(session_id: str, request: Dict[str, Any] = Body(...)):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    user_message = request.get("text", request.get("message", ""))
    session = sessions.get(session_id)
    messages = session.get("messages", [])
    messages.append(
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

    messages.append(
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
async def desktop_state():
    """返回當前桌面狀態"""
    state = get_desktop_interaction().get_desktop_state()
    return {"success": True, "state": {
        "total_files": getattr(state, "total_files", 0),
        "total_size": getattr(state, "total_size", 0),
        "categories": getattr(state, "categories", {}),
        "clutter_level": getattr(state, "clutter_level", 0.0),
    }}


@api_v1_router.post("/desktop/organize")
async def desktop_organize():
    """整理桌面文件"""
    ops = await get_desktop_interaction().organize_desktop()
    return {"success": True, "operations": [{
        "source": str(op.source) if hasattr(op, "source") else "",
        "destination": str(op.destination) if hasattr(op, "destination") else "",
        "category": op.category if hasattr(op, "category") else "",
    } for op in ops]}


@api_v1_router.post("/desktop/cleanup")
async def desktop_cleanup(days_old: int = 30):
    """清理桌面過期文件"""
    ops = await get_desktop_interaction().cleanup_desktop(days_old=days_old)
    return {"success": True, "operations": [{
        "source": str(op.source) if hasattr(op, "source") else "",
        "category": op.category if hasattr(op, "category") else "",
    } for op in ops]}


@api_v1_router.get("/actions/status")
async def actions_status():
    """返回動作執行器狀態"""
    stats = get_action_executor().get_execution_stats()
    return {"success": True, "stats": stats}


@api_v1_router.post("/actions/execute")
async def actions_execute(action_data: Dict[str, Any] = Body(...)):
    """提交並執行動作"""
    action_type = action_data.get("type", "general")
    parameters = action_data.get("parameters", {})
    priority = action_data.get("priority", "normal")
    result = await get_action_executor().handle_autonomous_action(action_type, parameters, priority)
    return {"success": True, "result": result}


@api_v1_router.post("/tactile/touch")
async def tactile_touch(touch_data: Dict[str, Any] = Body(...)):
    """模擬觸覺交互"""
    object_id = touch_data.get("object_id", "default")
    contact_point = touch_data.get("contact_point", {"body_part": "generic", "pressure": 0.5})
    origin = touch_data.get("origin", "System")
    result = await get_tactile_service().simulate_touch(object_id, contact_point, origin)
    return {"success": True, "feedback": result}


@api_v1_router.post("/brain/metrics")
async def brain_metrics():
    """返回完整腦指標（HSM, CDM, 生命強度等）"""
    digital_life = get_digital_life()
    summary = digital_life.get_formula_metrics()
    return {"success": True, "metrics": summary.get("formula_status", {}) if summary else {}}


@api_v1_router.post("/brain/dividend")
async def brain_dividend():
    """返回 CDM 經濟模型數據"""
    digital_life = get_digital_life()
    summary = digital_life.get_formula_metrics()
    if summary and "formula_status" in summary:
        return summary["formula_status"].get("cdm", {})
    return {"message": "Dividend data not available"}


# --- WebSocket Endpoint for Desktop App ---

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
    # Accept the WebSocket connection
    await websocket.accept()
    
    # DEBUG: Wrap the receive function to log ASGI events
    orig_receive = websocket._receive
    async def debug_receive():
        msg = await orig_receive()
        sys.stderr.write(f"[DEBUG WS endpoint] ASGI msg type={msg.get('type')} keys={list(msg.keys())}\n")
        if msg.get('type') == 'websocket.receive':
            text = msg.get('text')
            bytes_d = msg.get('bytes')
            if text:
                sys.stderr.write(f"[DEBUG WS endpoint] text content: {repr(text[:80])}\n")
            if bytes_d:
                sys.stderr.write(f"[DEBUG WS endpoint] bytes content: {repr(bytes_d[:80])}\n")
        return msg
    websocket._receive = debug_receive
    
    # Wait for initial handshake message with session_id
    try:
        raw_data = await asyncio.wait_for(websocket.receive_text(), timeout=10)
        logger.info(f"[WebSocket] Raw handshake data: {raw_data[:200]}")
        try:
            handshake = json.loads(raw_data)
        except json.JSONDecodeError as e:
            logger.warning(f"[WebSocket] Handshake is not valid JSON: {raw_data[:100]}")
            await websocket.close(code=4002, reason="Invalid handshake format")
            return
    except asyncio.TimeoutError:
        logger.warning("[WebSocket] Handshake timeout, closing connection")
        try:
            await websocket.close(code=4001, reason="Handshake timeout")
        except Exception:
            pass
        return
    except WebSocketDisconnect:
        logger.warning("[WebSocket] Client disconnected during handshake")
        return
    
    # Extract session info from handshake
    session_id = handshake.get("session_id") or str(uuid.uuid4())
    client_type = handshake.get("client_type", "desktop")
    client_version = handshake.get("client_version", "unknown")
    
    # Register with session_id
    session = await manager._sm.register(websocket, session_id, {
        "client_type": client_type,
        "client_version": client_version,
    }, single_device_mode=True)
    client_id = session.client_id
    
    logger.info(f"[WebSocket] Incoming connection - client_id: {client_id}, session_id: {session_id}, remote: {websocket.client}")
    msg_count = 0

    # After handshake, give time for messages to arrive
    logger.info(f"[WebSocket] Waiting for next message from {client_id}...")

    # Send initial connection confirmation with session info
    logger.info(f"[WebSocket] Sending 'connected' response to client_id: {client_id}")
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
    logger.info(f"[WebSocket] Entering message loop for client_id={client_id}, session_id={session_id}")
    msg_count = 0
    while True:
        msg_count += 1
        try:
            data = await asyncio.wait_for(
                websocket.receive_json(), timeout=manager.heartbeat_timeout
            )

            logger.info(f"[WebSocket] >>> Received message #{msg_count} from {client_id}: type={data.get('type')}, keys={list(data.keys())}")

            # Update heartbeat and sequence
            await manager._sm.update_heartbeat(client_id)
            sequence = manager._sm.increment_sequence(client_id)

            if data.get("type") in ["heartbeat", "ping"]:
                await websocket.send_json(
                    {
                        "type": (
                            "heartbeat_ack" if data.get("type") == "heartbeat" else "echo"
                        ),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            elif data.get("type") == "state_update":
                await manager.broadcast(
                    {
                        "type": "state_update",
                        "data": data.get("data", {}),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            elif data.get("type") == "tactile_event":
                tactile_data = data.get("data", {})
                tactile_service = get_tactile_service()
                res = await tactile_service.simulate_touch("user_hand", tactile_data, origin="Human")

                await manager.send_personal_message({
                    "type": "biological_feedback",
                    "status": res.get("status"),
                    "reflex": res.get("reflex"),
                    "intensity": res.get("feedback", {}).get("intensity")
                }, websocket)

            elif data.get("type") == "chat_message":
                user_message = data.get("data", {}).get("content", "")
                message_id = data.get("data", {}).get("message_id", "")
                user_name = data.get("data", {}).get("user_name", "朋友")

                logger.info(f"💬 [WS] Chat message from {client_id}: {user_message[:50]}...")
                logger.info(f"🔍 [WS] About to call _handle_chat_request for session_id={session_id}, user={user_name}")
                logger.info(f"🔍 [WS] Message payload: {data}")

                try:
                    chat_res = await _handle_chat_request(
                        user_message=user_message,
                        user_name=user_name,
                        history=[],
                        session_id=session_id,
                        origin="Human"
                    )

                    logger.info(f"🧠 [WS] _handle_chat_request returned: {chat_res.get('response_text', '')[:50]}...")

                    logger.info(f"🧠 [WS] About to call send_personal_message. Looking for websocket in sessions...")
                    for cid, sess in manager._sm._sessions.items():
                        logger.info(f"  Session {cid}: websocket={sess.websocket is not None}, state={sess.state}")
                    logger.info(f"  Target websocket: {websocket}")

                    await manager.send_personal_message(
                        {
                            "type": "chat_response",
                            "data": {
                                "message_id": message_id,
                                "content": chat_res["response_text"],
                                "sender": "angela",
                                "emotion": chat_res.get("emotion", "happy"),
                                "emotion_intensity": chat_res.get("emotion_intensity", 0.5),
                            },
                            "timestamp": datetime.now().isoformat(),
                        },
                        websocket,
                    )
                    logger.info(f"✅ [WS] Sent chat response to {client_id}")
                except Exception as chat_err:
                    logger.error(f"❌ [WS] Chat error for {client_id}: {chat_err}")
                    await manager.send_personal_message(
                        {
                            "type": "chat_response",
                            "data": {
                                "message_id": message_id,
                                "content": "（我的大腦似乎遇到了一點點小干擾，能再說一次嗎？）",
                                "sender": "angela",
                                "error": str(chat_err)
                            },
                            "timestamp": datetime.now().isoformat(),
                        },
                        websocket,
                    )

            else:
                await websocket.send_json(
                    {
                        "type": "echo",
                        "original": data,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        except asyncio.TimeoutError:
            logger.warning(f"[WebSocket] Heartbeat timeout for client: {client_id}")
            break

        except WebSocketDisconnect:
            logger.info(f"[WebSocket] Client disconnected: {client_id}")
            break

        except Exception as e:
            logger.error(f"[WebSocket] Message error for {client_id}: {e}")
            continue

    asyncio.create_task(manager.unregister(client_id))


from services.atlassian_api import atlassian_router
from services.api.state_matrix_api import state_matrix_router

# Include existing routers
app.include_router(api_v1_router)
app.include_router(atlassian_router)
app.include_router(state_matrix_router, prefix="/api/v1")


# ================================================================
# REPL Mode: uvicorn daemon + interactive chat loop
# ================================================================

def _run_uvicorn_in_thread():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")


async def _run_repl():
    import logging
    logging.disable(logging.WARNING)

    from services.chat_service import get_angela_chat_service

    print("[REPL] Angela brain initializing...")
    service = get_angela_chat_service()
    await service.initialize()
    print("[REPL] Angela ready! (exit/quit to stop)\n")
    print("[Hint] Type /help for commands, /state to view 8D matrix\n")

    loop = asyncio.get_event_loop()
    cmd_history: List[str] = []
    _last_intent: str = "general"

    while True:
        try:
            user_input = await loop.run_in_executor(None, lambda: input("\n\U0001F4AC  你: "))
        except (EOFError, KeyboardInterrupt):
            print("\n[REPL] Shutting down...")
            break

        text = user_input.strip()
        if text.lower() in ("exit", "quit"):
            print("[REPL] Good bye!")
            break
        if not text:
            continue

        if text.startswith("/") or text.startswith(":"):
            intent_name, response_text = _handle_repl_command(text, service, cmd_history)
            if response_text is not None:
                _last_intent = intent_name
                print(f"\U0001F4AD Angela [{intent_name}]: {response_text}")
                continue

        print("\U0001F4AD Angela: ", end="", flush=True)
        response = await service.generate_response(text)
        print(response)
        cmd_history.append(text)
        if len(cmd_history) > 100:
            cmd_history = cmd_history[-100:]


def _handle_repl_command(text: str, service: Any, history: List[str]) -> Tuple[str, Optional[str]]:
    """Parse and handle REPL commands. Returns (intent, response_text or None for passthrough)."""
    parts = text.lstrip("/:").split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd in ("h", "help"):
        return ("system", _build_help_text())

    if cmd in ("s", "state"):
        return ("system", _format_state_snapshot(service))

    if cmd in ("m", "mem", "memory"):
        return ("system", _format_memory_summary(service, args))

    if cmd in ("c", "clear"):
        return ("system", "\033[2J\033[H")

    if cmd in ("cfg", "config"):
        return ("system", _format_config_summary(service))

    if cmd in ("i", "intent"):
        return ("system", _format_intent_registry())

    if cmd in ("r", "route"):
        return ("system", _format_llm_routing(service))

    if cmd in ("tickle", "tkl"):
        return ("system", _handle_tickle_command(args))

    if cmd in ("model", "m") and args:
        return ("system", _handle_model_command(args, service))

    if cmd in ("drive", "gd", "cloud"):
        return ("system", _handle_drive_command(args))

    if cmd in ("hist", "history"):
        lines = [f"  {i+1}. {h[:60]}" for i, h in enumerate(history[-10:])]
        return ("system", f"Recent history:\n" + "\n".join(lines) if lines else "(empty)")

    return ("unknown", None)


def _build_help_text() -> str:
    return """Angela REPL Commands:
  /help, /h        — This help
  /state, /s        — 8D state matrix snapshot
  /memory, /m [q]   — Memory summary (optional search)
  /tickle, /tkl [part] [intensity] — Trigger tickle reflex
  /model [list|stats|switch <name>|auto] — LLM model management
  /drive [status|auth|list|search <q>|sync|analyze|logout] — Google Drive
  /clear, /c        — Clear screen
  /config, /cfg     — Current YAML config summary
  /intent, /i       — Intent registry overview
  /route, /r        — LLM routing status
  /history          — Recent command history
  /eval <expr>      — Evaluate Python expression
  exit/quit         — Stop REPL"""


def _format_state_snapshot(service: Any) -> str:
    try:
        sm = service.state_matrix
        lines = ["--- 8D State Matrix ---"]
        for axis in ("alpha", "beta", "gamma", "delta", "epsilon", "theta", "zeta"):
            ax = getattr(sm, axis, None)
            if ax and hasattr(ax, "values"):
                vals = list(ax.values.items())[:4]
                vals_str = ", ".join(f"{k}={v:.2f}" for k, v in vals)
                lines.append(f"  [{axis}] {vals_str}")
        eta = service.eta_state
        if eta:
            lines.append(f"  [eta] exec={eta.execution_count}, success={eta.success_rate:.1%}, drift={eta.structural_drift:.3f}")
        theta = sm.theta if hasattr(sm, "theta") else None
        if theta:
            lines.append(f"  [theta] novelty={theta.values.get('novelty',0):.2f}, correction={theta.values.get('correction_urge',0):.2f}")
        return "\n".join(lines)
    except Exception as e:
        return f"State unavailable: {e}"


def _format_memory_summary(service: Any, search: str) -> str:
    try:
        if hasattr(service, "memory_manager") and service.memory_manager:
            import asyncio
            loop = asyncio.new_event_loop()
            results = loop.run_until_complete(service.memory_manager.query_core_memory(
                keywords=[search] if search else ["experience"], limit=5
            ))
            loop.close()
            if not results:
                return "(no memories found)"
            lines = [f"Memory {i+1}: {r.get('content','')[:80]}" for i, r in enumerate(results)]
            return "\n".join(lines)
        return "(memory manager not initialized)"
    except Exception as e:
        return f"Memory error: {e}"


def _format_config_summary(service: Any) -> str:
    try:
        cfg = service._angela_config
        intents = list(cfg.get_intents().keys())
        thresholds = cfg.get_complexity_thresholds()
        llm = cfg.get_llm_config()
        providers = list(llm.get("providers", {}).keys()) if llm else []
        routing = cfg.get_routing_policy()
        chain = routing.get("fallback_chain", [])
        return f"Intents: {intents}\nComplexity thresholds: {thresholds}\nLLM providers: {providers}\nFallback chain: {chain}"
    except Exception as e:
        return f"Config error: {e}"


def _format_intent_registry() -> str:
    try:
        from core.intent_registry import IntentRegistry
        reg = IntentRegistry()
        lines = ["Intent Registry:"]
        for p in reg.patterns:
            lines.append(f"  {p.name} (pri={p.priority}): {p.keywords[:5]}")
        return "\n".join(lines)
    except Exception as e:
        return f"Intent registry error: {e}"


def _format_llm_routing(service: Any) -> str:
    try:
        from services.angela_llm_service import get_llm_service
        llm_svc = get_llm_service()
        backends = list(llm_svc.backends.keys()) if hasattr(llm_svc, "backends") else []
        active = getattr(llm_svc, "active_backend", None)
        chain = getattr(llm_svc, "_angela_fallback_chain", [])
        stats = getattr(llm_svc, "stats", {})
        return f"Backends: {backends}\nActive: {active}\nFallback chain: {chain}\nStats: {stats}"
    except Exception as e:
        return f"LLM routing error: {e}"


def _handle_tickle_command(args: str) -> str:
    """Handle /tickle command: /tickle <part> [intensity]"""
    parts = args.strip().split()
    if not parts:
        from core.autonomous.tickle_reflex_system import get_reflex_system
        reflex = get_reflex_system()
        all_parts = reflex.get_all_body_parts()
        sensitive = reflex.get_sensitive_parts()
        thresholds = reflex.get_intensity_thresholds()
        return (f"Tickle Reflex System\nParts: {all_parts}\nSensitive: {sensitive}\n"
                f"Thresholds: {thresholds}\n\nUsage: /tickle <part> [intensity 0-1]")

    body_part = parts[0]
    intensity = float(parts[1]) if len(parts) > 1 else 0.5

    import asyncio
    from core.autonomous.tickle_reflex_system import get_reflex_system

    reflex = get_reflex_system()

    async def run_tickles():
        return await reflex.trigger_tickles(
            body_part=body_part,
            intensity=intensity,
            duration_seconds=1.0,
            origin="REPL"
        )

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(run_tickles())
    finally:
        loop.close()

    phase1 = result.get("phase1", {})
    phase2 = result.get("phase2", {})
    anim = phase1.get("animation", {})
    return (f"[Tickle] {body_part} intensity={intensity:.1f}\n"
            f"Level: {result.get('intensity_level', '?')}\n"
            f"Output: {phase1.get('output_mode', '?')}\n"
            f"Animation: {anim.get('motion_name', '?')} ({anim.get('duration_ms', 0)}ms)\n"
            f"Expression: {anim.get('expression', '?')}\n"
            f"Phase2 triggered: {phase2.get('triggered', False)}\n"
            f"Elapsed: {result.get('elapsed_ms', 0)}ms")


def _handle_model_command(args: str, service: Any) -> str:
    """Handle /model command: /model [list|stats|switch <name>|auto]"""
    parts = args.strip().split(maxsplit=1)
    subcmd = parts[0].lower() if parts else "list"
    subarg = parts[1] if len(parts) > 1 else ""

    try:
        from services.angela_llm_service import get_llm_service
        llm_svc = get_llm_service()

        if subcmd in ("list", "ls", "l"):
            backends = list(llm_svc.backends.keys()) if hasattr(llm_svc, "backends") else []
            active = getattr(llm_svc, "active_backend", None)
            return f"Available models: {backends}\nActive: {active}"

        if subcmd in ("stats", "s"):
            stats = getattr(llm_svc, "stats", {})
            return f"LLM Stats: {stats}"

        if subcmd in ("switch", "sw", "set"):
            if not subarg:
                return "Usage: /model switch <name>\nAvailable: " + str(list(getattr(llm_svc, "backends", {}).keys()))
            backend_key = subarg.strip()
            for btype, bobj in getattr(llm_svc, "backends", {}).items():
                if backend_key.lower() in btype.name.lower():
                    llm_svc.active_backend = bobj
                    return f"[OK] Switched to {btype.name}"
            return f"[FAIL] Model '{backend_key}' not found"

        if subcmd in ("auto", "a"):
            routing = getattr(llm_svc, "_angela_routing", {})
            return f"Auto routing enabled. Policy: {routing}"

        return f"Unknown subcommand: {subcmd}\nUsage: /model [list|stats|switch <name>|auto]"

    except Exception as e:
        return f"Model command error: {e}"


def _handle_drive_command(args: str) -> str:
    """Handle /drive command: /drive [status|auth|url|list|search <q>|sync|analyze|logout]"""
    import httpx
    from core.config_loader import get_angela_config

    parts = args.strip().split(maxsplit=1)
    subcmd = parts[0].lower() if parts else "status"
    subarg = parts[1] if len(parts) > 1 else ""

    cfg = get_angela_config()
    ops = cfg.get_drive_all_operations()

    def resolve_op(cmd: str) -> Optional[str]:
        for op_name, op_cfg in ops.items():
            if cmd in op_cfg.get("aliases", []):
                return op_name
        return None

    op = resolve_op(subcmd)
    base = "http://127.0.0.1:8000/api/v1/drive"

    try:
        if op == "status" or subcmd in ("status", "s"):
            resp = httpx.get(f"{base}/status", timeout=10)
            d = resp.json()
            auth = d.get("authenticated", False)
            quota = d.get("quota", {})
            lines = [
                f"Google Drive: {'✅ 已認證' if auth else '❌ 未認證'}",
                f"  用戶: {quota.get('user', 'N/A')}",
                f"  已用: {quota.get('used', 'N/A')} / {quota.get('total', 'N/A')}",
                f"  狀態: {d.get('status', 'unknown')}",
            ]
            return "\n".join(lines)

        if op == "auth" or (subcmd in ("auth", "a") and subarg in ("", "url")):
            resp = httpx.get(f"{base}/auth/url", timeout=10)
            url = resp.json().get("url", "")
            return f"授權 URL：\n{url}\n\n請用瀏覽器打開這個連結，授權後把回傳的 code 貼給我。"

        if op == "auth" or subcmd in ("callback", "cb"):
            resp = httpx.post(f"{base}/auth/callback", json={"code": subarg}, timeout=15)
            if resp.status_code == 200:
                return "✅ Google Drive 認證成功！"
            return f"❌ 認證失敗：{resp.text}"

        if op == "logout" or subcmd in ("logout", "out"):
            httpx.post(f"{base}/auth/logout", timeout=5)
            return "✅ 已登出 Google Drive。"

        if op == "list" or subcmd in ("list", "ls", "l"):
            n = int(subarg) if subarg.isdigit() else 10
            resp = httpx.get(f"{base}/files?page_size={n}", timeout=15)
            files = resp.json().get("files", [])
            if not files:
                return "📂 雲端硬碟是空的。"
            lines = [f"📄 {f.get('name')} ({f.get('mimeType', '').split('.')[-1]})" for f in files]
            return "📂 Google Drive 檔案列表：\n" + "\n".join(lines)

        if op == "list" or subcmd in ("search", "q"):
            resp = httpx.post(f"{base}/files/search", json={"query": subarg, "page_size": 10}, timeout=15)
            files = resp.json().get("files", [])
            if not files:
                return f"🔍 找不到包含「{subarg}」的檔案。"
            lines = [f"📄 {f.get('name')} ({f.get('mimeType', '').split('.')[-1]})" for f in files]
            return f"🔍 搜尋「{subarg}」結果：\n" + "\n".join(lines)

        if op == "sync" or subcmd in ("sync", "download", "dl"):
            resp = httpx.get(f"{base}/files?page_size=10", timeout=15)
            files = resp.json().get("files", [])
            if not files:
                return "沒有找到可以同步的檔案。"
            resp = httpx.post(f"{base}/files/sync", json={"file_ids": [f["id"] for f in files[:5]]}, timeout=60)
            r = resp.json()
            return (f"✅ 同步完成！下載了 {r.get('synced', 0)} 個檔案，"
                    f"跳過 {r.get('skipped', 0)} 個（已存在），"
                    f"存入記憶 {r.get('memorized_count', 0)} 個。")

        if op == "analyze" or subcmd in ("analyze", "ana"):
            resp = httpx.post(f"{base}/analyze", json={"limit": 3}, timeout=60)
            r = resp.json()
            _trunc = 1500
            try:
                from core.config_loader import get_angela_config
                _cfg = get_angela_config()
                _trunc = _cfg.get_authority("angela_core", {}).get("state_constants", {}).get("file_content_truncation", 1500)
            except Exception:
                pass
            return f"📊 分析結果：\n{r.get('analysis', '無法分析')[:_trunc]}"

        return (
            "Google Drive 命令用法：\n"
            "  /drive status     — 連接狀態\n"
            "  /drive auth       — 取得授權 URL\n"
            "  /drive callback <code>  — 用授權碼完成認證\n"
            "  /drive list [n]   — 列出檔案（預設10個）\n"
            "  /drive search <q>  — 搜尋檔案\n"
            "  /drive sync        — 下載並存入記憶\n"
            "  /drive analyze     — 分析檔案內容\n"
            "  /drive logout      — 登出"
        )

    except httpx.ConnectError:
        return "❌ 無法連接後端，請先啟動伺服器（launch_angela.bat --repl）"
    except Exception as e:
        return f"❌ Drive 錯誤：{e}"


if __name__ == "__main__":
    import sys, threading, time

    if "--repl" in sys.argv:
        server_thread = threading.Thread(target=_run_uvicorn_in_thread, daemon=True)
        server_thread.start()
        print("[REPL] Backend starting on http://127.0.0.1:8000 ...")
        time.sleep(3)
        asyncio.run(_run_repl())
    else:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
