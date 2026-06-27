"""Tests for connection_session.py — SessionManager and session lifecycle.

Covers:
- SessionState enum values
- ConnectionSession dataclass properties
- SessionManager initialization and configuration
- Session registration (with/without session_id, metadata, single_device_mode)
- Session unregistration
- Message sending (to_session, to_client, broadcast)
- Message buffering for disconnected clients
- Heartbeat monitoring
- Stats tracking
- Singleton pattern (get_session_manager, shutdown_session_manager)
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps/backend/src"))


# =============================================================================
# Mock WebSocket helper
# =============================================================================

def _mock_ws():
    """Create a mock WebSocket that behaves like FastAPI's WebSocket."""
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


# =============================================================================
# SessionState enum tests
# =============================================================================

class TestSessionState:
    """Verify SessionState enum values."""

    def test_has_all_states(self):
        """SessionState has all expected lifecycle states."""
        from services.connection_session import SessionState
        assert SessionState.CLOSED.value == "closed"
        assert SessionState.CONNECTING.value == "connecting"
        assert SessionState.OPEN.value == "open"
        assert SessionState.CLOSING.value == "closing"
        assert SessionState.RECONNECTING.value == "reconnecting"

    def test_state_comparison(self):
        """SessionState values compare correctly."""
        from services.connection_session import SessionState
        assert SessionState.OPEN != SessionState.CLOSED
        assert SessionState.OPEN == SessionState.OPEN


# =============================================================================
# ConnectionSession dataclass tests
# =============================================================================

class TestConnectionSession:
    """Verify ConnectionSession dataclass."""

    def test_create_default_state(self):
        """ConnectionSession defaults to CONNECTING state."""
        from services.connection_session import ConnectionSession, SessionState
        ws = _mock_ws()
        session = ConnectionSession(
            client_id="test-client-1",
            session_id="test-session-1",
            websocket=ws,
        )
        assert session.client_id == "test-client-1"
        assert session.session_id == "test-session-1"
        assert session.websocket is ws
        assert session.state == SessionState.CONNECTING
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.last_heartbeat, datetime)
        assert session.sequence == 0
        assert session.metadata == {}

    def test_create_with_all_fields(self):
        """ConnectionSession accepts all fields."""
        from services.connection_session import ConnectionSession, SessionState
        ws = _mock_ws()
        now = datetime.now()
        session = ConnectionSession(
            client_id="c1",
            session_id="s1",
            websocket=ws,
            state=SessionState.OPEN,
            created_at=now,
            last_heartbeat=now,
            sequence=5,
            metadata={"client_type": "web", "version": "1.0"},
        )
        assert session.client_id == "c1"
        assert session.state == SessionState.OPEN
        assert session.sequence == 5
        assert session.metadata["client_type"] == "web"

    def test_is_active_open(self):
        """is_active returns True for OPEN state."""
        from services.connection_session import ConnectionSession, SessionState
        session = ConnectionSession(client_id="c1", session_id="s1", websocket=_mock_ws())
        session.state = SessionState.OPEN
        assert session.is_active is True

    def test_is_active_connecting(self):
        """is_active returns True for CONNECTING state."""
        from services.connection_session import ConnectionSession, SessionState
        session = ConnectionSession(client_id="c1", session_id="s1", websocket=_mock_ws())
        session.state = SessionState.CONNECTING
        assert session.is_active is True

    def test_is_active_closed(self):
        """is_active returns False for CLOSED state."""
        from services.connection_session import ConnectionSession, SessionState
        session = ConnectionSession(client_id="c1", session_id="s1", websocket=_mock_ws())
        session.state = SessionState.CLOSED
        assert session.is_active is False

    def test_hashable(self):
        """ConnectionSession is hashable by client_id."""
        from services.connection_session import ConnectionSession
        s1 = ConnectionSession(client_id="c1", session_id="s1", websocket=_mock_ws())
        s2 = ConnectionSession(client_id="c1", session_id="s1", websocket=_mock_ws())
        assert hash(s1) == hash(s2)


# =============================================================================
# SessionStats dataclass tests
# =============================================================================

class TestSessionStats:
    """Verify SessionStats dataclass."""

    def test_default_values(self):
        """SessionStats defaults to zeros."""
        from services.connection_session import SessionStats
        stats = SessionStats()
        assert stats.total_sessions == 0
        assert stats.active_sessions == 0
        assert stats.total_messages == 0
        assert stats.failed_messages == 0


# =============================================================================
# SessionManager initialization tests
# =============================================================================

class TestSessionManagerInit:
    """Verify SessionManager initialization."""

    def test_default_config(self):
        """SessionManager uses sane defaults."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        assert sm.heartbeat_interval == 30
        assert sm.heartbeat_timeout == 120
        assert sm.max_buffer_size == 10
        assert sm._lock is not None

    def test_custom_config(self):
        """SessionManager accepts custom configuration."""
        from services.connection_session import SessionManager
        sm = SessionManager(heartbeat_interval=10, heartbeat_timeout=60, max_buffer_size=5)
        assert sm.heartbeat_interval == 10
        assert sm.heartbeat_timeout == 60
        assert sm.max_buffer_size == 5

    def test_initial_state_empty(self):
        """SessionManager starts with no sessions."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        assert len(sm._sessions) == 0
        assert len(sm._sessions_by_id) == 0
        assert len(sm._message_buffers) == 0
        assert len(sm._heartbeat_tasks) == 0

    def test_initial_stats_zero(self):
        """SessionManager initial stats are zero."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        stats = sm.get_stats()
        assert stats.total_sessions == 0
        assert stats.active_sessions == 0


# =============================================================================
# SessionManager register tests
# =============================================================================

@pytest.mark.asyncio
class TestSessionManagerRegister:
    """Verify session registration."""

    async def test_register_generates_client_id(self):
        """register generates a unique client_id and returns session."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws = _mock_ws()
        session = await sm.register(ws)
        assert session is not None
        assert len(session.client_id) > 0
        assert session.state.value == "open"

    async def test_register_with_session_id(self):
        """register accepts a provided session_id."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws = _mock_ws()
        session = await sm.register(ws, session_id="my-session")
        assert session.session_id == "my-session"

    async def test_register_with_metadata(self):
        """register stores metadata on the session."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws = _mock_ws()
        meta = {"client_type": "mobile", "version": "2.0"}
        session = await sm.register(ws, metadata=meta)
        assert session.metadata == meta

    async def test_register_updates_stats(self):
        """register increments total_sessions and active_sessions."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws = _mock_ws()
        await sm.register(ws)
        stats = sm.get_stats()
        assert stats.total_sessions == 1
        assert stats.active_sessions == 1

    async def test_register_multiple_sessions_same_id(self):
        """Multiple connections can share the same session_id (multi-device)."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws1 = _mock_ws()
        ws2 = _mock_ws()
        s1 = await sm.register(ws1, session_id="shared-session")
        s2 = await sm.register(ws2, session_id="shared-session")
        assert s1.client_id != s2.client_id
        sessions = sm.get_by_session_id("shared-session")
        assert len(sessions) == 2

    async def test_register_single_device_replaces(self):
        """single_device_mode replaces old connections with same session_id."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws_old = _mock_ws()
        ws_new = _mock_ws()

        s_old = await sm.register(ws_old, session_id="single-device", single_device_mode=True)
        s_new = await sm.register(ws_new, session_id="single-device", single_device_mode=True)

        # Old websocket should have been closed
        ws_old.close.assert_awaited_once()
        # Old session should be gone
        assert sm.get(s_old.client_id) is None
        # New session should be registered
        assert sm.get(s_new.client_id) is not None

    async def test_register_starts_heartbeat_task(self):
        """register starts a heartbeat monitor task."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws = _mock_ws()
        session = await sm.register(ws)
        assert session.client_id in sm._heartbeat_tasks
        assert sm._heartbeat_tasks[session.client_id].done() is False

    async def test_register_in_message_buffers(self):
        """register initializes message buffer for client."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws = _mock_ws()
        session = await sm.register(ws)
        assert session.client_id in sm._message_buffers
        assert sm._message_buffers[session.client_id] == []


# =============================================================================
# SessionManager unregister tests
# =============================================================================

@pytest.mark.asyncio
class TestSessionManagerUnregister:
    """Verify session unregistration."""

    async def test_unregister_removes_session(self):
        """unregister removes session from storage."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws = _mock_ws()
        session = await sm.register(ws)
        await sm.unregister(session.client_id)
        assert sm.get(session.client_id) is None

    async def test_unregister_cancels_heartbeat(self):
        """unregister cancels heartbeat task."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws = _mock_ws()
        session = await sm.register(ws)
        task = sm._heartbeat_tasks[session.client_id]
        await sm.unregister(session.client_id)
        # Cancel is scheduled; yield to event loop so CancelledError propagates
        await asyncio.sleep(0)
        assert task.done() is True

    async def test_unregister_clears_buffer(self):
        """unregister clears the message buffer."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws = _mock_ws()
        session = await sm.register(ws)
        sm._buffer_message(session.client_id, {"test": "data"})
        assert len(sm.get_buffered_messages(session.client_id)) > 0
        await sm.unregister(session.client_id)
        assert sm.get_buffered_messages(session.client_id) == []

    async def test_unregister_unknown_client(self):
        """unregister with unknown client_id does not raise."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        # Should not raise
        await sm.unregister("nonexistent-client")

    async def test_unregister_updates_stats(self):
        """unregister decrements active_sessions."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws = _mock_ws()
        session = await sm.register(ws)
        await sm.unregister(session.client_id)
        stats = sm.get_stats()
        assert stats.active_sessions == 0


# =============================================================================
# SessionManager send tests
# =============================================================================

@pytest.mark.asyncio
class TestSessionManagerSend:
    """Verify message sending methods."""

    async def test_send_to_session_success(self):
        """send_to_session sends to all connections with session_id."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws = _mock_ws()
        session = await sm.register(ws, session_id="sid")
        msg = {"type": "test", "payload": "hello"}
        sent = await sm.send_to_session("sid", msg)
        assert sent == 1
        ws.send_json.assert_awaited_once_with(msg)

    async def test_send_to_session_multiple_clients(self):
        """send_to_session sends to all connections sharing session_id."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws1 = _mock_ws()
        ws2 = _mock_ws()
        await sm.register(ws1, session_id="sid")
        await sm.register(ws2, session_id="sid")
        sent = await sm.send_to_session("sid", {"msg": "test"})
        assert sent == 2

    async def test_send_to_session_unknown_id(self):
        """send_to_session with unknown session_id returns 0."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        sent = await sm.send_to_session("nonexistent", {"msg": "test"})
        assert sent == 0

    async def test_send_to_session_failure_buffers(self):
        """send_to_session buffers message on send failure."""
        from services.connection_session import SessionManager, SessionState
        sm = SessionManager()
        ws = _mock_ws()
        ws.send_json.side_effect = Exception("Connection lost")
        session = await sm.register(ws, session_id="sid")
        # Force state to OPEN so send_to_session attempts delivery
        session.state = SessionState.OPEN
        sent = await sm.send_to_session("sid", {"msg": "buffered"})
        assert sent == 0
        buffered = sm.get_buffered_messages(session.client_id)
        assert len(buffered) >= 1

    async def test_send_to_client_success(self):
        """send_to_client sends to a specific client."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws = _mock_ws()
        session = await sm.register(ws)
        result = await sm.send_to_client(session.client_id, {"msg": "private"})
        assert result is True
        ws.send_json.assert_awaited_once()

    async def test_send_to_client_unknown(self):
        """send_to_client with unknown client returns False."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        result = await sm.send_to_client("nonexistent", {"msg": "fail"})
        assert result is False

    async def test_send_to_client_failure(self):
        """send_to_client returns False on send failure."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws = _mock_ws()
        ws.send_json.side_effect = Exception("Failed")
        session = await sm.register(ws)
        result = await sm.send_to_client(session.client_id, {"msg": "fail"})
        assert result is False

    async def test_broadcast_to_all(self):
        """broadcast sends to all registered sessions."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws1 = _mock_ws()
        ws2 = _mock_ws()
        await sm.register(ws1)
        await sm.register(ws2)
        sent = await sm.broadcast({"msg": "broadcast"})
        assert sent == 2

    async def test_broadcast_exclude_session(self):
        """broadcast excludes specified session_ids."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws1 = _mock_ws()
        ws2 = _mock_ws()
        s1 = await sm.register(ws1, session_id="excluded")
        await sm.register(ws2, session_id="included")
        sent = await sm.broadcast({"msg": "test"}, exclude_session_ids=["excluded"])
        assert sent == 1

    async def test_stats_tracking(self):
        """send operations update stats correctly."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws = _mock_ws()
        session = await sm.register(ws)
        await sm.send_to_session(session.session_id, {"msg": "stats_test"})
        stats = sm.get_stats()
        assert stats.total_messages >= 1


# =============================================================================
# SessionManager message buffering tests
# =============================================================================

class TestSessionManagerBuffering:
    """Verify message buffering."""

    def test_buffer_message(self):
        """_buffer_message stores a message in the buffer."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        sm._buffer_message("client-1", {"msg": "hello"})
        buffered = sm.get_buffered_messages("client-1")
        assert len(buffered) == 1
        assert buffered[0]["msg"] == "hello"

    def test_buffer_limit(self):
        """Buffer is limited to max_buffer_size."""
        from services.connection_session import SessionManager
        sm = SessionManager(max_buffer_size=3)
        for i in range(5):
            sm._buffer_message("client-1", {"seq": i})
        buffered = sm.get_buffered_messages("client-1")
        assert len(buffered) == 3
        assert buffered[0]["seq"] == 2  # oldest retained

    def test_clear_buffer(self):
        """clear_buffer empties the buffer."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        sm._buffer_message("client-1", {"msg": "test"})
        sm.clear_buffer("client-1")
        assert sm.get_buffered_messages("client-1") == []

    def test_get_buffered_returns_copy(self):
        """get_buffered_messages returns a copy, not a reference."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        sm._buffer_message("client-1", {"msg": "test"})
        buffered = sm.get_buffered_messages("client-1")
        buffered.append({"msg": "extra"})
        # Original buffer should not be modified
        assert len(sm.get_buffered_messages("client-1")) == 1


# =============================================================================
# SessionManager query methods tests
# =============================================================================

class TestSessionManagerQueries:
    """Verify query and accessor methods."""

    def test_get_existing(self):
        """get returns session for existing client_id."""
        import asyncio

        from services.connection_session import SessionManager
        sm = SessionManager()
        ws = _mock_ws()
        session = asyncio.run(sm.register(ws))
        retrieved = sm.get(session.client_id)
        assert retrieved is not None
        assert retrieved.client_id == session.client_id

    def test_get_nonexistent(self):
        """get returns None for unknown client_id."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        assert sm.get("nonexistent") is None

    def test_get_by_session_id(self):
        """get_by_session_id returns list of sessions sharing session_id."""
        import asyncio

        from services.connection_session import SessionManager
        sm = SessionManager()
        ws1 = _mock_ws()
        ws2 = _mock_ws()
        asyncio.run(sm.register(ws1, session_id="shared"))
        asyncio.run(sm.register(ws2, session_id="shared"))
        sessions = sm.get_by_session_id("shared")
        assert len(sessions) == 2

    def test_get_by_session_id_unknown(self):
        """get_by_session_id returns empty list for unknown session_id."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        assert sm.get_by_session_id("unknown") == []

    def test_get_active_session_ids(self):
        """get_active_session_ids returns all registered session_ids."""
        import asyncio

        from services.connection_session import SessionManager
        sm = SessionManager()
        ws1 = _mock_ws()
        ws2 = _mock_ws()
        asyncio.run(sm.register(ws1, session_id="a"))
        asyncio.run(sm.register(ws2, session_id="b"))
        ids = sm.get_active_session_ids()
        assert "a" in ids
        assert "b" in ids

    def test_get_all_connections_info(self):
        """get_all_connections_info returns detailed info."""
        import asyncio

        from services.connection_session import SessionManager
        sm = SessionManager()
        ws = _mock_ws()
        session = asyncio.run(sm.register(ws, session_id="info-test",
                                          metadata={"client_type": "test"}))
        info_list = sm.get_all_connections_info()
        assert len(info_list) == 1
        entry = info_list[0]
        assert entry["client_id"] == session.client_id
        assert entry["session_id"] == "info-test"
        assert entry["state"] == "open"
        assert entry["metadata"]["client_type"] == "test"


# =============================================================================
# SessionManager heartbeat tests
# =============================================================================

@pytest.mark.asyncio
class TestSessionManagerHeartbeat:
    """Verify heartbeat operations."""

    async def test_update_heartbeat_updates_timestamp(self):
        """update_heartbeat refreshes last_heartbeat on the session."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws = _mock_ws()
        session = await sm.register(ws)
        # Set a past timestamp so the update is unambiguous
        import datetime
        session.last_heartbeat = datetime.datetime.now() - datetime.timedelta(seconds=10)
        old_ts = session.last_heartbeat

        await sm.update_heartbeat(session.client_id)

        assert session.last_heartbeat > old_ts

    async def test_update_heartbeat_unknown(self):
        """update_heartbeat for unknown client does not raise."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        # Should not raise
        await sm.update_heartbeat("nonexistent")

    async def test_heartbeat_timeout_closes_session(self):
        """heartbeat monitor closes session on timeout."""
        from services.connection_session import SessionManager
        sm = SessionManager(heartbeat_interval=0.05, heartbeat_timeout=0.3)
        ws = _mock_ws()
        session = await sm.register(ws)

        # Set last_heartbeat far in the past to trigger timeout
        session.last_heartbeat = datetime.now() - timedelta(seconds=1)

        # Wait for heartbeat monitor to detect timeout
        await asyncio.sleep(0.6)

        # Session should have been unregistered and websocket closed
        assert sm.get(session.client_id) is None
        ws.close.assert_awaited()

    async def test_increment_sequence(self):
        """increment_sequence increases sequence number."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        ws = _mock_ws()
        session = await sm.register(ws)
        seq = sm.increment_sequence(session.client_id)
        assert seq == 1
        seq = sm.increment_sequence(session.client_id)
        assert seq == 2

    async def test_increment_sequence_unknown(self):
        """increment_sequence for unknown client returns 0."""
        from services.connection_session import SessionManager
        sm = SessionManager()
        seq = sm.increment_sequence("nonexistent")
        assert seq == 0


# =============================================================================
# Singleton pattern tests
# =============================================================================

class TestSessionManagerSingleton:
    """Verify get_session_manager and shutdown_session_manager."""

    def test_get_session_manager_returns_singleton(self):
        """get_session_manager returns the same instance on repeated calls."""
        # Reset first
        import services.connection_session as cs
        from services.connection_session import _session_manager, get_session_manager
        cs._session_manager = None
        sm1 = get_session_manager()
        sm2 = get_session_manager()
        assert sm1 is sm2

    def test_get_session_manager_creates_new_instance(self):
        """get_session_manager creates a new SessionManager if none exists."""
        import services.connection_session as cs
        from services.connection_session import get_session_manager
        cs._session_manager = None
        sm = get_session_manager()
        from services.connection_session import SessionManager
        assert isinstance(sm, SessionManager)

    @pytest.mark.asyncio
    async def test_shutdown_clears_singleton(self):
        """shutdown_session_manager sets global to None."""
        import services.connection_session as cs
        from services.connection_session import get_session_manager, shutdown_session_manager
        cs._session_manager = None
        sm = get_session_manager()
        assert cs._session_manager is sm

        # Register a session so there are heartbeat tasks to cancel
        ws = _mock_ws()
        await sm.register(ws)

        await shutdown_session_manager()
        assert cs._session_manager is None

    @pytest.mark.asyncio
    async def test_shutdown_cancels_heartbeat_tasks(self):
        """shutdown_session_manager cancels all heartbeat tasks."""
        import services.connection_session as cs
        from services.connection_session import get_session_manager, shutdown_session_manager
        cs._session_manager = None
        sm = get_session_manager()

        ws1 = _mock_ws()
        ws2 = _mock_ws()
        await sm.register(ws1)
        await sm.register(ws2)
        assert len(sm._heartbeat_tasks) == 2

        await shutdown_session_manager()
        # All tasks should be done (cancelled)
        assert len(sm._heartbeat_tasks) == 0 or all(
            t.done() for t in sm._heartbeat_tasks.values()
        )

    @pytest.mark.asyncio
    async def test_shutdown_idempotent(self):
        """shutdown_session_manager can be called multiple times safely."""
        import services.connection_session as cs
        from services.connection_session import shutdown_session_manager
        cs._session_manager = None
        # First call does nothing (already None)
        await shutdown_session_manager()
        # Second call also does nothing
        await shutdown_session_manager()
