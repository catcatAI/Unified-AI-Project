"""
ANGELA-MATRIX: [L4-L5] [αβγδ] [A] [L3]
Chat & session API routes extracted from main_api_server.py (A3 god module split).
"""

import asyncio
import logging
import random
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Body, Request

from api.lifespan import (
    _angela_cfg,
    _get_chat_service,
    get_digital_life,
    get_abc_key_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class TTLSessionManager:
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


async def _handle_chat_request(
    user_message: str, user_name: str, history: List[Dict[str, Any]], session_id: str, origin: str = "Human"
) -> Dict[str, Any]:
    logger.info(f"\U0001f4e9 [LIS] Raw message received: '{user_message}' from {origin} (Session: {session_id})")

    if not user_message or not user_message.strip():
        raise HTTPException(status_code=400, detail="\u8a0a\u865f\u905a\u5931\uff1a\u6d88\u606f\u4e0d\u80fd\u70ba\u7a7a")

    _chat_cfg = _angela_cfg.get_authority("angela_core", {}).get("chat_flow", {}) if _angela_cfg else {}
    _max_len = _chat_cfg.get("max_message_length", 4000)
    _trunc_len = _chat_cfg.get("truncation_length", 1000)
    _http_timeout = _chat_cfg.get("http_timeout", 30.0)
    if len(user_message) > _max_len:
        logger.warning(f"\U0001f6df [LIS] Intercepted oversized input ({len(user_message)} chars)")
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
                    return _build_math_response(verification, matrix, user_message, session_id)
                is_math = False
        except Exception as math_err:
            logger.warning(f"\u26a0 [DualRail] Math verification failed: {math_err}")
            is_math = False

        _chat_svc = await _get_chat_service()
        response_text = await asyncio.wait_for(
            _chat_svc.generate_response(user_message, user_name),
            timeout=_http_timeout,
        )
        _flow_source = _chat_cfg.get("default_flow", "angela_chat_service")
        _trunc_msg = _chat_cfg.get("truncation_message", "...\uff08\u622a\u65b7\uff09")
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
            "response_text": "\uff08\u6211\u7684\u5927\u8166\u4f3c\u4e4e\u9047\u5230\u4e86\u4e00\u9ede\u9ede\u5c0f\u5e72\u6270\uff0c\u80fd\u518d\u8aaa\u4e00\u6b21\u55ce\uff1f\uff09",
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


@router.get("/security/sync-key-c")
async def sync_key_c(request: Request):
    client_host = request.client.host
    if client_host not in ["127.0.0.1", "::1", "localhost"]:
        logger.warning(f"Unauthorized access attempt to sync-key-c from {client_host}")
        raise HTTPException(status_code=403, detail="Access restricted to localhost")
    abc_key_manager = get_abc_key_manager()
    key_c = abc_key_manager.get_key("KeyC")
    if not key_c:
        raise HTTPException(status_code=404, detail="Security keys not initialized")
    return {"key_available": True}


@router.post("/session/start")
async def start_session(request: Dict[str, Any] = Body(default={})):
    session_id = f"sess-{uuid.uuid4().hex[:8]}"
    sessions.set(session_id, {
        "created_at": datetime.now().isoformat(),
        "messages": [],
        "user_name": request.get("user_name", "User"),
    })
    return {"session_id": session_id, "message": "Welcome to Angela AI!"}


@router.post("/session/{session_id}/send")
async def send_message(session_id: str, request: Dict[str, Any] = Body(...)):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    user_message = request.get("text", request.get("message", ""))
    session = sessions.get(session_id)
    messages = session.get("messages", [])
    messages.append({"role": "user", "content": user_message, "timestamp": datetime.now().isoformat()})
    responses = [
        "\u6211\u660e\u767d\u4e86\uff01\u8ba9\u6211\u5e2e\u4f60\u60f3\u60f3...",
        "\u8fd9\u662f\u4e2a\u5f88\u6709\u8da3\u7684\u60f3\u6cd5\uff01",
        "\u6211\u53ef\u4ee5\u5e2e\u4f60\u5904\u7406\u8fd9\u4e2a\u3002",
        "\u8ba9\u6211\u5206\u6790\u4e00\u4e0b...",
        "\u6ca1\u95ee\u9898\uff0c\u6211\u8fd9\u5c31\u5e2e\u4f60\u505a\uff01",
    ]
    ai_response = random.choice(responses)
    messages.append({"role": "assistant", "content": ai_response, "timestamp": datetime.now().isoformat()})
    return {"session_id": session_id, "response_text": ai_response}


@router.post("/angela/chat")
async def angela_chat(request: Dict[str, Any] = Body(...)):
    user_message = request.get("message", request.get("text", ""))
    session_id = request.get("session_id", f"angela-{uuid.uuid4().hex[:8]}")
    user_name = request.get("user_name", "\u670b\u53cb")
    history = request.get("history", [])
    origin = request.get("origin", "Human")
    return await _handle_chat_request(user_message, user_name, history, session_id, origin=origin)


@router.post("/dialogue")
async def dialogue(request: Dict[str, Any] = Body(...)):
    user_message = request.get("message", request.get("text", ""))
    session_id = request.get("session_id", f"angela-{uuid.uuid4().hex[:8]}")
    user_name = request.get("user_name", "\u670b\u53cb")
    history = request.get("history", [])
    origin = request.get("origin", "Human")
    return await _handle_chat_request(user_message, user_name, history, session_id, origin=origin)


@router.post("/chat/unified")
async def unified_chat(request: Dict[str, Any] = Body(...)):
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
