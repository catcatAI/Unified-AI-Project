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
# - GET /api/v1/ops/status - 运维状态
# - POST /api/v1/chat/unified - 统一聊天接口 (集成 LLM)
# - WebSocket /ws - 实时双向通信
# - WebSocket /multimodal/stream - 多模态流
#
# 集成服务:
# - VisionService: 视觉处理
# - AudioService: 音频处理
# - ChatService: 对话生成
# - AngelaLLMService: LLM 服务 (Ollama/GPT/Gemini)
# - DigitalLifeIntegrator: 数字生命集成
# - BrainBridgeService: 大脑桥接服务
# - CausalReasoningEngine: 因果推理引擎
# - PluginSystem: 插件系统
#
# =============================================================================

import logging
import sys
from pathlib import Path
from typing import Any, Dict

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
        "python-dotenv not installed, environment variables will not be loaded from .env file",
        exc_info=True,
    )

from api.router import router as api_v1_router  # noqa: E402
from fastapi import FastAPI  # noqa: E402
# get_llm_service is imported lazily by ChatService during lifespan startup

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


from services.websocket_manager import websocket_handler

app.websocket("/ws")(websocket_handler)

from services.multimodal_ws_handler import multimodal_stream_handler  # noqa: E402

app.websocket("/multimodal/stream")(multimodal_stream_handler)

from services.atlassian_api import atlassian_router  # noqa: E402

# Include existing routers
# NOTE: state_matrix_router is already included via api_v1_router (see api/router.py).
# DO NOT duplicate it here — FastAPI would register duplicate routes.
app.include_router(api_v1_router)
app.include_router(atlassian_router)


@app.get("/health", tags=["health"])
async def health() -> Dict[str, Any]:
    """Lightweight root liveness probe (documented module contract).

    Detailed subsystem health lives under ``/api/v1/ops/health``; this root
    endpoint exists for load balancers / uptime checks that expect ``/health``.
    """
    return {"status": "healthy", "service": "angela-ai", "version": app.version}


if __name__ == "__main__":

    if "--repl" in sys.argv:
        from cli.repl import run_repl_mode

        run_repl_mode()
    else:
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=8000)
