"""
Angela AI Backend API Server v7.5.0-dev
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

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

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
    logger.warning("python-dotenv not installed, skipping .env loading")
except Exception:
    # broad except acceptable: startup env loading is unpredictable; may fail for many reasons
    logger.warning("Failed to load .env file", exc_info=True)


def _ensure_src_in_path() -> None:
    """Ensure src directory is in Python path (called once at module init)."""
    _backend_dir = Path(__file__).parent.parent.parent
    _src_path = str(_backend_dir / "src")
    if _src_path not in sys.path:
        sys.path.insert(0, _src_path)


def _init_logging() -> None:
    """Initialize the unified logging system (called once at module init)."""
    from core.logging.setup import setup_logging
    setup_logging(level=logging.INFO, log_file="angela_ai.log")


# Module-level initialization
_ensure_src_in_path()
_init_logging()

# 現在可以安全地記錄環境變量加載狀態
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
        , exc_info=True
    )

# ========== 修复：系统指标管理器 ==========
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available, system metrics will use fallback values", exc_info=True)


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

        def compute() -> str:
            return psutil.cpu_percent(interval=0.1)

        return self._get_cached_or_compute("cpu_percent", compute)

    def get_memory_percent(self) -> float:
        """获取内存使用率（统一数据源）"""
        if not PSUTIL_AVAILABLE:
            return 0.0

        def compute() -> str:
            return psutil.virtual_memory().percent

        return self._get_cached_or_compute("memory_percent", compute)

    def get_disk_percent(self) -> float:
        """获取磁盘使用率（统一数据源）"""
        if not PSUTIL_AVAILABLE:
            return 0.0

        def compute() -> str:
            return psutil.disk_usage("/").percent

        return self._get_cached_or_compute("disk_percent", compute)

    def get_all_metrics(self) -> Dict[str, float]:
        """获取所有系统指标"""
        return {
            "cpu_percent": self.get_cpu_percent(),
            "memory_percent": self.get_memory_percent(),
            "disk_percent": self.get_disk_percent(),
        }

    def clear_cache(self) -> None:
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

    def cache_message(self, message_id: str, message_data: Dict[str, Any]) -> None:
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

    def record_state(self, state_id: str, state_data: Dict[str, Any]) -> None:
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

from api.router import router as api_v1_router  # noqa: E402
from fastapi import (  # noqa: E402
    Body,
    Depends,
    FastAPI,
)
from services.angela_llm_service import get_llm_service  # noqa: E402

app = FastAPI(
    title="Angela AI API",
    description="Backend API for Angela AI Desktop Companion",
    version="7.5.0-dev",
)

from api.lifespan import (  # noqa: E402
    lifespan,
    setup_middleware,
)

setup_middleware(app)
app.router.lifespan_context = lifespan


from services.websocket_manager import broadcast_state_updates
from services.websocket_manager import manager as ws_manager  # noqa: E402
from services.websocket_manager import websocket_handler

app.websocket("/ws")(websocket_handler)

from services.multimodal_ws_handler import multimodal_stream_handler  # noqa: E402

app.websocket("/multimodal/stream")(multimodal_stream_handler)

from services.api.state_matrix_api import state_matrix_router  # noqa: E402
from services.atlassian_api import atlassian_router  # noqa: E402

# Include existing routers
app.include_router(api_v1_router)
app.include_router(atlassian_router)
app.include_router(state_matrix_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health() -> Dict[str, Any]:
    """Lightweight root liveness probe (documented module contract).

    Detailed subsystem health lives under ``/api/v1/ops/health``; this root
    endpoint exists for load balancers / uptime checks that expect ``/health``.
    """
    return {"status": "healthy", "service": "angela-ai", "version": app.version}


class MainApiServer:
    """Stub class for legacy integration test compatibility.

    Provides is_connected, reconnect, and queue_request methods
    for use in error recovery tests (test_error_recovery.py).
    """

    def __init__(self) -> None:
        self._connected = False
        self._request_queue: List[Dict[str, Any]] = []
        self._logger = logging.getLogger(f"{__name__}.MainApiServer")

    async def is_connected(self) -> bool:
        """Check if the API server is connected to external services."""
        return self._connected

    async def reconnect(self) -> Dict[str, Any]:
        """Attempt to reconnect the API server to external services."""
        self._connected = True
        self._logger.info("MainApiServer reconnected successfully")
        return {"reconnected": True, "attempts": 1}

    async def queue_request(self, request: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Queue a request for deferred processing.

        Args:
            request: The request data to queue. If None, just returns
                     the current queue position.

        Returns:
            Dict with queue status and position.
        """
        if request:
            self._request_queue.append(request)
        return {"queued": True, "queue_position": len(self._request_queue)}


if __name__ == "__main__":
    import sys
    if "--repl" in sys.argv:
        from cli.repl import run_repl_mode
        run_repl_mode()
    else:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
