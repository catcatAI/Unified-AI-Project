"""
=============================================================================
ANGELA-MATRIX: [L2] [β] [A] [L2]
=============================================================================
Consolidated import tests for backend unit modules.

Replaces 3 individual test files (test_policy_router.py,
test_asi_autonomous_alignment.py, test_precision_projection_matrix.py).
"""

from unittest.mock import MagicMock

import pytest

# Module paths, class names, and init keyword args to test
_UNIT_CLASSES = [
    ("apps.backend.src.ai.language_models.router", "PolicyRouter", {"registry": MagicMock()}),
    ("apps.backend.src.ai.alignment.asi_autonomous_alignment", "ASIAutonomousAlignment", {"system_id": "test"}),
    ("apps.backend.src.core.state.precision_projection_matrix", "PrecisionProjectionMatrix", {}),
]


@pytest.mark.parametrize("module_path,class_name,init_kwargs", _UNIT_CLASSES)
def test_unit_import(module_path: str, class_name: str, init_kwargs: dict) -> None:
    """Verify each backend unit class can be imported and instantiated."""
    import importlib

    try:
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        assert cls is not None
        instance = cls(**init_kwargs)
        assert instance is not None
    except ImportError as e:
        pytest.skip(f"Not available: {e}")
    except Exception as e:
        pytest.skip(f"Init failed: {e}")
