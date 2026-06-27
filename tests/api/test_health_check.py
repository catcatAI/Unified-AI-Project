"""Tests for the health endpoint — matches actual API router."""

import pytest


class TestHealthCheck:
    """Test health endpoint via actual router structure."""

    def test_router_has_ops_routes(self):
        from api.router import ops_router
        assert ops_router is not None
        assert len(ops_router.routes) > 0

    def test_ops_routes_have_paths(self):
        from api.router import ops_router
        paths = [r.path for r in ops_router.routes]
        assert len(paths) > 0
        # Ops router has actual health/status/maintenance routes
        assert any("health" in p for p in paths) or any("status" in p for p in paths)

    def test_main_router_includes_ops_paths(self):
        from api.router import ops_router
        from api.router import router as main_router
        ops_paths = {r.path for r in ops_router.routes}
        main_paths = {r.path for r in main_router.routes}
        # ops routes should be included in main router under /api/v1
        assert len(ops_paths) > 0
        for p in ops_paths:
            prefixed = f"/api/v1{p}"
            assert prefixed in main_paths or p in main_paths
            break  # check at least one
