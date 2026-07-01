"""§X #100 — DynamicThresholdManager: update_from_state_matrix() real implementation.

Previously a pass placeholder, now reads alpha/gamma/beta dimension values
from StateMatrix4D to dynamically adjust emotion thresholds.
"""

import pytest


class TestDynamicThresholdManager:
    """Verify DynamicThresholdManager threshold adjustment from state matrix."""

    @pytest.fixture
    def mgr(self):
        from core.life.dynamic_parameters import DynamicThresholdManager
        return DynamicThresholdManager()

    def test_init_defaults(self, mgr):
        assert mgr.get_parameter("emotion_happiness_threshold") == 0.6
        assert mgr.get_parameter("emotion_sadness_threshold") == 0.5
        assert mgr.get_parameter("emotion_anger_threshold") == 0.5
        assert mgr.get_parameter("social_initiative_threshold") == 0.5

    def test_none_state_matrix_no_error(self, mgr):
        mgr.update_from_state_matrix(None)
        assert mgr.get_parameter("emotion_happiness_threshold") == 0.6

    def test_high_energy_lowers_happiness_threshold(self, mgr):
        from core.engine.state_matrix import StateMatrix4D
        sm = StateMatrix4D()
        sm.update_alpha(energy=0.9)
        mgr.update_from_state_matrix(sm)
        assert mgr.get_parameter("emotion_happiness_threshold") < 0.6

    def test_high_energy_raises_anger_threshold(self, mgr):
        from core.engine.state_matrix import StateMatrix4D
        sm = StateMatrix4D()
        sm.update_alpha(energy=0.9)
        mgr.update_from_state_matrix(sm)
        assert mgr.get_parameter("emotion_anger_threshold") > 0.5

    def test_high_happiness_lowers_sadness_threshold(self, mgr):
        from core.engine.state_matrix import StateMatrix4D
        sm = StateMatrix4D()
        sm.update_gamma(happiness=0.9)
        mgr.update_from_state_matrix(sm)
        assert mgr.get_parameter("emotion_sadness_threshold") < 0.5

    def test_high_curiosity_raises_social_initiative(self, mgr):
        from core.engine.state_matrix import StateMatrix4D
        sm = StateMatrix4D()
        sm.update_beta(curiosity=0.9)
        mgr.update_from_state_matrix(sm)
        assert mgr.get_parameter("social_initiative_threshold") > 0.5

    def test_low_energy_leaves_thresholds_near_default(self, mgr):
        from core.engine.state_matrix import StateMatrix4D
        sm = StateMatrix4D()
        sm.update_alpha(energy=0.1)
        mgr.update_from_state_matrix(sm)
        assert mgr.get_parameter("emotion_happiness_threshold") >= 0.58
        assert mgr.get_parameter("emotion_anger_threshold") <= 0.51
