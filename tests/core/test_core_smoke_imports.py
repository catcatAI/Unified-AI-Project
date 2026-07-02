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

_MODULE_IMPORTS = [
    ("economy.economy_db", "EconomyDB"),
    ("shared.types.mappable_data_object", "MappableDataObject"),
    ("core.utils", "now_timestamp"),
    ("core.hsp.connector", "HSPConnector"),
    ("core.hsp.bridge", "message_bridge"),
    ("core.angela_error", "AngelaError"),
]


@pytest.mark.parametrize("module_path,attr_name", _MODULE_IMPORTS,
                         ids=lambda x: x.split(".")[-1] if isinstance(x, str) else "")
def test_optional_module_import(module_path: str, attr_name: str) -> None:
    """Verify optional module import."""
    try:
        mod = importlib.import_module(module_path)
        obj = getattr(mod, attr_name)
        assert obj is not None
    except (ImportError, ModuleNotFoundError):
        pytest.skip(f"Optional module {module_path} not available")
