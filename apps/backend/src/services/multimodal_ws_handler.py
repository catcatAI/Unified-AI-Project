"""
ANGELA-MATRIX: [L5] [αβγδεθ] [A] [L3]
Dedicated WebSocket handler for /multimodal/stream — persistent connection for real-time multimodal operations.
"""

import json
import logging
from typing import Any, Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect

from services.multimodal_service import MultimodalService

logger = logging.getLogger(__name__)

_SERVICE: Optional[MultimodalService] = None


def _get_service() -> MultimodalService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = MultimodalService()
    return _SERVICE


async def multimodal_stream_handler(websocket: WebSocket) -> None:
    await websocket.accept()
    svc = _get_service()

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
                continue

            action = data.get("action", data.get("type", ""))
            payload = data.get("data", data.get("payload", {}))

            try:
                result = await _dispatch(svc, action, payload)
                await websocket.send_json({"action": action, "status": "ok", "result": result})
            except Exception as e:
                logger.warning(f"Multimodal WS action '{action}' failed: {e}")
                await websocket.send_json({"action": action, "status": "error", "error": str(e)})

    except WebSocketDisconnect:
        logger.info("Multimodal WS client disconnected")
    except Exception as e:
        logger.error(f"Multimodal WS error: {e}")


async def _dispatch(svc: MultimodalService, action: str, payload: Dict[str, Any]) -> Any:
    if action in ("encode", "multimodal_encode"):
        return await svc.encode(
            payload["content"].encode() if isinstance(payload.get("content"), str) else payload.get("content", b""),
            payload.get("modality", "vision"),
            payload.get("item_id"),
        )
    elif action in ("decode", "multimodal_decode"):
        return await svc.decode(
            payload["item_id"],
            payload.get("modality", "vision"),
            payload.get("output_format", "base64"),
        )
    elif action == "compare":
        return await svc.compare(payload["item_a"], payload["item_b"])
    elif action == "generate":
        return await svc.generate(payload["source_item_id"], payload.get("target_modality", "text"))
    elif action == "retrieve":
        return await svc.retrieve(
            payload.get("query_id", ""),
            payload.get("top_k", 5),
            payload.get("modality_filter"),
        )
    elif action == "train":
        return await svc.train(
            payload.get("mode", "full"),
            payload.get("epochs", 5),
            payload.get("lr", 0.01),
            payload.get("use_real", False),
        )
    elif action == "evaluate":
        return await svc.evaluate(
            payload.get("item_id"),
            payload.get("modality", "vision"),
            payload.get("n_samples", 5),
        )
    elif action == "health":
        return await svc.health()
    elif action == "memory_search":
        return await svc.memory_search(payload.get("query", ""), payload.get("top_k", 5))
    else:
        raise ValueError(f"Unknown multimodal action: {action}")
