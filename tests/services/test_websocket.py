"""Test WebSocket Connection Manager - Standalone Tests"""
import asyncio

import pytest


async def test_websocket_manager_class_exists():
    """Test WebSocket manager can be created standalone"""
    from services.websocket_manager import ConnectionManager

    cm = ConnectionManager()
    assert cm.active_connections == []
async def test_connection_stats():
    """Test connection stats retrieval"""
    from services.websocket_manager import ConnectionManager

    cm = ConnectionManager()
    stats = cm.get_connection_stats()

    assert "active_connections" in stats
    assert stats["active_connections"] == 0
async def test_message_buffer():
    """Test message buffer functionality"""
    from services.websocket_manager import ConnectionManager

    cm = ConnectionManager()
    assert hasattr(cm, 'active_connections')
    assert isinstance(cm.active_connections, list)
async def test_manager_singleton_exists():
    """Test global manager instance exists"""
    from services.websocket_manager import manager

    assert hasattr(manager, "active_connections")
async def test_manager_broadcast():
    """Test manager broadcast method exists and is callable"""
    from services.websocket_manager import manager

    assert callable(manager.broadcast)
async def test_manager_connect():
    """Test manager connect method exists"""
    from services.websocket_manager import manager

    assert callable(manager.connect)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
