"""
ANGELA-MATRIX: [L5-L6] [γδ] [A] [L2]
WebSocket connection management and real-time state broadcast.
Extracted from main_api_server.py (A3 god module split).
"""

import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from fastapi import WebSocket, WebSocketDisconnect

from services.connection_session import get_session_manager

logger = logging.getLogger(__name__)

# Per-session conversation history (max 30 messages per session)
_session_history = {}  # session_id -> list of {"role": str, "content": str}
_MAX_HISTORY = 30
_session_history_lock = asyncio.Lock()


class ConnectionManager:
    """
    WebSocket connection manager - uses SessionManager internally.
    Provides backward-compatible API while delegating to SessionManager.
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

    async def connect(self, websocket: WebSocket, session_id: str = None, metadata: dict = None) -> str:
        """Establish connection."""
        await websocket.accept()
        session = await self._sm.register(websocket, session_id, metadata, single_device_mode=True)
        return session

    def disconnect(self, websocket: WebSocket) -> None:
        """Close connection."""
        for client_id, session in list(self._sm._sessions.items()):
            if session.websocket == websocket:
                task = asyncio.create_task(self._sm.unregister(client_id, "Normal close"))
                task.add_done_callback(lambda t: logger.debug(f"Unregister failed: {t.exception()}") if not t.cancelled() and t.exception() else None)
                break

    async def broadcast(self, message: dict) -> str:
        return await self._sm.broadcast(message)

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> bool:
        """Send personal message."""
        for client_id, session in self._sm._sessions.items():
            if session.websocket == websocket:
                return await self._sm.send_to_client(client_id, message)
        return False

    async def send_to_session(self, session_id: str, message: dict) -> str:
        return await self._sm.send_to_session(session_id, message)

    async def unregister(self, client_id: str) -> str:
        return await self._sm.unregister(client_id)

    def get_all_connections_info(self) -> str:
        return self._sm.get_all_connections_info()

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection stats."""
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


async def broadcast_state_updates() -> None:
    """Periodically broadcast state updates (bio + Live2D) to all connected clients."""
    _bio_integrator = None
    while True:
        try:
            if _bio_integrator is None:
                try:
                    from core.bio.biological_integrator import BiologicalIntegrator
                    _bio_integrator = BiologicalIntegrator()
                except Exception as e:
                    logger.debug("BiologicalIntegrator broadcast failed: %s", e)
                    await asyncio.sleep(5.0)
                    continue

            bio_state = _bio_integrator.get_biological_state()

            # HIGH-4: dynamic beta from neuroplasticity system
            _lr = 0.01
            _cl = 0.0
            try:
                np_sys = _bio_integrator.neuroplasticity_system
                if np_sys and hasattr(np_sys, "hebbian_rule"):
                    _lr = np_sys.hebbian_rule.learning_rate
                if np_sys and hasattr(np_sys, "memory_traces"):
                    _cl = min(1.0, len(np_sys.memory_traces) / 50.0)
            except Exception as e:
                logger.debug(f"Neuroplasticity state read failed: {e}")

            # HIGH-5: dynamic spatial posture from cerebellum
            _posture = {"theta_matrix": [0.0] * 9, "finger_matrix": {"left": [0.0] * 5, "right": [0.0] * 5}}
            try:
                _cb = _bio_integrator.cerebellum
                if _cb and hasattr(_cb, "get_posture"):
                    _p = _cb.get_posture()
                    _posture["theta_matrix"] = _p.get("theta_matrix", [0.0] * 9)
            except Exception as e:
                logger.debug(f"Cerebellum posture read failed: {e}")

            state_data = {
                "alpha": {
                    "energy": (100.0 - bio_state.get("stress_level", 0.0)) / 100.0,
                    "stress": bio_state.get("stress_level", 0.0),
                    "hormones": bio_state.get("hormonal_effects", {}),
                },
                "beta": {
                    "learning_rate": _lr,
                    "cognitive_load": _cl,
                },
                "gamma": {
                    "happiness": bio_state.get("mood", 0.5),
                    "emotion": bio_state.get("dominant_emotion", "calm"),
                },
                "delta": {
                    "intensity": bio_state.get("arousal", 50.0) / 100.0,
                },
                "spatial": {
                    "x": 200.0,
                    "y": 0.0,
                    "posture": _posture,
                },
                "timestamp": datetime.now().isoformat(),
            }

            # C2: include Live2D state (from service registry singleton) in broadcast
            try:
                from core.interfaces.service_registry import get_registry
                reg_live2d = get_registry().get("live2d_integration")
                if reg_live2d is not None and hasattr(reg_live2d, 'get_live2d_state'):
                    state_data["live2d"] = reg_live2d.get_live2d_state()
            except Exception as e:
                logger.warning(f"Failed to get live2d state for broadcast: {e}", exc_info=True)

            await manager.broadcast(
                {
                    "type": "state_update",
                    "data": state_data,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting state update: {e}", exc_info=True)

        await asyncio.sleep(0.2)


async def _handle_handshake(websocket: WebSocket) -> Optional[tuple]:
    try:
        raw_data = await asyncio.wait_for(websocket.receive_text(), timeout=10)
        try:
            handshake = json.loads(raw_data)
        except json.JSONDecodeError:
            await websocket.close(code=4002, reason="Invalid handshake format")
            return None
    except asyncio.TimeoutError:
        try:
            await websocket.close(code=4001, reason="Handshake timeout")
        except Exception as e:
            logger.warning(f"Failed to close websocket on handshake timeout: {e}", exc_info=True)
        return None
    except WebSocketDisconnect:
        logger.debug("WebSocket disconnected during handshake")
        return None

    session_id = handshake.get("session_id") or str(uuid.uuid4())
    client_type = handshake.get("client_type", "desktop")
    client_version = handshake.get("client_version", "unknown")

    session = await manager._sm.register(websocket, session_id, {
        "client_type": client_type,
        "client_version": client_version,
    }, single_device_mode=True)
    client_id = session.client_id

    logger.info(f"[WebSocket] Connected - client_id: {client_id}, session_id: {session_id}")

    await websocket.send_json({
        "type": "connected",
        "client_id": client_id,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "server_version": "7.5.0-dev",
    })
    return client_id, session_id


async def _handle_chat_message(websocket: WebSocket, data: dict, session_id: str) -> None:
    from api.routes.chat_routes import _handle_chat_request
    user_message = data.get("data", {}).get("content", "")
    message_id = data.get("data", {}).get("message_id", "")
    user_name = data.get("data", {}).get("user_name", "朋友")

    try:
        async with _session_history_lock:
            history = _session_history.get(session_id, [])[-_MAX_HISTORY:]
        chat_res = await _handle_chat_request(
            user_message=user_message,
            user_name=user_name,
            history=history,
            session_id=session_id,
            origin="Human"
        )
        # Store both user message and assistant response in history
        async with _session_history_lock:
            if session_id not in _session_history:
                _session_history[session_id] = []
            _session_history[session_id].append({"role": "user", "content": user_message})
            _session_history[session_id].append({"role": "assistant", "content": chat_res.get("response_text", "")})
            # Trim to max size
            if len(_session_history[session_id]) > _MAX_HISTORY * 2:
                _session_history[session_id] = _session_history[session_id][-_MAX_HISTORY * 2:]
        _resp_preview = chat_res.get("response_text", "")[:80]
        _hit = chat_res.get("hit_score", 0.0)
        _src = chat_res.get("hit_source", "none")
        logger.info(f"[WebSocket] Chat response sent ({_src}, score={_hit:.2f}): {_resp_preview}...")
        await manager.send_personal_message({
            "type": "chat_response",
            "data": {
                "message_id": message_id,
                "content": chat_res["response_text"],
                "sender": "angela",
                "hit_score": chat_res.get("hit_score", 0.0),
                "hit_source": chat_res.get("hit_source", "none"),
                "route": chat_res.get("route", "llm"),
                "emotion": chat_res.get("emotion", "happy"),
                "emotion_intensity": chat_res.get("emotion_intensity", 0.5),
            },
            "timestamp": datetime.now().isoformat(),
        }, websocket)
    except Exception as chat_err:
        logger.error(f"[WebSocket] Chat error: {chat_err}", exc_info=True)
        await manager.send_personal_message({
            "type": "chat_response",
            "data": {
                "message_id": message_id,
                "content": "（我的大腦似乎遇到了一點點小干擾，能再說一次嗎？）",
                "sender": "angela",
                "error": str(chat_err)
            },
            "timestamp": datetime.now().isoformat(),
        }, websocket)


async def _handle_tactile_event(websocket: WebSocket, data: dict) -> None:
    from api.lifespan import get_tactile_service
    tactile_data = data.get("data", {})
    tactile_service = get_tactile_service()
    if not tactile_service:
        logger.warning("TactileService unavailable for tactile_event")
        return
    res = await tactile_service.simulate_touch("user_hand", tactile_data, origin="Human")
    await manager.send_personal_message({
        "type": "biological_feedback",
        "status": res.get("status"),
        "reflex": res.get("reflex"),
        "intensity": res.get("feedback", {}).get("intensity")
    }, websocket)


async def _handle_heartbeat(websocket: WebSocket, data: dict) -> None:
    await websocket.send_json({
        "type": "heartbeat_ack" if data.get("type") == "heartbeat" else "echo",
        "timestamp": datetime.now().isoformat(),
    })


async def websocket_handler(websocket: WebSocket) -> str:
    """
    WebSocket endpoint handler for real-time communication with desktop app.
    Handles handshake, message routing, heartbeat, and chat.
    """
    await websocket.accept()

    result = await _handle_handshake(websocket)
    if result is None:
        return
    client_id, session_id = result

    while True:
        try:
            data = await asyncio.wait_for(
                websocket.receive_json(), timeout=manager.heartbeat_timeout
            )

            await manager._sm.update_heartbeat(client_id)

            msg_type = data.get("type")

            if msg_type in ("heartbeat", "ping"):
                await _handle_heartbeat(websocket, data)

            elif msg_type == "state_update":
                await manager.broadcast({
                    "type": "state_update",
                    "data": data.get("data", {}),
                    "timestamp": datetime.now().isoformat(),
                })

            elif msg_type == "tactile_event":
                await _handle_tactile_event(websocket, data)

            elif msg_type == "chat_message":
                await _handle_chat_message(websocket, data, session_id)

            else:
                await websocket.send_json({
                    "type": "echo",
                    "original": data,
                    "timestamp": datetime.now().isoformat(),
                })

        except asyncio.TimeoutError:
            logger.warning(f"[WebSocket] Heartbeat timeout: {client_id}", exc_info=True)
            break
        except WebSocketDisconnect:
            logger.info(f"[WebSocket] Disconnected: {client_id}")
            break
        except Exception as e:
            logger.error(f"[WebSocket] Error for {client_id}: {e}", exc_info=True)
            continue

    task = asyncio.create_task(manager.unregister(client_id))
    task.add_done_callback(lambda t: logger.debug(f"Final unregister failed: {t.exception()}") if not t.cancelled() and t.exception() else None)
    async with _session_history_lock:
        _session_history.pop(session_id, None)
