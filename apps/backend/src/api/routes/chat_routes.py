"""
ANGELA-MATRIX: [L4-L5] [αβγδ] [A] [L3]
Chat & session API routes extracted from main_api_server.py (A3 god module split).
"""

import asyncio
import logging
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from api.lifespan import (
    _angela_cfg,
    _get_chat_service,
    get_abc_key_manager,
    get_causal_reasoning,
    get_crisis_system,
    get_digital_life,
    get_level5_asi,
)
from fastapi import APIRouter, Body, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter()

_background_tasks: set = set()


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


class TTLSessionManager:
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._config = _angela_cfg.get_authority("angela_core", {}).get("session_manager", {}) if _angela_cfg else {}
        self._ttl = self._config.get("ttl_seconds", 3600)
        self._max_sessions = self._config.get("max_sessions", 1000)

    def _purge_expired(self) -> None:
        """Purge expired."""
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
        """Execute the get operation."""
        with self._lock:
            self._purge_expired()
            return self._sessions.get(session_id)

    def set(self, session_id: str, data: Dict[str, Any]) -> None:
        """Execute the set operation."""
        with self._lock:
            self._purge_expired()
            if len(self._sessions) >= self._max_sessions:
                oldest = min(self._sessions.keys(), key=lambda k: self._sessions[k].get("created_at", ""))
                del self._sessions[oldest]
            self._sessions[session_id] = data

    def __contains__(self, session_id: str) -> bool:
        """Execute the   contains   operation."""
        with self._lock:
            self._purge_expired()
            return session_id in self._sessions

    def items(self) -> list:
        """Execute the items operation."""
        with self._lock:
            self._purge_expired()
            return list(self._sessions.items())


sessions = TTLSessionManager()

_ed3n_engine = None


def _get_ed3n_engine():
    global _ed3n_engine
    if _ed3n_engine is None:
        from ai.ed3n.ed3n_engine import ED3NEngine
        _ed3n_engine = ED3NEngine.get_shared()
    return _ed3n_engine


_bio_integrator = None


def _get_bio_integrator():
    global _bio_integrator
    if _bio_integrator is None:
        from core.bio.biological_integrator import BiologicalIntegrator
        _bio_integrator = BiologicalIntegrator()
    return _bio_integrator


_dialogue_ctx_mgr = None


def _get_dialogue_ctx():
    global _dialogue_ctx_mgr
    if _dialogue_ctx_mgr is None:
        from ai.context.dialogue_context import DialogueContextManager
        _dialogue_ctx_mgr = DialogueContextManager()
    return _dialogue_ctx_mgr


_emotion_analyzer = None
_emotion_system = None
_lifecycle_fallback = None
_modality_gateway = None


def _get_modality_gateway():
    """Get the shared ModalityGateway, preferring the DLI's live instance.

    When DigitalLifeIntegrator is running, its modality_gateway is updated
    by _health_check_loop() with live arousal + introspection data.
    Falls back to a standalone singleton when DLI is unavailable.
    """
    try:
        dli = get_digital_life()
        if dli and hasattr(dli, 'modality_gateway'):
            return dli.modality_gateway
    except Exception:
        logger.warning("_get_modality_gateway: DLI unavailable, using standalone", exc_info=True)
    global _modality_gateway
    if _modality_gateway is None:
        from core.life.digital_life_integrator import ModalityGateway
        _modality_gateway = ModalityGateway()
    return _modality_gateway


def _get_lifecycle():
    """Get the shared AutonomousLifeCycle singleton from lifespan."""
    try:
        from api.lifespan import get_lifecycle as _lifespan_get_lifecycle
        return _lifespan_get_lifecycle()
    except Exception:
        logger.warning("_get_lifecycle: lifespan unavailable, using fallback", exc_info=True)
    # Fallback: create own singleton if lifespan not available
    global _lifecycle_fallback
    if _lifecycle_fallback is None:
        from core.life.autonomous_life_cycle import AutonomousLifeCycle
        _lifecycle_fallback = AutonomousLifeCycle()
    return _lifecycle_fallback


def _get_emotion_analyzer():
    global _emotion_analyzer
    if _emotion_analyzer is None:
        from services.llm.emotion_analyzer import EmotionAnalyzer
        _emotion_analyzer = EmotionAnalyzer()
    return _emotion_analyzer


def _get_emotion_system():
    global _emotion_system
    if _emotion_system is None:
        from ai.alignment.emotion_system import EmotionSystem
        _emotion_system = EmotionSystem()
    return _emotion_system


_state_matrix = None


def _get_state_matrix():
    global _state_matrix
    if _state_matrix is None:
        from core.engine.state_matrix import StateMatrix4D
        _state_matrix = StateMatrix4D()
    return _state_matrix


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


async def _inject_emotion_behavioral_context(
    emotion_result: Optional[Dict[str, Any]],
    context: Dict[str, Any],
    bio: Optional[Any] = None,
) -> None:
    """Inject emotional behavioral adjustments into context.

    Maps detected user emotion to routing_mode and response_style
    so that the LLM prompt receives behavioral guidance beyond
    just the emotion text. Also updates Angela's internal EmotionSystem
    and cross-component Emotion→Biological stress/relaxation (C³ 4.0).
    """
    if not emotion_result:
        return
    emotion = emotion_result.get("emotion", "neutral")
    behavior = _ANGELA_EMOTION_BEHAVIOR_MAP.get(emotion, {
        "routing_mode": "neutral", "response_style": "standard"
    })
    context["emotional_behavior"] = behavior

    # Apply influence to Angela's EmotionSystem for internal state tracking
    try:
        es = _get_emotion_system()
        if es:
            intensity = emotion_result.get("intensity", 0.5)
            es.apply_influence("user_message", emotion, intensity * 0.3, 0.5)
            adj = es.get_behavioral_adjustment()
            context["angela_emotion"] = adj

        # Cross-component: Emotion → Biological stress/relaxation (C³ 4.0)
        if bio is not None:
            await _apply_emotion_to_biology(emotion, intensity, bio)
    except Exception as e:
        logger.debug(f"EmotionSystem behavioral injection failed: {e}")


# Emotion → Biological stress/relaxation mapping for C³ 4.0 cross-component chain
_EMOTION_TO_STRESS_MAP: Dict[str, float] = {
    "anger": 0.3, "fear": 0.35, "sadness": 0.15,
    "disgust": 0.12, "surprise": 0.05, "anticipation": 0.05,
}

_EMOTION_TO_RELAXATION_MAP: Dict[str, float] = {
    "joy": 0.2, "trust": 0.1,
}


async def _apply_emotion_to_biology(
    emotion: str, intensity: float, bio: Any,
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
    """Validate user message and truncate if it exceeds the maximum length."""
    if not user_message or not user_message.strip():
        raise ValueError("訊號遺失：消息不能為空")
    max_len = chat_cfg.get("max_message_length", 4000)
    trunc_len = chat_cfg.get("truncation_length", 1000)
    if len(user_message) > max_len:
        logger.warning(f"\U0001f6df [LIS] Intercepted oversized input ({len(user_message)} chars)")
        user_message = user_message[:trunc_len]
    return user_message


async def _try_math_verification(
    user_message: str,
    user_name: str,
    session_id: str,
    schema_ver: str,
    trunc_msg: str,
) -> Optional[Dict[str, Any]]:
    """Try dual-rail math verification. Returns response dict if math detected, else None."""
    try:
        from services.math_verifier import MathVerifier
        digital_life = get_digital_life()
        matrix = digital_life.state_matrix if digital_life and hasattr(digital_life, "state_matrix") else None
        verifier = MathVerifier(state_matrix=matrix)
        if verifier.is_math_message(user_message):
            logger.info("\U0001f9ee [DualRail] Math task detected")
            verification = await verifier.verify(user_message, user_name)
            if verification.response_text:
                return _build_math_response(verification, matrix, user_message, session_id, schema_ver, trunc_msg)
    except Exception as e:
        logger.warning(f"\u26a0 [DualRail] Math verification failed: {e}")
    return None


async def _analyze_emotion_and_crisis(
    user_message: str,
    context: Dict[str, Any],
    bio: Any,
) -> Tuple[Optional[Dict[str, Any]], int]:
    """Analyze user emotion + assess crisis level. Fires biological stimulus as side-effect."""
    emotion_result: Optional[Dict[str, Any]] = None
    try:
        emotion_result = _get_emotion_analyzer().analyze_emotion(user_message)
        logger.debug(f"Emotion analysis: {emotion_result}")
    except Exception as e:
        logger.info(f"Emotion analysis unavailable: {e}")

    crisis_level = 0
    try:
        crisis_sys = get_crisis_system()
        if crisis_sys:
            crisis_level = crisis_sys.assess_input_for_crisis({"text": user_message})
            if crisis_level > 0:
                logger.info(f"[CrisisSystem] Level {crisis_level} detected")
    except Exception as e:
        logger.debug(f"Crisis assessment unavailable: {e}")

    # Fire-and-forget: biological stimulus processing
    try:
        _spawn_background_task(
            bio.process_auditory_stimulus(volume=0.6, content=user_message), "auditory_stimulus")
        if emotion_result:
            emotion = emotion_result.get("emotion", "neutral")
            intensity = emotion_result.get("intensity", 0.5)
            if emotion in ("sad", "angry", "fear"):
                _spawn_background_task(
                    bio.process_stress_event(intensity=intensity * 0.3), "stress_event")
            elif emotion in ("happy", "calm"):
                _spawn_background_task(
                    bio.process_relaxation_event(intensity=intensity * 0.2), "relaxation_event")
    except Exception as e:
        logger.debug(f"Biological state update from chat failed: {e}")

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
            alignment_result = await asi.process_request({
                "request_id": str(uuid.uuid4()),
                "capability_id": "chat_response",
                "user_intent": {"text": user_message, "crisis_level": crisis_level},
                "ethical_constraints": ["user_safety", "empathy", "no_harm"],
            })
            if alignment_result.get("status") == "alignment_failed":
                logger.warning(f"[Level5ASI] Alignment failed: {alignment_result.get('reason')}")
                context["alignment_override"] = "prioritize_safety"
    except Exception as e:
        logger.debug(f"Level5ASI alignment check unavailable: {e}")


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
    # Bio state
    try:
        context["bio_state"] = bio.get_biological_state()
    except Exception as e:
        logger.debug(f"Biological state retrieval failed: {e}")

    # State matrix 4D axes
    try:
        sm = _get_state_matrix()
        axes = {}
        for ax_name in ("alpha", "beta", "gamma", "delta", "epsilon", "zeta"):
            dim = sm.dimensions.get(ax_name)
            if dim:
                axes[ax_name] = {"values": dim.values.copy()}
        th = sm.theta.values if hasattr(sm, "theta") else {}
        context["state_for_llm"] = {
            "axes": axes,
            "theta": {
                "novelty": th.get("novelty", 0.0),
                "theta_negativity": th.get("theta_negativity", 0.0),
                "creation_urge": th.get("creation_urge", 0.0),
                "correction_urge": th.get("correction_urge", 0.0),
            },
            "eta": {"module_count": 0, "success_rate": 0.0, "structural_drift": 0.0},
            "guidance": [],
        }
    except Exception as e:
        logger.debug(f"StateMatrix4D unavailable: {e}")

    # ED3N context retrieval from history
    retrieved_ctx: List[Dict[str, Any]] = []
    if history and len(history) > 0:
        try:
            ed3n = _get_ed3n_engine()
            query_keys = set(ed3n.dictionary.encode(user_message))
            for entry in history:
                content = entry.get("content", "")
                if not content:
                    continue
                entry_keys = set(ed3n.dictionary.encode(content))
                overlap = len(query_keys & entry_keys)
                if overlap > 0:
                    retrieved_ctx.append({**entry, "relevance": float(overlap)})
            retrieved_ctx.sort(key=lambda x: x["relevance"], reverse=True)
            retrieved_ctx = retrieved_ctx[:5]
        except Exception as e:
            logger.debug(f"ED3N context retrieval failed: {e}")
    context["retrieved_context"] = retrieved_ctx

    # Dialogue context injection
    try:
        dialogue_ctx = _get_dialogue_ctx()
        if session_id:
            dialogue_ctx.add_message(session_id, "Human", user_message)
            conv_ctx = dialogue_ctx.get_conversation_context(session_id)
            if conv_ctx:
                context["dialogue_context"] = conv_ctx
    except Exception as e:
        logger.debug(f"Dialogue context unavailable: {e}")

    # Memory context injection
    try:
        from ai.context.memory_context import MemoryContextManager
        memory_ctx = MemoryContextManager()
        recent_memories = memory_ctx.get_memories_by_type("short_term", limit=5)
        if recent_memories:
            context["recent_memories"] = recent_memories
    except Exception as e:
        logger.debug(f"Memory context unavailable: {e}")

    # History in context
    if history:
        context["history"] = history


async def _handle_execution_gate(
    user_message: str,
    chat_svc: Any,
    context: Dict[str, Any],
    schema_ver: str,
    session_id: str,
) -> Optional[Dict[str, Any]]:
    """Run execution gate: intent classification → decide auto/confirm/reject.
    Returns a response dict if gate short-circuits (confirm or reject), else None."""
    try:
        from ai.core.execution_gate import ExecutionGate
        from ai.core.query_classifier import QueryClassifier

        # Handle pending action from previous turn
        pending = context.pop("pending_action", None)
        if pending:
            msg_lower = user_message.strip().lower()
            confirm_words = {"\u597d", "\u662f", "\u786e\u8ba4", "ok", "yes", "sure", "\u786e\u5b9a", "\u5bf9"}
            cancel_words = {"\u4e0d\u8981", "\u53d6\u6d88", "\u7b97\u4e86", "no", "cancel", "skip", "\u4e0d\u7528"}

            if msg_lower in confirm_words:
                handler_id = pending.get("handler")
                if handler_id and chat_svc and chat_svc.model_bus:
                    try:
                        action_result = await chat_svc.model_bus.execute_handler(
                            handler_id, pending.get("original_query", user_message), context
                        )
                        context["last_action_result"] = action_result
                        context["continuation_count"] = 0
                        # Record confirm-path success for ExecutionGate C³ feedback loop (C³ 6.0)
                        try:
                            ExecutionGate().record_result(handler_id, True)
                        except Exception:
                            logger.warning("Failed to record execution gate success feedback", exc_info=True)
                    except Exception as e:
                        logger.warning(f"Execution gate handler failed: {e}")
                        # Record confirm-path failure for ExecutionGate C³ feedback loop
                        try:
                            ExecutionGate().record_result(handler_id, False)
                        except Exception:
                            logger.warning("Failed to record execution gate failure feedback", exc_info=True)
            elif msg_lower in cancel_words:
                return {
                    "response_text": "\u597d\u7684\uff0c\u4e0d\u6267\u884c\u3002\u8fd8\u6709\u4ec0\u4e48\u9700\u8981\u5e2e\u5fd9\u7684\u5417\uff1f",
                    "source": "gate_cancel",
                    "schema_version": schema_ver,
                    "truncation_message": "",
                    "emotion": "neutral",
                    "emotion_confidence": 0.5,
                    "emotion_intensity": 0.5,
                    "session_id": session_id,
                }

        # Intent classification + Execution gate decision
        classifier = QueryClassifier(ed3n_engine=_get_ed3n_engine())
        classify_result = classifier.classify(user_message)
        gate = ExecutionGate(model_bus=chat_svc.model_bus if chat_svc else None)
        decision = gate.decide(
            query_type=classify_result.primary_type.value,
            action_type=classify_result.action_type,
            user_message=user_message,
            confidence=classify_result.confidence,
            context=context,
        )

        if decision.action == "auto_execute":
            if decision.handler and chat_svc and chat_svc.model_bus:
                try:
                    action_result = await chat_svc.model_bus.execute_handler(
                        decision.handler, user_message, context
                    )
                    context["last_action_result"] = action_result
                    context["continuation_count"] = 0
                    gate.record_result(decision.handler, True)
                except Exception as e:
                    logger.warning(f"Execution gate auto-execute failed: {e}")
                    gate.record_result(decision.handler, False)
        elif decision.action == "confirm_then_execute":
            context["pending_action"] = {
                "handler": decision.handler,
                "action_type": decision.action_type,
                "original_query": decision.original_query,
            }
            return {
                "response_text": decision.confirm_message,
                "source": "gate_confirm",
                "schema_version": schema_ver,
                "truncation_message": "",
                "emotion": "neutral",
                "emotion_confidence": classify_result.confidence,
                "emotion_intensity": 0.5,
                "hit_score": classify_result.confidence,
                "hit_source": "gate_confirm",
                "route": classify_result.primary_type.value,
                "session_id": session_id,
            }
        # reject: clear action result, continue to LLM
        context["last_action_result"] = None
    except Exception as e:
        logger.debug(f"Execution gate unavailable: {e}")
    return None


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
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier(ed3n_engine=_get_ed3n_engine())
        classify_result = classifier.classify(user_message)

        # Only route non-actionable intents (execution gate handles actionable ones)
        actionable = {QueryType.FILE, QueryType.SEARCH, QueryType.CODE, QueryType.EXECUTE, QueryType.TASK}
        if classify_result.primary_type in actionable:
            return None

        # Map QueryType to agent suitability threshold — route all non-actionable intents
        agent_types = {QueryType.CREATIVE, QueryType.KNOWLEDGE, QueryType.OPINION,
                       QueryType.VISION, QueryType.AUDIO, QueryType.LOGIC, QueryType.COMMAND}
        if classify_result.primary_type not in agent_types and classify_result.confidence < 0.3:
            return None

        # Lazy-init agent manager + orchestrator
        agent_mgr = AgentManager(enable_process_agents=False, enable_router=False)
        register_specialized_agents(agent_mgr)
        orchestrator = AgentOrchestrator(agent_manager=agent_mgr)
        route_result = await orchestrator.route_task(user_message, context)

        primary = route_result.get("results", [{}])[0] if route_result.get("results") else {}
        agent_result = primary.get("result")
        if agent_result and isinstance(agent_result, dict) and agent_result.get("result"):
            response_text = str(agent_result["result"])
            return {
                "response_text": response_text,
                "source": f"agent_{primary.get('agent', 'unknown')}",
                "schema_version": schema_ver,
                "truncation_message": "",
                "emotion": context.get("emotion", {}).get("emotion", "neutral"),
                "emotion_confidence": classify_result.confidence,
                "emotion_intensity": 0.5,
                "session_id": session_id,
            }
    except Exception as e:
        logger.debug(f"Agent routing unavailable: {e}")
    return None


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
            return {"temperature_bias": 0.0, "max_tokens_bias": 0, "causal_confidence": 0.0, "effective_guidance": ""}

        rels = causal.get_relationships()
        if not rels:
            return {"temperature_bias": 0.0, "max_tokens_bias": 0, "causal_confidence": 0.0, "effective_guidance": ""}

        temp_bias = 0.0
        tokens_bias = 0
        confidence = 0.0
        guidance_parts = []

        # Shortcut: get average prediction strength for a cause
        def _avg_strength(cause: str) -> float:
            preds = causal.predict(cause)
            if not preds:
                return 0.0
            return sum(p["strength"] for p in preds) / len(preds)

        # user_input → angela_response: high strength = predictable pattern
        # → reduce temperature for more consistent, reliable output
        ui_strength = _avg_strength("user_input")
        if ui_strength > 0.5:
            adj = -(0.15 * min(1.0, ui_strength))
            temp_bias += adj
            confidence += 0.3
            guidance_parts.append(f"user_input→response (strength={ui_strength:.2f}, temp{adj:+.3f})")

        # query_complexity → angela_response: complex queries need precise responses
        # → reduce temperature + increase max_tokens
        qc_strength = _avg_strength("query_complexity")
        if qc_strength > 0.3:
            temp_adj = -(0.1 * min(1.0, qc_strength))
            temp_bias += temp_adj
            token_adj = int(128 * min(1.0, qc_strength))
            tokens_bias += token_adj
            confidence += 0.3
            guidance_parts.append(f"complexity→response (strength={qc_strength:.2f}, temp{temp_adj:+.3f}, +{token_adj}tok)")

        # conversation_momentum → user_input: high momentum = engaging conversation
        # → increase temperature for more creative, exploratory responses
        cm_strength = _avg_strength("conversation_momentum")
        if cm_strength > 0.4:
            temp_adj = 0.1 * min(1.0, cm_strength)
            temp_bias += temp_adj
            token_adj = int(64 * min(1.0, cm_strength))
            tokens_bias += token_adj
            confidence += 0.2
            guidance_parts.append(f"momentum→input (strength={cm_strength:.2f}, temp{temp_adj:+.3f}, +{token_adj}tok)")

        # interaction_value → user_input: high value interaction → boost response depth
        iv_strength = _avg_strength("interaction_value")
        if iv_strength > 0.3:
            token_adj = int(128 * min(1.0, iv_strength))
            tokens_bias += token_adj
            confidence += 0.2
            guidance_parts.append(f"interaction_value→input (strength={iv_strength:.2f}, +{token_adj}tok)")

        effective_guidance = "; ".join(guidance_parts) if guidance_parts else ""
        return {
            "temperature_bias": round(max(-0.3, min(0.3, temp_bias)), 3),
            "max_tokens_bias": max(-256, min(256, tokens_bias)),
            "causal_confidence": round(min(1.0, confidence), 3),
            "effective_guidance": effective_guidance,
        }
    except Exception as e:
        logger.debug(f"Causal routing adjustment failed: {e}")
        return {"temperature_bias": 0.0, "max_tokens_bias": 0, "causal_confidence": 0.0, "effective_guidance": ""}


def _inject_causal_predictions(
    context: Dict[str, Any]
) -> None:
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
                logger.debug(
                    f"Injected {len(predictions)} causal predictions into context"
                )
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
        logger.debug(f"Causal prediction injection failed: {e}")


# ── Per-session temporal buffers for causal learning ─────────────────────
# Accumulates time-series data across multiple interactions so Granger
# causality can fire (requires >= 5 samples per variable).
_CAUSAL_BUFFERS: Dict[str, Dict[str, List[float]]] = {}

# TemporalState bridge for causal ingest_temporal_state() (C³ 4.0)
_CAUSAL_TEMPORAL_STATE = None

def _get_causal_temporal_state():
    global _CAUSAL_TEMPORAL_STATE
    if _CAUSAL_TEMPORAL_STATE is None:
        from core.state.temporal import TemporalState
        _CAUSAL_TEMPORAL_STATE = TemporalState(max_size=200)
    return _CAUSAL_TEMPORAL_STATE


def _get_causal_buffer(session_id: str) -> Dict[str, List[float]]:
    """Get or create a temporal buffer for the given session."""
    if session_id not in _CAUSAL_BUFFERS:
        _CAUSAL_BUFFERS[session_id] = {
            "msg_lengths": [],
            "resp_lengths": [],
            "engagement_ratios": [],
        }
    return _CAUSAL_BUFFERS[session_id]


def _fire_causal_learning(
    response_text: str, user_message: str, session_id: str
) -> None:
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
        engagement = resp_len / max(msg_len, 1.0)

        buf["msg_lengths"].append(msg_len)
        buf["resp_lengths"].append(resp_len)
        buf["engagement_ratios"].append(engagement)

        # Emotion feedback loop: interaction outcome → emotional state adjustment
        try:
            es = _get_emotion_system()
            if es:
                # Determine if there was a processing error during this interaction
                had_error = len(response_text) == 0
                es.process_interaction_feedback(
                    engagement_ratio=engagement,
                    had_error=had_error,
                    response_success=None,  # Let engagement_ratio determine
                )
        except Exception as e:
            logger.debug(f"Emotion feedback loop failed: {e}")

        # Dynamic strength: higher when response is substantive relative to query
        dynamic_strength = min(0.9, max(0.1, engagement / 5.0))

        # Only pass the accumulated series (not a single value) once we have
        # enough temporal depth for Granger causality.
        data: Dict[str, List[float]]
        if len(buf["msg_lengths"]) >= 5:
            data = {
                "user_input": list(buf["msg_lengths"]),
                "angela_response": list(buf["resp_lengths"]),
            }
        else:
            data = {
                "user_input": [msg_len],
                "angela_response": [resp_len],
            }

        causal.learn({
            "variables": ["user_input", "angela_response"],
            "data": data,
            "relationships": [{
                "cause": "user_input",
                "effect": "angela_response",
                "strength": dynamic_strength,
                "source": f"chat_{session_id}",
            }],
        })

        # C³ 4.0: Record snapshot into TemporalState bridge and periodically
        # call ingest_temporal_state() for Granger causality over chat data.
        ts = _get_causal_temporal_state()
        ts.record({
            "interaction": {
                "msg_length": msg_len,
                "resp_length": resp_len,
                "engagement_ratio": engagement,
            },
        })
        if ts.size() >= 5 and ts.size() % 5 == 0:
            causal.ingest_temporal_state(ts, window=20)

        # Cap buffer at 100 entries per session to prevent unbounded growth
        if len(buf["msg_lengths"]) > 100:
            buf["msg_lengths"] = buf["msg_lengths"][-50:]
            buf["resp_lengths"] = buf["resp_lengths"][-50:]
            buf["engagement_ratios"] = buf["engagement_ratios"][-50:]

    except Exception as e:
        logger.debug(f"Causal learning failed: {e}")


def _handle_timeout(session_id: str, schema_ver: str) -> Dict[str, Any]:
    """Handle LLM timeout with fallback response."""
    logger.warning(f"LLM response timeout for session: {session_id}")
    try:
        timeout_text = _get_ed3n_engine().process(
            "timeout_response", context={"fallback": True}, depth="reflex"
        )
    except Exception as e:
        logger.debug(f"ED3N fallback failed in timeout handler: {e}")
        timeout_text = "\u62b1\u6b49\uff0c\u6211\u76ee\u524d\u65e0\u6cd5\u56de\u5e94\uff0c\u8bf7\u7a0d\u540e\u518d\u8bd5\u3002"
    return {
        "response_text": timeout_text,
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
) -> Dict[str, Any]:
    """Build the final standardized chat response dict."""
    return {
        "response_text": response_text,
        "source": source,
        "schema_version": schema_ver,
        "truncation_message": trunc_msg if len(user_message) > max_len else "",
        "emotion": emotion_result.get("emotion", "neutral") if emotion_result else "neutral",
        "emotion_confidence": emotion_result.get("confidence", 0.5) if emotion_result else 0.5,
        "emotion_intensity": emotion_result.get("intensity", 0.5) if emotion_result else 0.5,
        "hit_score": getattr(llm_response, 'hit_score', 0.0),
        "hit_source": getattr(llm_response, 'hit_source', 'none'),
        "route": getattr(llm_response, 'route', 'llm'),
        "session_id": session_id,
    }


async def _handle_chat_request(
    user_message: str, user_name: str, history: List[Dict[str, Any]], session_id: str, origin: str = "Human",
    extra_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Orchestrate the full chat pipeline: validate → math → context → emotion/crisis → execution gate → agent routing → LLM."""
    logger.info(f"\U0001f4e9 [LIS] Raw message received: '{user_message}' from {origin} (Session: {session_id})")

    chat_cfg = _angela_cfg.get_authority("angela_core", {}).get("chat_flow", {}) if _angela_cfg else {}
    max_len = chat_cfg.get("max_message_length", 4000)
    schema_ver = chat_cfg.get("response_schema_version", "2.0")
    trunc_msg = chat_cfg.get("truncation_message", "...\uff08\u622a\u65ad\uff09")
    timeout = chat_cfg.get("http_timeout", 30.0)
    flow_source = chat_cfg.get("default_flow", "angela_chat_service")

    # Step 1: Validate and truncate input
    user_message = _validate_and_truncate_input(user_message, chat_cfg)

    # Step 2: Initialize session
    if session_id not in sessions:
        sessions.set(session_id, {
            "created_at": datetime.now().isoformat(), "origin": origin, "user_name": user_name,
        })

    # Step 3: Math dual-rail verification (fast path — returns early if math detected)
    math_result = await _try_math_verification(user_message, user_name, session_id, schema_ver, trunc_msg)
    if math_result:
        return math_result

    # Step 4: Initialize base context + bio integrator
    context: Dict[str, Any] = {"user_name": user_name}
    if extra_context:
        context.update(extra_context)

    # Step 5: Emotion analysis + crisis assessment + biological stimulus
    bio = _get_bio_integrator()
    emotion_result, crisis_level = await _analyze_emotion_and_crisis(user_message, context, bio)
    if emotion_result:
        context["emotion"] = emotion_result
        # Step 5b: Inject emotional behavioral context (routing_mode + response_style)
        await _inject_emotion_behavioral_context(emotion_result, context, bio)
        # Step 5c: Inject autonomous lifecycle behavioral adjustment
        try:
            lc = _get_lifecycle()
            if lc:
                lc_adj = lc.get_behavioral_adjustment()
                context["lifecycle_behavior"] = lc_adj
                logger.debug(
                    f"Lifecycle behavioral adjustment: {lc_adj.get('routing_mode')} / {lc_adj.get('response_style')} "
                    f"(phase={lc_adj.get('phase')}, decision={lc_adj.get('decision_type')})"
                )
        except Exception as e:
            logger.debug(f"Lifecycle behavioral adjustment unavailable: {e}")
        # Step 5d: Inject modality gateway state (C³ 3.0 — was never consumed)
        try:
            mg = _get_modality_gateway()
            if mg:
                context["modality_state"] = mg.get_modality_summary()
                logger.debug(
                    f"Modality state: {len(context['modality_state'].get('active', []))} active / "
                    f"{len(context['modality_state'].get('inactive', []))} inactive"
                )
        except Exception as e:
            logger.debug(f"Modality state unavailable: {e}")
    if crisis_level > 0:
        context["crisis_level"] = crisis_level
        context["crisis_instruction"] = (
            f"User input has crisis level {crisis_level}. "
            "Respond with empathy, provide support resources if appropriate, "
            "and prioritize user safety in your response."
        )
    await _try_alignment_check(user_message, crisis_level, context)

    # Step 6: Build full LLM context (bio state, state matrix, ED3N retrieval, dialogue, memory)
    chat_svc = await _get_chat_service()
    await _build_chat_context(context, user_message, user_name, history, session_id, chat_svc, bio)

    # Step 7: Execution gate (intent classification → auto/confirm/reject — may short-circuit)
    gate_result = await _handle_execution_gate(user_message, chat_svc, context, schema_ver, session_id)
    if gate_result:
        return gate_result

    # Step 8: Agent auto-routing (creative/knowledge/opinion/vision/audio — may short-circuit)
    agent_result = await _try_agent_routing(user_message, context, schema_ver, session_id)
    if agent_result:
        return agent_result

    # Step 9: Inject causal predictions into context (learned from past interactions)
    _inject_causal_predictions(context)

    # Step 10: Generate LLM response
    try:
        llm_response = await asyncio.wait_for(
            chat_svc.generate_response(user_message, user_name, context=context),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        return _handle_timeout(session_id, schema_ver)
    except asyncio.CancelledError:
        logger.info("Client disconnected mid-response, cancelling")
        raise
    except Exception as e:
        logger.error(f"Error in _handle_chat_request: {e}", exc_info=True)
        raise RuntimeError(f"chat request failed: {e}")

    response_text = llm_response.text if hasattr(llm_response, 'text') else str(llm_response)
    context["continuation_count"] = context.get("continuation_count", 0) + 1
    _fire_causal_learning(response_text, user_message, session_id)

    return _format_chat_response(response_text, llm_response, emotion_result, schema_ver, trunc_msg, user_message, max_len, session_id, source=flow_source)


def _build_math_response(verification, matrix, user_message: str, session_id: str, schema_version: str = "2.0", truncation_message: str = "") -> Dict[str, Any]:
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
        epsilon_conf = verification.extraction.get("confidence", 0.5) if verification.extraction else 0.5
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
        "schema_version": schema_version,
        "truncation_message": truncation_message,
        "emotion": emotion,
        "emotion_confidence": emotion_confidence,
        "emotion_intensity": emotion_intensity,
        "session_id": session_id,
    }


@router.get("/security/sync-key-c")
async def sync_key_c(request: Request) -> dict:
    """Log a diagnostic message."""
    client_host = request.client.host
    if client_host not in ["127.0.0.1", "::1", "localhost"]:
        logger.warning(f"Unauthorized access attempt to sync-key-c from {client_host}", exc_info=True)
        raise HTTPException(status_code=403, detail="Access restricted to localhost")
    abc_key_manager = get_abc_key_manager()
    key_c = abc_key_manager.get_key("KeyC")
    if not key_c:
        raise HTTPException(status_code=404, detail="Security keys not initialized")
    return {"key_available": True}


@router.post("/session/start")
async def start_session(request: Dict[str, Any] = Body(default={})) -> dict:
    """Execute the start session operation."""
    session_id = f"sess-{uuid.uuid4().hex[:8]}"
    sessions.set(session_id, {
        "created_at": datetime.now().isoformat(),
        "messages": [],
        "user_name": request.get("user_name", "User"),
    })
    return {"session_id": session_id, "message": _get_ed3n_engine().process("welcome", context={"session_id": session_id}, depth="reflex")}


@router.post("/session/{session_id}/send")
async def send_message(session_id: str, request: Dict[str, Any] = Body(...)) -> dict:
    """Execute the send message operation."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    user_message = request.get("text", request.get("message", ""))
    session = sessions.get(session_id)
    messages = session.get("messages", [])
    messages.append({"role": "user", "content": user_message, "timestamp": datetime.now().isoformat()})
    ai_response = _get_ed3n_engine().process("session_response", context={"user_message": user_message}, depth="reflex")
    messages.append({"role": "assistant", "content": ai_response, "timestamp": datetime.now().isoformat()})
    return {"session_id": session_id, "response_text": ai_response}


@router.post("/angela/chat")
async def angela_chat(request: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Execute the angela chat operation.

    ⚠️ DEPRECATED: Use POST /api/v1/chat/unified instead.
    This endpoint is kept for backward compatibility and will be removed in a future release.
    """
    import warnings
    warnings.warn("POST /angela/chat is deprecated, use POST /chat/unified", DeprecationWarning, stacklevel=2)
    user_message = request.get("message", request.get("text", ""))
    session_id = request.get("session_id", f"angela-{uuid.uuid4().hex[:8]}")
    user_name = request.get("user_name", "\u670b\u53cb")
    history = request.get("history", [])
    origin = request.get("origin", "Human")
    return await _handle_chat_request(user_message, user_name, history, session_id, origin=origin)


@router.post("/dialogue")
async def dialogue(request: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Execute the dialogue operation.

    ⚠️ DEPRECATED: Use POST /api/v1/chat/unified instead.
    This endpoint is kept for backward compatibility and will be removed in a future release.
    """
    import warnings
    warnings.warn("POST /dialogue is deprecated, use POST /chat/unified", DeprecationWarning, stacklevel=2)
    user_message = request.get("message", request.get("text", ""))
    session_id = request.get("session_id", f"angela-{uuid.uuid4().hex[:8]}")
    user_name = request.get("user_name", "\u670b\u53cb")
    history = request.get("history", [])
    origin = request.get("origin", "Human")
    return await _handle_chat_request(user_message, user_name, history, session_id, origin=origin)


@router.post("/chat/unified")
async def unified_chat(request: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Execute the unified chat operation."""
    user_message = request.get("message", request.get("text", ""))
    context = {
        "user_id": request.get("user_name", request.get("user_id", "User")),
        "tenant_id": request.get("tenant_id", "default"),
        "persona_id": request.get("persona_id", "angela"),
        "client_id": request.get("origin", request.get("client_id", "desktop")),
    }
    user_name = request.get("user_name", context["user_id"])
    history = request.get("history", [])
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


@router.post("/vision/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    question: str = Form(default="這張圖片裡有什麼？"),
    session_id: str = Form(default=""),
) -> Dict[str, Any]:
    """Analyze an uploaded image using VisionService.

    ⚠️ DEPRECATED: Use POST /chat/with-image instead.
    This endpoint is kept for backward compatibility and will be removed in a future release.

    Accepts image file upload + optional question, returns analysis result.
    """
    import warnings
    warnings.warn("POST /vision/analyze is deprecated, use POST /chat/with-image", DeprecationWarning, stacklevel=2)
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are accepted")

    try:
        image_data = await file.read()
        if len(image_data) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="Image too large (max 10MB)")

        from services.vision_service import VisionService
        vision = VisionService()
        result = await vision.process({
            "image_data": image_data,
            "filename": file.filename,
            "question": question,
        })

        return {
            "analysis": result,
            "filename": file.filename,
            "session_id": session_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vision analysis failed: {e}", exc_info=True)
        raise RuntimeError(f"Vision analysis failed: {e}")


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

    clip_response = None
    image_data = None
    if file and file.content_type and file.content_type.startswith("image/"):
        try:
            image_data = await file.read()

            from ai.ed3n.ed3n_engine import ED3NEngine
            from ai.multimodal.concept_library import ConceptLibrary
            from ai.multimodal.semantic_visual import SemanticVisualEncoder
            from ai.multimodal.vision_response_generator import VisionResponseGenerator

            encoder = SemanticVisualEncoder()
            if encoder.is_available:
                ed3n = ED3NEngine.get_shared()
                if len(ed3n.dictionary.entries) < 100:
                    ed3n.load_external_dictionaries()

                from ai.multimodal.semantic_key_mapper import SemanticKeyMapper
                mapper = SemanticKeyMapper(max_entries=1000)
                library = ConceptLibrary(
                    semantic_encoder=encoder,
                    dictionary=ed3n.dictionary,
                    key_mapper=mapper,
                )
                library.build()

                results = library.classify(image_data, top_k=1)
                if results and results[0]["confidence"] > 0.15:
                    generator = VisionResponseGenerator(dictionary=ed3n.dictionary)
                    for cname, info in library._concepts.items():
                        generator.register_concept(cname, info["dict_key"], info["labels"])
                    top_concept = results[0]["concept_name"]
                    concept_info = library._concepts.get(top_concept, {})
                    action = concept_info.get("action", "") or message or ""
                    clip_response = generator.generate_response(
                        results, language="zh", action=action
                    )
        except Exception as e:
            logger.debug(f"CLIP classification failed, falling back to LLM: {e}")

    if clip_response:
        return {
            "response": clip_response,
            "session_id": session_id,
            "source": "clip_classify",
            "confidence": results[0]["confidence"],
        }

    image_context = None
    if file and file.content_type and file.content_type.startswith("image/"):
        try:
            if image_data is None:
                image_data = await file.read()
            from services.vision_service import VisionService
            vision = VisionService()
            analysis = await vision.process({
                "image_data": image_data,
                "filename": file.filename,
                "question": message or "描述這張圖片",
            })
            image_context = {
                "filename": file.filename,
                "analysis": analysis,
                "image_data": image_data,
            }
        except Exception as e:
            logger.warning(f"Image analysis failed, continuing with text only: {e}")

    history = []
    context = {"user_name": user_name}
    if image_context:
        context["image_analysis"] = image_context

    return await _handle_chat_request(
        user_message=message or "我上傳了一張圖片",
        user_name=user_name,
        history=history,
        session_id=session_id,
        origin="Human",
        extra_context=context if image_context else None,
    )


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

    if file and file.content_type and (
        file.content_type.startswith("audio/") or file.content_type == "application/octet-stream"
    ):
        try:
            audio_data = await file.read()
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
                "error": str(e),
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
