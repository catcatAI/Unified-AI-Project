"""
ANGELA-MATRIX: [L4-L5] [αβγδ] [A] [L3]
Chat & session API routes extracted from main_api_server.py (A3 god module split).
"""

import asyncio
import json
import logging
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Dict, List, NamedTuple, Optional, Tuple

from api.lifespan import (
    _angela_cfg,
    _get_chat_service,
    get_abc_key_manager,
    get_causal_reasoning,
    get_crisis_system,
    get_digital_life,
    get_level5_asi,
)
from core.system.state_store import state_store
from core.utils import safe_error
from fastapi import APIRouter, Body, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from services.document_router import try_intent_routing as _try_intent_routing
from services.execution.gate_execution import TTLSessionManager as _GateTTLSessionManager
from services.execution.gate_execution import sessions as _gate_sessions

logger = logging.getLogger(__name__)

router = APIRouter()

_background_tasks: set = set()


def _backbone_module(module_key: str, factory: Any) -> Any:
    """Resolve a shared module via the backbone registry, creating on first use.

    Step B1: `_get_*` factories now delegate caching to `get_backbone()` so the
    backbone registry is the single source of truth for shared singletons.
    Falls back to `factory()` (the original creation logic) on first use and
    registers the result back into the backbone registry.
    """
    from core.backbone import get_backbone

    bb = get_backbone()
    cached = bb.get_module(module_key)
    if cached is not None:
        return cached
    instance = factory()
    if instance is not None:
        bb.register_module(module_key, instance)
    return instance


def _spawn_background_task(coro, description: str = "") -> asyncio.Task:
    """Create a tracked background task with error logging."""
    task = asyncio.create_task(coro)
    _background_tasks.add(task)

    def _on_done(t: asyncio.Task) -> None:
        _background_tasks.discard(t)
        if t.cancelled():
            return
        exc = t.exception()
        if exc:
            logger.warning(f"Background task '{description}' failed: {exc}")

    task.add_done_callback(_on_done)
    return task


def _display_name(user_name: Optional[str], user_id: Optional[str]) -> str:
    """A display name that is not a raw user id.

    The clients send ``user_id`` (a stable key) and sometimes a display
    name. When only the id is known, the id must NOT become the name the
    assistant greets the user with ("smoke_user，這個任務我目前做不到…"
    reads like a bug). An empty name makes the fallback use a neutral
    salutation instead.
    """
    name = (user_name or "").strip()
    if not name or (user_id and name == str(user_id).strip()):
        return ""
    return name


def _bind_current_user(user_id: Optional[str]) -> Any:
    """Bind the requesting user so the instance name resolves per user."""
    try:
        from core.system.config.identity import set_current_user

        return set_current_user(user_id)
    except Exception as exc:  # pragma: no cover - identity layer unavailable
        logger.warning("Could not bind current user: %s", exc, exc_info=True)
        return None


def _unbind_current_user(token: Any) -> None:
    """Undo the user binding made by `_bind_current_user`."""
    if token is None:
        return
    try:
        from core.system.config.identity import reset_current_user

        reset_current_user(token)
    except Exception as exc:  # pragma: no cover - identity layer unavailable
        logger.debug("Could not unbind current user: %s", exc)


# Session store: owned by services.execution.gate_execution so the HTTP route and
# the REPL / ChatService path share ONE gate + session owner.
TTLSessionManager = _GateTTLSessionManager
sessions = _gate_sessions

# Latest pipeline response, captured so _handle_chat_request can persist the turn.
# Bounded to prevent unbounded memory growth (matches TTLSessionManager max_sessions).
_MAX_LATEST_RESPONSES = 1000
_latest_responses: Dict[str, Dict[str, Any]] = {}
_latest_responses_order: List[str] = []  # insertion order for LRU eviction
_latest_responses_lock = threading.Lock()


def _set_latest_response(session_id: str, data: Dict[str, Any]) -> None:
    """Store a response with bounded eviction to prevent memory leaks."""
    with _latest_responses_lock:
        if session_id in _latest_responses:
            # Update existing — move to end
            _latest_responses[session_id] = data
            if session_id in _latest_responses_order:
                _latest_responses_order.remove(session_id)
            _latest_responses_order.append(session_id)
        else:
            _latest_responses[session_id] = data
            _latest_responses_order.append(session_id)
        # Evict oldest entries if over limit
        while len(_latest_responses) > _MAX_LATEST_RESPONSES:
            oldest = _latest_responses_order.pop(0)
            _latest_responses.pop(oldest, None)


def _get_ed3n_engine():
    def _factory():
        from ai.ed3n.ed3n_engine import ED3NEngine

        return ED3NEngine.get_shared()

    return _backbone_module("chat.ed3n_engine", _factory)


def _get_query_classifier():
    """Shared QueryClassifier singleton.

    Construction wires the ED3N engine + compiles pattern tables — not cheap,
    and the classifier is stateless across requests, so one instance serves
    all call sites (was previously rebuilt per request in 3 places).
    """

    def _factory():
        from ai.core.query_classifier import QueryClassifier

        return QueryClassifier(ed3n_engine=_get_ed3n_engine())

    return _backbone_module("chat.query_classifier", _factory)


def _get_shared_garden():
    """Shared GARDENEngine singleton for document-learning endpoints.

    Delegates to GARDENEngine.get_shared() — one process-wide engine so
    learned associations accumulate (mirrors ED3NEngine.get_shared()).
    """

    from ai.garden.garden_engine import GARDENEngine

    return GARDENEngine.get_shared()


def _invalidate_router_cache(reason: str) -> None:
    """Drop the LLM router's response cache after a learning event.

    Prevents freshly-learned knowledge from being masked by stale cached
    answers (intelligence must never regress behind the cache).
    """
    try:
        from services.llm.router import _llm_service as svc

        if svc is not None and hasattr(svc, "invalidate_response_cache"):
            dropped = svc.invalidate_response_cache()
            if dropped:
                logger.info("Response cache invalidated (%d entries) after %s", dropped, reason)
    except Exception as e:
        logger.debug("Response cache invalidation skipped (%s): %s", reason, e)


# Stopwords excluded from keyword-learning cycles (function-word greetings,
# politeness and pronouns carry no learnable content). Named constant — was
# an inline tuple with a duplicate "什麼" entry.
_LEARNING_STOPWORDS = frozenset(
    {
        "你好",
        "請問",
        "可以",
        "幫我",
        "想要",
        "這個",
        "那個",
        "什麼",
        "怎麼",
        "為什麼",
        "如何",
        "我們",
        "你們",
        "他們",
        "hello",
        "help",
        "please",
        "can",
        "you",
        "the",
    }
)


def _get_bio_integrator():
    def _factory():
        from core.bio.biological_integrator import BiologicalIntegrator

        return BiologicalIntegrator()

    return _backbone_module("chat.bio_integrator", _factory)


def _get_vision_service():
    def _factory():
        try:
            from api.lifespan import get_vision_service

            return get_vision_service()
        except ImportError:
            from services.vision_service import VisionService

            return VisionService()

    return _backbone_module("chat.vision_service", _factory)


def _get_dialogue_ctx():
    def _factory():
        from ai.context.dialogue_context import DialogueContextManager

        return DialogueContextManager()

    return _backbone_module("chat.dialogue_ctx", _factory)


def _get_modality_gateway():
    """Get the shared ModalityGateway, preferring the DLI's live instance.

    When DigitalLifeIntegrator is running, its modality_gateway is updated
    by _health_check_loop() with live arousal + introspection data.
    Falls back to a standalone singleton when DLI is unavailable.
    """

    def _factory():
        from core.life.digital_life_integrator import ModalityGateway

        return ModalityGateway()

    try:
        dli = get_digital_life()
        if dli and hasattr(dli, "modality_gateway"):
            return dli.modality_gateway
    except Exception:
        logger.warning("_get_modality_gateway: DLI unavailable, using standalone", exc_info=True)
    return _backbone_module("chat.modality_gateway", _factory)


def _get_lifecycle():
    """Get the shared AutonomousLifeCycle singleton from lifespan."""

    def _factory():
        from core.life.autonomous_life_cycle import AutonomousLifeCycle

        return AutonomousLifeCycle()

    try:
        from api.lifespan import get_lifecycle as _lifespan_get_lifecycle

        return _lifespan_get_lifecycle()
    except Exception:
        logger.warning("_get_lifecycle: lifespan unavailable, using fallback", exc_info=True)
    # Fallback: backbone-cached singleton if lifespan not available
    return _backbone_module("chat.lifecycle", _factory)


def _get_intent_manager():
    """Get the IntentManager from the DLI singleton."""
    try:
        from api.lifespan import get_digital_life

        dli = get_digital_life()
        if dli and hasattr(dli, "intent_manager"):
            return dli.intent_manager
        return None
    except Exception:
        logger.warning("_get_intent_manager: DLI unavailable", exc_info=True)
        return None


def _get_emotion_analyzer():
    def _factory():
        from services.llm.emotion_analyzer import EmotionAnalyzer

        return EmotionAnalyzer()

    return _backbone_module("chat.emotion_analyzer", _factory)


def _get_emotion_system():
    def _factory():
        from ai.alignment.emotion_system import EmotionSystem

        return EmotionSystem()

    return _backbone_module("chat.emotion_system", _factory)


def _get_state_matrix():
    """Get live state matrix from DLI when available, fallback to shared singleton."""

    def _factory():
        from core.engine.state_matrix import get_shared_state_matrix

        return get_shared_state_matrix()

    try:
        dli = get_digital_life()
        if dli and hasattr(dli, "state_matrix"):
            return dli.state_matrix
    except Exception:
        logger.warning("_get_state_matrix: DLI unavailable, using standalone", exc_info=True)
    return _backbone_module("chat.state_matrix", _factory)


def _get_eta_axis():
    """Get shared EtaAxisState (execution/operation layer η)."""

    def _factory():
        from core.engine.eta_axis import EtaAxisState, create_default_modules

        state = EtaAxisState()
        for name, config in create_default_modules().items():
            state.register_module(config)
        # Boot baseline for η.drift (Phase 2 item 2): the defaults are the
        # composition this process started with, so later hotplug-style
        # register/unregister/activate/deactivate shows up as measured drift.
        state.mark_structural_baseline()
        return state

    return _backbone_module("chat.eta_axis", _factory)


def _get_msba_pipeline():
    """Get shared MSBA pipeline (Multi-Dimensional Semantic Block Architecture)."""

    def _factory():
        try:
            from ai.msba.block_factory import create_all_blocks
            from ai.msba.pipeline import MSBAPipeline

            blocks = create_all_blocks()
            return MSBAPipeline(blocks=blocks)
        except Exception as e:
            logger.warning("MSBA pipeline creation failed: %s", e)
            return None

    return _backbone_module("chat.msba_pipeline", _factory)


# Behavioral adjustments mapped by detected emotion
_ANGELA_EMOTION_BEHAVIOR_MAP = {
    "joy": {"routing_mode": "exploratory", "response_style": "enthusiastic"},
    "trust": {"routing_mode": "exploratory", "response_style": "warm"},
    "fear": {"routing_mode": "conservative", "response_style": "soothing"},
    "surprise": {"routing_mode": "exploratory", "response_style": "curious"},
    "sadness": {"routing_mode": "conservative", "response_style": "empathetic"},
    "disgust": {"routing_mode": "conservative", "response_style": "guarded"},
    "anger": {"routing_mode": "conservative", "response_style": "calming"},
    "anticipation": {"routing_mode": "exploratory", "response_style": "encouraging"},
}


def _adjust_emotion_threshold(adj: Dict[str, Any]) -> None:
    """狀態(6D)→情緒(PAD)→閾值 自調閉環: 情緒直接調節語義 QA 閾值。

    exploratory/高 valence+arousal → 更開放 (閾值 -0.05),
    conservative/低 valence/疲勞 → 更保守 (+0.08)
    """
    try:
        from ai.unified_engine.semantic_qa import set_emotion_threshold_adjustment

        delta = 0.0
        routing = adj.get("routing_mode", "")
        valence = float(adj.get("valence", 0.0) or 0.0)
        arousal = float(adj.get("arousal", 0.5) or 0.5)
        sustained = int(adj.get("sustained_negative_counter", 0) or 0)
        if routing == "exploratory":
            delta -= 0.05
        if routing == "conservative":
            delta += 0.05
        if valence > 0.3 and arousal > 0.5:
            delta -= 0.03
        if valence < -0.3:
            delta += 0.03
        if sustained >= 3:
            delta += 0.08
        set_emotion_threshold_adjustment(delta)
    except Exception as e:
        logger.debug(f"Emotion threshold adjustment failed: {e}", exc_info=True)


async def _inject_emotion_behavioral_context(
    emotion_result: Optional[Dict[str, Any]],
    context: Dict[str, Any],
    bio: Optional[Any] = None,
) -> None:
    """Inject emotional behavioral adjustments into context.

    Maps keyword-detected user-text emotion (EmotionAnalyzer output — an
    inference from word choice, not a measurement of the user's feelings)
    to routing_mode and response_style so that the LLM prompt receives
    behavioral guidance beyond just the emotion text. Also updates Angela's
    internal EmotionSystem (PAD simulation state) and cross-component
    Emotion→Biological stress/relaxation (C³ 4.0).
    """
    if not emotion_result:
        return
    emotion = emotion_result.get("emotion", "neutral")
    # Map EmotionAnalyzer output keys to behavior map keys
    _EMOTION_TO_BEHAVIOR_KEY = {
        "happy": "joy",
        "sad": "sadness",
        "angry": "anger",
        "fear": "fear",
        "surprise": "surprise",
        "curious": "anticipation",
        "calm": "trust",
    }
    mapped = _EMOTION_TO_BEHAVIOR_KEY.get(emotion, emotion)
    behavior = _ANGELA_EMOTION_BEHAVIOR_MAP.get(
        mapped, {"routing_mode": "neutral", "response_style": "standard"}
    )
    context["emotional_behavior"] = behavior

    # Apply influence to Angela's EmotionSystem for internal state tracking
    try:
        es = _get_emotion_system()
        if es:
            intensity = emotion_result.get("intensity", 0.5)
            es.apply_influence("user_message", mapped, intensity * 0.3, 0.5)
            adj = es.get_behavioral_adjustment()
            context["angela_emotion"] = adj
            _adjust_emotion_threshold(adj)

        # Cross-component: Emotion → Biological stress/relaxation (C³ 4.0)
        if bio is not None:
            await _apply_emotion_to_biology(emotion, intensity, bio)
    except Exception as e:
        logger.warning(f"EmotionSystem behavioral injection failed: {e}", exc_info=True)


# Emotion → Biological stress/relaxation mapping for C³ 4.0 cross-component chain
_EMOTION_TO_STRESS_MAP: Dict[str, float] = {
    "anger": 0.3,
    "fear": 0.35,
    "sadness": 0.15,
    "disgust": 0.12,
    "surprise": 0.05,
    "anticipation": 0.05,
}

_EMOTION_TO_RELAXATION_MAP: Dict[str, float] = {
    "joy": 0.2,
    "trust": 0.1,
}


async def _apply_emotion_to_biology(
    emotion: str,
    intensity: float,
    bio: Any,
) -> None:
    """Map detected emotion to BiologicalIntegrator stress/relaxation event."""
    stress_intensity = _EMOTION_TO_STRESS_MAP.get(emotion, 0.0)
    relax_intensity = _EMOTION_TO_RELAXATION_MAP.get(emotion, 0.0)

    if stress_intensity > 0:
        effective = min(1.0, stress_intensity * intensity * 2.0)
        await bio.process_stress_event(effective, duration=15.0)
    elif relax_intensity > 0:
        effective = min(1.0, relax_intensity * intensity * 1.5)
        await bio.process_relaxation_event(effective)


# =============================================================================
# Extracted helpers for _handle_chat_request (Phase 5.1 refactoring)
# =============================================================================


def _validate_and_truncate_input(
    user_message: str,
    chat_cfg: Dict[str, Any],
) -> str:
    """Validate user message and truncate if it exceeds the maximum length.

    Returns the (possibly truncated) message. Use ``len(raw) > max_len`` on the
    original input to know whether truncation occurred — the returned value is
    already clamped and cannot be re-checked for its original length.
    """
    if not user_message or not user_message.strip():
        raise ValueError("訊號遺失：消息不能為空")
    max_len = chat_cfg.get("max_message_length", 4000)
    trunc_len = chat_cfg.get("truncation_length", 1000)
    if len(user_message) > max_len:
        logger.warning(f"\U0001f6df [LIS] Intercepted oversized input ({len(user_message)} chars)")
        user_message = user_message[:trunc_len]
    return user_message


def _try_taught_facts(
    user_message: str,
    session_id: str,
    schema_version: str = "2.0",
    truncation_message: str = "",
) -> Optional[Dict[str, Any]]:
    """Answer from facts the user taught in conversation — *memory*, not knowledge.

    Layer contract (docs/06-project-management/LAYER_SEPARATION.md): a user's
    statement is a record attributable to that user, not a verified fact, so the
    reply must say so ("你教過我") and is labelled ``source=memory``. It also
    never runs through ``route_knowledge``: memory must not be scored as
    knowledge. Runs after the teaching step and before recall/LLM so a
    correction applies to the next question immediately.
    """
    try:
        from ai.memory.taught_facts import get_taught_facts

        answer = get_taught_facts().lookup(user_message)
    except Exception as exc:  # pragma: no cover - optional store
        logger.debug("taught-facts lookup unavailable: %s", exc)
        return None
    if not answer:
        return None
    attributed = f"你教過我：{answer}"
    result = {
        "response_text": attributed,
        "response": attributed,
        "source": "memory",
        "backend": "dialogue-memory",
        "model": "memory",
        "schema_version": schema_version,
        "truncation_message": truncation_message,
        "emotion": "calm",
        "emotion_confidence": 0.7,
        "emotion_intensity": 0.4,
        "session_id": session_id,
    }
    try:
        _set_latest_response(session_id, result)
    except Exception:  # pragma: no cover - diagnostics only
        logger.debug("latest-response cache unavailable", exc_info=True)
    return result


async def _try_math_verification(
    user_message: str,
    user_name: str,
    session_id: str,
    schema_ver: str,
    trunc_msg: str,
    was_truncated: bool = False,
) -> Optional[Dict[str, Any]]:
    """Try dual-rail math verification. Returns response dict if math detected, else None."""
    try:
        from services.math_verifier import MathVerifier

        digital_life = get_digital_life()
        matrix = (
            digital_life.state_matrix
            if digital_life and hasattr(digital_life, "state_matrix")
            else None
        )
        verifier = MathVerifier(state_matrix=matrix)
        if verifier.is_math_message(user_message):
            logger.info("\U0001f9ee [DualRail] Math task detected")
            verification = verifier.verify(user_message, user_name)
            # Apply bounded, meaningful-only cognition to the live state matrix.
            # Stateless arithmetic (e.g. "917 * 814") applies NOTHING; a meaningful
            # problem (e.g. "HP is 9999") nudges joy/high-value happiness. This is
            # the production counterpart of CognitivePipeline and reuses the exact
            # same code path (ai.memory.domain_ripple.apply_domain_cognition), so
            # the lab and live behaviour can never diverge (§11.5 / §11.9).
            if matrix is not None:
                try:
                    from ai.memory.domain_ripple import apply_domain_cognition

                    apply_domain_cognition(matrix, user_message)
                except Exception as e:  # pragma: no cover - defensive
                    logger.warning(f"Bounded math cognition failed: {e}", exc_info=True)
            if verification.response_text:
                return _build_math_response(
                    verification,
                    matrix,
                    user_message,
                    session_id,
                    schema_ver,
                    trunc_msg if was_truncated else "",
                )
    except Exception as e:
        logger.warning(f"\u26a0 [DualRail] Math verification failed: {e}")
    return None


def _analyze_user_emotion(user_message: str) -> Optional[Dict[str, Any]]:
    """Keyword-detected user-text emotion (inference, not measurement)."""
    try:
        emotion_result: Optional[Dict[str, Any]] = _get_emotion_analyzer().analyze_emotion(
            user_message
        )
        logger.debug(f"Emotion analysis: {emotion_result}")
        return emotion_result
    except Exception as e:
        logger.info(f"Emotion analysis unavailable: {e}")
    return None


def _assess_crisis_level(user_message: str) -> int:
    """Assess crisis level from the user input (0 when unavailable)."""
    crisis_level = 0
    try:
        crisis_sys = get_crisis_system()
        if crisis_sys:
            crisis_level = crisis_sys.assess_input_for_crisis({"text": user_message})
            if crisis_level > 0:
                logger.info(f"[CrisisSystem] Level {crisis_level} detected")
    except Exception as e:
        logger.warning(f"Crisis assessment unavailable: {e}", exc_info=True)
    return crisis_level


async def _fire_bio_stimulus(
    bio: Any, user_message: str, emotion_result: Optional[Dict[str, Any]]
) -> None:
    """Fire-and-forget: biological stimulus processing."""
    try:
        _spawn_background_task(
            bio.process_auditory_stimulus(volume=0.6, content=user_message), "auditory_stimulus"
        )
        if emotion_result:
            emotion = emotion_result.get("emotion", "neutral")
            intensity = emotion_result.get("intensity", 0.5)
            if emotion in ("sad", "angry", "fear"):
                _spawn_background_task(
                    bio.process_stress_event(intensity=intensity * 0.3), "stress_event"
                )
            elif emotion in ("happy", "calm"):
                _spawn_background_task(
                    bio.process_relaxation_event(intensity=intensity * 0.2), "relaxation_event"
                )
    except Exception as e:
        logger.warning(f"Biological state update from chat failed: {e}", exc_info=True)


async def _analyze_emotion_and_crisis(
    user_message: str,
    context: Dict[str, Any],
    bio: Any,
) -> Tuple[Optional[Dict[str, Any]], int]:
    """Analyze user emotion + assess crisis level. Fires biological stimulus as side-effect."""
    emotion_result = _analyze_user_emotion(user_message)
    crisis_level = _assess_crisis_level(user_message)
    await _fire_bio_stimulus(bio, user_message, emotion_result)
    return emotion_result, crisis_level


async def _try_alignment_check(
    user_message: str, crisis_level: int, context: Dict[str, Any]
) -> None:
    """Fire-and-forget: check alignment via Level5 ASI for high-crisis inputs."""
    if crisis_level < 2:
        return
    try:
        asi = await get_level5_asi()
        if asi and asi.is_running:
            alignment_result = await asi.process_request(
                {
                    "request_id": str(uuid.uuid4()),
                    "capability_id": "chat_response",
                    "user_intent": {"text": user_message, "crisis_level": crisis_level},
                    "ethical_constraints": ["user_safety", "empathy", "no_harm"],
                }
            )
            if alignment_result.get("status") == "alignment_failed":
                logger.warning(f"[Level5ASI] Alignment failed: {alignment_result.get('reason')}")
                context["alignment_override"] = "prioritize_safety"
    except Exception as e:
        logger.warning(f"Level5ASI alignment check unavailable: {e}", exc_info=True)


def _ctx_bio_state(context: Dict[str, Any], bio: Any) -> None:
    """Bio state injection."""
    try:
        context["bio_state"] = bio.get_biological_state()
    except Exception as e:
        logger.warning(f"Biological state retrieval failed: {e}", exc_info=True)


def _ctx_state_matrix(context: Dict[str, Any]) -> None:
    """State matrix 4D axes + theta + eta injection."""
    try:
        sm = _get_state_matrix()
        eta_state = _get_eta_axis()
        axes = {}
        # zeta arrives through a per-key observation gate (three-core plan,
        # Phase 2 item 2): compute_zeta_values() writes each sub-metric only
        # once TemporalState holds >= 2 observations, and zeta_observed_fields
        # reports which keys those are. A default nobody computed stays out —
        # Phase 1's honesty rule became a filter, not a whole-axis exclusion.
        for ax_name in ("alpha", "beta", "gamma", "delta", "epsilon"):
            dim = sm.dimensions.get(ax_name)
            if dim:
                axes[ax_name] = {"values": dim.values.copy()}
        zdim = sm.dimensions.get("zeta")
        observed: Any = getattr(sm, "zeta_observed_fields", frozenset())
        if zdim and observed:
            axes["zeta"] = {
                "values": {k: zdim.values[k] for k in sorted(observed) if k in zdim.values}
            }
        th = sm.theta.values if hasattr(sm, "theta") else {}
        from core.engine.eta_axis import measured_eta_metrics

        # None = "not measured", never 0.0 — see measured_eta_metrics(), the
        # single place that decides which η numbers have an observation.
        eta_metrics = measured_eta_metrics(eta_state)
        # Phase 3 item 1: η.structural_drift belongs to the AL snapshot
        # (drift.eta, §9) — the prompt reads it there, so this AI-side copy
        # would have no reader left. AI-layer execution stats (module_count,
        # execution_count, success_rate) are not snapshot fields and stay.
        eta_metrics.pop("structural_drift", None)
        context["state_for_llm"] = {
            "axes": axes,
            "theta": {
                "novelty": th.get("novelty", 0.0),
                "theta_negativity": th.get("theta_negativity", 0.0),
                "creation_urge": th.get("creation_urge", 0.0),
                "correction_urge": th.get("correction_urge", 0.0),
            },
            "eta": eta_metrics,
            "guidance": [],
        }
    except Exception as e:
        logger.warning(f"StateMatrix4D unavailable: {e}", exc_info=True)


def _ctx_retrieved(
    context: Dict[str, Any], history: List[Dict[str, Any]], user_message: str
) -> None:
    """ED3N context retrieval from history."""
    retrieved_ctx: List[Dict[str, Any]] = []
    if history and len(history) > 0:
        try:
            ed3n = _get_ed3n_engine()
            # Per-request memo: encode() scans the 460k-entry index; history
            # repeats content across turns and within a turn (audit 2026-10-10).
            _encode_memo: Dict[str, set] = {}

            def _encode_cached(text: str) -> set:
                hit = _encode_memo.get(text)
                if hit is None:
                    hit = set(ed3n.dictionary.encode(text))
                    _encode_memo[text] = hit
                return hit

            query_keys = _encode_cached(user_message)
            for entry in history:
                content = entry.get("content", "")
                if not content:
                    continue
                entry_keys = _encode_cached(content)
                overlap = len(query_keys & entry_keys)
                if overlap > 0:
                    retrieved_ctx.append({**entry, "relevance": float(overlap)})
            retrieved_ctx.sort(key=lambda x: x["relevance"], reverse=True)
            retrieved_ctx = retrieved_ctx[:5]
        except Exception as e:
            logger.warning(f"ED3N context retrieval failed: {e}", exc_info=True)
    context["retrieved_context"] = retrieved_ctx


def _ctx_dialogue(context: Dict[str, Any], session_id: str, user_message: str) -> None:
    """Dialogue context injection."""
    try:
        dialogue_ctx = _get_dialogue_ctx()
        if session_id:
            dialogue_ctx.add_message(session_id, "Human", user_message)
            conv_ctx = dialogue_ctx.get_conversation_context(session_id)
            if conv_ctx:
                context["dialogue_context"] = conv_ctx
    except Exception as e:
        logger.warning(f"Dialogue context unavailable: {e}", exc_info=True)


def _ctx_memories(context: Dict[str, Any]) -> None:
    """Memory context injection."""
    try:
        dialogue_ctx = _get_dialogue_ctx()
        recent_memories = dialogue_ctx.get_recent_conversations(limit=5)
        if recent_memories:
            context["recent_memories"] = recent_memories
    except Exception as e:
        logger.warning(f"Memory context unavailable: {e}", exc_info=True)


async def _build_chat_context(
    context: Dict[str, Any],
    user_message: str,
    user_name: str,
    history: List[Dict[str, Any]],
    session_id: str,
    chat_svc: Any,
    bio: Any,
) -> None:
    """Build the full LLM context: bio state, state matrix, retrieved context, dialogue, memory.
    Mutates the `context` dict in-place."""
    _ctx_bio_state(context, bio)
    _ctx_state_matrix(context)
    _ctx_retrieved(context, history, user_message)
    _ctx_dialogue(context, session_id, user_message)
    _ctx_memories(context)

    # History in context
    if history:
        context["history"] = history

    _ctx_al_state(context, stage="context")


def _gate_detail_text(action_result: Any) -> str:
    """Handler 回傳裡的人讀細節（dict.message/status/path 或純字串）。"""
    if isinstance(action_result, dict):
        payload = action_result.get("result")
        if isinstance(payload, dict):
            return str(payload.get("message") or payload.get("status") or payload.get("path") or "")
        if payload:
            return str(payload)
    if isinstance(action_result, str):
        return action_result.strip()
    return ""


def _gate_execution_response(
    *,
    executed: bool,
    handler_id: str,
    action_result: Any,
    error: str,
    schema_ver: str,
    session_id: str,
) -> Dict[str, Any]:
    """Report the outcome of a user-confirmed action.

    The gate executed the action, so the user must be told what happened —
    including failures. Returning None here previously let the LLM answer a
    request whose side effect had already been applied (or lost).
    """
    if executed:
        detail = _gate_detail_text(action_result)
        text = f"已執行：{handler_id}。" + (f"（{detail}）" if detail else "")
        source = "gate_executed"
        hit_source = "gate_executed"
    else:
        text = f"執行失敗：{handler_id}。" + (f"原因：{error}" if error else "")
        source = "gate_execute_failed"
        hit_source = "gate_execute_failed"
        logger.warning("Confirmed action failed: handler=%s error=%s", handler_id, error)
    return {
        "response_text": text,
        "response": text,
        "source": source,
        "schema_version": schema_ver,
        "truncation_message": "",
        "emotion": "neutral",
        "emotion_confidence": 0.5,
        "emotion_intensity": 0.5,
        "hit_score": 1.0 if executed else 0.0,
        "hit_source": hit_source,
        "route": f"gate:{handler_id}",
        "session_id": session_id,
    }


async def _persist_gate_interaction(
    user_message: str, response_text: str, chat_svc: Any, context: Dict[str, Any]
) -> None:
    """Gate 捷徑也要寫對話記憶（audit 2026-10-18：研究結果原本不進
    /context/memory/recent——gate 提前 return 跳過了 generate 路徑的
    ``_store_interaction_memories``）。Best-effort：失敗只記日誌不擋回應。
    """
    if not chat_svc or not response_text:
        return
    store = getattr(chat_svc, "store_gate_interaction", None)
    if store is None:
        return
    try:
        await store(user_message, response_text, context)
    except Exception as e:
        logger.warning("Gate interaction memory store failed: %s", e, exc_info=True)


async def _synthesize_research_response(
    user_message: str, extractive_answer: str, chat_svc: Any
) -> str:
    """web_search gate：LLM 把抽取式材料歸納成自然語言終答（走 AI）。

    audit 2026-10-18 第二輪：研究回答「不走 AI」——handler 只吐結構化
    材料。此處在 gate 回應前過一遍 LLM（短提示、低溫、只准用材料），
    失敗/超時/LLM 不可用 → 原樣回傳抽取式答案（結構完整仍可答）。
    來源清單不可丟：LLM 輸出缺「【來源」時從材料尾端補回。
    """
    if not chat_svc or not extractive_answer:
        logger.info(
            "[Research-Synth] no chat_svc=%s material=%d → extractive",
            bool(chat_svc),
            len(extractive_answer),
        )
        return extractive_answer
    gen = getattr(chat_svc, "generate_text", None)
    if gen is None:
        logger.info("[Research-Synth] chat_svc lacks generate_text → extractive")
        return extractive_answer
    from core.system.config.magic_numbers import timeout_value

    system_prompt = (
        "你是研究助理。只根據給定的來源材料回答，嚴禁編造材料沒有的數字或結論。"
        "材料不足以回答問題時，明說缺口並列出已知事實。150-350 字，"
        "可條列；若多來源互相矛盾，指出矛盾並建議以官方頁為準。"
        "結尾保留原樣的「【來源】」清單（含可信度標記）。"
    )
    prompt = f"研究問題：{user_message}\n\n來源材料：\n{extractive_answer}"
    try:
        out = await asyncio.wait_for(
            gen(prompt=prompt, max_tokens=600, temperature=0.2, system_prompt=system_prompt),
            timeout=timeout_value("research.llm_synthesis", 60.0),
        )
    except Exception as e:
        logger.debug("research LLM synthesis skipped: %s", e)
        return extractive_answer
    if not out or len(str(out).strip()) < 40:
        logger.info(
            "[Research-Synth] empty/short LLM output (%s chars) → extractive",
            0 if not out else len(str(out).strip()),
        )
        return extractive_answer
    text = str(out).strip()
    if "【來源" not in text:
        tail_at = extractive_answer.rfind("【來源")
        if tail_at != -1:
            text = text + "\n" + extractive_answer[tail_at:]
    logger.info(
        "[Research-Synth] LLM answer applied (%d chars, material %d chars)",
        len(text),
        len(extractive_answer),
    )
    return text


async def _handle_execution_gate(
    user_message: str,
    chat_svc: Any,
    context: Dict[str, Any],
    schema_ver: str,
    session_id: str,
) -> Optional[Dict[str, Any]]:
    """Delegate to the shared execution-gate owner and shape its response.

    GateExecutionOwner is the single owner of "may this action run"; this
    wrapper only translates the transport-neutral GateOutcome into the route
    response dict. Returns a response dict when the gate short-circuits
    (confirm / cancel / executed / failed), else None.
    """
    from services.execution.gate_execution import (
        OUTCOME_AGENT_EXECUTED,
        OUTCOME_CANCEL,
        OUTCOME_CONFIRM,
        OUTCOME_EXECUTED,
        GateExecutionOwner,
    )

    try:
        from ai.agents.agent_orchestrator import AgentOrchestrator

        if (
            AgentOrchestrator.is_eda_execution_request(user_message)
            or AgentOrchestrator.is_ai_card_request(user_message)
            or (
                context.get("_eda_followup") is True
                and AgentOrchestrator.is_eda_followup_request(user_message)
            )
        ):
            context["eda_request"] = True
            return None
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("EDA request detection failed: %s", exc, exc_info=True)

    model_bus = getattr(chat_svc, "model_bus", None) if chat_svc else None
    owner = GateExecutionOwner(session_store=sessions)
    outcome = await owner.process(user_message, context, session_id, model_bus)
    # Mark the context so downstream services (ChatService) do not run a second
    # gate pass for the same request.
    context["_gate_processed"] = True
    if not outcome.is_terminal:
        return None

    if outcome.action in (OUTCOME_EXECUTED, OUTCOME_AGENT_EXECUTED):
        resp = _gate_execution_response(
            executed=True,
            handler_id=outcome.handler or "",
            action_result=outcome.result,
            error=outcome.error,
            schema_ver=schema_ver,
            session_id=session_id,
        )
        # web_search：回應本體是研究答案（AI 歸納；不套「已執行：」殼）。
        if "web_search" in (outcome.handler or ""):
            material = _gate_detail_text(outcome.result)
            if material:
                resp["response_text"] = resp["response"] = await _synthesize_research_response(
                    user_message, material, chat_svc
                )
        await _persist_gate_interaction(
            user_message, resp.get("response_text", ""), chat_svc, context
        )
        return resp
    if outcome.action == OUTCOME_CANCEL:
        return {
            "response_text": outcome.message,
            "response": outcome.message,
            "source": "gate_cancel",
            "schema_version": schema_ver,
            "truncation_message": "",
            "emotion": "neutral",
            "emotion_confidence": 0.5,
            "emotion_intensity": 0.5,
            "hit_score": 0.0,
            "hit_source": "gate_cancel",
            "route": "gate_cancel",
            "session_id": session_id,
        }
    if outcome.action == OUTCOME_CONFIRM:
        return {
            "response_text": outcome.message,
            "response": outcome.message,
            "source": "gate_confirm",
            "schema_version": schema_ver,
            "truncation_message": "",
            "emotion": "neutral",
            "emotion_confidence": outcome.confidence,
            "emotion_intensity": 0.5,
            "hit_score": outcome.confidence,
            "hit_source": "gate_confirm",
            "route": outcome.query_type,
            "session_id": session_id,
        }
    # failed / agent_failed — never hide a failed side effect behind the LLM
    return _gate_execution_response(
        executed=False,
        handler_id=outcome.handler or "",
        action_result=None,
        error=outcome.error,
        schema_ver=schema_ver,
        session_id=session_id,
    )


# Module-level singleton caches for AgentManager + AgentOrchestrator
# Created once on first request to avoid reinitializing AgentManager
# (which re-registers all specialized agents) on every chat request.
_agent_manager_instance = None
_agent_orchestrator_instance = None


def _agent_route_clock_skip(user_message: str) -> bool:
    """Deterministic clock owns time/date questions — skip agent handling.

    The knowledge agent would otherwise answer with dictionary translation
    fragments ("the present"). Skip so the router's clock step answers
    (live probe 2026-10-09).
    """
    try:
        from services.llm.router import clock_query_kind

        if clock_query_kind(user_message) is not None:
            return True
    except Exception:
        logger.warning(
            "clock_query_kind probe failed; time questions may leak to " "knowledge agent",
            exc_info=True,
        )
    return False


def _agent_route_classify(user_message: str, context: Dict[str, Any]) -> Tuple[str, float]:
    """Reuse the classification already computed by _handle_execution_gate.

    Stored on context to avoid classifying the same message twice per request
    — QueryClassifier construction + ED3N encode is not cheap.
    """
    cached_type = context.get("_classify_result_type")
    cached_conf = context.get("_classify_result_confidence")
    if cached_type is not None:
        return str(cached_type), float(cached_conf) if cached_conf is not None else 0.0
    from services.llm.context_scheduler import get_context_scheduler

    plan = get_context_scheduler().plan_query(user_message, context)
    return plan.query_type, plan.confidence


def _agent_route_eda_override(
    user_message: str,
    context: Dict[str, Any],
    agent_orchestrator_cls: Any,
    primary_type_name: str,
    confidence: float,
) -> Tuple[str, float]:
    """EDA/AI-card requests override the classification to eda (high confidence)."""
    eda_request = agent_orchestrator_cls.is_eda_execution_request(user_message)
    ai_card_request = agent_orchestrator_cls.is_ai_card_request(user_message)
    eda_followup = context.get(
        "_eda_followup"
    ) is True and agent_orchestrator_cls.is_eda_followup_request(user_message)
    if eda_request or ai_card_request or eda_followup:
        return "eda", max(confidence, 0.8)
    return primary_type_name, confidence


def _agent_route_filter_skip(
    primary_type_name: str, confidence: float, query_type_cls: Any
) -> bool:
    """Only route non-actionable intents with agent suitability (else fall to LLM)."""
    actionable = {
        t.value
        for t in (
            query_type_cls.FILE,
            query_type_cls.SEARCH,
            query_type_cls.CODE,
            query_type_cls.EXECUTE,
            query_type_cls.TASK,
            query_type_cls.SYSTEM,
        )
    }
    if primary_type_name in actionable:
        return True
    agent_types = {
        t.value
        for t in (
            query_type_cls.CREATIVE,
            query_type_cls.KNOWLEDGE,
            query_type_cls.OPINION,
            query_type_cls.VISION,
            query_type_cls.AUDIO,
            query_type_cls.LOGIC,
            query_type_cls.COMMAND,
        )
    }
    agent_types.add("eda")
    if primary_type_name not in agent_types and confidence < 0.3:
        return True
    return False


def _agent_route_init_singletons(
    lifespan_get_agent_manager: Any,
    get_training_coordinator: Any,
    agent_manager_cls: Any,
    agent_orchestrator_cls: Any,
    register_specialized_agents: Any,
) -> Any:
    """Lazy-init agent manager + orchestrator singletons, reuse across requests.

    Prefer the lifespan-initialized AgentManager singleton when available so
    specialized agents are only registered once per process.
    """
    global _agent_manager_instance, _agent_orchestrator_instance
    if _agent_manager_instance is None and lifespan_get_agent_manager is not None:
        _agent_manager_instance = lifespan_get_agent_manager()
    if _agent_manager_instance is None:
        _agent_manager_instance = agent_manager_cls(
            enable_process_agents=False, enable_router=False
        )
        training_coordinator = (
            get_training_coordinator() if get_training_coordinator is not None else None
        )
        register_specialized_agents(
            _agent_manager_instance,
            training_coordinator=training_coordinator,
        )
        _agent_orchestrator_instance = agent_orchestrator_cls(agent_manager=_agent_manager_instance)
        logger.info("AgentManager/AgentOrchestrator singletons initialized")
    elif _agent_orchestrator_instance is None:
        _agent_orchestrator_instance = agent_orchestrator_cls(agent_manager=_agent_manager_instance)
    return _agent_orchestrator_instance


async def _agent_wire_model_bus(orchestrator: Any) -> None:
    # Handler-backed intents (file/code/web_search) execute through the
    # per-request ChatService's ModelBus; the orchestrator singleton must
    # see it to route them (previously never wired → those intents were
    # dead and silently fell back to the LLM).
    agent_chat_svc = await _get_chat_service()
    if agent_chat_svc and agent_chat_svc.model_bus:
        orchestrator.model_bus = agent_chat_svc.model_bus


def _agent_route_code_write_bypass(user_message: str) -> bool:
    """Code-WRITE requests must reach the LLM, not a code agent's confirm gate.

    There is no code to run yet (mirrors the execution-gate bypass; live
    2026-10-10 Unity script blocked here instead). Message-level detection
    (not agent-name): the blocking agent varies while the request shape is
    constant.
    """
    try:
        from services.execution.gate_execution import GateExecutionOwner

        if (
            GateExecutionOwner.is_code_write_request(user_message)
            and GateExecutionOwner._llm_generation_available()
        ):
            logger.debug("Agent routing skipped for code-write request")
            return True
    except Exception:
        logger.warning(
            "code-write gate probe failed; code-write requests may fall "
            "through to general agent routing",
            exc_info=True,
        )
    return False


def _agent_route_gate(
    primary: Dict[str, Any],
    user_message: str,
    context: Dict[str, Any],
    schema_ver: str,
    session_id: str,
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Handle ExecutionGate confirm/reject. Returns (handled, response)."""
    gate_action = primary.get("gate_action")
    if gate_action not in ("confirm_then_execute", "reject"):
        return False, None
    # ExecutionGate blocked the specialized agent (irreversible action needs
    # explicit confirmation). Surface the confirmation instead of silently
    # falling through to the LLM, mirroring the handler gate flow above.
    confirm_text = primary.get("confirm_message") or (
        "這個操作需要你確認後我才會執行：" f"{user_message}"
    )
    if gate_action == "confirm_then_execute":
        pending = {
            "kind": "agent",
            "agent": primary.get("agent"),
            "intent": primary.get("intent"),
            "original_query": user_message,
        }
        context["pending_action"] = pending
        session_data = sessions.get(session_id) or {}
        session_data["pending_action"] = pending
        sessions.set(session_id, session_data)
        return True, {
            "response_text": confirm_text,
            "response": confirm_text,
            "source": "gate_confirm",
            "schema_version": schema_ver,
            "truncation_message": "",
            "emotion": "neutral",
            "emotion_confidence": 0.5,
            "emotion_intensity": 0.5,
            "hit_score": 0.0,
            "hit_source": "gate_confirm",
            "route": "agent_gate_confirm",
            "session_id": session_id,
        }
    logger.info(
        "ExecutionGate rejected agent %s: %s",
        primary.get("agent"),
        primary.get("gate_reason"),
    )
    return True, None


def _agent_route_result(
    primary: Dict[str, Any], context: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Extract the specialized agent's result into a response dict."""
    agent_result = primary.get("result")
    if not (agent_result and isinstance(agent_result, dict) and agent_result.get("result")):
        return None
    inner = agent_result["result"]
    # Specialized agents return dicts like {"status": "success"} — an
    # error/unavailable status must not be presented as a successful
    # response (fall through to the LLM instead).
    if isinstance(inner, dict) and inner.get("status") in (
        "error",
        "unavailable",
        "failed",
    ):
        logger.debug(
            "Agent %s returned non-success status; falling back to LLM: %s",
            primary.get("agent", "unknown"),
            inner.get("status"),
        )
        return None
    response_text = (
        inner.get("message") if isinstance(inner, dict) and inner.get("message") else str(inner)
    )
    context["_agent_result"] = response_text
    context["_agent_result_source"] = primary.get("agent", "unknown")
    return {
        "response": response_text,
        "source": primary.get("agent", "unknown"),
        "confidence": primary.get("confidence", 0.8),
    }


async def _try_agent_routing(
    user_message: str,
    context: Dict[str, Any],
    schema_ver: str,
    session_id: str,
) -> Optional[Dict[str, Any]]:
    """Try agent auto-routing for non-execution intents (creative/knowledge/opinion/search).
    Returns a response dict if an agent handled the query, else None (falls through to LLM)."""
    try:
        from ai.agents.agent_adapter import register_specialized_agents
        from ai.agents.agent_manager import AgentManager
        from ai.agents.agent_orchestrator import AgentOrchestrator
        from ai.core.query_classifier import QueryType

        try:
            from api.lifespan import get_agent_manager as _lifespan_get_agent_manager
            from api.lifespan import get_training_coordinator as _get_training_coordinator
        except ImportError:
            _lifespan_get_agent_manager = None  # type: ignore[assignment]
            _get_training_coordinator = None  # type: ignore[assignment]

        if _agent_route_clock_skip(user_message):
            return None

        primary_type_name, confidence = _agent_route_classify(user_message, context)
        primary_type_name, confidence = _agent_route_eda_override(
            user_message, context, AgentOrchestrator, primary_type_name, confidence
        )
        if _agent_route_filter_skip(primary_type_name, confidence, QueryType):
            return None

        orchestrator = _agent_route_init_singletons(
            _lifespan_get_agent_manager,
            _get_training_coordinator,
            AgentManager,
            AgentOrchestrator,
            register_specialized_agents,
        )
        await _agent_wire_model_bus(orchestrator)
        route_result = await orchestrator.route_task(user_message, context)

        primary = route_result.get("results", [{}])[0] if route_result.get("results") else {}

        if _agent_route_code_write_bypass(user_message):
            return None
        handled, gate_resp = _agent_route_gate(
            primary, user_message, context, schema_ver, session_id
        )
        if handled:
            return gate_resp
        return _agent_route_result(primary, context)
    except Exception as e:
        logger.warning(f"Agent routing unavailable: {e}", exc_info=True)
    return None


# Table-driven causal→routing bias rules (see _get_causal_routing_adjustment).
_CAD_RULES = (
    # (cause, threshold, temp_coeff, token_coeff, conf_gain, label)
    ("user_input", 0.5, -0.15, 0.0, 0.3, "user_input→response"),
    ("query_complexity", 0.3, -0.1, 128.0, 0.3, "complexity→response"),
    ("conversation_momentum", 0.4, 0.1, 64.0, 0.2, "momentum→input"),
    ("interaction_value", 0.3, 0.0, 128.0, 0.2, "interaction_value→input"),
)


def _cad_zero() -> Dict[str, Any]:
    """Neutral causal-routing adjustment (fresh dict per call — no aliasing)."""
    return {
        "temperature_bias": 0.0,
        "max_tokens_bias": 0,
        "causal_confidence": 0.0,
        "effective_guidance": "",
    }


def _cad_apply_rule(
    causal: Any,
    cause: str,
    threshold: float,
    temp_coeff: float,
    token_coeff: float,
    conf_gain: float,
    label: str,
) -> Optional[Tuple[float, int, float, str]]:
    """Apply one causal-adjustment rule. Returns None when strength is below threshold."""
    preds: List[Dict[str, float]] = causal.predict(cause)
    strength = (sum(p["strength"] for p in preds) / len(preds)) if preds else 0.0
    if strength <= threshold:
        return None
    temp_adj = temp_coeff * min(1.0, strength)
    token_adj = int(token_coeff * min(1.0, strength))
    parts = [f"strength={strength:.2f}"]
    if temp_coeff != 0:
        parts.append(f"temp{temp_adj:+.3f}")
    if token_coeff != 0:
        parts.append(f"+{token_adj}tok")
    return temp_adj, token_adj, conf_gain, f"{label} ({', '.join(parts)})"


def _get_causal_routing_adjustment() -> Dict[str, Any]:
    """Compute concrete routing adjustments from learned causal relationships.

    Reads the CausalReasoningEngine's predictions and translates them into
    actionable LLM generation parameter biases. This closes the C³ loop:
    causal predictions → actual routing parameter changes (not just prompt text).

    Returns:
        Dict with:
        - temperature_bias: float (-0.3 to +0.3) modifier for LLM temperature
        - max_tokens_bias: int (-256 to +256) modifier for max_tokens
        - causal_confidence: float (0-1) confidence in the routing adjustment
        - effective_guidance: str human-readable description of the adjustment
    """
    try:
        causal = get_causal_reasoning()
        if not causal:
            return _cad_zero()

        rels = causal.get_relationships()
        if not rels:
            return _cad_zero()

        temp_bias = 0.0
        tokens_bias = 0
        confidence = 0.0
        guidance_parts: List[str] = []

        for rule in _CAD_RULES:
            hit = _cad_apply_rule(causal, *rule)
            if hit is None:
                continue
            temp_adj, token_adj, conf, guidance = hit
            temp_bias += temp_adj
            tokens_bias += token_adj
            confidence += conf
            guidance_parts.append(guidance)

        effective_guidance = "; ".join(guidance_parts) if guidance_parts else ""
        return {
            "temperature_bias": round(max(-0.3, min(0.3, temp_bias)), 3),
            "max_tokens_bias": max(-256, min(256, tokens_bias)),
            "causal_confidence": round(min(1.0, confidence), 3),
            "effective_guidance": effective_guidance,
        }
    except Exception as e:
        logger.warning(f"Causal routing adjustment failed: {e}", exc_info=True)
        return _cad_zero()


def _inject_causal_predictions(context: Dict[str, Any]) -> None:
    """Inject causal reasoning predictions into LLM context before generation.

    Calls causal.predict() to surface learned causal relationships,
    which are then injected into context for the prompt builder to read.
    Also computes concrete routing adjustments (temperature_bias, max_tokens_bias)
    to close the causal closed-loop — predictions affect actual LLM parameters.
    """
    try:
        causal = get_causal_reasoning()
        if causal:
            predictions = causal.predict("user_input")
            if predictions:
                context["causal_insights"] = {
                    "predictions": predictions[:3],
                    "has_causal_data": len(causal.get_relationships()) > 0,
                    "total_relationships": len(causal.get_relationships()),
                }
                logger.debug(f"Injected {len(predictions)} causal predictions into context")
            # C³ closed-loop: inject concrete routing adjustments
            routing_adj = _get_causal_routing_adjustment()
            if routing_adj["causal_confidence"] >= 0.25:
                context["causal_routing"] = routing_adj
                logger.debug(
                    f"Causal routing adjustment: temp={routing_adj['temperature_bias']:+.3f}, "
                    f"tokens={routing_adj['max_tokens_bias']:+d}, "
                    f"confidence={routing_adj['causal_confidence']:.2f} — "
                    f"{routing_adj['effective_guidance']}"
                )
    except Exception as e:
        logger.warning(f"Causal prediction injection failed: {e}", exc_info=True)


# ── Per-session temporal buffers for causal learning ─────────────────────
# Accumulates time-series data across multiple interactions so Granger
# causality can fire (requires >= 5 samples per variable).
_CAUSAL_BUFFERS: Dict[str, Dict[str, List[float]]] = {}
_CAUSAL_BUFFER_MAX_SESSIONS = 200  # Evict oldest when exceeded
# Per-variable cap: a single long session must not grow its series without
# bound (200 sessions x 3 vars x 1000 floats ≈ 5MB worst case). Granger needs
# >= 5 samples; 1000 keeps 200x headroom.
_CAUSAL_BUFFER_MAX_SAMPLES = 1000
_CAUSAL_BUFFERS_LOCK = threading.Lock()


def _get_causal_buffer(session_id: str) -> Dict[str, List[float]]:
    """Get or create a temporal buffer for the given session (true LRU)."""
    with _CAUSAL_BUFFERS_LOCK:
        if session_id in _CAUSAL_BUFFERS:
            # Touch on access: eviction must drop the least-RECENTLY-used,
            # not least-recently-inserted (audit 2026-10-10). Plain dicts
            # have no move_to_end: pop + reinsert instead.
            buf = _CAUSAL_BUFFERS.pop(session_id)
            _CAUSAL_BUFFERS[session_id] = buf
            return buf
        if len(_CAUSAL_BUFFERS) >= _CAUSAL_BUFFER_MAX_SESSIONS:
            oldest = next(iter(_CAUSAL_BUFFERS))
            del _CAUSAL_BUFFERS[oldest]
        _CAUSAL_BUFFERS[session_id] = {
            "msg_lengths": [],
            "resp_lengths": [],
            "engagement_ratios": [],
        }
        return _CAUSAL_BUFFERS[session_id]


def _trim_causal_series(buf: Dict[str, List[float]]) -> None:
    """Trim per-session series to the sample cap (keeps the recent window)."""
    for key in ("msg_lengths", "resp_lengths", "engagement_ratios"):
        series = buf[key]
        if len(series) > _CAUSAL_BUFFER_MAX_SAMPLES:
            del series[: len(series) - _CAUSAL_BUFFER_MAX_SAMPLES]


def _log_loop_signal(response_text: str, session_id: str) -> None:
    """Observability only: log when a response enters a repetition loop.

    Never alters, blocks, or retries the response. Research verdict (E2/E6):
    the loop detector is validated, but no proven transmission shaft exists —
    so production monitors instead of intervening.
    """
    try:
        from ai.attention.degeneracy import detect_loop

        if response_text and detect_loop(response_text):
            logger.warning(
                "Loop detected in response (session=%s, len=%d)",
                session_id,
                len(response_text),
            )
    except Exception as e:
        logger.debug(f"Loop monitor skipped: {e}", exc_info=True)


def _causal_feedback_loops(resp_msg_ratio: float, empty_response: bool) -> None:
    """Emotion/DLI/Lifecycle feedback loops: proxy ratio → adjustments (C³ 4.0)."""
    # Emotion feedback loop: proxy ratio → internal emotion-label adjustment
    try:
        es = _get_emotion_system()
        if es:
            es.process_interaction_feedback(
                engagement_ratio=resp_msg_ratio,
                had_error=empty_response,
                response_success=None,
            )
    except Exception as e:
        logger.warning(f"Emotion feedback loop failed: {e}", exc_info=True)

    # DLI feedback loop: proxy ratio → modality gateway adjustment
    try:
        dli = get_digital_life()
        if dli:
            dli.process_interaction_feedback(
                engagement_ratio=resp_msg_ratio,
                success=not empty_response,
            )
    except Exception as e:
        logger.warning(f"DLI feedback loop failed: {e}", exc_info=True)

    # Lifecycle feedback loop: proxy ratio → phase-aware routing
    try:
        alc = _get_lifecycle()
        if alc:
            alc.feed_interaction_outcome(
                engagement_ratio=resp_msg_ratio,
                success=not empty_response,
            )
    except Exception as e:
        logger.warning(f"Lifecycle feedback loop failed: {e}", exc_info=True)


def _causal_build_data(
    buf: Dict[str, List[float]], msg_len: float, resp_len: float
) -> Dict[str, List[float]]:
    """Only pass the accumulated series (not a single value) once we have
    enough temporal depth for Granger causality."""
    if len(buf["msg_lengths"]) >= 5:
        return {
            "user_input": list(buf["msg_lengths"]),
            "angela_response": list(buf["resp_lengths"]),
        }
    return {"user_input": [msg_len], "angela_response": [resp_len]}


def _causal_record_temporal(
    causal: Any, msg_len: float, resp_len: float, resp_msg_ratio: float
) -> None:
    """C³ 4.0: Record snapshot into the AL-side temporal bridge and
    periodically call ingest_temporal_state() for Granger causality.

    The bridge lives in ``core.life.al_temporal`` (Phase 3 item 2): writes go
    through its controlled entry ``record_interaction()``, reads (deciding
    when to feed the causal engine) stay here in the assembly layer.
    """
    from core.life.al_temporal import record_interaction

    ts = record_interaction(msg_len, resp_len, resp_msg_ratio)
    if ts.size() >= 5 and ts.size() % 5 == 0:
        causal.ingest_temporal_state(ts, window=20)


def _fire_causal_learning(response_text: str, user_message: str, session_id: str) -> None:
    """Accumulate temporal data and learn causal relationships per session.

    Maintains per-session buffers so Granger causality (>= 5 samples) can
    detect temporal precedence in real conversation patterns.
    """
    try:
        causal = get_causal_reasoning()
        if not causal or not response_text:
            return

        buf = _get_causal_buffer(session_id)
        msg_len = float(len(user_message))
        resp_len = float(len(response_text))
        # 定義（非事實）：resp_msg_ratio := 回應字元數 / 提問字元數。
        # 這是下游 feedback 迴路使用的「投入度代理訊號」——它衡量回應
        # 相對提問的長度比，不是使用者投入度的量測本身。下游 API 參數名
        # 沿用歷史名稱 engagement_ratio；語意以此處定義為準。
        resp_msg_ratio = resp_len / max(msg_len, 1.0)
        # 定義（非事實）：empty_response := 回應為空。呼叫端以它作為
        # had_error / success 的最低限度代理——「非空」不等於「正確」
        # 或「有用」，只表示 LLM 產出了非零字元。
        empty_response = not response_text

        buf["msg_lengths"].append(msg_len)
        buf["resp_lengths"].append(resp_len)
        buf["engagement_ratios"].append(resp_msg_ratio)
        _trim_causal_series(buf)

        _causal_feedback_loops(resp_msg_ratio, empty_response)

        # Dynamic strength: scales with the length-ratio proxy (see definition
        # above), not with any measured quality of the response.
        dynamic_strength = min(0.9, max(0.1, resp_msg_ratio / 5.0))

        causal.learn(
            {
                "variables": ["user_input", "angela_response"],
                "data": _causal_build_data(buf, msg_len, resp_len),
                "relationships": [
                    {
                        "cause": "user_input",
                        "effect": "angela_response",
                        "strength": dynamic_strength,
                        "source": f"chat_{session_id}",
                    }
                ],
            }
        )

        _causal_record_temporal(causal, msg_len, resp_len, resp_msg_ratio)

        # Cap buffer at 100 entries per session to prevent unbounded growth
        if len(buf["msg_lengths"]) > 100:
            buf["msg_lengths"] = buf["msg_lengths"][-50:]
            buf["resp_lengths"] = buf["resp_lengths"][-50:]
            buf["engagement_ratios"] = buf["engagement_ratios"][-50:]

    except Exception as e:
        logger.warning(f"Causal learning failed: {e}", exc_info=True)


def _classify_feedback_target(
    response_text: str, context: Dict[str, Any], qc: Any
) -> Optional[Tuple[str, Any]]:
    """Determine best target type (priority: routing intent > response class > lifecycle).

    Returns (target_type, response_type), or None when still unknown.
    """
    # Step 1: Classify the LLM response to infer the user's true intent
    # (response usually contains content matching the intended type)
    response_type = qc.classify(response_text)

    # Also check routing context for ground truth
    lifecycle_adj = context.get("lifecycle_behavior", {})
    lc_mode = lifecycle_adj.get("routing_mode", "")
    intent_routing = context.get("intent_routing", {})
    intent_mode = intent_routing.get("routing_mode", "")

    # Determine best target type (priority: routing intent > response class > lifecycle)
    target_type = response_type.primary_type.value
    if intent_mode:
        target_type = intent_mode
    elif lc_mode and lc_mode != "neutral":
        target_type = lc_mode

    # Skip learning if still unknown
    if target_type == "unknown":
        return None
    return target_type, response_type


def _extract_learning_keywords(user_message: str) -> List[str]:
    """Step 2: Extract good keywords from the user's input (2-12 char tokens)."""
    import re

    tokens = re.findall(r"[\w\u4e00-\u9fff]+", user_message)
    keywords = [t for t in tokens if 2 <= len(t) <= 12 and t not in _LEARNING_STOPWORDS]
    return keywords[:3]  # Max 3 keywords per learning cycle


def _learn_keywords(
    dc: Any,
    keywords: List[str],
    target_type: str,
    target_action: str,
    user_message: str,
    response_type: Any,
) -> None:
    """Steps 4-5: Learn each keyword, then batch-persist the training data once."""
    learned_count = 0
    for kw in keywords:
        kw_lower = kw.lower().strip()
        if len(kw_lower) < 2:
            continue
        key = dc.learn(kw_lower, target_type, target_action, confidence=0.5, persist=False)
        if key:
            learned_count += 1

    # Step 5: Batch persist once
    if learned_count > 0:
        dc._persist_training_data()
        logger.info(
            f"Online learned {learned_count} keyword(s) from UNKNOWN input: "
            f"'{user_message[:40]}' → {target_type}/{target_action} "
            f"(response_type={response_type.primary_type.value})"
        )


def _learn_from_classification_feedback(
    user_message: str, response_text: str, context: Dict[str, Any]
) -> None:
    """Online self-learning: teach dictionary classifier from LLM responses.

    Triggered after every LLM response. If the QueryClassifier was uncertain
    (UNKNOWN or low confidence) but the LLM produced a good response, we:
    1. Extract distinguishing keywords from the user input
    2. Infer the correct query type from the LLM response text
    3. Add these keywords as training entries to DictionaryClassifier
    4. The next time a similar input arrives, it's classified correctly.
    """
    orig_type = context.get("_classify_result_type", "unknown")
    orig_confidence = context.get("_classify_result_confidence", 0.0)
    orig_action = context.get("_classify_result_action", "none")

    # Only learn from uncertain classifications
    if orig_type != "unknown" and orig_confidence >= 0.5:
        return

    if not response_text or len(response_text.strip()) < 5:
        return

    from ai.core.dictionary_classifier import get_dictionary_classifier

    dc = get_dictionary_classifier()

    qc = _get_query_classifier()
    classified = _classify_feedback_target(response_text, context, qc)
    if classified is None:
        return
    target_type, response_type = classified

    keywords = _extract_learning_keywords(user_message)
    if not keywords:
        return

    # Step 3: Infer best action_type from the original classify
    target_action = orig_action if orig_action != "none" else "read"

    # Step 4-5: Learn each keyword, then batch persist once
    _learn_keywords(dc, keywords, target_type, target_action, user_message, response_type)


def _handle_timeout(session_id: str, schema_ver: str) -> Dict[str, Any]:
    """Handle LLM timeout with fallback response."""
    logger.warning(f"LLM response timeout for session: {session_id}")
    try:
        timeout_text = _get_ed3n_engine().process(
            "timeout_response", context={"fallback": True}, depth="reflex"
        )
    except Exception as e:
        logger.warning(f"ED3N fallback failed in timeout handler: {e}", exc_info=True)
        timeout_text = "\u62b1\u6b49\uff0c\u6211\u76ee\u524d\u65e0\u6cd5\u56de\u5e94\uff0c\u8bf7\u7a0d\u540e\u518d\u8bd5\u3002"
    return {
        "response_text": timeout_text,
        "response": timeout_text,
        "source": "fallback-timeout",
        "schema_version": schema_ver,
        "truncation_message": "",
        "emotion": "neutral",
        "emotion_confidence": 0.5,
        "emotion_intensity": 0.5,
        "session_id": session_id,
    }


def _format_chat_response(
    response_text: str,
    llm_response: Any,
    emotion_result: Optional[Dict[str, Any]],
    schema_ver: str,
    trunc_msg: str,
    user_message: str,
    max_len: int,
    session_id: str,
    source: str = "angela_chat_service",
    was_truncated: bool = False,
) -> Dict[str, Any]:
    """Build the final standardized chat response dict."""
    # Make the actual provider/model explicit so callers can see exactly which
    # engine answered (local neural SNN, deterministic knowledge layer, model
    # bus, or a cloud LLM). The internal ``route`` field is unreliable for the
    # non-LLM paths (template/memory/knowledge/model_bus never set it and fall
    # back to the default "llm"), so derive an accurate route from ``backend``.
    # llm_response may be a plain dict (knowledge_pipeline / agent early
    # returns); getattr on a dict always misses and every such answer showed
    # backend "unknown", hiding the true source (live 2026-10-09: a
    # dictionary translation served as backend unknown). Read dict keys too.
    if isinstance(llm_response, dict):
        _backend = llm_response.get("backend") or "unknown"
        # A dict's keys are not attributes: reading only getattr() here made
        # every dict-returning producer lose its declared route and fall through
        # to "llm" (a knowledge lookup was reported as an LLM reply).
        _declared_route = llm_response.get("route")
        _metadata = llm_response.get("metadata") or {}
    else:
        _backend = getattr(llm_response, "backend", None) or "unknown"
        _declared_route = getattr(llm_response, "route", None)
        _metadata = getattr(llm_response, "metadata", {}) or {}
    _route_map = {
        "knowledge": "knowledge",
        "knowledge_base": "knowledge",
        "knowledge_pipeline": "knowledge",
        "dialogue-memory": "memory",
        "composed-template": "template",
        "deterministic-math": "computed",
        "model_bus": "model_bus",
        "ed3n": "ed3n",
        "garden": "garden",
        "unified": "unified",
        "neuro-blender": "fallback",
        "local-fallback": "fallback",
        "google": "llm",
        "openai": "llm",
        "anthropic": "llm",
        "ollama": "llm",
        "llamacpp": "llm",
        "error": "error",
    }
    _derived_route = _declared_route or _metadata.get("route") or _route_map.get(_backend)
    if _derived_route is None:
        _derived_route = "fallback" if _metadata.get("fallback") else "unknown"
    return {
        "response_text": response_text,
        "response": response_text,
        "source": source,
        "schema_version": schema_ver,
        "truncation_message": trunc_msg if was_truncated else "",
        "emotion": emotion_result.get("emotion", "neutral") if emotion_result else "neutral",
        "emotion_confidence": emotion_result.get("confidence", 0.5) if emotion_result else 0.5,
        "emotion_intensity": emotion_result.get("intensity", 0.5) if emotion_result else 0.5,
        "backend": _backend,
        "model": getattr(llm_response, "model", None) or "unknown",
        "confidence": getattr(llm_response, "confidence", None),
        "hit_score": getattr(llm_response, "hit_score", 0.0),
        "hit_source": getattr(llm_response, "hit_source", "none"),
        "route": _derived_route,
        # Abstain 通道（v1）：結構化棄權信封（無棄權=None，形狀穩定）。
        "abstain": _extract_abstain_envelope(llm_response),
        "session_id": session_id,
    }


async def _handle_chat_request(
    user_message: str,
    user_name: str,
    history: List[Dict[str, Any]],
    session_id: str,
    origin: str = "Human",
    extra_context: Optional[Dict[str, Any]] = None,
    mode: str = "1:1",
) -> Dict[str, Any]:
    """Orchestrate the full chat pipeline and persist the turn to session memory.

    Delegates to ``_run_chat_pipeline`` and always appends the user message +
    assistant response to the session's ``messages`` history (multi-turn memory),
    even on early-return paths (math/gate/agent/timeout).
    """
    # Session lifecycle is owned by the wrapper so every path (including
    # exceptions) has a session to persist the turn into.
    if session_id not in sessions:
        sessions.set(
            session_id,
            {
                "created_at": datetime.now().isoformat(),
                "origin": origin,
                "user_name": user_name,
                "messages": [],
            },
        )
    # Multi-turn memory: when the caller did not supply history, fall back to
    # the messages persisted for this session so past turns are not lost.
    # A copy is passed downstream so pipeline mutations never alias the
    # persisted session messages.
    session = sessions.get(session_id) or {}
    if not history:
        history = list(session.get("messages", []))
    result = None
    # Bind the requesting user for the whole turn: the instance name is
    # resolved per user, and every downstream consumer (prompt builder, reflex
    # engines, subtitle/TTS layer) reads the same binding.
    _user_token = _bind_current_user((extra_context or {}).get("user_id") or user_name)
    try:
        result = await _run_chat_pipeline(
            user_message,
            user_name,
            history,
            session_id,
            origin,
            extra_context,
            mode=mode,
        )
        return result
    finally:
        _unbind_current_user(_user_token)
        # Prefer the pipeline return value; fall back to the last captured
        # response so exceptions/partial failures still persist the turn.
        response_text = (result or {}).get("response_text") or _latest_responses.get(
            session_id, {}
        ).get("response_text")
        if session_id in sessions and user_message and response_text:
            try:
                # .get() 可回 None — Optional 型別如实宣告（原 Dict+ignore 与
                # 紧随的 is None 判斷自相矛盾）
                session_data: Optional[Dict[str, Any]] = sessions.get(session_id)
                if session_data is None:
                    raise HTTPException(status_code=404, detail="Session not found")
                messages_raw = session_data.get("messages")
                messages: List[Dict[str, Any]] = (
                    messages_raw if isinstance(messages_raw, list) else []
                )
                if not messages:
                    session["messages"] = messages
                messages.append(
                    {
                        "role": "user",
                        "content": user_message,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                messages.append(
                    {
                        "role": "assistant",
                        "content": response_text,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                # Bound history to avoid unbounded growth (keep last 40 turns)
                if len(messages) > 80:
                    del messages[: len(messages) - 80]
                session["messages"] = messages
                sessions.set(session_id, session)
            except Exception as e:
                logger.warning(f"Session history persistence failed: {e}", exc_info=True)


async def _run_chat_pipeline(
    user_message: str,
    user_name: str,
    history: List[Dict[str, Any]],
    session_id: str,
    origin: str = "Human",
    extra_context: Optional[Dict[str, Any]] = None,
    mode: str = "1:1",
) -> Dict[str, Any]:
    """Core chat pipeline: validate → math → context → emotion/crisis → execution gate → agent routing → LLM."""
    logger.info(
        f"\U0001f4e9 [LIS] Raw message received: '{user_message}' from {origin} (Session: {session_id})"
    )

    chat_cfg = (
        _angela_cfg.get_authority("angela_core", {}).get("chat_flow", {}) if _angela_cfg else {}
    )
    max_len = chat_cfg.get("max_message_length", 4000)
    schema_ver = chat_cfg.get("response_schema_version", "2.0")
    trunc_msg = chat_cfg.get("truncation_message", "...\uff08\u622a\u65ad\uff09")
    timeout = chat_cfg.get("http_timeout", 60.0)
    flow_source = chat_cfg.get("default_flow", "angela_chat_service")

    # Step 1: Validate and truncate input (raises HTTP 400 when invalid)
    _raw_input_len = len(user_message)
    user_message = _validate_input_or_400(user_message, chat_cfg)
    _was_truncated = _raw_input_len > max_len

    # Step 1b: dialogue teaching — a user statement becomes a taught fact (or
    # a relation alias: "首府和首都指的是同一件事"). This is the only training
    # signal that layer gets, and it runs before answering so a correction
    # applies to the very next question.
    try:
        from ai.memory.taught_facts import get_taught_facts

        get_taught_facts().learn_from_turn(user_message)
    except Exception:  # pragma: no cover - teaching must never break chat
        logger.debug("taught-facts learning failed", exc_info=True)

    # Step 1c: answer from what the user just taught. Freshest state wins over
    # recall/LLM, so "不是 A，是 B" is reflected in the very next question.
    taught_shortcircuit = _try_taught_facts(user_message, session_id, schema_ver, trunc_msg)
    if taught_shortcircuit is not None:
        return taught_shortcircuit

    # Step 2: Initialize context + best-effort priming (EDA / dispatch / MSBA)
    context = _prime_chat_context(user_message, user_name, origin, extra_context, history)
    # Step 2b: role binding (backend slot / memory namespace / trace id)
    _apply_role_binding(context)

    # Step 3: Math dual-rail verification (IntentRegistry-confirmed result short-circuits)
    math_shortcircuit = await _gate_math(
        user_message, user_name, session_id, schema_ver, trunc_msg, _was_truncated, context
    )
    if math_shortcircuit is not None:
        return math_shortcircuit

    # Step 4-5f: Emotion analysis + behavioral context injections + crisis
    bio = _get_bio_integrator()
    emotion_result, crisis_level = await _analyze_emotion_and_crisis(user_message, context, bio)
    if emotion_result:
        context["emotion"] = emotion_result
        await _inject_behavioral_context(context, emotion_result, bio)
    if crisis_level > 0:
        context["crisis_level"] = crisis_level
        context["crisis_instruction"] = (
            f"User input has crisis level {crisis_level}. "
            "Respond with empathy, provide support resources if appropriate, "
            "and prioritize user safety in your response."
        )
    await _try_alignment_check(user_message, crisis_level, context)

    # Step 5g-5h: Intent routing + DesktopInteraction wiring (context enrichment)
    chat_svc = await _get_chat_service()
    intent_result = await _try_intent_routing(user_message, chat_svc, user_name, context)
    if intent_result:
        context["_intent_result"] = intent_result
    _wire_desktop_interaction(context)

    # Step 6: Build full LLM context (bio state, state matrix, ED3N retrieval, dialogue, memory)
    chat_svc = await _get_chat_service()
    await _build_chat_context(context, user_message, user_name, history, session_id, chat_svc, bio)

    # Step 7: Execution gate (intent classification → auto/confirm/reject — may short-circuit)
    gate_result = await _handle_execution_gate(
        user_message, chat_svc, context, schema_ver, session_id
    )
    if gate_result:
        _set_latest_response(session_id, gate_result)
        return gate_result

    # Step 8: Agent auto-routing (creative/knowledge/opinion/vision/audio — may short-circuit)
    agent_result = await _try_agent_routing(user_message, context, schema_ver, session_id)
    if agent_result:
        agent_response = _wrap_agent_response(
            agent_result, schema_ver, trunc_msg, _was_truncated, session_id
        )
        _set_latest_response(session_id, agent_response)
        return agent_response

    # Step 9: Inject causal predictions into context (learned from past interactions)
    _inject_causal_predictions(context)

    # Step 9.5: Collect the scheduled MSBA result into context (best-effort)
    await _collect_msba_result(context)

    # Step 10: Generate LLM response (mode-aware; timeout → serve latest cached)
    try:
        llm_response = await _generate_llm_response(
            user_message, user_name, context, chat_svc, mode, timeout
        )
    except _LLMTimeoutError:
        _set_latest_response(session_id, _handle_timeout(session_id, schema_ver))
        return _latest_responses[session_id]

    response_text = _extract_response_text(llm_response)
    # Abstain 通道（v1）：把結構化棄權信封放進 context，供回饋閉環（10b/10d）
    # 與 API payload 使用（additive；無棄權=None）。每回合重算——同回合內
    # 生成完成後才 stamp，不會殘留上一回合的值。
    context["_abstain"] = _extract_abstain_envelope(llm_response)
    context["continuation_count"] = context.get("continuation_count", 0) + 1
    _fire_causal_learning(response_text, user_message, session_id)
    _log_loop_signal(response_text, session_id)

    # Step 10b/10c/10e: Post-response feedback loops (online learning + intent
    # outcome + solution-rule outcome)
    _record_post_response_feedback(context, response_text, user_message, _was_truncated, chat_svc)

    _set_latest_response(
        session_id,
        _format_chat_response(
            response_text,
            llm_response,
            emotion_result,
            schema_ver,
            trunc_msg,
            user_message,
            max_len,
            session_id,
            source=flow_source,
            was_truncated=_was_truncated,
        ),
    )
    return _latest_responses[session_id]


def _validate_input_or_400(user_message: str, chat_cfg: Dict[str, Any]) -> str:
    """Step 1: validate + truncate input. Raises HTTP 400 on invalid input."""
    try:
        return _validate_and_truncate_input(user_message, chat_cfg)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _detect_eda_followup(context: Dict[str, Any], history: List[Dict[str, Any]]) -> None:
    """EDA follow-up context detection (best-effort)."""
    try:
        from ai.agents.agent_orchestrator import AgentOrchestrator

        if any(
            AgentOrchestrator.is_ai_card_request(str(item.get("content", ""))) for item in history
        ):
            context["_eda_followup"] = True
    except Exception as exc:
        logger.debug("EDA follow-up context detection unavailable: %s", exc)


def _run_mainline_dispatch(
    context: Dict[str, Any],
    user_message: str,
    origin: str,
    extra_context: Optional[Dict[str, Any]],
) -> None:
    """Step 2.5: main-line dispatch hook — judges generation vs learning signal
    vs training data; enqueues training when a TrainingCoordinator exists."""
    try:
        from services.mainline_dispatcher import dispatch as _ml_dispatch

        _tc = None
        try:
            from core.backbone import get_backbone

            _tc = get_backbone().get_module("training_coordinator")
        except Exception:
            _tc = None
        _dispatch_decision = _ml_dispatch(
            {
                "text": user_message,
                "origin": origin,
                "time": (extra_context or {}).get("time"),
            },
            training_coordinator=_tc,
        )
        context["_dispatch_intent"] = _dispatch_decision.intent.value
    except Exception as _e:  # pragma: no cover - defensive
        logger.debug("Main-line dispatch hook skipped: %s", _e)


def _schedule_msba(context: Dict[str, Any], user_message: str) -> None:
    """Step 2.75: MSBA multi-dimensional semantic block processing — schedule
    non-blocking; result collected in Step 9.5."""
    try:
        from ai.msba.neuroblender_bridge import NeuroBlenderBridge

        _msba = _get_msba_pipeline()
        if _msba is not None:
            import asyncio as _asyncio

            # The context carries the classification the pipeline already
            # computed — the MSBA pipeline must not classify the message a
            # second time.
            _fused = _asyncio.ensure_future(_msba.process(user_message, context))
            context["_msba_task"] = _fused
            context["_msba_bridge"] = NeuroBlenderBridge()
            logger.debug("MSBA pipeline scheduled for input")
            if _msba_ab_enabled():
                context["_msba_ab_task"] = _asyncio.ensure_future(
                    _run_msba_ab_comparison(user_message)
                )
    except Exception as _e:
        logger.debug("MSBA scheduling skipped: %s", _e)


def _prime_chat_context(
    user_message: str,
    user_name: str,
    origin: str,
    extra_context: Optional[Dict[str, Any]],
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Step 2: initialize base context and run best-effort priming hooks.

    Base context must exist before any hook writes to it. EDA follow-up
    detection, main-line dispatch, and MSBA scheduling are all best-effort —
    they never raise into the response path.
    """
    context: Dict[str, Any] = {"user_name": user_name}
    if extra_context:
        context.update(extra_context)
    # The stable user key must reach the prompt layer: the instance name is
    # resolved per user, so without user_id a renamed instance would fall
    # back to the configured default name.
    _fallback_user = (extra_context or {}).get("user_id") or user_name
    if not _fallback_user:
        # The display name may be empty (only a user id was sent); the bound
        # current user still identifies this turn.
        try:
            from core.system.config.identity import current_user_id

            _fallback_user = current_user_id() or ""
        except Exception as _exc:
            logger.debug(f"Current user lookup unavailable: {_exc}")
    context.setdefault("user_id", _fallback_user)
    _detect_eda_followup(context, history)
    _run_mainline_dispatch(context, user_message, origin, extra_context)
    _schedule_msba(context, user_message)
    return context


def _apply_role_binding(context: Dict[str, Any]) -> None:
    """P2-4: a ``role_id`` pins the role's backend slot, memory namespace, trace id.

    The role comes from the server-side registry (``ai.roleplay.runtime``), never
    from the payload: a client chooses a role, it cannot define one. Unknown ids
    fail loudly (400) instead of silently answering as Angela — a wrong-voice
    answer is worse than an error the caller can see.
    """
    role_id = str(context.get("role_id") or "").strip()
    if not role_id:
        return

    from ai.roleplay.runtime import build_role_persona, resolve_role

    role = resolve_role(role_id)
    if role is None:
        raise HTTPException(status_code=400, detail=f"unknown role: {role_id}")

    context["_role_id"] = role.role_id
    context["_memory_namespace"] = role.memory_namespace
    context["_force_backend_slot"] = role.backend_slot
    context["_role_display_name"] = role.display_name
    # Without this the role gets its own model + memory but keeps Angela's voice.
    context["_role_persona"] = build_role_persona(role)
    logger.info(
        "Role binding: %s -> backend_slot=%s namespace=%s",
        role.role_id,
        role.backend_slot,
        role.memory_namespace,
    )


async def _gate_math(
    user_message: str,
    user_name: str,
    session_id: str,
    schema_ver: str,
    trunc_msg: str,
    was_truncated: bool,
    context: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Step 3: math dual-rail verification — gate through IntentRegistry.

    Returns the math response to short-circuit with (IntentRegistry confirms
    math) or None to continue (enriching context with the unconfirmed result).
    """
    math_result = await _try_math_verification(
        user_message, user_name, session_id, schema_ver, trunc_msg, was_truncated
    )
    if not math_result:
        return None
    try:
        from core.intent_registry import IntentRegistry

        ir = IntentRegistry()
        ir_name, ir_conf = ir.detect(user_message)
        if ir_name == "math" and ir_conf >= 0.1:
            _set_latest_response(session_id, math_result)
            return math_result  # IntentRegistry confirms -> fast path
    except Exception as e:
        logger.warning("IntentRegistry math gate failed: %s", e, exc_info=True)
    # IntentRegistry didn't confirm -> enrich context instead
    context["_math_result"] = math_result
    return None


def _ctx_al_state(context: Dict[str, Any], *, stage: str = "context") -> None:
    """Sole AI-side reader of AL state (Phase 3 item 2: converged).

    The chat pipeline reads AL assets at two moments, so this one reader
    takes a ``stage`` instead of living as five scattered
    ``_ctx_*``/``_apply_*`` helpers:

    - ``stage="context"``: LifeEssence tendencies, read while the LLM
      context is built (early, stable for the whole turn).
    - ``stage="behavioral"``: lifecycle/intent/modality/awareness (was
      Steps 5c-5f), read after emotion so the values reflect this turn.

    Not to be confused with the schema snapshot: ``get_al_state()`` (the
    contract §9 exchange quantity) is injected once per turn by the
    router's ``_inject_al_state`` and never read here. This reader
    reaches the AL-side *sources* (ALC/DLI/LifeEssence) for their advice
    dicts, and those reads are why AL readers converge into this one
    function — audit this, not the whole route module.

    Every segment stays best-effort-isolated: one broken AL source must
    never block the others or the reply.
    """
    if stage == "context":
        try:
            from core.life.life_essence import get_life_essence

            le = get_life_essence()
            if le:
                summary = le.get_essence_summary()
                context["life_essence"] = {
                    "tendencies": le.get_all_blended_tendencies(),
                    "generation": le.generation,
                    "total_traces": summary.get("total_traces", 0),
                    "ancestral_cores": summary.get("ancestral_cores", 0),
                }
                logger.debug("LifeEssence tendencies injected into chat context")
        except Exception as e:
            logger.warning(f"LifeEssence injection unavailable: {e}", exc_info=True)
        return
    if stage != "behavioral":
        raise ValueError(f"unknown _ctx_al_state stage: {stage!r}")

    try:
        lc = _get_lifecycle()
        if lc:
            lc_adj = lc.get_behavioral_adjustment()
            context["lifecycle_behavior"] = lc_adj
            logger.debug(
                f"Lifecycle behavioral adj: {lc_adj.get('routing_mode')} / "
                f"{lc_adj.get('response_style')} "
                f"(phase={lc_adj.get('phase')}, decision={lc_adj.get('decision_type')})"
            )
    except Exception as e:
        logger.warning(f"lifecycle_behavior unavailable: {e}", exc_info=True)
    try:
        im = _get_intent_manager()
        if im:
            intent_adj = im.get_intent_routing_adjustment()
            if intent_adj.get("routing_mode"):
                context["intent_routing"] = intent_adj
                logger.debug(
                    f"Intent routing adjustment: mode={intent_adj['routing_mode']}, "
                    f"style={intent_adj['response_style']}, "
                    f"strength={intent_adj['intent_strength']}"
                )
    except Exception as e:
        logger.warning(f"intent_routing unavailable: {e}", exc_info=True)
    try:
        mg = _get_modality_gateway()
        if mg:
            context["modality_state"] = mg.get_modality_summary()
            logger.debug(
                f"Modality state: {len(context['modality_state'].get('active', []))} active / "
                f"{len(context['modality_state'].get('inactive', []))} inactive"
            )
    except Exception as e:
        logger.warning(f"modality_state unavailable: {e}", exc_info=True)
    try:
        dli = get_digital_life()
        if dli:
            context["awareness_injection"] = dli.get_awareness_injection()
    except Exception as e:
        logger.warning(f"awareness_injection unavailable: {e}", exc_info=True)


async def _inject_behavioral_context(
    context: Dict[str, Any], emotion_result: Any, bio: Any
) -> None:
    """Steps 5b-5f: inject behavioral/routing context (all best-effort).

    5b emotional behavioral context, then the converged AL reader
    (``_ctx_al_state(stage="behavioral")``) for what used to be the
    lifecycle/intent/modality/awareness helpers — each segment isolated
    inside the reader so one failure never blocks the others.
    """
    await _inject_emotion_behavioral_context(emotion_result, context, bio)
    _ctx_al_state(context, stage="behavioral")


def _wire_desktop_interaction(context: Dict[str, Any]) -> None:
    """Step 5h: wire DesktopInteraction into context for generic file operations."""
    try:
        from api.lifespan import get_desktop_interaction

        _desktop = get_desktop_interaction()
        if _desktop is not None:
            context["desktop_interaction"] = _desktop
            logger.info("DesktopInteraction wired into chat context")
    except Exception as e:
        logger.warning(f"DesktopInteraction wiring failed: {e}", exc_info=True)


def _wrap_agent_response(
    agent_result: Dict[str, Any],
    schema_ver: str,
    trunc_msg: str,
    was_truncated: bool,
    session_id: str,
) -> Dict[str, Any]:
    """Step 8: normalize an agent-routing result into a chat response dict."""
    return {
        "response_text": agent_result["response"],
        "response": agent_result["response"],
        "source": agent_result.get("source", "agent"),
        "schema_version": schema_ver,
        "truncation_message": trunc_msg if was_truncated else "",
        "emotion": "calm",
        "emotion_confidence": 0.6,
        "emotion_intensity": 0.4,
        "session_id": session_id,
    }


def _msba_ab_enabled() -> bool:
    """Whether the MSBA A/B comparison runs (off by default).

    The comparison runs the block pipeline and the pre-block path on the same
    input and records both — it measures, it does not change the answer.
    Configured under ``system/core → msba.ab_testing``.
    """
    try:
        from core.system.config.tiered_loader import get_config

        cfg = get_config("system/core") or {}
        section = cfg.get("msba") or {}
        return bool(section.get("ab_testing", False))
    except Exception as exc:
        logger.debug(f"MSBA A/B flag unavailable: {exc}")
        return False


async def _run_msba_ab_comparison(user_message: str) -> None:
    """Measure the MSBA path against the pre-block path (best effort)."""
    try:
        _msba = _get_msba_pipeline()
        if _msba is None:
            return
        comparison = await _msba.compare(user_message)
        context_payload = {"msba": {"ab_comparison": comparison}}
        state_store.update_state("routing", context_payload, notify=False)
        logger.debug(
            "MSBA A/B: agree=%s msba=%.1fms legacy=%.1fms",
            comparison.get("agree"),
            comparison.get("msba_latency_ms", 0.0),
            comparison.get("legacy_latency_ms", 0.0),
        )
    except Exception as exc:
        logger.debug(f"MSBA A/B comparison skipped: {exc}")


async def _collect_msba_ab_task(context: Dict[str, Any]) -> None:
    """Collect the scheduled MSBA A/B comparison (measurement only)."""
    task = context.pop("_msba_ab_task", None)
    if task is None:
        return
    try:
        # The A/B comparison is a measurement: it must not delay the answer.
        await asyncio.wait_for(task, timeout=0.5)
    except asyncio.TimeoutError:
        logger.debug("MSBA A/B comparison timed out")
    except Exception as exc:
        logger.debug(f"MSBA A/B comparison not collected: {exc}")


def _apply_msba_blender(context: Dict[str, Any], output: Any, bridge: Any) -> None:
    """Convert the MSBA fusion into the NeuroBlender 9D LLM context."""
    try:
        if hasattr(output, "primary"):
            blander_vec = bridge.fused_to_blender_vector(output)
            context["msba_blender_9d"] = bridge.blender_to_context(blander_vec)
            context["msba_dominant"] = bridge.get_dominant_dimension(blander_vec)
    except Exception as exc:
        logger.debug("MSBA->NeuroBlender conversion skipped: %s", exc)


async def _collect_msba_result(context: Dict[str, Any]) -> None:
    """Step 9.5: collect the scheduled MSBA result (best-effort) into context."""
    _msba_task = context.pop("_msba_task", None)
    _msba_bridge = context.pop("_msba_bridge", None)
    await _collect_msba_ab_task(context)
    if _msba_task is None:
        return
    try:
        _msba_output = await asyncio.wait_for(_msba_task, timeout=0.05)
        if _msba_output and _msba_bridge is not None:
            context["msba_output"] = _msba_output
            _apply_msba_blender(context, _msba_output, _msba_bridge)
    except asyncio.TimeoutError:
        logger.debug("MSBA result not ready within budget, continuing")
    except Exception as _e:
        logger.debug("MSBA result collection failed: %s", _e)


def _extract_response_text(llm_response: Any) -> str:
    """Normalize an LLM response (dict or object) into plain response text."""
    if isinstance(llm_response, dict):
        response_text = (
            llm_response.get("text")
            or llm_response.get("response")
            or llm_response.get("response_text")
            or ""
        )
        if not response_text and llm_response.get("error"):
            # Error dicts without text must not become silent empty replies
            # (audit 2026-10-10): surface honestly instead of HTTP 200 + "".
            logger.warning(
                "Chat dict response carried error without text: %s",
                str(llm_response.get("error"))[:200],
            )
            response_text = "抱歉，剛才的處理遇到問題，請再說一次。"
        return response_text
    return (
        llm_response.text
        if hasattr(llm_response, "text")
        else getattr(llm_response, "response", None) or str(llm_response)
    )


def _extract_abstain_envelope(llm_response: Any) -> Optional[Dict[str, Any]]:
    """Structured abstain channel (v1): read metadata["abstain"] if present.

    Additive contract — absent (None) for served answers; the envelope carries
    {"v", "reason", "language", "tier"}. Clients must ignore unknown
    keys/reasons inside the envelope (upgrade path: bump "v" only on
    breaking reshapes).
    """
    meta = getattr(llm_response, "metadata", None)
    if not isinstance(meta, dict):
        return None
    env = meta.get("abstain")
    return env if isinstance(env, dict) else None


def _record_meta_calibration_sample(context: Dict[str, Any], response_text: str) -> None:
    """10d: feed chat routing confidence into MetaController (問題單 6).

    Chat traffic never called record_confidence, so calibration stayed at
    zero samples and save_calibration_state had no reason to fire. Best-effort:
    never raises into the response path.
    """
    try:
        from api.routes.meta_routes import _get_controller as _get_meta_controller

        mc = _get_meta_controller()
        intent_routing = context.get("intent_routing", {}) or {}
        mode = intent_routing.get("routing_mode")
        if mc is None or not mode:
            return
        try:
            conf = float(intent_routing.get("intent_strength", 0.5))
        except (TypeError, ValueError):
            conf = 0.5
        conf = max(0.0, min(1.0, conf))
        # Abstain-aware：棄權不是「答對了」——不可餵給校準當正樣本。
        success = bool(response_text and len(response_text) > 10) and not context.get("_abstain")
        mc.record_confidence("chat:intent_routing", conf, correct=success)
    except Exception as e:
        logger.warning(f"Meta confidence recording unavailable: {e}", exc_info=True)


def _record_solution_rule_outcome(
    context: Dict[str, Any],
    response_text: str,
    was_truncated: bool,
) -> None:
    """Step 10e: the solution-rule outcome (規則沉澱層閉環回饋).

    Success = the stored answer really reached the user (verbatim or
    contained in the reply, tolerating light post-processing) and the reply
    was not truncated; an empty/truncated reply counts as a failure and
    lowers the rule's confidence (two-strikes-out loop).
    """
    hit = context.pop("_solution_rule_hit", None)
    if not hit:
        return
    try:
        from ai.rules import get_rule_store

        answer = str(hit.get("answer") or "").strip()
        resp = (response_text or "").strip()
        compact_answer = "".join(answer.split())
        compact_resp = "".join(resp.split())
        if len(answer) >= 8:
            served = bool(compact_answer) and compact_answer in compact_resp
        else:
            served = bool(compact_answer) and compact_answer == compact_resp
        success = served and not was_truncated and bool(resp)
        recorded = get_rule_store().record_outcome(str(hit.get("rule_id") or ""), success)
        logger.debug(
            "Solution rule outcome: rule=%s success=%s recorded=%s",
            hit.get("rule_id"),
            success,
            recorded,
        )
    except Exception as e:
        logger.warning(f"Solution rule feedback skipped: {e}", exc_info=True)


def _record_post_response_feedback(
    context: Dict[str, Any],
    response_text: str,
    user_message: str,
    was_truncated: bool = False,
    chat_svc: Any = None,
) -> None:
    """Steps 10b/10c/10d/10e: post-response feedback loops (best-effort).

    10c online self-learning (dictionary classifier) + 10b intent outcome
    recording (C³ 5.0→6.0) + 10d meta calibration sampling (問題單 6)
    + 10e solution-rule outcome (規則沉澱層閉環回饋 → RuleStore.record_outcome).
    Abstain-aware (v1): context["_abstain"] 信封存在時，10b/10d 不把棄權
    當成功樣本；10b 之後把非棄權回合經 chat_svc.record_served_turn() 記進
    路由器的 abstain 閉環分母。None may raise into the response path.
    """
    _record_solution_rule_outcome(context, response_text, was_truncated)

    try:
        _learn_from_classification_feedback(user_message, response_text, context)
    except Exception as e:
        logger.warning(f"Online learning step skipped: {e}", exc_info=True)

    try:
        im = _get_intent_manager()
        if im:
            actual_mode = context.get("_actual_routing_mode")
            intent_routing = context.get("intent_routing", {})
            recommended_mode = intent_routing.get("routing_mode") if intent_routing else None
            # Abstain-aware：honest 拒答/拒做不是 routing 成功（2026-10-19
            # 前 ~50 字的拒答文案被當成功樣本餵進 IntentModel 閉環）。
            _is_abstain = bool(context.get("_abstain"))
            success = bool(response_text and len(response_text) > 10) and not _is_abstain
            im.record_intent_outcome(recommended_mode, success)
            logger.debug(
                f"Intent outcome: recommended={recommended_mode}, "
                f"actual={actual_mode}, success={success}, abstain={_is_abstain}"
            )
    except Exception as e:
        logger.warning(f"Intent outcome recording unavailable: {e}", exc_info=True)

    # Abstain 閉環分母：非棄權的正常送出回合記進路由器近期窗口（棄權本體
    # 在 Tier 1.5/1.6 建立時已自記 True），recent rate 餵給 abstain_voter。
    if chat_svc is not None and not context.get("_abstain"):
        try:
            recorder = getattr(chat_svc, "record_served_turn", None)
            if recorder:
                recorder()
        except Exception as e:
            logger.debug(f"Served-turn abstain tracking skipped: {e}", exc_info=True)

    _record_meta_calibration_sample(context, response_text)


class _LLMTimeoutError(Exception):
    """Internal: LLM generation exceeded its timeout budget (not user-visible)."""


async def _generate_via_chat_service(
    user_message: str,
    user_name: str,
    context: Dict[str, Any],
    chat_svc: Any,
    timeout: float,
) -> Any:
    """Generate a response via ChatService.generate_response.

    Raises _LLMTimeoutError on timeout (caller serves the latest cached
    response). CancelledError and RuntimeError propagate to the caller.
    """
    try:
        return await asyncio.wait_for(
            chat_svc.generate_response(user_message, user_name, context=context),
            timeout=timeout,
        )
    except asyncio.CancelledError:
        logger.info("Client disconnected mid-response, cancelling")
        raise
    except asyncio.TimeoutError as e:
        raise _LLMTimeoutError from e
    except Exception as e:
        logger.error(f"Error in _handle_chat_request: {e}", exc_info=True)
        raise RuntimeError(f"chat request failed: {e}") from e


async def _generate_llm_response(
    user_message: str,
    user_name: str,
    context: Dict[str, Any],
    chat_svc: Any,
    mode: str,
    timeout: float,
) -> Any:
    """Step 10: mode-aware LLM generation.

    響應模式選取器（§5.6 backbone.respond）：1:1 / layered / stream / layered_stream.
    mode == "1:1" uses ChatService directly; other modes try backbone.respond
    and fall back to ChatService on failure. Raises _LLMTimeoutError on
    timeout; CancelledError and RuntimeError propagate to the caller.
    """
    if mode == "1:1":
        return await _generate_via_chat_service(user_message, user_name, context, chat_svc, timeout)
    try:
        from core.backbone import get_backbone

        return await asyncio.wait_for(
            get_backbone().respond(user_message, context=context, mode=mode),
            timeout=timeout,
        )
    except asyncio.CancelledError:
        logger.info("Client disconnected mid-response, cancelling")
        raise
    except asyncio.TimeoutError as e:
        raise _LLMTimeoutError from e
    except Exception as e:
        logger.warning(f"Response mode {mode} failed, falling back to 1:1: {e}")
        return await _generate_via_chat_service(user_message, user_name, context, chat_svc, timeout)


def _build_math_response(
    verification,
    matrix,
    user_message: str,
    session_id: str,
    schema_version: str = "2.0",
    truncation_message: str = "",
) -> Dict[str, Any]:
    """Build math response."""
    if verification.needs_clarification:
        emotion, emotion_confidence, emotion_intensity = "confused", 0.7, 0.6
    elif not verification.matches:
        emotion, emotion_confidence, emotion_intensity = "surprised", 0.8, 0.7
    elif verification.extraction and verification.extraction.get("confidence", 0.0) >= 0.8:
        emotion, emotion_confidence, emotion_intensity = "happy", 0.9, 0.6
    else:
        emotion, emotion_confidence, emotion_intensity = "calm", 0.6, 0.4

    if matrix and verification.final_answer is not None:
        epsilon_conf = (
            verification.extraction.get("confidence", 0.5) if verification.extraction else 0.5
        )
        matrix.epsilon.values["certainty"] = min(1.0, 0.5 + epsilon_conf * 0.5)
        matrix.epsilon.values["complexity"] = min(1.0, len(user_message) / 50.0)
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

    return {
        "response_text": verification.response_text,
        "response": verification.response_text,
        "source": "dual_rail",
        "backend": "deterministic-math",
        "model": "dual-rail-verifier",
        "schema_version": schema_version,
        "truncation_message": truncation_message,
        "emotion": emotion,
        "emotion_confidence": emotion_confidence,
        "emotion_intensity": emotion_intensity,
        "session_id": session_id,
    }


@router.get("/security/sync-key-c")
async def sync_key_c(request: Request) -> dict:
    """Report Key C availability without ever returning key material.

    Loopback-only existence check: returns {"key_available": True} when the
    key manager holds Key C. Callers must handle absence via their own
    fallback — the key value itself is never placed in the response body.
    """
    from core.system.config.network_defaults import LOCAL_TRUSTED_HOSTS

    client_host = request.client.host if request.client else ""
    # Loopback whitelist is configurable (ANGELA_TRUSTED_HOSTS env, comma
    # separated) so deployments behind a trusted reverse proxy can extend it.
    import os

    trusted = tuple(
        h.strip()
        for h in os.getenv("ANGELA_TRUSTED_HOSTS", ",".join(LOCAL_TRUSTED_HOSTS)).split(",")
        if h.strip()
    )
    if client_host not in trusted:
        logger.warning(f"Unauthorized access attempt to sync-key-c from {client_host}")
        raise HTTPException(status_code=403, detail="Access restricted to localhost")
    abc_key_manager = get_abc_key_manager()
    key_c = abc_key_manager.get_key("KeyC")
    if not key_c:
        raise HTTPException(status_code=404, detail="Security keys not initialized")
    return {"key_available": True}


@router.post("/session/start")
async def start_session(request: Optional[Dict[str, Any]] = Body(default=None)) -> dict:
    """Execute the start session operation.

    Legacy compat route: session ids are namespaced tenant::persona like the
    unified route (audit 2026-10-10) so reusing an id across tenants/personas
    cannot collide. Old sess-* ids already stored keep working (lookup is by
    exact id in /send).
    """
    request = request or {}
    tenant_id = request.get("tenant_id", "default")
    persona_id = request.get("persona_id", "angela")
    session_id = f"sess-{tenant_id}::{persona_id}::{uuid.uuid4().hex[:8]}"
    sessions.set(
        session_id,
        {
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "user_name": request.get("user_name", request.get("user_id", "User")),
            "user_id": request.get("user_id") or request.get("user_name", "User"),
            "tenant_id": tenant_id,
            "persona_id": persona_id,
        },
    )
    return {
        "session_id": session_id,
        "message": _get_ed3n_engine().process(
            "welcome", context={"session_id": session_id}, depth="reflex"
        ),
    }


@router.post("/session/{session_id}/send")
async def send_message(session_id: str, request: Dict[str, Any] = Body(...)) -> dict:
    """Execute the send message operation via the unified chat pipeline."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    user_message = request.get("text", request.get("message", ""))
    session = sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    user_name = _display_name(session.get("user_name"), session.get("user_id"))
    # Carry the session's namespaced identity downstream so legacy sessions
    # get the same tenant/persona isolation as unified ones.
    legacy_context = {
        "user_id": session.get("user_id", user_name),
        "tenant_id": session.get("tenant_id", "default"),
        "persona_id": session.get("persona_id", "angela"),
    }
    return await _handle_chat_request(
        user_message,
        user_name,
        session.get("messages", []),
        session_id,
        extra_context=legacy_context,
    )


@router.post("/chat/unified")
async def unified_chat(request: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Execute the unified chat operation."""
    user_message = request.get("message", request.get("text", ""))
    mode = request.get("mode", "1:1")
    # Identity rule (audit 2026-10-10): user_id is the stable key and wins
    # when both are sent; user_name is display-only. The old order read
    # user_name first, so a display name overwrote the identity in logs,
    # context and session classification (multi-tenant hazard). Single-field
    # clients (user_name only) behave exactly as before.
    user_id = request.get("user_id") or request.get("user_name", "User")
    context = {
        "user_id": user_id,
        "tenant_id": request.get("tenant_id", "default"),
        "persona_id": request.get("persona_id", "angela"),
        "client_id": request.get("origin", request.get("client_id", "desktop")),
    }
    # P2-4: role selection must reach the pipeline. Without this the binding
    # step had nothing to read and every request answered as Angela.
    if request.get("role_id"):
        context["role_id"] = str(request["role_id"]).strip()
    user_name = _display_name(request.get("user_name"), user_id)
    history = request.get("history", [])
    # Bound history to prevent OOM from attacker-controlled large arrays
    if isinstance(history, list) and len(history) > 100:
        history = history[-100:]
        logger.warning("History truncated to last 100 entries for session")
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
        mode=mode,
        # The namespaced identity must reach the pipeline: the instance name
        # is resolved per user, and the legacy session path already carried
        # it (audit 2026-10-10) — the unified path used to drop it.
        extra_context=context,
    )
    response["context"] = context
    response["mode"] = mode
    response["migration_note"] = (
        "Use /api/v1/chat/unified for multi-persona isolation; "
        "legacy /dialogue and /angela/chat removed in v7.5.0. "
        "Compat routes still served: /session/start|/session/{id}/send "
        "(now tenant::persona-namespaced), /chat/stream, /chat/with-image, "
        "/chat/with-audio."
    )
    return response


MAX_GROUP_ROLES = 4


@router.post("/chat/group")
async def group_chat(request: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Ask several roles the same message; replies are keyed by role id.

    Each role runs the full pipeline (validation / math / crisis / gate), not a
    stripped-down LLM call — a group turn must never be a way around the safety
    gates. Sessions are namespaced per role so one transcript cannot bleed into
    another.
    """
    user_message = request.get("message", request.get("text", ""))
    role_ids = request.get("role_ids") or request.get("roles") or []
    if not isinstance(role_ids, list) or not role_ids:
        raise HTTPException(status_code=400, detail="role_ids must be a non-empty list")
    if len(role_ids) > MAX_GROUP_ROLES:
        raise HTTPException(
            status_code=400, detail=f"at most {MAX_GROUP_ROLES} roles per group turn"
        )

    grouped = list(dict.fromkeys(str(role) for role in role_ids))
    user_id = request.get("user_id") or request.get("user_name", "User")
    user_name = _display_name(request.get("user_name"), user_id)
    origin = request.get("origin", "desktop")
    base_session = request.get("session_id") or f"group::{uuid.uuid4().hex[:8]}"
    history = request.get("history", [])
    if not isinstance(history, list):
        history = []

    replies: Dict[str, Any] = {}
    for role_id in grouped:
        replies[role_id] = await _handle_chat_request(
            user_message=user_message,
            user_name=user_name,
            history=list(history),
            session_id=f"{base_session}::{role_id}",
            origin=origin,
            extra_context={
                "user_id": user_id,
                "tenant_id": request.get("tenant_id", "default"),
                "persona_id": role_id,
                "client_id": origin,
                "role_id": role_id,
                "group_id": base_session,
            },
            mode="group",
        )
    return {"session_id": base_session, "role_ids": grouped, "replies": replies}


async def _sse_pump(
    token_queue: "asyncio.Queue", task: "asyncio.Future", judge: Any
) -> AsyncGenerator[str, None]:
    """Pump tokens from the queue until the task completes. Yields SSE lines."""
    while True:
        try:
            item = await asyncio.wait_for(token_queue.get(), timeout=45.0)
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
            # Phase 2: judge on the rolling window (never blocks
            # generation — this runs in the endpoint loop, not the
            # provider callback). Lock events ride the same stream.
            try:
                verdict = judge.feed(str(item.get("token", "")))
                if verdict is not None:
                    yield f"data: {json.dumps(verdict, ensure_ascii=False)}\n\n"
            except Exception:
                # Lock/verdict events are one-shot on a live stream —
                # losing one is unrecoverable downstream.
                logger.warning("StreamJudge feed failed; verdict dropped", exc_info=True)
        except asyncio.TimeoutError:
            if task.done():
                break
            yield ": ping\n\n"
            continue
        if task.done() and token_queue.empty():
            break


async def _sse_finalize(task: "asyncio.Future", judge: Any) -> AsyncGenerator[str, None]:
    """Await the final result and yield the terminal SSE event."""
    try:
        result = await asyncio.wait_for(task, timeout=300.0)
    except asyncio.TimeoutError:
        task.cancel()
        yield f"data: {json.dumps({'error': 'overall timeout'})}\n\n"
        return
    except Exception as exc:
        yield f"data: {json.dumps({'error': str(exc)[:200]})}\n\n"
        return
    final_text = (result or {}).get("response_text", "")
    final_backend = (result or {}).get("backend", "unknown")
    # Never report success on an empty answer (audit 2026-10-10: a
    # failed pipeline yielded done:true with blank text and no signal).
    if not (final_text or "").strip() and final_backend == "unknown":
        yield f"data: {json.dumps({'error': 'empty response'})}\n\n"
        return
    try:
        consistency = judge.finalize(final_text)
    except Exception:
        consistency = {}
    final = {
        "done": True,
        "response_text": final_text,
        "backend": final_backend,
        "judge_consistency": consistency,
    }
    yield f"data: {json.dumps(final, ensure_ascii=False)}\n\n"


@router.post("/chat/stream")
async def chat_stream(request: Dict[str, Any] = Body(...)) -> StreamingResponse:
    """SSE streaming chat: tokens are emitted as the LLM generates them.

    Reuses the full pipeline (_handle_chat_request) unchanged: a
    ``_stream_callback`` rides extra_context into the router, which invokes
    it per generated token (Phase 1: transport streaming only — routing
    judgments still use the full text, so accuracy is unchanged). Non-LLM
    answers (template/math/clock/memory) arrive as one final event.
    Events: {"token": str}… then {"done": true, "response_text", "backend"}.
    """
    user_message = request.get("message", request.get("text", ""))
    mode = request.get("mode", "1:1")
    # Same identity rule as unified_chat (audit 2026-10-10): id wins.
    user_id = request.get("user_id") or request.get("user_name", "User")
    user_name = _display_name(request.get("user_name"), user_id)
    history = request.get("history", [])
    if isinstance(history, list) and len(history) > 100:
        history = history[-100:]
    session_id = request.get(
        "session_id",
        f"{request.get('tenant_id', 'default')}::{request.get('persona_id', 'angela')}::{uuid.uuid4().hex[:8]}",
    )
    origin = request.get("origin", request.get("client_id", "desktop"))
    token_queue: asyncio.Queue = asyncio.Queue()
    extra_context = {
        "user_id": user_id,
        "tenant_id": request.get("tenant_id", "default"),
        "persona_id": request.get("persona_id", "angela"),
        "client_id": origin,
    }

    def _token_callback(piece: str) -> None:
        try:
            token_queue.put_nowait({"token": piece})
        except Exception:
            # A dropped enqueue shows up as a truncated answer with no server
            # trace; at minimum it must be visible in the log.
            logger.warning("SSE token enqueue failed; token dropped", exc_info=True)

    extra_context["_stream_callback"] = _token_callback

    async def _event_gen() -> AsyncGenerator[str, None]:
        from services.llm.stream_judge import StreamJudgeWindow

        yield ": stream open\n\n"
        judge = StreamJudgeWindow()
        task = asyncio.ensure_future(
            _handle_chat_request(
                user_message=user_message,
                user_name=user_name,
                history=history,
                session_id=session_id,
                origin=origin,
                extra_context=extra_context,
                mode=mode,
            )
        )
        try:
            async for line in _sse_pump(token_queue, task, judge):
                yield line
            async for line in _sse_finalize(task, judge):
                yield line
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(_event_gen(), media_type="text/event-stream")


@router.post("/chat/with-image")
async def chat_with_image(
    message: str = Form(default=""),
    file: UploadFile = File(default=None),
    session_id: str = Form(default=""),
    user_name: str = Form(default="朋友"),
) -> Dict[str, Any]:
    """Chat with optional image context.

    Combines image analysis with chat message for multimodal conversation.
    CLIP-first: tries zero-shot classification before LLM fallback.
    """
    if not session_id:
        session_id = f"img-{uuid.uuid4().hex[:8]}"

    clip = await _clip_phase(file, message, session_id)
    if clip is None:
        clip = _ClipPhaseResult(None, None, 0.0, False, "", None)

    if clip.early_response is not None:
        return clip.early_response

    if clip.clip_response:
        return {
            "response": clip.clip_response,
            "session_id": session_id,
            "source": "clip_classify",
            "confidence": clip.confidence,
        }

    # Blank frames short-circuit everything: no CLIP/vision/LLM layer can
    # say anything true about an empty render except that it is empty.
    if clip.image_is_blank:
        return {
            "response": "（圖像質檢）畫面近乎空白，疑似渲染失敗或鏡頭沒對準物體。",
            "response_text": "（圖像質檢）畫面近乎空白，疑似渲染失敗或鏡頭沒對準物體。",
            "source": "visual-qa",
            "schema_version": "2.0",
            "session_id": session_id,
            "backend": "deterministic-visual",
            "model": "visual-qa",
        }

    image_context = await _vision_phase(file, clip, message)

    history: List[Dict[str, Any]] = []
    context: Dict[str, Any] = {"user_name": user_name}
    if image_context:
        context["image_analysis"] = image_context
    # Measurements ride the user message too: system-context JSON gets
    # skimmed, but user text gets attention (live 2026-10-11: two rounds of
    # metadata-only descriptions despite measurements in prompt).
    _vm = str(image_context.get("visual_measurements") or "").strip() if image_context else ""
    _user_message = message or "我上傳了一張圖片"
    if _vm:
        _user_message = f"{_user_message}\n【實測所見】{_vm}"

    return await _handle_chat_request(
        user_message=_user_message,
        user_name=user_name,
        history=history,
        session_id=session_id,
        origin="Human",
        extra_context=context if image_context else None,
    )


class _ClipPhaseResult(NamedTuple):
    """Result of the CLIP classification phase for an image upload."""

    early_response: Optional[Dict[str, Any]]
    clip_response: Optional[str]
    confidence: float
    image_is_blank: bool
    visual_concepts_text: str
    image_data: Optional[bytes]


def _clip_blank_gate(image_data: bytes) -> bool:
    """Blank-image gate: a single ≥98% color blob means an empty render."""
    try:
        from services.visual_qa import color_blobs

        _blobs = color_blobs(image_data)
        return len(_blobs) == 1 and (_blobs[0].get("fraction") or 0) >= 0.98
    except Exception:
        return False


def _is_describe_request(message: str) -> bool:
    """Describe/explain requests need vision+LLM, not a CLIP one-liner."""
    import re as _re_desc

    return bool(
        _re_desc.search(
            r"(描述|解釋|解释|說說|说说|介紹|介绍|講講|讲讲|告訴我|告诉我|"
            r"這是什麼|这是什么|裡有什麼|里有什么)",
            message or "",
        )
    )


async def _clip_run_classify(
    image_data: bytes, message: str, image_is_blank: bool, skip_clip_template: bool
) -> Tuple[Optional[str], float, str]:
    """Run CLIP zero-shot classify + template generation (best-effort).

    Returns (clip_response, confidence, visual_concepts_text).
    """
    clip_response = None
    confidence = 0.0
    visual_concepts_text = ""
    from ai.ed3n.ed3n_engine import ED3NEngine
    from ai.multimodal.concept_library import ConceptLibrary
    from ai.multimodal.semantic_visual import SemanticVisualEncoder
    from ai.multimodal.vision_response_generator import VisionResponseGenerator

    encoder = SemanticVisualEncoder()
    if not encoder.is_available:
        return clip_response, confidence, visual_concepts_text
    ed3n = ED3NEngine.get_shared()
    if len(ed3n.dictionary.entries) < 100:
        # 132MB sync load would block the event loop for seconds
        # (audit 2026-10-10): offload like the vector-store I/O.
        await asyncio.to_thread(ed3n.load_external_dictionaries)

    from ai.multimodal.semantic_key_mapper import SemanticKeyMapper

    mapper = SemanticKeyMapper(max_entries=1000)
    library = ConceptLibrary(
        semantic_encoder=encoder,
        dictionary=ed3n.dictionary,
        key_mapper=mapper,
    )
    library.build()
    results = library.classify(image_data, top_k=3)
    # Stash concepts for the LLM prompt even when the template path is
    # skipped: measurements must reach generation.
    try:
        visual_concepts_text = "、".join(
            f"{r.get('concept_name')}({float(r.get('confidence', 0)):.2f})"
            for r in (results or [])[:3]
        )
    except Exception:
        visual_concepts_text = ""
    if (
        results
        and results[0]["confidence"] > 0.15
        and not image_is_blank
        and not skip_clip_template
    ):
        generator = VisionResponseGenerator(dictionary=ed3n.dictionary)
        for cname, info in library._concepts.items():
            generator.register_concept(cname, info["dict_key"], info["labels"])
        top_concept = results[0]["concept_name"]
        concept_info = library._concepts.get(top_concept, {})
        action = concept_info.get("action", "") or message or ""
        confidence = results[0]["confidence"]
        clip_response = generator.generate_response(results, language="zh", action=action)
    return clip_response, confidence, visual_concepts_text


async def _clip_phase(file: Any, message: str, session_id: str) -> Optional[_ClipPhaseResult]:
    """Read + blank-gate + QA short-circuit + CLIP classify for an image upload.

    Returns None when the file is not an image (no CLIP phase applies).
    """
    if not (file and file.content_type and file.content_type.startswith("image/")):
        return None
    image_data = None
    image_is_blank = False
    visual_concepts_text = ""
    clip_response = None
    confidence = 0.0
    try:
        image_data = await file.read()
        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Image too large (>10MB limit)")
        image_is_blank = _clip_blank_gate(image_data)
        # QA questions answered deterministically BEFORE CLIP templates:
        # weak CLIP hits (0.22 noise) otherwise compose echoes.
        if _is_visual_qa_question(message):
            _qa = _visual_qa_response(image_data, session_id)
            if _qa is not None:
                return _ClipPhaseResult(_qa, None, 0.0, image_is_blank, "", image_data)
        # Describe/explain requests need vision+LLM, not a CLIP one-liner;
        # skip the CLIP template block entirely for these.
        skip_clip_template = _is_describe_request(message)
        if skip_clip_template:
            image_is_blank = False
        clip_response, confidence, visual_concepts_text = await _clip_run_classify(
            image_data, message, image_is_blank, skip_clip_template
        )
    except Exception as e:
        logger.warning(f"CLIP classification failed, falling back to LLM: {e}", exc_info=True)
    return _ClipPhaseResult(
        None, clip_response, confidence, image_is_blank, visual_concepts_text, image_data
    )


def _build_visual_measurements(visual_concepts_text: str, image_data: bytes) -> str:
    """Build assertive measurement sentences from CLIP concepts + color blobs."""
    _seen_bits: List[str] = []
    if visual_concepts_text:
        _concepts = [c.strip() for c in str(visual_concepts_text).split("、") if c.strip()]
        if _concepts:
            _seen_bits.append("圖中看起來像" + _concepts[0].split("(")[0] + "。")
    try:
        from services.visual_qa import color_blobs as _cb

        _blobs = _cb(image_data)[:3]
        if _blobs:
            _top = _blobs[0]
            _seen_bits.append(f"畫面以{_top['color']}色為主（佔{_top['fraction']:.0%}）。")
    except Exception:
        logger.debug("color_blobs enrichment failed", exc_info=True)
    return "\n".join(_seen_bits) if _seen_bits else ""


async def _vision_phase(
    file: Any, clip: _ClipPhaseResult, message: str
) -> Optional[Dict[str, Any]]:
    """Vision analysis for an image upload (None when not an image / failed)."""
    if not (file and file.content_type and file.content_type.startswith("image/")):
        return None
    try:
        image_data = clip.image_data
        if image_data is None:
            image_data = await file.read()
        vision = _get_vision_service()
        if vision is None:
            return None
        analysis = await vision.process(
            {
                "image_data": image_data,
                "filename": file.filename,
                "question": message or "描述這張圖片",
            }
        )
        # Measurements FIRST in the dict: the prompt builder dumps
        # image_analysis whole but truncates at 2000 chars, so anything
        # appended last never reaches the model (live 2026-10-11).
        return {
            "visual_measurements": _build_visual_measurements(
                clip.visual_concepts_text, image_data
            ),
            "filename": file.filename,
            "analysis": analysis,
            "image_data": image_data,
        }
    except Exception as e:
        logger.warning(f"Image analysis failed, continuing with text only: {e}")
        return None


def _is_visual_qa_question(message: str) -> bool:
    """Quality/inspection questions get measured verdicts, never templates."""
    import re as _re_qa

    return bool(
        _re_qa.search(
            r"(檢查|检查|質量|质量|品質|品质|怎麼樣|怎么样|如何|評價|评价|"
            r"看一下|看看|分析一下|合格|好不好|品質如何|"
            r"幾個色塊|几个色块|幾個區域|几个区域|幾個物體|几个物体|"
            r"幾個顏色|几个颜色)",
            message or "",
        )
    )


def _visual_qa_response(image_data: bytes, session_id: str) -> "Optional[Dict[str, Any]]":
    """Deterministic visual QA verdict dict, or None to continue pipeline."""
    try:
        from services.visual_qa import judge_render

        verdict = judge_render(image_data if isinstance(image_data, bytes) else b"")
        if verdict.get("verdict"):
            return {
                "response": f"（圖像質檢）{verdict['verdict']}",
                "response_text": f"（圖像質檢）{verdict['verdict']}",
                "source": "visual-qa",
                "schema_version": "2.0",
                "session_id": session_id,
                "backend": "deterministic-visual",
                "model": "visual-qa",
            }
    except Exception as exc:
        logger.debug(f"Visual QA skipped: {exc}")
    return None


@router.post("/chat/with-audio")
async def chat_with_audio(
    message: str = Form(default=""),
    file: UploadFile = File(default=None),
    session_id: str = Form(default=""),
    user_name: str = Form(default="朋友"),
) -> Dict[str, Any]:
    """Chat with voice input: speech-to-text → text chat → text-to-speech.

    Accepts WAV/MP3 audio, transcribes via Whisper/faster-whisper,
    feeds into chat pipeline, returns text response.
    """
    if not session_id:
        session_id = f"audio-{uuid.uuid4().hex[:8]}"

    transcribed_text = ""

    if (
        file
        and file.content_type
        and (
            file.content_type.startswith("audio/")
            or file.content_type == "application/octet-stream"
        )
    ):
        try:
            audio_data = await file.read()
            if len(audio_data) > 20 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="Audio too large (>20MB limit)")
            from services.audio_service import AudioService

            audio_svc = AudioService()
            stt_result = await audio_svc.speech_to_text(audio_data)
            transcribed_text = stt_result.get("text", "")
            if not transcribed_text:
                return {
                    "response": "抱歉，我聽不懂這段語音。",
                    "session_id": session_id,
                    "source": "stt_failed",
                    "error": stt_result.get("error", "Could not understand audio"),
                }
        except Exception as e:
            logger.warning("Audio transcription failed: %s", e)
            return {
                "response": "語音處理失敗，請重試。",
                "session_id": session_id,
                "source": "stt_error",
                "error": safe_error(e),
            }

    user_text = transcribed_text or message
    if not user_text:
        return {
            "response": "請提供語音或文字訊息。",
            "session_id": session_id,
            "source": "empty_input",
        }

    return await _handle_chat_request(
        user_message=user_text,
        user_name=user_name,
        history=[],
        session_id=session_id,
        origin="Human",
    )


@router.post("/document/learn")
async def learn_document(request: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Learn a document into GARDEN + ED3N engines."""
    text = request.get("text", request.get("content", ""))
    source = request.get("source", request.get("filename", "inline"))
    if not text:
        return {"status": "error", "message": "No text provided"}
    from ai.document.learner import DocumentLearner
    from ai.ed3n.ed3n_engine import ED3NEngine

    try:
        garden = _get_shared_garden()
        ed3n = ED3NEngine.get_shared(load_trained=False)
        learner = DocumentLearner(garden_engine=garden, ed3n_engine=ed3n)
        result = learner.learn(text, source=source)
        # New knowledge must not be masked by stale cached answers.
        _invalidate_router_cache("document learn")
        return {"status": result.get("status", "ok"), "sections": result.get("sections", 0)}
    except Exception as e:
        logger.warning("Document learn failed: %s", e, exc_info=True)
        return {"status": "error", "message": safe_error(e)}


@router.post("/document/stream")
async def stream_document(request: Dict[str, Any] = Body(...)) -> StreamingResponse:
    """SSE streaming endpoint: learn + stream document content progressively."""
    text = request.get("text", request.get("content", ""))
    if not text:
        return StreamingResponse(
            _sse_events([{"type": "error", "content": "No text provided"}]),
            media_type="text/event-stream",
        )
    from ai.ed3n.ed3n_engine import ED3NEngine

    garden = _get_shared_garden()
    ed3n = ED3NEngine.get_shared(load_trained=False)
    # Streaming learns progressively — invalidate upfront so concurrent
    # questions during/after the stream never see pre-learn stale answers.
    _invalidate_router_cache("document stream")
    return StreamingResponse(
        _stream_doc_events(text, garden, ed3n),
        media_type="text/event-stream",
    )


async def _stream_doc_events(text: str, garden, ed3n) -> AsyncGenerator[str, None]:
    """Async generator yielding SSE-formatted events from the streaming pipeline."""
    from ai.streaming import StreamingPipeline, TokenStream

    stream = TokenStream()
    pipeline = StreamingPipeline(garden=garden, ed3n=ed3n)
    pipeline_task = asyncio.create_task(pipeline.stream(text, stream))

    async for token in stream:
        if token.type.value == "control":
            if "DONE" in token.content:
                break
            continue
        event = {
            "type": "predicted" if token.confidence < 0.7 else "corrected",
            "content": token.content,
            "confidence": round(token.confidence, 2),
            "level": token.metadata.get("level", "unknown"),
            "pass": token.metadata.get("pass", "fast"),
        }
        yield f"data: {json.dumps(event)}\n\n"

    await pipeline_task
    yield f"data: {json.dumps({'type': 'control', 'content': '[DONE]'})}\n\n"


async def _sse_events(events: list) -> AsyncGenerator[str, None]:
    """Yield a list of events as SSE, for error responses."""
    for event in events:
        yield f"data: {json.dumps(event)}\n\n"
