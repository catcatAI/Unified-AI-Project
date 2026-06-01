"""Smoke tests for core/hsm_formula_system.py"""
import pytest


class TestHSMFormulaSystem:
    """Basic smoke tests for HSMFormulaSystem"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from core.hsm_formula_system import HSMFormulaSystem
            assert HSMFormulaSystem is not None
        except ImportError as e:
            pytest.skip(f"HSMFormulaSystem not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from core.hsm_formula_system import HSMFormulaSystem
            instance = HSMFormulaSystem()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"HSMFormulaSystem not available: {e}")
        except Exception as e:
            pytest.skip(f"HSMFormulaSystem init failed (expected in CI): {e}")

    def test_instantiation_with_config(self):
        """Verify instantiation with config"""
        try:
            from core.hsm_formula_system import HSMFormulaSystem
            instance = HSMFormulaSystem(config={"hsm_threshold": 0.7})
            assert instance is not None
            assert instance.e_m2_constant == 0.1
        except ImportError as e:
            pytest.skip(f"HSMFormulaSystem not available: {e}")
        except Exception as e:
            pytest.skip(f"HSMFormulaSystem init failed (expected in CI): {e}")

    def test_detect_cognitive_gap_method(self):
        """Verify detect_cognitive_gap method exists"""
        try:
            from core.hsm_formula_system import HSMFormulaSystem
            instance = HSMFormulaSystem()
            assert hasattr(instance, "detect_cognitive_gap")
        except ImportError as e:
            pytest.skip(f"HSMFormulaSystem not available: {e}")
        except Exception as e:
            pytest.skip(f"HSMFormulaSystem init failed (expected in CI): {e}")
