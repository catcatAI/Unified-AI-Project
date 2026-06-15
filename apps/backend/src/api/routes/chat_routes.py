"""
ANGELA-MATRIX: [L4-L5] [αβγδ] [A] [L3]
Chat & session API routes extracted from main_api_server.py (A3 god module split).
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Body, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse

from api.lifespan import (
    _angela_cfg,
    _get_chat_service,
    get_digital_life,
    get_abc_key_manager,
    get_crisis_system,
    get_causal_reasoning,
    get_level5_asi,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class TTLSessionManager:
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
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
        self._purge_expired()
        return self._sessions.get(session_id)

    def set(self, session_id: str, data: Dict[str, Any]) -> None:
        """Execute the set operation."""
        self._purge_expired()
        if len(self._sessions) >= self._max_sessions:
            oldest = min(self._sessions.keys(), key=lambda k: self._sessions[k].get("created_at", ""))
            del self._sessions[oldest]
        self._sessions[session_id] = data

    def __contains__(self, session_id: str) -> bool:
        """Execute the   contains   operation."""
        self._purge_expired()
        return session_id in self._sessions

    def items(self) -> str:
        """Execute the items operation."""
        self._purge_expired()
        return self._sessions.items()


sessions = TTLSessionManager()

_ed3n_engine = None


def _get_ed3n_engine():
    global _ed3n_engine
    if _ed3n_engine is None:
        from ai.ed3n.ed3n_engine import ED3NEngine
        engine = ED3NEngine()
        engine.reflex.load_presets()
        _ed3n_engine = engine
    return _ed3n_engine


async def _handle_chat_request(
    user_message: str, user_name: str, history: List[Dict[str, Any]], session_id: str, origin: str = "Human",
    extra_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Handle chat request request."""
    logger.info(f"\U0001f4e9 [LIS] Raw message received: '{user_message}' from {origin} (Session: {session_id})")

    if not user_message or not user_message.strip():
        raise ValueError("訊號遺失：消息不能為空")

    _chat_cfg = _angela_cfg.get_authority("angela_core", {}).get("chat_flow", {}) if _angela_cfg else {}
    _max_len = _chat_cfg.get("max_message_length", 4000)
    _trunc_len = _chat_cfg.get("truncation_length", 1000)
    _http_timeout = _chat_cfg.get("http_timeout", 30.0)
    _trunc_msg = _chat_cfg.get("truncation_message", "...\uff08\u622a\u65b7\uff09")
    _schema_ver = _chat_cfg.get("response_schema_version", "2.0")
    if len(user_message) > _max_len:
        logger.warning(f"\U0001f6df [LIS] Intercepted oversized input ({len(user_message)} chars)", exc_info=True)
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
                logger.info(f"\U0001f9ee [DualRail] Math task detected from {origin}")
                verification = await verifier.verify(user_message, user_name)
                if verification.response_text:
                    return _build_math_response(verification, matrix, user_message, session_id, _schema_ver, _trunc_msg)
                is_math = False
        except Exception as math_err:
            logger.warning(f"\u26a0 [DualRail] Math verification failed: {math_err}", exc_info=True)
            is_math = False

        emotion_result = None
        try:
            from services.llm.emotion_analyzer import EmotionAnalyzer
            _emotion_analyzer = EmotionAnalyzer()
            emotion_result = _emotion_analyzer.analyze_emotion(user_message)
            logger.debug(f"Emotion analysis: {emotion_result}")
        except Exception as e:
            logger.info(f"Emotion analysis unavailable: {e}")

        # Crisis safety assessment (fire-and-forget, adds context for LLM)
        crisis_level = 0
        try:
            crisis_sys = get_crisis_system()
            if crisis_sys:
                crisis_level = crisis_sys.assess_input_for_crisis({"text": user_message})
                if crisis_level > 0:
                    logger.info(f"[CrisisSystem] Level {crisis_level} detected for input from {origin}")
        except Exception as e:
            logger.debug(f"Crisis assessment unavailable: {e}")

        # Process chat as biological stimulus (fire-and-forget async)
        try:
            from core.bio.biological_integrator import BiologicalIntegrator
            _bio = BiologicalIntegrator()
            asyncio.create_task(_bio.process_auditory_stimulus(volume=0.6, content=user_message))
            if emotion_result:
                emotion = emotion_result.get("emotion", "neutral")
                intensity = emotion_result.get("intensity", 0.5)
                if emotion in ("sad", "angry", "fear"):
                    asyncio.create_task(_bio.process_stress_event(intensity=intensity * 0.3))
                elif emotion in ("happy", "calm"):
                    asyncio.create_task(_bio.process_relaxation_event(intensity=intensity * 0.2))
        except Exception as e:
            logger.debug(f"Biological state update from chat failed: {e}")

        _chat_svc = await _get_chat_service()
        context = {"user_name": user_name}
        if extra_context:
            context.update(extra_context)
        if emotion_result:
            context["emotion"] = emotion_result
        if crisis_level > 0:
            context["crisis_level"] = crisis_level
            context["crisis_instruction"] = (
                f"User input has crisis level {crisis_level}. "
                "Respond with empathy, provide support resources if appropriate, "
                "and prioritize user safety in your response."
            )
            # High-crisis alignment check via Level5 ASI (fire-and-forget)
            if crisis_level >= 2:
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
        if history:
            context["history"] = history

        # Get live biological state for LLM context
        try:
            from core.bio.biological_integrator import BiologicalIntegrator
            _bio = BiologicalIntegrator()
            context["bio_state"] = _bio.get_biological_state()
        except Exception:
            pass

        # Fill state_for_llm for prompt builder cognitive state block
        try:
            from core.engine.state_matrix import StateMatrix4D
            _sm = StateMatrix4D()
            _axes = {}
            for _ax_name in ("alpha", "beta", "gamma", "delta", "epsilon", "zeta"):
                _dim = _sm.dimensions.get(_ax_name)
                if _dim:
                    _axes[_ax_name] = {"values": _dim.values.copy()}
            _th = _sm.theta.values if hasattr(_sm, "theta") else {}
            context["state_for_llm"] = {
                "axes": _axes,
                "theta": {
                    "novelty": _th.get("novelty", 0.0),
                    "theta_negativity": _th.get("theta_negativity", 0.0),
                    "creation_urge": _th.get("creation_urge", 0.0),
                    "correction_urge": _th.get("correction_urge", 0.0),
                },
                "eta": {"module_count": 0, "success_rate": 0.0, "structural_drift": 0.0},
                "guidance": [],
            }
        except Exception:
            pass

        retrieved_ctx = []
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
            except Exception:
                pass
        context["retrieved_context"] = retrieved_ctx

        # === Execution Gate Flow (v2) ===
        # Handle pending confirmation from previous turn
        pending = context.get("pending_action")
        if pending:
            msg_lower = user_message.strip().lower()
            confirm_words = {"好", "是", "确认", "ok", "yes", "sure", "确定", "对"}
            cancel_words = {"不要", "取消", "算了", "no", "cancel", "skip", "不用"}

            if msg_lower in confirm_words:
                handler_id = pending.get("handler")
                if handler_id and _chat_svc and _chat_svc.model_bus:
                    try:
                        action_result = await _chat_svc.model_bus.execute_handler(
                            handler_id, pending.get("original_query", user_message), context
                        )
                        context["last_action_result"] = action_result
                        context["pending_action"] = None
                        context["continuation_count"] = 0
                    except Exception as e:
                        logger.warning(f"Execution gate handler failed: {e}")
                        context["pending_action"] = None
                else:
                    context["pending_action"] = None

            elif msg_lower in cancel_words:
                context["pending_action"] = None
                return {
                    "response_text": "好的，不执行。还有什么需要帮忙的吗？",
                    "source": "gate_cancel",
                    "schema_version": _schema_ver,
                    "truncation_message": "",
                    "emotion": "neutral",
                    "emotion_confidence": 0.5,
                    "emotion_intensity": 0.5,
                    "session_id": session_id,
                }
            else:
                # Not confirm or cancel → treat as new input, clear pending
                context["pending_action"] = None

        # Intent classification (QueryClassifier v2)
        try:
            from ai.core.query_classifier import QueryClassifier
            classifier = QueryClassifier()
            classify_result = classifier.classify(user_message)

            # Execution gate decision
            from ai.core.execution_gate import ExecutionGate
            gate = ExecutionGate(model_bus=_chat_svc.model_bus if _chat_svc else None)
            decision = gate.decide(
                query_type=classify_result.primary_type.value,
                action_type=classify_result.action_type,
                user_message=user_message,
                confidence=classify_result.confidence,
                context=context,
            )

            if decision.action == "auto_execute":
                if decision.handler and _chat_svc and _chat_svc.model_bus:
                    try:
                        action_result = await _chat_svc.model_bus.execute_handler(
                            decision.handler, user_message, context
                        )
                        context["last_action_result"] = action_result
                        context["continuation_count"] = 0
                    except Exception as e:
                        logger.warning(f"Execution gate auto-execute failed: {e}")

            elif decision.action == "confirm_then_execute":
                context["pending_action"] = {
                    "handler": decision.handler,
                    "action_type": decision.action_type,
                    "original_query": decision.original_query,
                }
                return {
                    "response_text": decision.confirm_message,
                    "source": "gate_confirm",
                    "schema_version": _schema_ver,
                    "truncation_message": "",
                    "emotion": "neutral",
                    "emotion_confidence": classify_result.confidence,
                    "emotion_intensity": 0.5,
                    "hit_score": classify_result.confidence,
                    "hit_source": "gate_confirm",
                    "route": classify_result.primary_type.value,
                    "session_id": session_id,
                }
            else:
                # reject
                context["last_action_result"] = None

        except Exception as e:
            logger.debug(f"Execution gate unavailable: {e}")

        _llm_response = await asyncio.wait_for(
            _chat_svc.generate_response(user_message, user_name, context=context),
            timeout=_http_timeout,
        )
        response_text = _llm_response.text if hasattr(_llm_response, 'text') else str(_llm_response)
        _flow_source = _chat_cfg.get("default_flow", "angela_chat_service")

        # Increment continuation count for loop protection
        context["continuation_count"] = context.get("continuation_count", 0) + 1

        # Fire-and-forget: learn causal relationship from this interaction
        try:
            _causal = get_causal_reasoning()
            if _causal and response_text:
                _causal.learn({
                    "variables": ["user_input", "angela_response"],
                    "data": {"user_input": [len(user_message)], "angela_response": [len(response_text)]},
                    "relationships": [{
                        "cause": "user_input",
                        "effect": "angela_response",
                        "strength": 0.5,
                        "source": f"chat_{session_id}",
                    }],
                })
        except Exception:
            pass

        return {
            "response_text": response_text,
            "source": _flow_source,
            "schema_version": _schema_ver,
            "truncation_message": _trunc_msg if len(user_message) > _max_len else "",
            "emotion": emotion_result.get("emotion", "neutral") if emotion_result else "neutral",
            "emotion_confidence": emotion_result.get("confidence", 0.5) if emotion_result else 0.5,
            "emotion_intensity": emotion_result.get("intensity", 0.5) if emotion_result else 0.5,
            "hit_score": getattr(_llm_response, 'hit_score', 0.0),
            "hit_source": getattr(_llm_response, 'hit_source', 'none'),
            "route": getattr(_llm_response, 'route', 'llm'),
            "session_id": session_id,
        }

    except asyncio.TimeoutError:
        logger.warning(f"LLM response timeout for message: {user_message[:50]}...", exc_info=True)
        try:
            _timeout_text = _get_ed3n_engine().process(
                "timeout_response", context={"fallback": True}, depth="reflex"
            )
        except Exception:
            _timeout_text = "抱歉，我目前無法回應，請稍後再試。"
        return {
            "response_text": _timeout_text,
            "source": "fallback-timeout",
            "schema_version": _schema_ver,
            "truncation_message": "",
            "emotion": "neutral",
            "emotion_confidence": 0.5,
            "emotion_intensity": 0.5,
            "session_id": session_id,
        }
    except asyncio.CancelledError:
        logger.info("Client disconnected mid-response, cancelling")
        try:
            _cancel_text = _get_ed3n_engine().process(
                "timeout_response", context={"fallback": True}, depth="reflex"
            )
        except Exception:
            _cancel_text = "抱歉，我目前無法回應，請稍後再試。"
        return {
            "response_text": _cancel_text,
            "source": "fallback-disconnect",
            "schema_version": _schema_ver,
            "truncation_message": "",
            "emotion": "neutral",
            "emotion_confidence": 0.5,
            "emotion_intensity": 0.5,
            "session_id": session_id,
        }
    except Exception as e:
        logger.error(f"Error in _handle_chat_request: {e}", exc_info=True)
        raise RuntimeError(f"chat request failed: {e}")


def _build_math_response(verification, matrix, user_message: str, session_id: str, schema_version: str = "2.0", truncation_message: str = "") -> Dict[str, Any]:
    """Build math response."""
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
    """Execute the angela chat operation."""
    user_message = request.get("message", request.get("text", ""))
    session_id = request.get("session_id", f"angela-{uuid.uuid4().hex[:8]}")
    user_name = request.get("user_name", "\u670b\u53cb")
    history = request.get("history", [])
    origin = request.get("origin", "Human")
    return await _handle_chat_request(user_message, user_name, history, session_id, origin=origin)


@router.post("/dialogue")
async def dialogue(request: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Execute the dialogue operation."""
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

    Accepts image file upload + optional question, returns analysis result.
    """
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
    """
    if not session_id:
        session_id = f"img-{uuid.uuid4().hex[:8]}"

    image_context = None
    if file and file.content_type and file.content_type.startswith("image/"):
        try:
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
