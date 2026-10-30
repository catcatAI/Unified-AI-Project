"""
ANGELA-MATRIX: [L4-L5] [βδ] [A] [L3]
Application lifecycle management — startup/shutdown + service factories.
Extracted from main_api_server.py (A3 god module split).
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Plugin imports are lazy inside lifespan() to avoid slow core package import

logger = logging.getLogger(__name__)

_STANDARD_HOOKS = [
    "on_message",
    "on_response",
    "on_state_change",
    "on_bio_event",
    "on_tick",
]

# Lazy-loaded service instances
_chat_service_instance = None
_digital_life_instance = None
_abc_key_manager_instance = None
_bio_integrator_instance = None
_agent_manager_instance = None
_crisis_system_instance = None
_causal_reasoning_instance = None
_level5_asi_instance = None
_training_coordinator_instance = None
_lifecycle_instance = None
_heartbeat_instance = None
_brain_bridge_instance = None
_proactive_instance = None


# --- Config (lazy proxy) ---
class _LazyAngelaConfig:
    """Lazy-loaded proxy for AngelaConfig that avoids heavy imports at module level."""

    def __init__(self):
        self._cfg = None
        self._loaded = False

    def _ensure(self):
        if not self._loaded:
            self._loaded = True
            try:
                from core.config_loader import get_angela_config

                self._cfg = get_angela_config()
            except Exception as e:
                logger.warning(f"AngelaConfig not available: {e}")

    def get_authority(self, section, default=None):
        self._ensure()
        if self._cfg is None:
            return default or {}
        return self._cfg.get_authority(section, default)

    def __bool__(self):
        self._ensure()
        return self._cfg is not None

    def __getattr__(self, name):
        self._ensure()
        if self._cfg is None:
            raise AttributeError("AngelaConfig not loaded")
        return getattr(self._cfg, name)


_angela_cfg = _LazyAngelaConfig()


# --- Service factories ---


async def _get_chat_service():
    """Get or create the chat service singleton."""
    global _chat_service_instance
    if _chat_service_instance is None:
        try:
            from services.chat_service import ChatService

            _chat_service_instance = ChatService()
            await _chat_service_instance.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize chat service: {e}", exc_info=True)
            # Don't cache the broken instance: the next call retries instead of
            # serving every future request from a half-initialized singleton.
            _chat_service_instance = None
            raise
    return _chat_service_instance


def get_abc_key_manager():
    """Get or create the ABC key manager singleton."""
    global _abc_key_manager_instance
    if _abc_key_manager_instance is None:
        try:
            from core.system.security_monitor import ABCKeyManager

            _abc_key_manager_instance = ABCKeyManager()
        except Exception as e:
            logger.warning(f"ABCKeyManager not available: {e}", exc_info=True)
            raise
    return _abc_key_manager_instance


def _make_user_monitor(user_id: str):
    """AI 側 UserMonitor 的注入工廠（契約 I8：core/life 不得出站 import ai.*）。"""
    from ai.lifecycle.user_monitor import UserMonitor

    return UserMonitor(user_id)


async def _make_llm_decision_loop(dli):
    """AI 側 LLM 決策迴圈的注入工廠（I8：HAM／LLM 服務在 AI 側組裝）。

    對應 DLI 原本內建的組裝（llm_service + HAMMemoryManager +
    LLMDecisionLoop）—— 依賴反轉後這裡是唯一組裝點，回傳**未啟動**的
    迴圈（``start()`` 仍由 DLI 的 ``_init_cognition`` 呼叫）。
    """
    from ai.lifecycle.llm_decision_loop import LLMDecisionLoop
    from ai.memory.ham_memory.ham_manager import HAMMemoryManager
    from services.angela_llm_service import get_llm_service

    llm_service = await get_llm_service()
    memory_manager = HAMMemoryManager(core_storage_filename="angela_conversations.json")
    return LLMDecisionLoop(
        llm_service=llm_service,
        state_manager=dli.state_matrix,
        memory_manager=memory_manager,
        user_monitor=dli.user_monitor,
        broadcast_callback=dli.broadcast_callback,
    )


def get_digital_life():
    """Get or create the digital life integrator singleton."""
    global _digital_life_instance
    if _digital_life_instance is None:
        try:
            from core.life.digital_life_integrator import DigitalLifeIntegrator

            # 三個 AI 側依賴全部注入（I8：core/life 執行期禁 import
            # ai./services./api./integrations.，門禁 al.boundary_outbound）。
            # lifecycle_provider 以函式傳遞 —— 呼叫時才解析，DLI 初始化時
            # 拿到的一定是共享單例（split-brain 修法不變）。
            _digital_life_instance = DigitalLifeIntegrator(
                user_monitor_factory=_make_user_monitor,
                llm_decision_loop_factory=_make_llm_decision_loop,
                lifecycle_provider=get_lifecycle,
            )
        except Exception as e:
            logger.warning(f"DigitalLifeIntegrator not available: {e}", exc_info=True)
            raise
    return _digital_life_instance


_desktop_interaction_instance = None


def get_desktop_interaction():
    """Lazy import for desktop interaction (cached singleton)."""
    global _desktop_interaction_instance
    if _desktop_interaction_instance is not None:
        return _desktop_interaction_instance
    try:
        from core.engine.desktop_interaction import DesktopInteraction

        _desktop_interaction_instance = DesktopInteraction()
        return _desktop_interaction_instance
    except Exception as e:
        logger.warning(f"DesktopInteraction not available: {e}")
        return None


_browser_controller_instance = None


def get_browser_controller():
    """Lazy import for browser controller (cached singleton)."""
    global _browser_controller_instance
    if _browser_controller_instance is not None:
        return _browser_controller_instance
    try:
        from core.engine.browser_controller import BrowserController

        _browser_controller_instance = BrowserController()
        return _browser_controller_instance
    except Exception as e:
        logger.warning(f"BrowserController not available: {e}")
        return None


_action_executor_instance = None


def get_action_executor():
    """Lazy import for action executor (cached singleton)."""
    global _action_executor_instance
    if _action_executor_instance is not None:
        return _action_executor_instance
    try:
        from core.engine.action_executor import ActionExecutor

        _action_executor_instance = ActionExecutor()
        return _action_executor_instance
    except Exception as e:
        logger.warning(f"ActionExecutor not available: {e}")
        return None


_agent_workspace_instance = None


def _get_registered_eda_agent():
    manager = get_agent_manager()
    if manager is None:
        return None
    registered = manager.get_agent("eda_agent")
    if registered is None:
        return None
    return getattr(registered, "agent", registered)


def get_agent_workspace():
    """統一上下文門面：全域上下文樹（五類上下文）＋應用會話閉環＋學習日誌。

    上下文系統是整個專案的核心（ai/context/），樹狀治理覆蓋工具／模型／
    代理／對話／記憶全部上下文，而非只有代理工作區。
    """
    global _agent_workspace_instance
    if _agent_workspace_instance is not None:
        return _agent_workspace_instance
    try:
        from services.agent_workspace import build_default_workspace
        from services.agent_workspace.global_tree import (
            GlobalContextProviders,
            GlobalContextTree,
            UnifiedWorkspace,
        )

        ws = build_default_workspace(
            desktop_interaction=get_desktop_interaction(),
            eda_agent_provider=_get_registered_eda_agent,
        )
        _agent_workspace_instance = UnifiedWorkspace(
            ws,
            GlobalContextTree(
                GlobalContextProviders(
                    workspace=ws,
                    agent_manager=get_agent_manager(),
                )
            ),
        )
        return _agent_workspace_instance
    except Exception as e:
        logger.warning(f"AgentWorkspace not available: {e}")
        return None


_vision_service_instance = None


def get_vision_service():
    global _vision_service_instance
    if _vision_service_instance is None:
        try:
            from services.vision_service import VisionService

            _vision_service_instance = VisionService()
        except Exception as e:
            logger.warning(f"VisionService not available: {e}")
            return None
    return _vision_service_instance


_tactile_service_instance = None


def get_tactile_service():
    """TactileService removed — all callers handle None gracefully."""
    return None


def get_agent_manager():
    """Get the AgentManager singleton (initialized during lifespan startup)."""
    return _agent_manager_instance


def get_crisis_system():
    """Get the CrisisSystem singleton (initialized during lifespan startup)."""
    return _crisis_system_instance


def get_causal_reasoning():
    """Get the CausalReasoningEngine singleton (initialized during lifespan startup)."""
    return _causal_reasoning_instance


def get_emotion_system():
    """Get or create the shared EmotionSystem singleton.

    Resolved through the backbone registry under the same module key that
    ``chat_routes._get_emotion_system()`` uses, so the last-resort branch of
    ``ai.unified_engine.semantic_qa._emotion_threshold_adjustment()`` observes
    the instance chat_routes actually applies influence to. That branch probes
    ``api.lifespan`` for this name; before it existed the probe always returned
    None and the EmotionSystem fallback could never fire.
    """
    try:
        from core.backbone import get_backbone

        bb = get_backbone()
        cached = bb.get_module("chat.emotion_system")
        if cached is not None:
            return cached
        from ai.alignment.emotion_system import EmotionSystem

        instance = EmotionSystem()
        # Adopt the emotion state another process wrote (the game agent runs
        # in its own process; without this the two never agree on how the
        # user feels).
        try:
            instance.adopt_shared_state()
        except Exception as exc:
            logger.debug("Shared emotion state not adopted: %s", exc)
        bb.register_module("chat.emotion_system", instance)
        return instance
    except Exception as e:
        logger.warning(f"[EmotionSystem] Unavailable: {e}")
        return None


def get_proactive():
    """Get the ProactiveInteractionSystem singleton (initialized during lifespan startup)."""
    return _proactive_instance


async def get_level5_asi():
    """Get or create the Level5ASISystem singleton (lazy initialization — heavy system)."""
    global _level5_asi_instance
    if _level5_asi_instance is None:
        try:
            from ai.level5_asi_system import Level5ASISystem

            _level5_asi_instance = Level5ASISystem()
            await _level5_asi_instance.initialize()
            await _level5_asi_instance.start()
            logger.info("[Level5ASI] Lazy-initialized and started — alignment gate available")
        except Exception as e:
            logger.warning(f"[Level5ASI] Initialization failed: {e}")
            _level5_asi_instance = None
    return _level5_asi_instance


def setup_middleware(app: FastAPI) -> None:
    """Configure application middleware."""
    from core.api.versioning import APIVersionMiddleware

    try:
        from core.system.config.network_defaults import get_cors_origins

        _origins = get_cors_origins()
    except Exception as e:
        logger.warning(f"CORS config failed, falling back to wildcard: {e}", exc_info=True)
        _origins = ["*"]
    # Browsers reject wildcard with credentials; fall back to no-credentials
    # when wildcard is in use so the header is spec-compliant.
    _allow_credentials = "*" not in _origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(APIVersionMiddleware)
    # 安全層掛載（§11.3 #10 步驟 C5）：AuthMiddleware + ContentFilter 下層入口。
    # enable_auth 預設關閉（公開模式），不破壞現有行為；內容過濾預設啟用。
    try:
        from core.backbone.security import SecurityFilterMiddleware, build_security_layer

        layer = build_security_layer(enable_auth=False)
        app.add_middleware(SecurityFilterMiddleware, layer=layer)
    except Exception:
        logger.warning(
            "[Security] SecurityFilterMiddleware failed to mount; continuing without it",
            exc_info=True,
        )


_metrics_handler = None


def _init_plugins():
    """Initialize plugin system with built-in handlers."""
    from core.plugin.handlers.audit_logger import AuditLoggerHandler
    from core.plugin.handlers.message_logger import MessageLoggerHandler
    from core.plugin.handlers.metrics_collector import MetricsCollectorHandler
    from core.plugin.plugin_manager import plugin_manager

    plugin_manager.register_plugin("core", "1.0.0", "Core built-in plugin handlers")

    msg_handler = MessageLoggerHandler()
    global _metrics_handler
    _metrics_handler = MetricsCollectorHandler()
    audit_handler = AuditLoggerHandler()

    plugin_manager.add_handler("core", "on_message", msg_handler)
    for hook in _STANDARD_HOOKS:
        plugin_manager.add_handler("core", hook, _metrics_handler.handler_for(hook))
        plugin_manager.add_handler("core", hook, audit_handler.handler_for(hook))

    stats = plugin_manager.get_stats()
    logger.info(
        "[Plugin] Initialized: %d hooks, %d handlers, %d plugins",
        stats["hook_registry"]["hook_count"],
        stats["hook_registry"]["handler_count"],
        stats["plugin_count"],
    )


async def _try_start_bio():
    """Initialize BiologicalIntegrator if available."""
    global _bio_integrator_instance
    try:
        from core.bio.biological_integrator import BiologicalIntegrator

        _bio_integrator_instance = BiologicalIntegrator()
        await _bio_integrator_instance.initialize()
        logger.info("[Bio] BiologicalIntegrator initialized and integration loop started")
    except Exception as e:
        logger.warning(f"[Bio] BiologicalIntegrator initialization failed: {e}")


async def _try_start_brain_bridge():
    """Start BrainBridgeService if DLI is available.

    BrainBridgeService writes data/brain_status.json which prompt_builder's
    get_biological_state() consumes as its Priority 2 fallback. Without this
    startup hook, the file is never produced and the consumer always misses.
    """
    global _brain_bridge_instance
    try:
        from services.brain_bridge_service import BrainBridgeService

        dli = get_digital_life()
        if not dli:
            logger.warning("[BrainBridge] DLI not available — bridge not started")
            return
        _brain_bridge_instance = BrainBridgeService(dli)
        await _brain_bridge_instance.start()
        logger.info("[BrainBridge] BrainBridgeService started")
    except Exception as e:
        logger.warning(f"[BrainBridge] Startup failed: {e}")


async def _try_start_digital_life():
    """Initialize the shared DigitalLifeIntegrator singleton.

    ``get_digital_life()`` only constructs the object; without ``initialize()``
    the core subsystems it owns (LLMDecisionLoop, AutonomousLifeCycle, the
    life-cycle state machine, and the health-check loop that updates the
    modality gateway) never start. Chat routes read ``intent_manager`` /
    ``state_matrix`` / ``modality_gateway`` off the singleton, and
    ``_try_wire_dli_broadcast()`` expects ``llm_decision_loop`` to exist — both
    silently degrade when initialization is skipped. ``initialize()`` is fully
    fault-tolerant (each step degrades gracefully), so this never blocks startup.
    """
    try:
        dli = get_digital_life()
        if not dli:
            logger.warning("[DLI] Not available — digital life not started")
            return
        if not getattr(dli, "is_initialized", False):
            await dli.initialize()
            logger.info("[DLI] DigitalLifeIntegrator initialized (life cycle state machine online)")
    except Exception as e:
        logger.warning(f"[DLI] Initialization failed: {e}")


async def _try_start_agents():
    """Initialize AgentManager and register specialized agents."""
    global _agent_manager_instance
    try:
        from ai.agents.agent_adapter import register_specialized_agents
        from ai.agents.agent_manager import AgentManager

        _agent_manager_instance = AgentManager(enable_router=False)
        count = register_specialized_agents(
            _agent_manager_instance,
            training_coordinator=get_training_coordinator(),
        )
        logger.info(f"[AgentManager] Initialized with {count} specialized agents")
    except Exception as e:
        logger.warning(f"[AgentManager] Initialization failed: {e}")


def _try_init_crisis():
    """Initialize CrisisSystem for user safety monitoring."""
    global _crisis_system_instance
    try:
        from ai.crisis.crisis_system import CrisisSystem

        _crisis_system_instance = CrisisSystem()
        logger.info("[CrisisSystem] Initialized — monitoring for crisis indicators")
    except Exception as e:
        logger.warning(f"[CrisisSystem] Initialization failed: {e}")


def get_lifecycle():
    """Get or create the shared AutonomousLifeCycle singleton.

    This is the single source of truth for lifecycle state, used by both
    chat_routes.py (behavioral adjustment injection) and prompt_builder.py
    (autonomous decisions text injection). Having a single shared instance
    ensures the prompt text reflects the actual running lifecycle state.
    """
    global _lifecycle_instance
    if _lifecycle_instance is None:
        try:
            from core.life.autonomous_life_cycle import AutonomousLifeCycle

            _lifecycle_instance = AutonomousLifeCycle()
            logger.info("[LifeCycle] Shared singleton initialized")
        except Exception as e:
            logger.warning(f"[LifeCycle] Initialization failed: {e}")
            raise
    return _lifecycle_instance


def get_metabolic_heartbeat():
    """Get or create the MetabolicHeartbeat singleton."""
    global _heartbeat_instance
    if _heartbeat_instance is None:
        try:
            from core.life.heartbeat import MetabolicHeartbeat

            _heartbeat_instance = MetabolicHeartbeat()
            logger.info("[Heartbeat] Shared singleton initialized")
        except Exception as e:
            logger.warning(f"[Heartbeat] Initialization failed: {e}")
            raise
    return _heartbeat_instance


def get_training_coordinator():
    """Get or create the TrainingCoordinator singleton."""
    global _training_coordinator_instance
    if _training_coordinator_instance is None:
        try:
            from ai.core.training_coordinator import TrainingCoordinator

            _training_coordinator_instance = TrainingCoordinator(
                max_examples_per_domain=100,
                max_hashes_per_domain=10000,
            )
            state_path = Path("data/training_coordinator.json")
            if state_path.is_file():
                _training_coordinator_instance.load(str(state_path))
            logger.info("[TrainingCoordinator] Initialized — domain training orchestration ready")
        except Exception as e:
            logger.warning(f"[TrainingCoordinator] Initialization failed: {e}")
            raise
    return _training_coordinator_instance


def _try_init_causal_reasoning():
    """Initialize CausalReasoningEngine for interaction learning."""
    global _causal_reasoning_instance
    try:
        from ai.reasoning.causal_reasoning_engine import CausalReasoningEngine

        _causal_reasoning_instance = CausalReasoningEngine()
        # Warm-start with retrospective baseline relationships so
        # predict() returns results from Round 1 of every conversation
        _causal_reasoning_instance.retrospective_warm_start()
        logger.info(
            "[CausalReasoning] Initialized — learning causal relationships from interactions"
        )
    except Exception as e:
        logger.warning(f"[CausalReasoning] Initialization failed: {e}")


def _try_init_session_manager():
    """Initialize SessionManager singleton for WebSocket connections."""
    try:
        from services.connection_session import get_session_manager

        get_session_manager()
        logger.info("[SessionManager] Initialized — ready for WebSocket connections")
    except Exception as e:
        logger.warning(f"[SessionManager] Initialization failed: {e}")


def _try_start_broadcast():
    """Start WebSocket state broadcast background task."""
    from core.system.live_logger import warn as _lw

    try:
        from services.websocket_manager import broadcast_state_updates

        task = asyncio.create_task(broadcast_state_updates())

        def _log_broadcast_end(t: asyncio.Task) -> None:
            if t.cancelled():
                return
            exc = t.exception()
            if exc is not None:
                logger.error(f"[Broadcast] State broadcast task died: {exc}", exc_info=exc)

        task.add_done_callback(_log_broadcast_end)
        logger.debug("Broadcast state update task started")
        return task
    except Exception as e:
        _lw(f"Broadcast start failed: {e}")
        return None


def _try_wire_dli_broadcast():
    """Wire DLI and LLMDecisionLoop broadcast_callback to WebSocket broadcast.

    Without this wiring, proactive actions (greet/comfort/remind/share/question)
    from LLMDecisionLoop and ProactiveInteractionSystem never reach frontend clients.
    """
    from core.system.live_logger import warn as _lw

    try:
        dli = get_digital_life()
        if not dli:
            _lw("DLI not available for broadcast wiring")
            return

        async def _dli_broadcast(data: dict) -> None:
            from services.websocket_manager import manager

            await manager.broadcast(
                {
                    "type": "angela_action",
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        dli.broadcast_callback = _dli_broadcast
        if dli.llm_decision_loop:
            dli.llm_decision_loop.broadcast_callback = _dli_broadcast

        # Wire BehaviorExecutor broadcast so autonomous lifecycle decisions reach users
        try:
            lc = get_lifecycle()
            if lc and hasattr(lc, "_behavior_executor"):
                # Access _broadcast_callback directly — this is the sole wiring point
                # from the application layer into the autonomy system's behavior dispatch.
                lc._behavior_executor._broadcast_callback = _dli_broadcast
                logger.debug("BehaviorExecutor broadcast_callback wired to WebSocket")
        except Exception as e:
            _lw(f"BehaviorExecutor broadcast wiring failed: {e}")

        logger.debug("DLI broadcast_callback wired to WebSocket")
    except Exception as e:
        _lw(f"DLI broadcast wiring failed: {e}")


def _try_warm_ed3n():
    """Pre-warm ED3N external dictionaries to avoid cold-start latency."""
    try:
        from ai.ed3n.ed3n_engine import ED3NEngine

        count = ED3NEngine.get_shared().warm_up()
        if count > 0:
            logger.info("[ED3N] Pre-warmed %d external dictionary entries", count)
    except Exception as e:
        logger.warning(f"[ED3N] Warm-up skipped (non-critical): {e}", exc_info=True)


async def _sd_agent_manager() -> None:
    if _agent_manager_instance is not None:
        try:
            _agent_manager_instance.shutdown_all_agents()
            logger.info("[AgentManager] Shut down")
        except Exception as e:
            logger.warning(f"[AgentManager] Shutdown error: {e}")


async def _sd_bio_integrator() -> None:
    if _bio_integrator_instance is not None:
        try:
            await _bio_integrator_instance.shutdown()
            logger.info("[Bio] BiologicalIntegrator shut down")
        except Exception as e:
            logger.warning(f"[Bio] BiologicalIntegrator shutdown error: {e}")


async def _sd_brain_bridge() -> None:
    if _brain_bridge_instance is not None:
        try:
            await _brain_bridge_instance.stop()
            logger.info("[BrainBridge] BrainBridgeService stopped")
        except Exception as e:
            logger.warning(f"[BrainBridge] Shutdown error: {e}")


async def _sd_chat_service() -> None:
    if _chat_service_instance is not None:
        try:
            await _chat_service_instance.shutdown()
        except Exception as e:
            logger.warning(f"[ChatService] Shutdown error: {e}")


async def _sd_digital_life() -> None:
    if _digital_life_instance is not None:
        try:
            await _digital_life_instance.shutdown()
            logger.info("[DLI] DigitalLifeIntegrator shut down")
        except Exception as e:
            logger.warning(f"[DLI] Shutdown error: {e}")


async def _sd_training_coordinator() -> None:
    if _training_coordinator_instance is None:
        return
    try:
        await _training_coordinator_instance.stop_training_worker()
        logger.info("[TrainingCoordinator] Worker stopped")
    except Exception as e:
        logger.warning(f"[TrainingCoordinator] Worker stop failed: {e}")
    try:
        _training_coordinator_instance.save("data/training_coordinator.json")
        logger.info("[TrainingCoordinator] State saved")
    except Exception as e:
        logger.warning(f"[TrainingCoordinator] State save skipped: {e}")


def _sd_lifecycle_state() -> None:
    # Lifecycle state save: server-side life growth (decisions, phase) is
    # written back to the shared JSON so the game agent process picks it up
    # on next start (save_state previously had zero callers repo-wide).
    try:
        _lc = get_lifecycle()
        if _lc is not None and getattr(_lc, "_persist_path", None):
            _lc.save_state(_lc._persist_path)
            logger.info("[LifeCycle] State saved to shared file")
    except Exception as e:
        logger.warning(f"[LifeCycle] State save skipped: {e}")


async def _sd_broadcast(broadcast_task) -> None:
    if broadcast_task is not None:
        broadcast_task.cancel()
        try:
            await broadcast_task
        except asyncio.CancelledError:
            pass  # awaiting a task we just cancelled: CancelledError is the expected outcome
        logger.info("[Broadcast] State broadcast task stopped")


async def _sd_session_manager() -> None:
    try:
        from services.connection_session import shutdown_session_manager

        await shutdown_session_manager()
    except Exception as e:
        logger.warning(f"[SessionManager] Shutdown error: {e}")


async def _sd_module_manager(module_manager) -> None:
    if module_manager is not None:
        try:
            await module_manager.stop()
            logger.info("[ModuleManager] Module system shut down cleanly")
        except Exception as e:
            logger.error(f"[ModuleManager] Shutdown error: {e}", exc_info=True)


async def _sd_llm() -> None:
    try:
        from services.llm.router import _llm_service as _llm

        if _llm is not None:
            await _llm.shutdown()
            logger.info("[LLM] Backend HTTP sessions closed")
    except Exception as e:
        logger.warning(f"[LLM] Shutdown skipped: {e}", exc_info=True)


def _sd_plugin_metrics() -> None:
    if _metrics_handler is not None:
        try:
            metric_data = _metrics_handler.get_metrics()
        except Exception as e:
            logger.warning(f"[Plugin] Shutdown metrics skipped: {e}", exc_info=True)
        else:
            logger.info("[Plugin] Shutdown — hook invocation counts: %s", metric_data["counts"])


async def _shutdown_services(broadcast_task, module_manager):
    """Gracefully shut down all services on application exit."""
    await _sd_agent_manager()
    await _sd_bio_integrator()
    await _sd_brain_bridge()
    await _sd_chat_service()
    await _sd_digital_life()
    await _sd_training_coordinator()
    _sd_lifecycle_state()
    await _sd_broadcast(broadcast_task)
    await _sd_session_manager()
    await _sd_module_manager(module_manager)
    await _sd_llm()
    _sd_plugin_metrics()


def _backbone_try(bb, name: str, fn, *, kind: str = "module", key: Optional[str] = None) -> None:
    """Register one backbone component, skipping on None/failure."""
    key = key or name
    try:
        obj = fn()
        if obj is None:
            logger.debug("[Backbone] %s None, skip", key)
            return
        if kind == "module":
            bb.register_module(key, obj)
        elif kind == "matrix":
            bb.register_matrix(key, obj)
        elif kind == "memory":
            bb.register_memory(key, obj)
        elif kind == "dictionary":
            bb.register_dictionary(key, obj)
        logger.debug("[Backbone] registered %s=%s", kind, key)
    except Exception as exc:
        logger.debug("[Backbone] skip %s=%s: %s", kind, key, exc)


def _register_state_matrix(bb) -> None:
    """核心矩陣（DLI 持有的 StateMatrix4D）。"""
    try:
        dli = get_digital_life()
        sm = getattr(dli, "state_matrix", None) or getattr(dli, "state", None)
        if sm is not None:
            _backbone_try(bb, "state_matrix", lambda: sm, kind="matrix")
    except Exception as exc:
        logger.debug("[Backbone] state_matrix unavailable: %s", exc)


# =========================================================================
# Phase 2 item ③ — AL provider 登記簿（I8：AL 不出站伸手，組裝層代取）
# =========================================================================
def _al_life_phase():
    """``life_phase`` ← 共享 AutonomousLifeCycle 的當前階段（str/enum 皆可）。"""
    return getattr(get_lifecycle(), "current_phase", None)


def _al_life_cycle_state():
    """``life_cycle_state`` ← DLI 的生命週期狀態（``LifeCycleState`` enum）。

    AL 的第二條生命軸：與 ``life_phase``（ALC 認知階段）是兩個獨立狀態機
    （§3.7 的「生命狀態散在 5 處」只收斂了 4 處，兩個階段詞彙尚未統一 ——
    快照照實報兩欄，不假裝已收斂）。DLI 尚未建立 → ``None``（D11）。
    """
    dli = get_digital_life()
    if dli is None:
        return None
    return getattr(dli, "life_cycle_state", None)


def _al_health():
    """``health`` ← 代謝心跳的系統健康分。

    D11 閘：``_health_update_count`` 為 0 表示心跳還沒重算過一次健康分
    （唯一重算點是 CNS 事件 handler），預設 0.5 沒有觀測背後 → 回
    ``None``，讓快照照報未觀測，不把預設值當測量。
    """
    info = get_metabolic_heartbeat().get_system_health()
    if not info.get("health_update_count"):
        return None
    return info.get("system_health")


def _al_drift() -> Optional[Dict[str, float]]:
    """``drift{zeta,eta}`` ← 兩個已定義觀測來源（2b / 2c），未觀測的鍵不寫。

    - ``eta``：``measured_eta_metrics()`` 的 ``structural_drift`` —— 2c 的
      observed 閘（有啟動基線才是比較值，裸態/還原態回 ``None`` → 不進 dict）。
    - ``zeta``：值漂移 = 觀測窗口內被判異常的 ``(axis, field)`` 對佔比，
      即 2b ``compute_zeta_values()`` 的 ``1 - temporal_coherence``（同一
      觀測源，不新算）；``temporal_coherence`` 未觀測（<2 筆）→ 不進 dict。

    兩鍵皆缺 → 回 ``None``（D11：整個欄位未觀測，不是 ``{}`` 裝可觀測）。
    """
    from api.routes.chat_routes import _get_eta_axis, _get_state_matrix
    from core.engine.eta_axis import measured_eta_metrics

    drift: Dict[str, float] = {}
    eta_metrics = measured_eta_metrics(_get_eta_axis())
    if eta_metrics["structural_drift"] is not None:
        drift["eta"] = float(eta_metrics["structural_drift"])

    matrix = _get_state_matrix()
    if "temporal_coherence" in getattr(matrix, "zeta_observed_fields", frozenset()):
        values = getattr(getattr(matrix, "zeta", None), "values", {})
        coherence = values.get("temporal_coherence")
        if coherence is not None:
            drift["zeta"] = round(1.0 - float(coherence), 4)

    # 身份漂移（契約 §6 三層錨的「距離錨」量測）：LifeEssence 的世代序列，
    # 第 0 代祖先核心就是錨 —— 觀測得到、跨重啟持久（`data/life_essence_state.json`）。
    # 時間係數走配置（identity_tau_* / identity_z_threshold / identity_min_points，
    # §7.2「τ 是配置鍵」）。τ 用 `lifecycle_value` 而**不是** `timing_value`：
    # 後者會乘硬體倍率（同鍵在本機量出 40 而非 20）—— 身份的時間常數是語義，
    # 不該隨機器快慢變（測量隨硬體變 = 量測缺陷）。觀測不足 → 不進 dict（D11）；本段失敗也不拖垮
    # eta/zeta 兩鍵（`_call_source` 兜底，這裡再就地圈住）。
    try:
        from core.life.identity_drift import worst_identity_drift
        from core.life.life_essence import get_life_essence
        from core.system.config.magic_numbers import lifecycle_value, limit_value, threshold_value

        worst = worst_identity_drift(
            get_life_essence().mu_history(),
            tau_slow=lifecycle_value("identity_tau_slow", 20.0),
            tau_fast=lifecycle_value("identity_tau_fast", 5.0),
            z_threshold=threshold_value("identity_z_threshold", 2.0),
            min_points=int(limit_value("identity_min_points", 6)),
        )
        if worst is not None:
            dimension, evidence = worst
            drift["identity"] = round(float(evidence.drift), 4)
            logger.debug(
                "[ALState] identity drift via %s: distance=%s z=%s moving=%s",
                dimension,
                evidence.distance,
                evidence.z,
                evidence.moving,
            )
    except Exception:
        logger.debug("[ALState] identity drift unavailable", exc_info=True)
    return drift or None


def _register_al_sources() -> None:
    """Phase 2 item ③：三個 provider 由 lifespan 統一註冊進 AL 登記簿。

    item 1 的契約：``life_phase``/``life_cycle_state``/``health``/``drift``
    的實例握在 api 側，
    AL 出站不 import ``ai.*``/``api.*``（I8），所以由組裝層（本檔）在
    啟動序列裡注入。註冊後讀一次快照並落 log —— server 執行下的自檢：
    來源解析到值與否，直接進 server log，不需要額外面。
    """
    try:
        from core.life.al_state import register_al_source

        register_al_source("life_phase", _al_life_phase)
        register_al_source("life_cycle_state", _al_life_cycle_state)
        register_al_source("health", _al_health)
        register_al_source("drift", _al_drift)
    except Exception:
        logger.warning("[ALState] provider registration failed", exc_info=True)
        return
    try:
        from core.backbone import get_backbone
        from core.life.al_state import get_al_state

        snap = get_al_state()
        logger.info(
            "[ALState] providers live: life_phase=%r life_cycle_state=%r "
            "health=%r drift=%r sources=%s al_state_on_backbone=%s",
            snap.life_phase,
            snap.life_cycle_state,
            snap.health,
            snap.drift,
            {k: snap.source[k] for k in ("life_phase", "life_cycle_state", "health", "drift")},
            get_backbone().get_module("al_state") is not None,
        )
    except Exception:
        logger.warning("[ALState] boot snapshot failed", exc_info=True)


def _al_state_module():
    """AL 單一狀態面模組（契約 §9 的唯一對外交換量）—— 供 backbone 註冊。

    它是模組級 API（``get_al_state()`` 出口），不是可實例化的單例；註冊
    模組本身讓 ``dump`` 反映「AL 狀態面已接上主幹線」，消費端經
    ``get_module("al_state").get_al_state()`` 讀快照。
    """
    from core.life import al_state

    return al_state


def _register_backbone() -> None:
    """把已建好的核心單例註冊進主幹線（讓 backbone 直接連接到實際元件）。

    每一項皆 try/except：元件缺失或建立失敗就跳過，絕不因單一失敗阻塞啟動。
    註冊的元件讓 `python -m core.backbone dump` 的打印反映真實連接。
    """
    try:
        from core.backbone import get_backbone
    except Exception as exc:
        logger.debug("[Backbone] unavailable, skip registration: %s", exc)
        return

    bb = get_backbone()

    _register_state_matrix(bb)

    # AL 單一狀態面（Phase 2 item ③）— 聚合器註冊進既有主幹線，不新造
    _backbone_try(bb, "al_state", _al_state_module, kind="module", key="al_state")

    # 模組（lifespan 單例）
    _backbone_try(bb, "digital_life", get_digital_life, kind="module", key="digital_life")
    _backbone_try(bb, "lifecycle", get_lifecycle, kind="module", key="lifecycle")
    _backbone_try(
        bb, "heartbeat", get_metabolic_heartbeat, kind="module", key="metabolic_heartbeat"
    )
    _backbone_try(
        bb, "causal_reasoning", get_causal_reasoning, kind="module", key="causal_reasoning"
    )
    _backbone_try(bb, "crisis", get_crisis_system, kind="module", key="crisis_system")
    _backbone_try(bb, "agent_manager", get_agent_manager, kind="module", key="agent_manager")
    _backbone_try(
        bb, "desktop_interaction", get_desktop_interaction, kind="module", key="desktop_interaction"
    )
    _backbone_try(
        bb,
        "training_coordinator",
        get_training_coordinator,
        kind="module",
        key="training_coordinator",
    )

    # ChatService（重元件：含 model_bus / memory managers）
    chat = globals().get("_chat_service_instance")
    if chat is not None:
        _backbone_try(bb, "chat_service", lambda: chat, kind="module", key="chat_service")

    # 記憶（HAM / vector / memory_manager）
    _backbone_try(bb, "ham", lambda: _memory_backend_from_chat(), kind="memory", key="ham")

    logger.info(
        "[Backbone] registration done; modules=%d matrices=%d memories=%d",
        bb.registries.modules.count(),
        bb.registries.matrices.count(),
        bb.memories.names().__len__() if hasattr(bb.memories, "names") else 0,
    )


def _memory_backend_from_chat():
    """從 ChatService 取出 HAM memory manager（惰性）。"""
    chat = globals().get("_chat_service_instance")
    if chat is None:
        return None
    for attr in ("ham_manager", "memory_manager", "ham"):
        value = getattr(chat, attr, None)
        if value is not None and not isinstance(value, bool):
            return value
    return None


async def _try_start_proactive() -> None:
    global _proactive_instance
    try:
        from ai.lifecycle.proactive_interaction_system import ProactiveInteractionSystem
        from ai.lifecycle.user_monitor import UserMonitor
        from services.websocket_manager import push_to_all

        async def _broadcast_proactive(message: dict) -> None:
            message["timestamp"] = datetime.now().isoformat()
            await push_to_all(message)

        user_monitor = UserMonitor()
        _proactive_instance = ProactiveInteractionSystem(
            llm_service=None,
            state_manager=None,
            memory_manager=_memory_backend_from_chat(),
            user_monitor=user_monitor,
            broadcast_callback=_broadcast_proactive,
        )
        # await instead of floating create_task: start() returns promptly after
        # spawning self._proactive_task internally; a detached create_task here
        # could be GC'd before running (event loop only holds weak refs).
        await _proactive_instance.start()
        logger.info("[ProactiveInteractionSystem] Started with WebSocket broadcast")
    except Exception:
        logger.warning("[Proactive] Init skipped — will not run proactively", exc_info=True)


async def _sync_register_listeners() -> None:
    # Register the perception sync listeners.
    # VisionService/AudioService are constructed at *import* time, when no
    # event loop is running, so their own
    # `create_task(self._init_sync_listener())` is skipped with a debug log and
    # `sync_manager._clients` stays empty. /mobile/module-control therefore
    # broadcast to nobody and the module on/off switch silently did nothing.
    # Register the two endpoint-owned singletons here, where a loop exists.
    try:
        from core.sync.realtime_sync import sync_manager

        await sync_manager.initialize()
        from api.v1.endpoints import audio as _audio_endpoint
        from api.v1.endpoints import vision as _vision_endpoint

        await _vision_endpoint._vision_service._init_sync_listener()
        await _audio_endpoint.get_audio_service()._init_sync_listener()
        logger.info("[Sync] Listeners registered: %s", sync_manager.get_status()["clients"])
    except Exception:
        logger.warning("[Sync] Perception listener registration skipped", exc_info=True)


async def _training_start_worker() -> None:
    # TrainingCoordinator owns training execution: its worker dispatches queued
    # samples to the processors registered by each domain owner. Without a
    # processor every sample was deferred forever, so the processors are
    # registered here — before the worker starts — pointing at the trainer that
    # already owns learning (ContinuousLearningPipeline).
    try:
        _coordinator = get_training_coordinator()
        from ai.core.training_processors import register_default_processors

        register_default_processors(_coordinator)
        await _coordinator.start_training_worker()
    except Exception:
        logger.warning(
            "[TrainingCoordinator] Worker start skipped — samples stay queued",
            exc_info=True,
        )


def _preinit_lifecycle() -> None:
    # Pre-initialize lifecycle singleton during startup (lazy creates it on first use)
    try:
        _ = get_lifecycle()
    except Exception:
        logger.warning(
            "[LifeCycle] Pre-init skipped — will lazily initialize on first use", exc_info=True
        )


async def _preinit_heartbeat() -> None:
    # Initialize heartbeat singleton (C³ 6.0: start during lifespan)
    try:
        hb = get_metabolic_heartbeat()
        await hb.start()
        logger.info("[Heartbeat] MetabolicHeartbeat started during lifespan")
    except Exception:
        logger.warning(
            "[Heartbeat] Pre-init skipped — will lazily initialize on first use", exc_info=True
        )


async def _preinit_chat_service() -> None:
    # Pre-initialize ChatService at startup so its (potentially slow) memory
    # backends (e.g. chromadb PersistentClient) are warmed up before the first
    # user request, instead of blocking the first chat call for many seconds.
    try:
        await _get_chat_service()
        logger.info("[ChatService] Pre-initialized during lifespan")
    except Exception:
        logger.warning(
            "[ChatService] Pre-init skipped — will lazily initialize on first use", exc_info=True
        )


def _preinit_backbone() -> None:
    # 把實際單例註冊進主幹線（backbone 直接連接核心元件）
    try:
        _register_backbone()
    except Exception:
        logger.warning("[Backbone] registration failed during startup", exc_info=True)


async def _startup_services():
    """Full startup sequence. Returns the broadcast task for shutdown."""
    _init_plugins()
    await _try_start_bio()
    await _try_start_digital_life()
    await _try_start_brain_bridge()
    await _try_start_agents()
    _try_init_crisis()
    _try_init_causal_reasoning()
    _try_init_session_manager()

    await _sync_register_listeners()
    await _training_start_worker()
    _broadcast_task = _try_start_broadcast()
    _try_warm_ed3n()
    _preinit_lifecycle()

    # Wire DLI broadcast_callback so LLMDecisionLoop proactive actions reach frontend
    _try_wire_dli_broadcast()

    await _preinit_heartbeat()

    # Start ProactiveInteractionSystem (Angela can initiate conversations)
    await _try_start_proactive()

    await _preinit_chat_service()
    _preinit_backbone()
    # Phase 2 item ③：AL provider 登記（backbone 先行，自檢 log 才能報
    # al_state_on_backbone）；函式內部全 try/except，不會阻塞啟動。
    _register_al_sources()

    return _broadcast_task


async def _shutdown_pre_lifespan() -> None:
    """Stop heartbeat + proactive before the full service shutdown."""
    try:
        hb_inst = get_metabolic_heartbeat()
        await hb_inst.stop()
    except Exception as err:
        logger.warning(f"Heartbeat stop on shutdown skipped: {err}", exc_info=True)
    if _proactive_instance is not None:
        try:
            await _proactive_instance.stop()
            logger.info("[ProactiveInteractionSystem] Stopped during shutdown")
        except Exception as err:
            logger.warning(f"Proactive stop on shutdown skipped: {err}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: initialize services on startup, shutdown on exit."""
    _module_manager = None
    _broadcast_task = await _startup_services()

    yield

    await _shutdown_pre_lifespan()
    await _shutdown_services(_broadcast_task, _module_manager)
