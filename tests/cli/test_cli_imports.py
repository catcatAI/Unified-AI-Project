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


_DELETED_MODULES = [
    "cli.cli",
    "cli.cli_publish_fact",
    "cli.client",
    "cli.error_handler",
    # Merged from tests/tools/test_tools_imports.py (§X #120)
    "training_manager",
    "integration.agent_collaboration",
    # Merged from tests/core/test_core_smoke_imports.py (§X #122)
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
    # Merged from tests/unit/test_unit_backend_imports.py (§X #123)
    "apps.backend.src.ai.language_models.router",
    # Merged from skip-only test files (§X #125)
    "learning.content_analyzer_module",
    "tools.math_model.lightweight_math_model",
    "tools.logic_tool",
    "tools.logic_model.logic_parser_eval",
    # Deleted ai.ops modules (§X #126)
    "ai.ops",
    "ai.ops.intelligent_ops_manager",
    "ai.ops.ai_ops_engine",
    "ai.ops.capacity_planner",
    "ai.ops.performance_optimizer",
    "ai.ops.predictive_maintenance",
    # Merged from tests/ai/test_trained_models.py (§X #134)
    "ai.models.model_data_types",
    "ai.models.model_types",
    "ai.models.trained_model_manager",
    # Merged from orphan test files referencing deleted modules (§X #144)
    "ai.code_inspection.code_inspector",
    "ai.code_inspection.code_learning",
    "apps.backend.src.ai.code_inspection.code_learning",
    # Deleted empty stub mcp.context7_connector (§X #204-5)
    "mcp.context7_connector",
]


@pytest.mark.parametrize("module_path", _DELETED_MODULES)
def test_deleted_module(module_path: str) -> None:
    """Verify that a Phase 9-12 deleted module is (still) gone."""
    try:
        importlib.import_module(module_path)
        pytest.fail(f"{module_path} was re-introduced but should remain deleted")
    except ModuleNotFoundError:
        pytest.skip(f"{module_path} deleted in Phase 9-12 cleanup")
