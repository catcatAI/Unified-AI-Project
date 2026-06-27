"""Tests for ops_routes API endpoints.

Covers:
- Route import and registration (4 endpoints)
- Helper functions (cpu, memory, disk metrics)
- Endpoint response structure and status logic
- Health check degraded condition
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps/backend/src"))


@pytest.mark.asyncio
class TestOpsRoutesImport:
    """Verify module imports and route registration."""

    async def test_module_importable(self):
        """Module imports without error."""
        from api.routes import ops_routes
        assert ops_routes is not None

    async def test_router_exported(self):
        """Module exports a router with routes."""
        from api.routes.ops_routes import router
        assert router is not None
        assert len(router.routes) >= 4

    async def test_router_has_expected_paths(self):
        """Router has all expected endpoint paths."""
        from api.routes.ops_routes import router
        paths = {r.path for r in router.routes}
        expected = {"/ops/status", "/ops/health", "/ops/maintenance", "/ops/metrics"}
        for ep in expected:
            assert ep in paths, f"Missing endpoint: {ep}"

    async def test_router_http_methods(self):
        """Verify HTTP methods on each route."""
        from api.routes.ops_routes import router
        route_map = {}
        for r in router.routes:
            methods = set(r.methods) if hasattr(r, "methods") else {"GET"}
            route_map[r.path] = methods

        assert "GET" in route_map.get("/ops/status", set())
        assert "GET" in route_map.get("/ops/health", set())
        assert "POST" in route_map.get("/ops/maintenance", set())
        assert "GET" in route_map.get("/ops/metrics", set())

    async def test_router_prefix(self):
        """Router has /ops prefix."""
        from api.routes.ops_routes import router
        assert router.prefix == "/ops"
        assert router.tags == ["Operations"]


@pytest.mark.asyncio
class TestOpsHelpers:
    """Verify helper functions (with mocked psutil)."""

    async def test_get_cpu_percent_with_psutil(self):
        """_get_cpu_percent returns value from psutil when available."""
        from api.routes.ops_routes import _get_cpu_percent
        mock_psutil = MagicMock()
        mock_psutil.cpu_percent.return_value = 42.5
        with patch.dict("sys.modules", {"psutil": mock_psutil}):
            # Re-import to use mocked module
            import importlib

            from api.routes import ops_routes
            importlib.reload(ops_routes)
            result = ops_routes._get_cpu_percent()
            assert result == 42.5

    async def test_get_cpu_percent_without_psutil(self):
        """_get_cpu_percent returns 0.0 when psutil not available."""
        from api.routes.ops_routes import _get_cpu_percent
        with patch.dict("sys.modules", {"psutil": None}):
            import importlib

            from api.routes import ops_routes
            importlib.reload(ops_routes)
            result = ops_routes._get_cpu_percent()
            assert result == 0.0

    async def test_get_memory_percent_with_psutil(self):
        """_get_memory_percent returns value from psutil when available."""
        from api.routes.ops_routes import _get_memory_percent
        mock_psutil = MagicMock()
        mock_vmem = MagicMock()
        mock_vmem.percent = 65.3
        mock_psutil.virtual_memory.return_value = mock_vmem
        with patch.dict("sys.modules", {"psutil": mock_psutil}):
            import importlib

            from api.routes import ops_routes
            importlib.reload(ops_routes)
            result = ops_routes._get_memory_percent()
            assert result == 65.3

    async def test_get_memory_percent_without_psutil(self):
        """_get_memory_percent returns 0.0 when psutil not available."""
        from api.routes.ops_routes import _get_memory_percent
        with patch.dict("sys.modules", {"psutil": None}):
            import importlib

            from api.routes import ops_routes
            importlib.reload(ops_routes)
            result = ops_routes._get_memory_percent()
            assert result == 0.0

    async def test_get_disk_percent_with_psutil(self):
        """_get_disk_percent returns value from psutil when available."""
        from api.routes.ops_routes import _get_disk_percent
        mock_psutil = MagicMock()
        mock_du = MagicMock()
        mock_du.percent = 78.1
        mock_psutil.disk_usage.return_value = mock_du
        with patch.dict("sys.modules", {"psutil": mock_psutil}):
            import importlib

            from api.routes import ops_routes
            importlib.reload(ops_routes)
            result = ops_routes._get_disk_percent()
            assert result == 78.1

    async def test_get_all_metrics_structure(self):
        """_get_all_metrics returns dict with expected keys."""
        # Even without psutil, it should return a dict with zeros
        import importlib

        from api.routes import ops_routes
        from api.routes.ops_routes import _get_all_metrics
        importlib.reload(ops_routes)
        result = _get_all_metrics()
        expected_keys = {"cpu_percent", "memory_percent", "disk_percent"}
        assert expected_keys.issubset(result.keys()), f"Missing keys: {expected_keys - result.keys()}"
        for key in expected_keys:
            assert isinstance(result[key], (int, float))


@pytest.mark.asyncio
class TestOpsStatus:
    """Test GET /ops/status endpoint."""

    async def test_status_returns_dict(self):
        """GET /ops/status returns a dict."""
        from api.routes.ops_routes import get_ops_status
        result = await get_ops_status()
        assert isinstance(result, dict)

    async def test_status_has_expected_keys(self):
        """GET /ops/status has expected keys."""
        from api.routes.ops_routes import get_ops_status
        result = await get_ops_status()
        expected = {"status", "service", "timestamp", "metrics"}
        assert expected.issubset(result.keys()), f"Missing keys: {expected - result.keys()}"
        assert result["status"] == "ok"
        assert result["service"] == "ops"
        assert "metrics" in result


@pytest.mark.asyncio
class TestOpsHealth:
    """Test GET /ops/health endpoint."""

    async def test_health_returns_dict(self):
        """GET /ops/health returns a dict."""
        from api.routes.ops_routes import health_check
        result = await health_check()
        assert isinstance(result, dict)

    async def test_health_has_expected_keys(self):
        """GET /ops/health has expected keys."""
        from api.routes.ops_routes import health_check
        result = await health_check()
        expected = {"status", "service", "timestamp", "cpu_percent", "memory_percent", "disk_percent"}
        assert expected.issubset(result.keys()), f"Missing keys: {expected - result.keys()}"
        assert result["service"] == "ops"

    async def test_health_healthy_when_low_load(self):
        """Health check returns 'healthy' when CPU <= 80 and mem <= 90."""
        from api.routes.ops_routes import health_check

        # Mock helpers to return low values
        with patch("api.routes.ops_routes._get_cpu_percent", return_value=30.0), \
             patch("api.routes.ops_routes._get_memory_percent", return_value=50.0), \
             patch("api.routes.ops_routes._get_disk_percent", return_value=40.0):
            result = await health_check()
            assert result["status"] == "healthy"

    async def test_health_degraded_when_high_cpu(self):
        """Health check returns 'degraded' when CPU > 80."""
        from api.routes.ops_routes import health_check
        with patch("api.routes.ops_routes._get_cpu_percent", return_value=85.0), \
             patch("api.routes.ops_routes._get_memory_percent", return_value=50.0):
            result = await health_check()
            assert result["status"] == "degraded"

    async def test_health_degraded_when_high_memory(self):
        """Health check returns 'degraded' when memory > 90."""
        from api.routes.ops_routes import health_check
        with patch("api.routes.ops_routes._get_cpu_percent", return_value=30.0), \
             patch("api.routes.ops_routes._get_memory_percent", return_value=95.0):
            result = await health_check()
            assert result["status"] == "degraded"


@pytest.mark.asyncio
class TestOpsMaintenance:
    """Test POST /ops/maintenance endpoint."""

    async def test_maintenance_returns_dict(self):
        """POST /ops/maintenance returns a dict."""
        from api.routes.ops_routes import trigger_maintenance
        result = await trigger_maintenance()
        assert isinstance(result, dict)

    async def test_maintenance_has_expected_keys(self):
        """POST /ops/maintenance has expected keys."""
        from api.routes.ops_routes import trigger_maintenance
        result = await trigger_maintenance()
        expected = {"status", "task", "timestamp"}
        assert expected.issubset(result.keys()), f"Missing keys: {expected - result.keys()}"
        assert result["status"] == "started"
        assert result["task"] == "maintenance"


@pytest.mark.asyncio
class TestOpsMetrics:
    """Test GET /ops/metrics endpoint."""

    async def test_metrics_returns_dict(self):
        """GET /ops/metrics returns a dict."""
        from api.routes.ops_routes import get_prometheus_metrics
        result = await get_prometheus_metrics()
        assert isinstance(result, dict)

    async def test_metrics_has_expected_keys(self):
        """GET /ops/metrics has expected keys."""
        from api.routes.ops_routes import get_prometheus_metrics
        result = await get_prometheus_metrics()
        expected = {"cpu_percent", "memory_percent", "disk_percent", "timestamp"}
        assert expected.issubset(result.keys()), f"Missing keys: {expected - result.keys()}"
        assert "timestamp" in result
