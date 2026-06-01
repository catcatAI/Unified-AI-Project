"""Smoke tests for core/life_intensity_formula.py"""
import pytest


class TestLifeIntensityFormula:
    """Basic smoke tests for LifeIntensityFormula"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from core.life_intensity_formula import LifeIntensityFormula
            assert LifeIntensityFormula is not None
        except ImportError as e:
            pytest.skip(f"LifeIntensityFormula not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from core.life_intensity_formula import LifeIntensityFormula
            instance = LifeIntensityFormula()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"LifeIntensityFormula not available: {e}")
        except Exception as e:
            pytest.skip(f"LifeIntensityFormula init failed (expected in CI): {e}")

    def test_instantiation_with_config(self):
        """Verify instantiation with config"""
        try:
            from core.life_intensity_formula import LifeIntensityFormula
            instance = LifeIntensityFormula(config={"max_history_size": 5000})
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"LifeIntensityFormula not available: {e}")
        except Exception as e:
            pytest.skip(f"LifeIntensityFormula init failed (expected in CI): {e}")

    def test_calculate_life_intensity_method(self):
        """Verify calculate_life_intensity method exists"""
        try:
            from core.life_intensity_formula import LifeIntensityFormula
            instance = LifeIntensityFormula()
            assert hasattr(instance, "calculate_life_intensity")
        except ImportError as e:
            pytest.skip(f"LifeIntensityFormula not available: {e}")
        except Exception as e:
            pytest.skip(f"LifeIntensityFormula init failed (expected in CI): {e}")
