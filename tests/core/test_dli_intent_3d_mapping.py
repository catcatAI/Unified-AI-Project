"""§X #97 — Test 3D multi-parameter intent influence mapping in DLI _update_intent_state().

C³ 4.0: The 3D intent vector (ix, iy, iz) now maps to 3 distinct parameters per dimension
(instead of collapsing to a single scalar magnitude → only one parameter updated).
"""

from __future__ import annotations

import asyncio
from datetime import datetime

import pytest


def _make_dli():
    """Create a DigitalLifeIntegrator with backdated intent update."""
    from core.life.digital_life_integrator import DigitalLifeIntegrator
    dli = DigitalLifeIntegrator()
    dli._last_intent_update = datetime(2020, 1, 1)
    return dli


def _force_intent_update(dli):
    """Backdate _last_intent_update so the next _update_intent_state() call runs."""
    dli._last_intent_update = datetime(2020, 1, 1)
    asyncio.run(dli._update_intent_state())
    # After the call, _last_intent_update is now() — reset for next call
    dli._last_intent_update = datetime(2020, 1, 1)


class TestIntent3DMultiParameterMapping:
    """Verify each 3D vector component maps to a distinct parameter per dimension."""

    @pytest.fixture
    def dli(self):
        return _make_dli()

    def test_alpha_3param_mapping(self, dli):
        """Alpha: ix→energy, iy→comfort, iz→arousal"""
        dli.intent_manager.active_intent_vector["alpha"] = (0.5, 0.0, 0.0)  # only x
        dli.state_matrix.update_alpha(energy=0.5, comfort=0.5, arousal=0.5)
        _force_intent_update(dli)

        state = dli.state_matrix.get_state("alpha")
        assert state["energy"] > 0.5, "ix should increase energy"
        assert state["comfort"] == 0.5, "iy=0 → comfort unchanged"
        assert state["arousal"] == 0.5, "iz=0 → arousal unchanged"

    def test_beta_3param_mapping(self, dli):
        """Beta: ix→focus, iy→curiosity, iz→learning"""
        dli.intent_manager.active_intent_vector["beta"] = (0.0, 0.5, 0.0)  # only y
        dli.state_matrix.update_beta(focus=0.5, curiosity=0.5, learning=0.5)
        _force_intent_update(dli)

        state = dli.state_matrix.get_state("beta")
        assert state["focus"] == 0.5, "ix=0 → focus unchanged"
        assert state["curiosity"] > 0.5, "iy should increase curiosity"
        assert state["learning"] == 0.5, "iz=0 → learning unchanged"

    def test_gamma_3param_mapping(self, dli):
        """Gamma: ix→happiness, iy→trust, iz→anticipation"""
        dli.intent_manager.active_intent_vector["gamma"] = (0.0, 0.0, 0.5)  # only z
        dli.state_matrix.update_gamma(happiness=0.5, trust=0.5, anticipation=0.5)
        _force_intent_update(dli)

        state = dli.state_matrix.get_state("gamma")
        assert state["happiness"] == 0.5, "ix=0 → happiness unchanged"
        assert state["trust"] == 0.5, "iy=0 → trust unchanged"
        assert state["anticipation"] > 0.5, "iz should increase anticipation"

    def test_delta_3param_mapping(self, dli):
        """Delta: ix→bond, iy→trust, iz→attention"""
        dli.intent_manager.active_intent_vector["delta"] = (0.0, 0.5, 0.0)  # only y
        dli.state_matrix.update_delta(bond=0.5, trust=0.5, attention=0.5)
        _force_intent_update(dli)

        state = dli.state_matrix.get_state("delta")
        assert state["bond"] == 0.5, "ix=0 → bond unchanged"
        assert state["trust"] > 0.5, "iy should increase trust"
        assert state["attention"] == 0.5, "iz=0 → attention unchanged"

    def test_zero_vector_no_change(self, dli):
        """All-zero vector should not trigger any update."""
        dli.intent_manager.active_intent_vector["alpha"] = (0.0, 0.0, 0.0)
        dli.state_matrix.update_alpha(energy=0.3, comfort=0.4, arousal=0.5)
        _force_intent_update(dli)

        state = dli.state_matrix.get_state("alpha")
        assert state["energy"] == 0.3
        assert state["comfort"] == 0.4
        assert state["arousal"] == 0.5

    def test_directional_preservation(self, dli):
        """Different 3D directions produce different parameter profiles."""
        dli.state_matrix.update_gamma(happiness=0.5, trust=0.5, anticipation=0.5)
        # Vector (0.5, 0, 0) → happiness boost only
        dli.intent_manager.active_intent_vector["gamma"] = (0.5, 0.0, 0.0)
        _force_intent_update(dli)
        h1 = dli.state_matrix.get_state("gamma")["happiness"]
        a1 = dli.state_matrix.get_state("gamma")["anticipation"]

        dli.state_matrix.update_gamma(happiness=0.5, trust=0.5, anticipation=0.5)
        # Vector (0, 0, 0.5) → anticipation boost only
        dli.intent_manager.active_intent_vector["gamma"] = (0.0, 0.0, 0.5)
        _force_intent_update(dli)
        h2 = dli.state_matrix.get_state("gamma")["happiness"]
        a2 = dli.state_matrix.get_state("gamma")["anticipation"]

        assert h1 > 0.5 and a1 == 0.5, "x-only → happiness up, anticipation unchanged"
        assert h2 == 0.5 and a2 > 0.5, "z-only → anticipation up, happiness unchanged"

    def test_beta_does_not_use_gamma_params(self, dli):
        """Cross-contamination check: beta intent should not affect gamma params."""
        dli.state_matrix.update_gamma(happiness=0.5, trust=0.5, anticipation=0.5)
        dli.state_matrix.update_beta(focus=0.5, curiosity=0.5, learning=0.5)
        dli.intent_manager.active_intent_vector["beta"] = (0.5, 0.0, 0.0)
        dli.intent_manager.active_intent_vector["gamma"] = (0.0, 0.0, 0.0)
        _force_intent_update(dli)

        gamma_state = dli.state_matrix.get_state("gamma")
        beta_state = dli.state_matrix.get_state("beta")
        assert beta_state["focus"] > 0.5, "beta ix should increase focus"
        assert gamma_state["happiness"] == 0.5, "gamma not affected by beta intent"


class TestDliC3Feedback:
    """§X #140 — C³ 6.0: DLI feedback loop tests."""

    @pytest.fixture
    def dli(self):
        return _make_dli()

    def test_process_interaction_feedback_tracks_count(self, dli):
        dli.process_interaction_feedback(0.8, True)
        assert dli._interaction_feedback_count == 1
        assert len(dli._engagement_window) == 1

    def test_feedback_disables_visual_3d_on_low_engagement(self, dli):
        from core.life.digital_life_integrator import ModalityType
        dli.process_interaction_feedback(0.1, False)
        dli.process_interaction_feedback(0.2, False)
        assert not dli.modality_gateway.modalities[ModalityType.VISUAL_3D].is_active

    def test_feedback_enables_visual_3d_on_high_engagement(self, dli):
        from core.life.digital_life_integrator import ModalityType
        # First disable it
        dli.modality_gateway.disable_modality("visual_3d")
        assert not dli.modality_gateway.modalities[ModalityType.VISUAL_3D].is_active
        dli.process_interaction_feedback(1.5, True)
        assert dli.modality_gateway.modalities[ModalityType.VISUAL_3D].is_active

    def test_cns_subscription_attrs_exist(self, dli):
        assert hasattr(dli, '_routing_outcomes')
        assert hasattr(dli, '_engagement_window')

    def test_dli_state_voter_no_context(self):
        from ai.meta.priority_negotiator import dli_state_voter
        assert dli_state_voter({}) is None

    def test_dli_state_voter_dormant(self):
        from ai.meta.priority_negotiator import dli_state_voter
        r = dli_state_voter({"dli_state": {"life_cycle_state": "DORMANT"}})
        assert r is not None
        assert r.routing_mode == "conservative"
        assert r.response_style == "minimal"

    def test_dli_state_voter_mature_exploratory(self):
        from ai.meta.priority_negotiator import dli_state_voter
        r = dli_state_voter({"dli_state": {"life_cycle_state": "MATURE"}})
        assert r is not None
        assert r.routing_mode == "exploratory"

    def test_dli_state_voter_initializing_neutral(self):
        from ai.meta.priority_negotiator import dli_state_voter
        r = dli_state_voter({"dli_state": {"life_cycle_state": "INITIALIZING"}})
        assert r is not None
        assert r.routing_mode == "neutral"

    def test_dli_state_voter_growing_returns_none(self):
        from ai.meta.priority_negotiator import dli_state_voter
        r = dli_state_voter({"dli_state": {"life_cycle_state": "GROWING"}})
        assert r is None
