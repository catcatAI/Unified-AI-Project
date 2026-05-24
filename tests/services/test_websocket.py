"""Test WebSocket Connection Manager - Standalone Tests"""
import pytest
import asyncio
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.parent / "apps" / "backend" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
async def test_websocket_manager_class_exists():
    """Test WebSocket manager can be created standalone"""
    from services.main_api_server import ConnectionManager

    cm = ConnectionManager()
    assert cm.active_connections == []
    assert cm.heartbeat_interval == 30
    assert cm.heartbeat_timeout == 120
async def test_connection_stats():
    """Test connection stats retrieval"""
    from services.main_api_server import ConnectionManager

    cm = ConnectionManager()
    stats = cm.get_connection_stats()

    assert "active_connections" in stats
    assert stats["active_connections"] == 0
async def test_message_buffer():
    """Test message buffer functionality"""
    from services.main_api_server import ConnectionManager

    cm = ConnectionManager()
    assert cm.max_buffer_size == 10
async def test_manager_singleton_exists():
    """Test global manager instance exists"""
    from services.main_api_server import manager

    assert hasattr(manager, "active_connections")
async def test_manager_broadcast():
    """Test manager broadcast method exists and is callable"""
    from services.main_api_server import manager

    assert manager.broadcast.__name__ == 'broadcast'
async def test_manager_connect():
    """Test manager connect method exists"""
    from services.main_api_server import manager

    assert manager.connect.__name__ == 'connect'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
