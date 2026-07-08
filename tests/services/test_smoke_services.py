"""P10-1: Smoke tests for service modules — parameterized.

Consolidated from 3 standalone test functions into 1 parameterized test.
"""

import pytest

_SERVICE_CLASSES = [
    ("services.websocket_manager", "ConnectionManager"),
    ("services.math_verifier", "MathVerifier"),
    ("services.vision_service", "VisionService"),
]

_SERVICE_MODULES = [
    "services.main_api_server",
    "services.resource_awareness_service",
]


@pytest.mark.parametrize("module_path,class_name", _SERVICE_CLASSES)
def test_service_import_and_instantiate(module_path: str, class_name: str) -> None:
    """Verify each service class can be imported and instantiated."""
    import importlib

    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    instance = cls()
    assert instance is not None


@pytest.mark.parametrize("module_path", _SERVICE_MODULES)
def test_service_module_import(module_path: str) -> None:
    """Verify each service module can be imported with correct name."""
    import importlib

    module = importlib.import_module(module_path)
    assert module is not None
    assert module.__name__ == module_path, (
        f"Expected __name__ '{module_path}', got '{module.__name__}'"
    )
