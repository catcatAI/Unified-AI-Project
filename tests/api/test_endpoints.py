"""Tests for individual API endpoint modules."""

import pytest
from fastapi import APIRouter

ENDPOINT_MODULES = [
    "drive",
    "pet",
    "vision",
    "audio",
    "tactile",
    "mobile",
    "economy",
    "trace",
]


class TestEndpointModuleImports:
    """Verify each endpoint module imports correctly and exports a router."""

    @pytest.mark.parametrize("module_name", ENDPOINT_MODULES)
    def test_module_importable(self, module_name):
        import importlib
        mod = importlib.import_module(f"api.v1.endpoints.{module_name}")
        assert mod.__name__ == f"api.v1.endpoints.{module_name}"

    @pytest.mark.parametrize("module_name", ENDPOINT_MODULES)
    def test_module_exports_router(self, module_name):
        import importlib
        mod = importlib.import_module(f"api.v1.endpoints.{module_name}")
        assert hasattr(mod, "router")
        assert isinstance(mod.router, APIRouter)

    @pytest.mark.parametrize("module_name", ENDPOINT_MODULES)
    def test_module_router_has_at_least_one_route(self, module_name):
        import importlib
        mod = importlib.import_module(f"api.v1.endpoints.{module_name}")
        assert len(mod.router.routes) >= 1
