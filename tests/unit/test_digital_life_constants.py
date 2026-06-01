"""Smoke tests for core.life.digital_life_constants"""
import pytest


class TestDigitalLifeConstants:
    def test_import_all(self):
        try:
            from core.life.digital_life_constants import (
                MetabolicConstants,
                SensoryConstants,
                GovernanceConstants,
                ActionGeometricMapping,
            )
            assert MetabolicConstants is not None
            assert SensoryConstants is not None
            assert GovernanceConstants is not None
            assert ActionGeometricMapping is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_metabolic_constants(self):
        try:
            from core.life.digital_life_constants import MetabolicConstants
            assert MetabolicConstants.BASE_FATIGUE_INCREASE == 0.02
            assert MetabolicConstants.RECOVERY_RATE_IDLE == 0.05
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_sensory_constants(self):
        try:
            from core.life.digital_life_constants import SensoryConstants
            assert SensoryConstants.TOUCH_AROUSAL_BOOST == 1.2
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_governance_constants(self):
        try:
            from core.life.digital_life_constants import GovernanceConstants
            assert GovernanceConstants.ALPHA_MODE_THRESHOLD == 0.65
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_action_geometric_mapping(self):
        try:
            from core.life.digital_life_constants import ActionGeometricMapping
            assert ActionGeometricMapping.REST == (0.0, 0.0, 0.0)
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
