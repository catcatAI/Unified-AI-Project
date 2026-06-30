"""
Consolidated smoke tests for CLI modules.

Replaces 4 individual test files — all reference modules deleted
in Phase 9-12 cleanup.
"""

# =============================================================================
# ANGELA-MATRIX: L2 β A L2
# =============================================================================

import importlib

import pytest


_DELETED_CLI_MODULES = [
    "cli.cli",
    "cli.cli_publish_fact",
    "cli.client",
    "cli.error_handler",
]


@pytest.mark.parametrize("module_path", _DELETED_CLI_MODULES)
def test_deleted_cli_module(module_path: str) -> None:
    """Verify that a Phase 9-12 deleted CLI module is (still) gone."""
    try:
        importlib.import_module(module_path)
        pytest.fail(f"{module_path} was re-introduced but should remain deleted")
    except ModuleNotFoundError:
        pytest.skip(f"{module_path} deleted in Phase 9-12 cleanup")
