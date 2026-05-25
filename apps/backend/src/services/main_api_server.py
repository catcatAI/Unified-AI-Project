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
import asyncio
import httpx
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


def _ensure_src_in_path():
    """Ensure src directory is in Python path (called once at module init)."""
    _backend_dir = Path(__file__).parent.parent.parent
    _src_path = str(_backend_dir / "src")
    if _src_path not in sys.path:
        sys.path.insert(0, _src_path)


def _init_logging():
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

from fastapi import (
    FastAPI,
    Depends,
    Body,
)
from services.angela_llm_service import get_llm_service

from api.router import router as api_v1_router

app = FastAPI(
    title="Angela AI API",
    description="Backend API for Angela AI Desktop Companion",
    version="6.0.4",
)

from core.autonomous.desktop_interaction import DesktopInteraction
from core.autonomous.action_executor import ActionExecutor
from core.autonomous.digital_life_integrator import DigitalLifeIntegrator

from api.lifespan import (
    lifespan,
    setup_middleware,
    get_metabolic_heartbeat,
    get_desktop_interaction,
    get_action_executor,
    get_vision_service,
    get_audio_service,
    get_tactile_service,
    get_digital_life,
    get_economy_manager,
)

from api.routes.chat_routes import router as chat_router

setup_middleware(app)
app.router.lifespan_context = lifespan

# --- Desktop Interaction API ---


@api_v1_router.get("/desktop/state")
async def desktop_state(
    interaction: DesktopInteraction = Depends(get_desktop_interaction),
):
    """返回當前桌面狀態"""
    state = interaction.get_desktop_state()
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
async def actions_status(
    executor: ActionExecutor = Depends(get_action_executor),
):
    """返回動作執行器狀態"""
    stats = executor.get_execution_stats()
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
async def brain_metrics(
    digital_life: DigitalLifeIntegrator = Depends(get_digital_life),
):
    """返回完整腦指標（HSM, CDM, 生命強度等）"""
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


from services.websocket_manager import websocket_handler, broadcast_state_updates, manager as ws_manager

app.websocket("/ws")(websocket_handler)

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
    from api.lifespan import _get_chat_service

    import logging
    logging.disable(logging.WARNING)

    print("[REPL] Angela brain initializing...")
    service = await _get_chat_service()
    await service.initialize()
    print("[REPL] Angela ready! (exit/quit to stop)\n")
    print("[Hint] Type /help for commands, /state to view 8D matrix\n")

    loop = asyncio.get_event_loop()
    cmd_history: List[str] = []
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
