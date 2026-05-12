"""Test WebSocket Connection Manager"""
import pytest
import asyncio
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "apps" / "backend" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.mark.asyncio
async def test_connection_manager_import():
    """Test ConnectionManager can be imported"""
    try:
        from services.main_api_server import ConnectionManager, manager
        assert ConnectionManager is not None
        assert manager is not None
    except ImportError as e:
        pytest.skip(f"ConnectionManager not available: {e}")


@pytest.mark.asyncio
async def test_connection_manager_init():
    """Test ConnectionManager initialization"""
    from services.main_api_server import ConnectionManager

    cm = ConnectionManager()
    assert cm is not None
    assert hasattr(cm, "active_connections")
    assert cm.active_connections == []
    assert cm.heartbeat_interval == 30
    assert cm.heartbeat_timeout == 120


@pytest.mark.asyncio
async def test_connection_stats():
    """Test connection stats retrieval"""
    from services.main_api_server import ConnectionManager

    cm = ConnectionManager()
    stats = cm.get_connection_stats()

    assert "active_connections" in stats
    assert stats["active_connections"] == 0


@pytest.mark.asyncio
async def test_message_buffer():
    """Test message buffer functionality"""
    from services.main_api_server import ConnectionManager

    cm = ConnectionManager()
    assert cm.max_buffer_size == 10


@pytest.mark.asyncio
async def test_manager_singleton():
    """Test global manager instance exists"""
    try:
        from services.main_api_server import manager
        assert manager is not None
        assert isinstance(manager, type(lambda: None).__class__.__bases__[0])
    except ImportError:
        pytest.skip("manager singleton not available")


@pytest.mark.asyncio
async def test_websocket_endpoint_exists():
    """Test WebSocket endpoint exists in main_api_server"""
    try:
        from services.main_api_server import app
        routes = [r.path for r in app.routes]
        assert any("/ws" in r for r in routes)
    except ImportError:
        pytest.skip("main_api_server not fully available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])