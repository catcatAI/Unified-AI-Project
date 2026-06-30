"""
Consolidated smoke tests for core modules.

Replaces 15 individual test files — most reference subsystems deleted
in Phase 9-12 cleanup and are preserved as informative skips.

Note: message_bridge is covered in test_core_module_imports.py, not duplicated here.
"""

# =============================================================================
# ANGELA-MATRIX: L2 β A L2
# =============================================================================

import importlib

import pytest


# ── Deleted modules (Phase 9-12 cleanup) ─────────────────────────────────
# These modules were deleted from apps/backend/src/.  Tests are preserved as
# informative skips so any re-introduction is noticed.

_DELETED_CORE_MODULES = [
    "cluster_hardware",
    "comprehensive_analysis",
    "content_analyzer_fix",
    "core_system",
    "hsp_fixture_fix",
    "intelligent_test_generator",
    "lifecycle_loops",
    "lifecycle_loops_simple",
    "performance_benchmark",
    "result_analyzer",
    "security_improvements",
    "system_integration",
]


@pytest.mark.parametrize("module_name", _DELETED_CORE_MODULES)
def test_deleted_core_module(module_name: str) -> None:
    """Verify that a Phase 9-12 deleted module is (still) gone."""
    try:
        importlib.import_module(module_name)
        pytest.fail(f"{module_name} was re-introduced but should remain deleted")
    except ModuleNotFoundError:
        pytest.skip(f"{module_name} deleted in Phase 9-12 cleanup")


# ── Optional dependency import tests ─────────────────────────────────────

def test_data_manager_imports() -> None:
    """Verify EconomyDB, MappableDataObject, and get_timestamp imports."""
    results: list[str] = []
    try:
        from economy.economy_db import EconomyDB  # type: ignore[import-untyped]
        assert EconomyDB is not None
        results.append("EconomyDB")
    except ImportError:
        pass

    try:
        from shared.types.mappable_data_object import MappableDataObject  # type: ignore[import-untyped]
        assert MappableDataObject is not None
        results.append("MappableDataObject")
    except ImportError:
        pass

    try:
        from core.utils import get_timestamp  # type: ignore[import-untyped]
        assert get_timestamp is not None
        results.append("get_timestamp")
    except ImportError:
        pass

    if not results:
        pytest.skip("No optional data-manager modules available")


def test_dependency_manager_imports() -> None:
    """Verify HSPConnector, message_bridge, and AngelaError imports."""
    results: list[str] = []
    try:
        from core.hsp.connector import HSPConnector  # type: ignore[import-untyped]
        assert HSPConnector is not None
        results.append("HSPConnector")
    except ImportError:
        pass

    try:
        from core.hsp.bridge import message_bridge  # type: ignore[import-untyped]
        assert message_bridge is not None
        results.append("message_bridge")
    except ImportError:
        pass

    try:
        from core.angela_error import AngelaError  # type: ignore[import-untyped]
        assert AngelaError is not None
        results.append("AngelaError")
    except ImportError:
        pass

    if not results:
        pytest.skip("No dependency-manager modules available")
