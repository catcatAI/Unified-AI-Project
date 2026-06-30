"""
Consolidated smoke tests for tools, fragmenta, training, integration modules.

Replaces 4 individual test files:
  test_code_understanding_tool, test_parameter_extractor,
  test_fragmenta_orchestrator, test_training_manager,
  test_agent_collaboration
"""

# =============================================================================
# ANGELA-MATRIX: L2 β A L2
# =============================================================================

import importlib

import pytest


# ── Existing modules ─────────────────────────────────────────────────────

def test_code_understanding_tool_import() -> None:
    """Verify core.tools.code_understanding_tool imports and has known class."""
    mod = importlib.import_module("core.tools.code_understanding_tool")
    assert hasattr(mod, "CodeUnderstandingTool"), \
        "Expected CodeUnderstandingTool class in module"


def test_parameter_extractor_import() -> None:
    """Verify core.tools.parameter_extractor imports (package with __init__).
    Note: This package has no public members (empty module placeholder).
    """
    mod = importlib.import_module("core.tools.parameter_extractor")
    assert mod is not None, "parameter_extractor package should be importable"


def test_fragmenta_orchestrator_import() -> None:
    """Verify fragmenta.fragmenta_orchestrator imports and has known class."""
    mod = importlib.import_module("fragmenta.fragmenta_orchestrator")
    assert hasattr(mod, "FragmentaOrchestrator"), \
        "Expected FragmentaOrchestrator class in fragmenta_orchestrator"
    cls = getattr(mod, "FragmentaOrchestrator")
    assert callable(cls), "FragmentaOrchestrator should be a callable class"


# ── Deleted modules (Phase 9-12 cleanup) ─────────────────────────────────

def test_training_manager_import() -> None:
    """Verify training_manager (deleted in Phase 9-12)."""
    try:
        importlib.import_module("training_manager")
        pytest.fail("training_manager was re-introduced but should remain deleted")
    except ModuleNotFoundError:
        pytest.skip("training_manager deleted in Phase 9-12 cleanup")


def test_agent_collaboration_import() -> None:
    """Verify integration.agent_collaboration (deleted in Phase 9-12)."""
    try:
        importlib.import_module("integration.agent_collaboration")
        pytest.fail("agent_collaboration was re-introduced but should remain deleted")
    except ModuleNotFoundError:
        pytest.skip("integration.agent_collaboration deleted in Phase 9-12 cleanup")
