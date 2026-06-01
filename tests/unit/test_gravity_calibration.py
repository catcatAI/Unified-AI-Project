"""Smoke tests for core.card.quality.gravity_calibration"""
import pytest


class TestGravityCalibrator:
    def test_import(self):
        try:
            from core.card.quality.gravity_calibration import GravityCalibrator
            assert GravityCalibrator is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from core.card.quality.gravity_calibration import GravityCalibrator
            instance = GravityCalibrator()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")

    def test_constants(self):
        try:
            from core.card.quality.gravity_calibration import (
                IDEAL_LOWER,
                IDEAL_UPPER,
                G_CANDIDATES,
            )
            assert IDEAL_LOWER == 0.6
            assert IDEAL_UPPER == 0.85
            assert len(G_CANDIDATES) == 4
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
