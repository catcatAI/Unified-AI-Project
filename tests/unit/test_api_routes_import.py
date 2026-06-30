"""API route import tests — parameterized.

Consolidated from 9 standalone import-only test files into 1 parameterized test.
"""

import pytest

_API_ROUTES = [
    ("api.v1.endpoints.economy", "router", "/economy"),
    ("api.v1.endpoints.mobile", "router", "/mobile"),
    ("api.v1.endpoints.pet", "router", "/pet"),
    ("api.v1.endpoints.plugins", "router", "/plugins"),
    ("api.v1.endpoints.tactile", "router", "/tactile"),
    ("api.v1.endpoints.trace", "router", "/trace"),
    ("api.v1.endpoints.vision", "router", "/vision"),
    ("api.v1.endpoints.audio", "router", "/audio"),
    ("api.v1.endpoints.drive", "router", "/drive"),
]


@pytest.mark.parametrize("module_path,attr_name,expected_prefix", _API_ROUTES)
def test_api_route_import(module_path: str, attr_name: str, expected_prefix: str) -> None:
    """Verify each API route module imports and has a valid router with prefix."""
    import importlib

    module = importlib.import_module(module_path)
    router = getattr(module, attr_name)
    assert router is not None, f"{module_path} has no {attr_name}"
    # Verify the router has the expected path prefix
    prefix = getattr(router, "prefix", "")
    assert prefix is not None
    assert expected_prefix in prefix, (
        f"Expected prefix '{expected_prefix}' in router.prefix '{prefix}'"
    )
