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

    def test_router_has_prefix(self, router):
        assert router.prefix == "/api/v1"

    def test_health_route_registered(self, router):
        paths = {r.path for r in router.routes}
        assert "/api/v1/health" in paths

    def test_status_route_registered(self, router):
        paths = {r.path for r in router.routes}
        assert "/api/v1/status" in paths

    def test_agents_route_registered(self, router):
        paths = {r.path for r in router.routes}
        assert "/api/v1/agents" in paths

    def test_models_route_registered(self, router):
        paths = {r.path for r in router.routes}
        assert "/api/v1/models" in paths

    def test_system_emergency_route_registered(self, router):
        paths = {r.path for r in router.routes}
        assert "/api/v1/system/emergency" in paths

    def test_core_routes_present(self, router):
        paths = {r.path for r in router.routes}
        expected = {
            "/api/v1/health", "/api/v1/status", "/api/v1/agents",
            "/api/v1/models", "/api/v1/system/emergency", "/api/v1/system/status",
            "/api/v1/system/metrics/detailed", "/api/v1/system/cluster/status",
            "/api/v1/chat/completions", "/api/v1/angela/reload", "/api/v1/",
        }
        missing = expected - paths
        assert not missing, f"Missing core routes: {missing}"


class TestOpsRoutes:
    """Verify ops_routes are included properly."""

    def test_ops_router_is_apirouter(self):
        from api.routes.ops_routes import router as ops_router
        assert isinstance(ops_router, APIRouter)

    def test_ops_router_has_prefix(self):
        from api.routes.ops_routes import router as ops_router
        assert ops_router.prefix == "/ops"

    def test_ops_router_has_expected_routes(self):
        from api.routes.ops_routes import router as ops_router
        paths = {r.path for r in ops_router.routes}
        expected = {
            "/ops/dashboard",
            "/ops/insights",
            "/ops/insights/{insight_id}/action",
            "/ops/metrics",
        }
        assert paths == expected

    def test_ops_routes_included_in_main_router(self, router):
        paths = {r.path for r in router.routes}
        for p in ("/api/v1/ops/dashboard", "/api/v1/ops/insights",
                  "/api/v1/ops/insights/{insight_id}/action", "/api/v1/ops/metrics"):
            assert p in paths, f"Missing ops route: {p}"


class TestIncludeEndpointRouters:
    """Verify include_endpoint_routers includes all sub-routers."""

    def test_include_endpoint_routers_adds_subrouters(self):
        from api.v1.endpoints import include_endpoint_routers
        test_router = APIRouter()
        include_endpoint_routers(test_router)
        paths = {r.path for r in test_router.routes}
        prefixes = ["/drive", "/pet", "/vision", "/audio",
                     "/tactile", "/mobile", "/economy", "/trace"]
        for prefix in prefixes:
            assert any(p.startswith(prefix) for p in paths), f"No routes with {prefix}"

    def test_all_endpoint_prefixes_in_main_router(self, router):
        paths = {r.path for r in router.routes}
        prefixes = ["/api/v1/drive", "/api/v1/pet", "/api/v1/vision",
                     "/api/v1/audio", "/api/v1/tactile", "/api/v1/mobile",
                     "/api/v1/economy", "/api/v1/trace"]
        for prefix in prefixes:
            assert any(p.startswith(prefix) for p in paths), f"No routes with {prefix}"
