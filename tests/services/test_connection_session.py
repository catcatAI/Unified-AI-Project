"""
Tests for Connection Session Management

Author: Angela AI v6.2.1
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from services.connection_session import (
    SessionManager,
    ConnectionSession,
    SessionState,
    get_session_manager,
)


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self, client_id=None):
        self.client_id = client_id or "mock-client"
        self._closed = False
        self.sent_messages = []
    
    async def send_json(self, message):
        self.sent_messages.append(message)
    
    async def close(self, code=1000, reason="Normal close"):
        self._closed = True
    
    @property
    def closed(self):
        return self._closed


class TestConnectionSession:
    """Tests for ConnectionSession dataclass"""
    
    def test_session_creation(self):
        ws = MockWebSocket()
        session = ConnectionSession(
            client_id="test-client-1",
            session_id="test-session-1",
            websocket=ws
        )
        
        assert session.client_id == "test-client-1"
        assert session.session_id == "test-session-1"
        assert session.websocket == ws
        assert session.state == SessionState.CONNECTING
        assert session.sequence == 0
        assert session.is_active is False
    
    def test_session_is_active(self):
        ws = MockWebSocket()
        session = ConnectionSession(
            client_id="test-client-1",
            session_id="test-session-1",
            websocket=ws,
            state=SessionState.OPEN
        )
        
        assert session.is_active is True
        
        session.state = SessionState.CLOSED
        assert session.is_active is False
    
    def test_session_hash(self):
        ws = MockWebSocket()
        session = ConnectionSession(
            client_id="test-client-1",
            session_id="test-session-1",
            websocket=ws
        )
        
        # Sessions should be hashable by client_id
        assert hash(session) == hash("test-client-1")


class TestSessionManager:
    """Tests for SessionManager"""
    
    @pytest.fixture
    async def sm(self):
        """Create a fresh SessionManager for each test"""
        manager = SessionManager(heartbeat_interval=5, heartbeat_timeout=10)
        yield manager
        # Cleanup
        for task in manager._heartbeat_tasks.values():
            if not task.done():
                task.cancel()
    async def test_register_new_session(self, sm):
        """Test registering a new session"""
        ws = MockWebSocket()
        
        session = await sm.register(ws, session_id="test-session-1")
        
        assert session.session_id == "test-session-1"
        assert isinstance(session.client_id, str)
        assert session.state == SessionState.OPEN
        
        # Check storage
        assert session.client_id in sm._sessions
        assert "test-session-1" in sm._sessions_by_id
        assert session in sm._sessions_by_id["test-session-1"]
    async def test_register_auto_generate_session_id(self, sm):
        """Test that session_id is auto-generated if not provided"""
        ws = MockWebSocket()
        
        session = await sm.register(ws)
        
        assert len(session.session_id) > 0
    async def test_register_replaces_existing_session(self, sm):
        """Test that registering with same session_id replaces old session in single-device mode"""
        ws1 = MockWebSocket("client-1")
        ws2 = MockWebSocket("client-2")
        
        # Register first session
        session1 = await sm.register(ws1, session_id="shared-session", single_device_mode=True)
        client_id_1 = session1.client_id
        
        # Register second session with same session_id (single-device mode)
        session2 = await sm.register(ws2, session_id="shared-session", single_device_mode=True)
        client_id_2 = session2.client_id
        
        # Old session should be replaced
        assert client_id_1 != client_id_2
        assert ws1._closed  # Old WebSocket should be closed
        assert client_id_1 not in sm._sessions
        assert client_id_2 in sm._sessions
    async def test_unregister_session(self, sm):
        """Test unregistering a session"""
        ws = MockWebSocket()
        session = await sm.register(ws, session_id="test-session")
        client_id = session.client_id
        
        await sm.unregister(client_id)
        
        assert client_id not in sm._sessions
        assert "test-session" not in sm._sessions_by_id
    async def test_send_to_session(self, sm):
        """Test sending message to a specific session"""
        ws = MockWebSocket()
        session = await sm.register(ws, session_id="test-session")
        
        sent = await sm.send_to_session("test-session", {"type": "test", "data": "hello"})
        
        assert sent == 1
        assert len(ws.sent_messages) == 1
        assert ws.sent_messages[0]["type"] == "test"
    async def test_send_to_nonexistent_session(self, sm):
        """Test sending to a session that doesn't exist"""
        sent = await sm.send_to_session("nonexistent", {"type": "test"})
        assert sent == 0
    async def test_broadcast(self, sm):
        """Test broadcasting to all sessions"""
        ws1 = MockWebSocket("client-1")
        ws2 = MockWebSocket("client-2")
        ws3 = MockWebSocket("client-3")
        
        await sm.register(ws1, session_id="session-1")
        await sm.register(ws2, session_id="session-2")
        await sm.register(ws3, session_id="session-3")
        
        sent = await sm.broadcast({"type": "broadcast", "data": "hello all"})
        
        assert sent == 3
        assert len(ws1.sent_messages) == 1
        assert len(ws2.sent_messages) == 1
        assert len(ws3.sent_messages) == 1
    async def test_broadcast_excludes(self, sm):
        """Test broadcasting with exclusions"""
        ws1 = MockWebSocket("client-1")
        ws2 = MockWebSocket("client-2")
        
        await sm.register(ws1, session_id="include-me")
        await sm.register(ws2, session_id="exclude-me")
        
        sent = await sm.broadcast(
            {"type": "test"},
            exclude_session_ids=["exclude-me"]
        )
        
        assert sent == 1
        assert len(ws1.sent_messages) == 1
        assert len(ws2.sent_messages) == 0
    async def test_get_session(self, sm):
        """Test getting session by client_id"""
        ws = MockWebSocket()
        session = await sm.register(ws, session_id="test-session")
        
        retrieved = sm.get(session.client_id)
        
        assert retrieved.client_id == session.client_id
    async def test_get_by_session_id(self, sm):
        """Test getting sessions by session_id"""
        ws1 = MockWebSocket("client-1")
        ws2 = MockWebSocket("client-2")
        
        await sm.register(ws1, session_id="shared")
        await sm.register(ws2, session_id="shared")
        
        sessions = sm.get_by_session_id("shared")
        
        assert len(sessions) == 2
    async def test_get_all_connections_info(self, sm):
        """Test getting info about all connections"""
        ws1 = MockWebSocket("client-1")
        ws2 = MockWebSocket("client-2")
        
        await sm.register(ws1, session_id="session-1", metadata={"client_type": "desktop"})
        await sm.register(ws2, session_id="session-2", metadata={"client_type": "mobile"})
        
        info = sm.get_all_connections_info()
        
        assert len(info) == 2
        assert any(c["session_id"] == "session-1" for c in info)
        assert any(c["session_id"] == "session-2" for c in info)
        assert any(c["metadata"]["client_type"] == "desktop" for c in info)
    async def test_stats(self, sm):
        """Test session statistics"""
        ws1 = MockWebSocket("client-1")
        ws2 = MockWebSocket("client-2")
        
        await sm.register(ws1, session_id="session-1")
        await sm.register(ws2, session_id="session-2")
        
        stats = sm.get_stats()
        
        assert stats.total_sessions == 2
        assert stats.active_sessions == 2
    async def test_message_buffering(self, sm):
        """Test message buffering for disconnected clients"""
        ws = MockWebSocket()
        session = await sm.register(ws, session_id="test-session")
        
        # Simulate sending to disconnected client
        await sm.send_to_session("nonexistent-session", {"type": "buffered"}, buffer=True)
        
        # No crash, sent returns 0
        sent = await sm.send_to_session("nonexistent-session", {"type": "test"})
        assert sent == 0
    async def test_update_heartbeat(self, sm):
        """Test heartbeat update"""
        ws = MockWebSocket()
        session = await sm.register(ws, session_id="test-session")
        original_heartbeat = session.last_heartbeat
        
        await asyncio.sleep(0.01)  # Small delay
        await sm.update_heartbeat(session.client_id)
        
        assert session.last_heartbeat > original_heartbeat
    async def test_increment_sequence(self, sm):
        """Test sequence incrementing"""
        ws = MockWebSocket()
        session = await sm.register(ws, session_id="test-session")
        
        seq1 = sm.increment_sequence(session.client_id)
        seq2 = sm.increment_sequence(session.client_id)
        
        assert seq1 == 1
        assert seq2 == 2
        assert session.sequence == 2
    async def test_multi_device_same_session(self, sm):
        """Test multiple devices connecting with same session_id (multi-device mode, no replacement)"""
        ws1 = MockWebSocket("client-1")
        ws2 = MockWebSocket("client-2")
        ws3 = MockWebSocket("client-3")
        
        # Three clients sharing same session (multi-device mode, single_device_mode=False)
        await sm.register(ws1, session_id="family-session", single_device_mode=False)
        await sm.register(ws2, session_id="family-session", single_device_mode=False)
        await sm.register(ws3, session_id="family-session", single_device_mode=False)
        
        # Should have all three sessions
        sessions = sm.get_by_session_id("family-session")
        assert len(sessions) == 3
        
        # Broadcast should reach all three
        sent = await sm.send_to_session("family-session", {"type": "family-alert"})
        assert sent == 3
    async def test_clear_buffer(self, sm):
        """Test clearing message buffer"""
        ws = MockWebSocket()
        session = await sm.register(ws, session_id="test-session")
        
        # Add messages to buffer
        sm._message_buffers[session.client_id] = [{"type": "msg1"}, {"type": "msg2"}]
        
        sm.clear_buffer(session.client_id)
        
        assert len(sm._message_buffers[session.client_id]) == 0


class TestSessionManagerSingleton:
    """Tests for singleton behavior"""
    
    def test_get_session_manager(self):
        """Test getting singleton instance"""
        import services.connection_session as cs
        
        # Reset singleton
        cs._session_manager = None
        
        sm1 = get_session_manager()
        sm2 = get_session_manager()
        
        assert sm1 is sm2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])