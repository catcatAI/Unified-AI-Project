"""Tests for the health endpoint — matches actual API router."""

import pytest


def _collect_paths(router, prefix: str = ""):
    """Recursively collect absolute route paths (FastAPI-version robust).

    FastAPI >= 0.139 keeps included sub-routers as ``_IncludedRouter`` wrappers
    (``original_router`` + ``include_context.prefix``) instead of flattening
    them into ``APIRoute`` objects.
    """
    paths = set()
    for r in getattr(router, "routes", []):
        if hasattr(r, "original_router"):
            ctx = getattr(r, "include_context", None)
            sub_prefix = prefix + (getattr(ctx, "prefix", "") or "")
            paths |= _collect_paths(r.original_router, sub_prefix)
        elif hasattr(r, "path"):
            paths.add(prefix + r.path)
    return paths


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
        main_paths = _collect_paths(main_router)
        # ops routes should be included in main router under /api/v1
        assert len(ops_paths) > 0
        for p in ops_paths:
            prefixed = f"/api/v1{p}"
            assert prefixed in main_paths or p in main_paths
            break  # check at least one
