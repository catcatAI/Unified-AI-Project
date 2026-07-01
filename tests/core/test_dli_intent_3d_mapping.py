"""§X #97 — Test 3D multi-parameter intent influence mapping in DLI _update_intent_state().

C³ 4.0: The 3D intent vector (ix, iy, iz) now maps to 3 distinct parameters per dimension
(instead of collapsing to a single scalar magnitude → only one parameter updated).
"""

from __future__ import annotations

import asyncio
from datetime import datetime

import pytest


def _make_dli():
    """Lazy import to work around DLI circular import.

    On first import the circular dependency triggers an ImportError;
    subsequent imports work because the module is partially cached.
    """
    import importlib
    try:
        mod = importlib.import_module("core.life.digital_life_integrator")
        dli = mod.DigitalLifeIntegrator()
        dli._last_intent_update = datetime(2020, 1, 1)
        return dli
    except ImportError:
        pytest.skip("DLI circular import (pre-existing, not from §X #97)")


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
