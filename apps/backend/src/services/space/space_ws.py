# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
# =============================================================================
"""Space WebSocket: one room, many viewers, one authoritative snapshot.

Protocol (JSON):
  server -> client  {"type": "space.snapshot", "rev": n, "data": {...}}
  client -> server  {"type": "space.action", "data": {"type": "say", ...}}
  client -> server  {"type": "space.ping"}
  server -> client  {"type": "space.pong"}
  server -> client  {"type": "space.error", "message": "..."}

The handler is intentionally tolerant: a malformed frame gets an error reply, it
does not drop the connection — a stage viewer that loses its view because of one
bad message is worse than one that sees an error and keeps standing there.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Set

from fastapi import WebSocket, WebSocketDisconnect
from services.space.space_service import DEFAULT_ROOM_ID, get_space_service

logger = logging.getLogger(__name__)

# room_id -> connected viewers. Module-level so every handler shares the set.
_ROOM_PEERS: Dict[str, Set[WebSocket]] = {}


async def _broadcast(room_id: str, payload: Dict[str, Any]) -> None:
    peers = _ROOM_PEERS.get(room_id) or set()
    dead = []
    for peer in list(peers):
        try:
            await peer.send_json(payload)
        except Exception as exc:  # noqa: BLE001 - one dead socket must not stop the rest
            logger.debug("space broadcast failed for a peer: %s", exc)
            dead.append(peer)
    for peer in dead:
        peers.discard(peer)


async def _handle_frame(websocket: WebSocket, room_id: str, service: Any, raw: str) -> None:
    """One client frame: ping, action, or a polite error. Never raises."""
    try:
        message = json.loads(raw)
    except (TypeError, ValueError):
        await websocket.send_json({"type": "space.error", "message": "malformed JSON"})
        return
    if not isinstance(message, dict):
        await websocket.send_json({"type": "space.error", "message": "expected an object"})
        return

    kind = message.get("type")
    if kind == "space.ping":
        await websocket.send_json({"type": "space.pong"})
        return
    if kind != "space.action":
        await websocket.send_json(
            {"type": "space.error", "message": f"unknown message type: {kind}"}
        )
        return

    try:
        snapshot = service.apply(message.get("data") or {})
    except (TypeError, ValueError, KeyError, IndexError) as exc:
        await websocket.send_json({"type": "space.error", "message": str(exc)})
        return
    await _broadcast(room_id, snapshot)


async def space_ws_handler(websocket: WebSocket) -> None:
    await websocket.accept()
    room_id = str(websocket.query_params.get("room_id") or DEFAULT_ROOM_ID)
    peers = _ROOM_PEERS.setdefault(room_id, set())
    peers.add(websocket)

    service = get_space_service()
    try:
        await websocket.send_json(service.snapshot(room_id))
        while True:
            await _handle_frame(websocket, room_id, service, await websocket.receive_text())
    except WebSocketDisconnect:
        logger.debug("space viewer disconnected", exc_info=True)
    except Exception as exc:  # noqa: BLE001 - never let a viewer crash the loop task
        logger.warning("space websocket closed with error: %s", exc, exc_info=True)
    finally:
        peers.discard(websocket)
        if not peers:
            _ROOM_PEERS.pop(room_id, None)
