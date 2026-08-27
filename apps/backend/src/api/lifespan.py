"""
ANGELA-MATRIX: [L4-L5] [βδ] [A] [L3]
Application lifecycle management — startup/shutdown + service factories.
Extracted from main_api_server.py (A3 god module split).
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncIterator

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


def get_digital_life():
    """Get or create the digital life integrator singleton."""
    global _digital_life_instance
    if _digital_life_instance is None:
        try:
            from core.life.digital_life_integrator import DigitalLifeIntegrator

            _digital_life_instance = DigitalLifeIntegrator()
        except Exception as e:
            logger.warning(f"DigitalLifeIntegrator not available: {e}", exc_info=True)
            raise
    return _digital_life_instance


def get_desktop_interaction():
    """Lazy import for desktop interaction."""
    try:
        from core.engine.desktop_interaction import DesktopInteraction

        return DesktopInteraction()
    except Exception as e:
        logger.warning(f"DesktopInteraction not available: {e}")
        return None


def get_action_executor():
    """Lazy import for action executor."""
    try:
        from core.engine.action_executor import ActionExecutor

        return ActionExecutor()
    except Exception as e:
        logger.warning(f"ActionExecutor not available: {e}")
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
    except Exception:
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
        count = register_specialized_agents(_agent_manager_instance)
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
    from core.system.live_logger import info as _li
    from core.system.live_logger import warn as _lw

    try:
        from services.websocket_manager import broadcast_state_updates

        task = asyncio.create_task(broadcast_state_updates())
        task.add_done_callback(lambda t: None)
        _li("Broadcast state update task started")
        return task
    except Exception as e:
        _lw(f"Broadcast start failed: {e}")
        return None


def _try_wire_dli_broadcast():
    """Wire DLI and LLMDecisionLoop broadcast_callback to WebSocket broadcast.

    Without this wiring, proactive actions (greet/comfort/remind/share/question)
    from LLMDecisionLoop and ProactiveInteractionSystem never reach frontend clients.
    """
    from core.system.live_logger import info as _li
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
                _li("BehaviorExecutor broadcast_callback wired to WebSocket")
        except Exception as e:
            _lw(f"BehaviorExecutor broadcast wiring failed: {e}")

        _li("DLI broadcast_callback wired to WebSocket")
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


async def _shutdown_services(broadcast_task, module_manager):
    """Gracefully shut down all services on application exit."""
    try:
        from services.llm.router import _llm_service as _llm

        if _llm is not None:
            await _llm.shutdown()
            logger.info("[LLM] Backend HTTP sessions closed")
    except Exception as e:
        logger.warning(f"[LLM] Shutdown skipped: {e}", exc_info=True)
    if _agent_manager_instance is not None:
        try:
            _agent_manager_instance.shutdown_all_agents()
            logger.info("[AgentManager] Shut down")
        except Exception as e:
            logger.warning(f"[AgentManager] Shutdown error: {e}")
    if _bio_integrator_instance is not None:
        try:
            await _bio_integrator_instance.shutdown()
            logger.info("[Bio] BiologicalIntegrator shut down")
        except Exception as e:
            logger.warning(f"[Bio] BiologicalIntegrator shutdown error: {e}")
    if _brain_bridge_instance is not None:
        try:
            await _brain_bridge_instance.stop()
            logger.info("[BrainBridge] BrainBridgeService stopped")
        except Exception as e:
            logger.warning(f"[BrainBridge] Shutdown error: {e}")
    if _digital_life_instance is not None:
        try:
            await _digital_life_instance.shutdown()
            logger.info("[DLI] DigitalLifeIntegrator shut down")
        except Exception as e:
            logger.warning(f"[DLI] DigitalLifeIntegrator shutdown error: {e}")
    if broadcast_task is not None:
        broadcast_task.cancel()
        try:
            await broadcast_task
        except asyncio.CancelledError:
            pass
        logger.info("[Broadcast] State broadcast task stopped")
    try:
        from services.connection_session import shutdown_session_manager

        await shutdown_session_manager()
    except Exception as e:
        logger.warning(f"[SessionManager] Shutdown error: {e}")
    if module_manager is not None:
        try:
            await module_manager.stop()
            logger.info("[ModuleManager] Module system shut down cleanly")
        except Exception as e:
            logger.error(f"[ModuleManager] Shutdown error: {e}", exc_info=True)
    if _metrics_handler is not None:
        metric_data = _metrics_handler.get_metrics()
        logger.info("[Plugin] Shutdown — hook invocation counts: %s", metric_data["counts"])


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

    def _try(name: str, fn, *, kind: str = "module", key: str = None) -> None:
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

    # 核心矩陣（DLI 持有的 StateMatrix4D）
    try:
        dli = get_digital_life()
        sm = getattr(dli, "state_matrix", None) or getattr(dli, "state", None)
        if sm is not None:
            _try("state_matrix", lambda: sm, kind="matrix")
    except Exception as exc:
        logger.debug("[Backbone] state_matrix unavailable: %s", exc)

    # 模組（lifespan 單例）
    _try("digital_life", get_digital_life, kind="module", key="digital_life")
    _try("lifecycle", get_lifecycle, kind="module", key="lifecycle")
    _try("heartbeat", get_metabolic_heartbeat, kind="module", key="metabolic_heartbeat")
    _try("causal_reasoning", get_causal_reasoning, kind="module", key="causal_reasoning")
    _try("crisis", get_crisis_system, kind="module", key="crisis_system")
    _try("agent_manager", get_agent_manager, kind="module", key="agent_manager")
    _try("desktop_interaction", get_desktop_interaction, kind="module", key="desktop_interaction")
    _try(
        "training_coordinator", get_training_coordinator, kind="module", key="training_coordinator"
    )

    # ChatService（重元件：含 model_bus / memory managers）
    chat = globals().get("_chat_service_instance")
    if chat is not None:
        _try("chat_service", lambda: chat, kind="module", key="chat_service")

    # 記憶（HAM / vector / memory_manager）
    _try("ham", lambda: _memory_backend_from_chat(), kind="memory", key="ham")

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


def _try_start_proactive() -> None:
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
        asyncio.create_task(_proactive_instance.start())
        logger.info("[ProactiveInteractionSystem] Started with WebSocket broadcast")
    except Exception:
        logger.warning(
            "[Proactive] Init skipped — will not run proactively", exc_info=True
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: initialize services on startup, shutdown on exit."""
    _module_manager = None

    _init_plugins()
    await _try_start_bio()
    await _try_start_digital_life()
    await _try_start_brain_bridge()
    await _try_start_agents()
    _try_init_crisis()
    _try_init_causal_reasoning()
    _try_init_session_manager()
    _broadcast_task = _try_start_broadcast()
    _try_warm_ed3n()
    # Pre-initialize lifecycle singleton during startup (lazy creates it on first use)
    try:
        _ = get_lifecycle()
    except Exception:
        logger.warning(
            "[LifeCycle] Pre-init skipped — will lazily initialize on first use", exc_info=True
        )

    # Wire DLI broadcast_callback so LLMDecisionLoop proactive actions reach frontend
    _try_wire_dli_broadcast()

    # Initialize heartbeat singleton (C³ 6.0: start during lifespan)
    try:
        hb = get_metabolic_heartbeat()
        await hb.start()
        logger.info("[Heartbeat] MetabolicHeartbeat started during lifespan")
    except Exception:
        logger.warning(
            "[Heartbeat] Pre-init skipped — will lazily initialize on first use", exc_info=True
        )

    # Start ProactiveInteractionSystem (Angela can initiate conversations)
    _try_start_proactive()

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

    # 把實際單例註冊進主幹線（backbone 直接連接核心元件）
    try:
        _register_backbone()
    except Exception:
        logger.warning("[Backbone] registration failed during startup", exc_info=True)

    yield

    await _shutdown_services(_broadcast_task, _module_manager)
    # Stop heartbeat on shutdown
    try:
        hb_inst = get_metabolic_heartbeat()
        await hb_inst.stop()
    except Exception as err:
        logger.warning(f"Heartbeat stop on shutdown skipped: {err}", exc_info=True)
    # Stop proactive interaction system on shutdown
    if _proactive_instance is not None:
        try:
            await _proactive_instance.stop()
            logger.info("[ProactiveInteractionSystem] Stopped during shutdown")
        except Exception as err:
            logger.warning(f"Proactive stop on shutdown skipped: {err}", exc_info=True)
