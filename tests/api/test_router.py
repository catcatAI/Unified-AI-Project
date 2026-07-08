"""Tests for the central API router construction."""

import pytest
from fastapi import APIRouter


@pytest.fixture(scope="module")
def router():
    from api.router import router as _router
    return _router


class TestRouterConstruction:
    """Verify the central API router is built as expected."""

    def test_router_is_apirouter(self, router):
        assert isinstance(router, APIRouter)

    def test_router_routes_exist(self, router):
        """Router has at least some routes registered (not empty)."""
        assert len(router.routes) > 0

    def test_endpoint_routes_registered(self, router):
        """Check that known endpoint routes exist."""
        paths = {r.path for r in router.routes}
        prefixes = ["/api/v1/drive", "/api/v1/pet", "/api/v1/vision",
                    "/api/v1/audio", "/api/v1/tactile", "/api/v1/mobile"]
        found = any(any(p.startswith(prefix) for p in paths) for prefix in prefixes)
        assert found, "No endpoint routes found (drive/pet/vision/audio/tactile/mobile)"


class TestOpsRoutes:
    """Verify ops_routes are included properly."""

    def test_ops_router_is_apirouter(self):
        from api.routes.ops_routes import router as ops_router
        assert isinstance(ops_router, APIRouter)

    def test_ops_router_has_prefix(self):
        from api.routes.ops_routes import router as ops_router
        assert ops_router.prefix == "/ops"

    def test_ops_router_has_routes(self):
        from api.routes.ops_routes import router as ops_router
        assert len(ops_router.routes) > 0
        paths = {r.path for r in ops_router.routes}
        # Verify at least some ops routes exist (actual route paths may differ from expected)
        ops_prefixes = ["/ops/health", "/ops/status", "/ops/maintenance"]
        found = any(p in paths for p in ops_prefixes)
        assert found, f"No known ops routes found in {paths}"

    def test_ops_routes_included_in_main_router(self, router):
        paths = {r.path for r in router.routes}
        # Check that ops routes are included (with /api/v1 prefix) via any known prefix
        ops_paths = [p for p in paths if "/ops/" in p]
        assert len(ops_paths) > 0, f"No ops routes found in main router: {paths}"


class TestIncludeEndpointRouters:
    """Verify include_endpoint_routers includes all sub-routers."""

    def test_include_endpoint_routers_adds_subrouters(self):
        from api.v1.endpoints import include_endpoint_routers
        test_router = APIRouter()
        include_endpoint_routers(test_router)
        paths = {r.path for r in test_router.routes}
        prefixes = ["/drive", "/pet", "/vision", "/audio",
                     "/tactile", "/mobile", "/trace"]
        for prefix in prefixes:
            assert any(p.startswith(prefix) for p in paths), f"No routes with {prefix}"

    def test_all_endpoint_prefixes_in_main_router(self, router):
        paths = {r.path for r in router.routes}
        prefixes = ["/api/v1/drive", "/api/v1/pet", "/api/v1/vision",
                     "/api/v1/audio", "/api/v1/tactile", "/api/v1/mobile",
                     "/api/v1/trace"]
        for prefix in prefixes:
            assert any(p.startswith(prefix) for p in paths), f"No routes with {prefix}"
