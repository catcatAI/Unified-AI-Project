"""Test WebSocket Connection Manager - Standalone Tests"""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from services import websocket_manager as wsm


@pytest.mark.asyncio
async def test_websocket_manager_class_exists():
    """Test WebSocket manager can be created standalone"""
    from services.websocket_manager import ConnectionManager

    cm = ConnectionManager()
    assert cm.active_connections == []
@pytest.mark.asyncio
async def test_connection_stats():
    """Test connection stats retrieval"""
    from services.websocket_manager import ConnectionManager

    cm = ConnectionManager()
    stats = cm.get_connection_stats()

    assert "active_connections" in stats
    assert stats["active_connections"] == 0
@pytest.mark.asyncio
async def test_message_buffer():
    """Test message buffer functionality"""
    from services.websocket_manager import ConnectionManager

    cm = ConnectionManager()
    assert hasattr(cm, 'active_connections')
    assert isinstance(cm.active_connections, list)
@pytest.mark.asyncio
async def test_manager_singleton_exists():
    """Test global manager instance exists"""
    from services.websocket_manager import manager

    assert hasattr(manager, "active_connections")
@pytest.mark.asyncio
async def test_manager_broadcast():
    """Test manager broadcast method exists and is callable"""
    from services.websocket_manager import manager

    assert callable(manager.broadcast)
@pytest.mark.asyncio
async def test_manager_connect():
    """Test manager connect method exists"""
    from services.websocket_manager import manager

    assert callable(manager.connect)


@pytest.mark.asyncio
async def test_chat_response_includes_session_id():
    """The chat_response payload must echo the session_id back to the client.

    The frontend BackendWebSocketClient._handleChatResponse reads
    data.session_id to correlate responses with sessions; omitting it is a
    content-delivery gap in the websocket contract.
    """
    wsm._session_history.clear()
    sent = []

    async def fake_send(payload, websocket):
        sent.append(payload)

    async def fake_wrapper(*args, **kwargs):
        return {
            "response_text": "Hello via websocket",
            "response": "Hello via websocket",
            "source": "test",
            "schema_version": "2.0",
            "session_id": kwargs["session_id"],
            "truncation_message": "",
            "emotion": "happy",
            "emotion_intensity": 0.8,
            "hit_score": 0.0,
            "hit_source": "none",
            "route": "llm",
        }

    original_send = wsm.manager.send_personal_message
    try:
        wsm.manager.send_personal_message = fake_send
        with patch(
            "api.routes.chat_routes._handle_chat_request",
            new_callable=AsyncMock,
            side_effect=fake_wrapper,
        ):
            from services.websocket_manager import _handle_chat_message

            await _handle_chat_message(
                None,
                {"data": {"message_id": "m1", "content": "hi"}, "type": "chat_message"},
                "sess-ws-1",
            )
    finally:
        wsm.manager.send_personal_message = original_send

    assert len(sent) == 1
    payload = sent[0]
    assert payload["type"] == "chat_response"
    assert payload["data"]["content"] == "Hello via websocket"
    assert payload["data"]["message_id"] == "m1"
    assert payload["data"]["session_id"] == "sess-ws-1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
