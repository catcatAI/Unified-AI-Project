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
from typing import Dict, Any

from fastapi import WebSocket, WebSocketDisconnect

from services.connection_session import get_session_manager, SessionState

logger = logging.getLogger(__name__)


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
                asyncio.create_task(self._sm.unregister(client_id, "Normal close"))
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
    while True:
        try:
            from api.lifespan import get_metabolic_heartbeat
            heartbeat = get_metabolic_heartbeat()
            bio_state = heartbeat.bio_integrator.get_biological_state()

            state_data = {
                "alpha": {
                    "energy": (100.0 - bio_state.get("fatigue", 0.0)) / 100.0,
                    "stress": bio_state.get("stress_level", 0.0),
                    "hormones": bio_state.get("hormones", {}),
                },
                "beta": {
                    "learning_rate": 0.01,
                    "cognitive_load": 0.0,
                },
                "gamma": {
                    "happiness": bio_state.get("mood", 0.5),
                    "emotion": bio_state.get("dominant_emotion", "calm"),
                },
                "delta": {
                    "intensity": bio_state.get("arousal", 50.0) / 100.0,
                },
                "spatial": {
                    "x": heartbeat.x,
                    "y": heartbeat.y,
                    "posture": heartbeat.posture,
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


async def websocket_handler(websocket: WebSocket) -> str:
    """
    WebSocket endpoint handler for real-time communication with desktop app.
    Handles handshake, message routing, heartbeat, and chat.
    """
    await websocket.accept()

    orig_receive = websocket._receive
    async def debug_receive() -> str:
        """Debug receive."""
        msg = await orig_receive()
        if msg.get('type') == 'websocket.receive':
            text = msg.get('text')
            bytes_d = msg.get('bytes')
            if text:
                sys.stderr.write(f"[DEBUG WS endpoint] text: {repr(text[:80])}\n")
            if bytes_d:
                sys.stderr.write(f"[DEBUG WS endpoint] bytes: {repr(bytes_d[:80])}\n")
        return msg
    websocket._receive = debug_receive

    try:
        raw_data = await asyncio.wait_for(websocket.receive_text(), timeout=10)
        try:
            handshake = json.loads(raw_data)
        except json.JSONDecodeError:
            await websocket.close(code=4002, reason="Invalid handshake format")
            return
    except asyncio.TimeoutError:
        try:
            await websocket.close(code=4001, reason="Handshake timeout")
        except Exception as e:
            logger.warning(f"Failed to close websocket on handshake timeout: {e}", exc_info=True)
        return

    except WebSocketDisconnect:
        return

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

    while True:
        try:
            data = await asyncio.wait_for(
                websocket.receive_json(), timeout=manager.heartbeat_timeout
            )

            await manager._sm.update_heartbeat(client_id)

            if data.get("type") in ["heartbeat", "ping"]:
                await websocket.send_json({
                    "type": "heartbeat_ack" if data.get("type") == "heartbeat" else "echo",
                    "timestamp": datetime.now().isoformat(),
                })

            elif data.get("type") == "state_update":
                await manager.broadcast({
                    "type": "state_update",
                    "data": data.get("data", {}),
                    "timestamp": datetime.now().isoformat(),
                })

            elif data.get("type") == "tactile_event":
                from api.lifespan import get_tactile_service
                tactile_data = data.get("data", {})
                tactile_service = get_tactile_service()
                res = await tactile_service.simulate_touch("user_hand", tactile_data, origin="Human")
                await manager.send_personal_message({
                    "type": "biological_feedback",
                    "status": res.get("status"),
                    "reflex": res.get("reflex"),
                    "intensity": res.get("feedback", {}).get("intensity")
                }, websocket)

            elif data.get("type") == "chat_message":
                from api.routes.chat_routes import _handle_chat_request
                user_message = data.get("data", {}).get("content", "")
                message_id = data.get("data", {}).get("message_id", "")
                user_name = data.get("data", {}).get("user_name", "朋友")

                try:
                    chat_res = await _handle_chat_request(
                        user_message=user_message,
                        user_name=user_name,
                        history=[],
                        session_id=session_id,
                        origin="Human"
                    )
                    await manager.send_personal_message({
                        "type": "chat_response",
                        "data": {
                            "message_id": message_id,
                            "content": chat_res["response_text"],
                            "sender": "angela",
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

    asyncio.create_task(manager.unregister(client_id))
