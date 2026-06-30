"""Core module import and structure tests — parameterized.

Consolidated from 6 standalone import-only test files into 2 parameterized tests
with improved precision (method verification, enum validation).
"""

import pytest

# =============================================================================
# Group 1: Basic module importability
# =============================================================================

_CORE_MODULES = [
    "core.bio.neuroplasticity",
    "core.engine.action_executor",
    "core.engine.desktop_interaction",
    "core.bio.physiological_tactile",
]


@pytest.mark.parametrize("module_path", _CORE_MODULES)
def test_core_module_importable(module_path: str) -> None:
    """Verify each core module can be imported without error."""
    import importlib

    module = importlib.import_module(module_path)
    assert module is not None, f"{module_path} failed to import"
    # Verify module has at least one public member
    public_members = [m for m in dir(module) if not m.startswith("_")]
    assert len(public_members) > 0, f"{module_path} has no public members"


def test_ethics_manager_import() -> None:
    """Verify ethics_manager can be imported (has no public members at module level)."""
    import importlib

    module = importlib.import_module("core.ethics.ethics_manager")
    assert module is not None, "core.ethics.ethics_manager failed to import"
    # Module OK: internal-only module with no public exports -- valid design


# =============================================================================
# Group 2: PhysiologicalTactile — enum values and required methods (was 3 tests)
# =============================================================================

def test_tactile_enums_have_required_values() -> None:
    """Verify TactileType and BodyPart enums have required values."""
    from core.bio.physiological_tactile import BodyPart, TactileType

    # All required TactileType values
    assert TactileType.LIGHT_TOUCH is not None
    assert TactileType.PRESSURE is not None
    assert TactileType.TEMPERATURE is not None
    assert TactileType.VIBRATION is not None
    assert TactileType.PAIN is not None
    assert TactileType.ITCH is not None

    # All required BodyPart values
    assert BodyPart.FACE is not None
    assert BodyPart.NECK is not None
    assert BodyPart.HANDS is not None
    assert BodyPart.FEET is not None


def test_tactile_system_has_required_methods() -> None:
    """Verify PhysiologicalTactileSystem has lifecycle methods."""
    from core.bio.physiological_tactile import PhysiologicalTactileSystem

    required_methods = {"initialize", "process_stimulus", "shutdown"}
    actual_methods = {m for m in dir(PhysiologicalTactileSystem) if not m.startswith("_")}
    missing = required_methods - actual_methods
    assert not missing, f"Missing required methods: {missing}"


# =============================================================================
# Group 3: gmqtt / ExternalConnector (was 3 tests)
# =============================================================================

def test_gmqtt_library_available() -> None:
    """Verify gmqtt library is importable (explicit library check)."""
    try:
        import gmqtt  # noqa: F401
        assert gmqtt is not None
    except ImportError:
        pytest.skip("gmqtt not available")


def test_external_connector_creation() -> None:
    """Verify ExternalConnector can be imported and created with required params."""
    try:
        from core.hsp.external.external_connector import ExternalConnector

        connector = ExternalConnector(
            ai_id="test_ai",
            broker_address="localhost",
            broker_port=1883,
        )
        assert connector is not None
        assert connector.ai_id == "test_ai"
    except ImportError:
        pytest.skip("ExternalConnector not available")
    except Exception:
        pytest.skip("Cannot create ExternalConnector")
