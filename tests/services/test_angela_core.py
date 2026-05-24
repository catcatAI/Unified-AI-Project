"""Test Main API Server - Standalone Tests"""
import pytest
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.parent / "apps" / "backend" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
async def test_main_api_server_import():
    """Test main API server module can be imported"""
    from services.main_api_server import app
    assert app.title == "Angela AI API"
async def test_app_title():
    """Test FastAPI app has correct title"""
    from services.main_api_server import app

    assert app.title == "Angela AI API"
    assert app.version == "6.0.4"
async def test_app_has_websocket_route():
    """Test app has WebSocket route configured"""
    from services.main_api_server import app

    route_paths = [r.path for r in app.routes]
    assert any("/ws" in path for path in route_paths)
async def test_system_metrics_manager():
    """Test SystemMetricsManager can be imported"""
    from services.main_api_server import SystemMetricsManager

    smm = SystemMetricsManager()
    assert smm.cache_ttl == 5.0
async def test_message_manager():
    """Test MessageManager can be imported"""
    from services.main_api_server import MessageManager

    mm = MessageManager()
    assert mm.message_counter == 0
    assert mm.max_cache_size == 1000
async def test_message_id_generation():
    """Test MessageManager generates unique IDs"""
    from services.main_api_server import MessageManager

    mm = MessageManager()
    id1 = mm.get_next_message_id()
    id2 = mm.get_next_message_id()

    assert id1 != id2
    assert "msg_" in id1
async def test_message_deduplication():
    """Test MessageManager message deduplication"""
    from services.main_api_server import MessageManager

    mm = MessageManager()
    msg_id = "test_msg_001"

    assert not mm.is_duplicate_message(msg_id)
    mm.cache_message(msg_id, {"content": "test"})
    assert mm.is_duplicate_message(msg_id)
async def test_state_merge():
    """Test MessageManager state merging"""
    from services.main_api_server import MessageManager

    mm = MessageManager()
    current = {"a": 1, "b": 2}
    new = {"b": 3, "c": 4}
    merged = mm.merge_state(current, new)

    assert merged["a"] == 1
    assert merged["b"] == 3
    assert merged["c"] == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
