"""Test Main API Server - Standalone Tests"""
import pytest


async def test_main_api_server_import():
    """Test main API server module can be imported"""
    from services.main_api_server import app
    assert app.title == "Angela AI API"


async def test_app_title():
    """Test FastAPI app has correct title"""
    from services.main_api_server import app

    assert app.title == "Angela AI API"
    assert app.version == "7.5.0-dev"


async def test_app_has_websocket_route():
    """Test app has WebSocket route configured"""
    from services.main_api_server import app

    # FastAPI >= 0.139 includes _IncludedRouter wrappers (no ``.path``) in
    # app.routes alongside the WebSocketRoute; filter to routes that carry a path.
    route_paths = [r.path for r in app.routes if hasattr(r, "path")]
    assert any("/ws" in path for path in route_paths)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
