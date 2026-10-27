"""Phase 2 item 2b of the three-core plan — ζ is computed, not frozen.

Phase 1 removed the four ζ sub-metrics from the prompt/context because
``update_zeta()`` had no production caller: the axis held defaults
(memory_depth 0.6, identity_continuity 0.75, ...) presented as current
state. This file pins the Phase 2 replacement:

1. **``compute_zeta_values()`` is a pure function of TemporalState** —
   ``{}`` until there are >= 2 observations, otherwise exactly four
   values in [0, 1] that partition as
   ``temporal_coherence == identity_continuity + narrative_flow``.
2. **StateMatrix4D feeds TemporalState on every non-ζ update** and
   recomputes ζ from it; ``zeta_observed_fields`` reports which keys
   carry an observation — that set is what the renderers filter on.
3. **An explicit ``update_zeta()`` write is not itself an observation**
   (ζ does not enter the snapshot — it is computed, not observed): it
   stands until the next real observation supersedes it, and the recompute
   never routes through ``_post_update()`` (that would append a duplicate
   snapshot and recurse).
"""

import sys
from pathlib import Path

import pytest

BACKEND_SRC = Path(__file__).resolve().parents[2] / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from core.engine.state_matrix import StateMatrix4D, compute_zeta_values  # noqa: E402
from core.state.temporal import TemporalState  # noqa: E402

ZETA_KEYS = {
    "memory_depth",
    "temporal_coherence",
    "identity_continuity",
    "narrative_flow",
}


def _series(records):
    """Build a TemporalState whose alpha.energy follows ``records``."""
    ts = TemporalState(max_size=500)
    for i, value in enumerate(records):
        ts.record({"timestamp": f"t{i}", "alpha": {"energy": value}})
    return ts


class TestComputeZetaValuesIsPure:
    def test_below_two_observations_returns_nothing(self):
        assert compute_zeta_values(TemporalState()) == {}
        assert compute_zeta_values(_series([0.5])) == {}

    def test_observations_yield_exactly_the_four_keys(self):
        values = compute_zeta_values(_series([0.5, 0.5, 0.5, 0.5, 0.5]))
        assert set(values) == ZETA_KEYS
        assert all(0.0 <= v <= 1.0 for v in values.values())

    def test_keys_partition_as_coherence_equals_continuity_plus_flow(self):
        values = compute_zeta_values(_series([0.5, 0.5, 0.5, 0.5, 0.5]))
        assert values["temporal_coherence"] == pytest.approx(
            values["identity_continuity"] + values["narrative_flow"]
        )

    def test_flat_state_reads_as_perfect_continuity(self):
        values = compute_zeta_values(_series([0.5] * 10))
        assert values["temporal_coherence"] == 1.0
        assert values["identity_continuity"] == 1.0
        assert values["narrative_flow"] == 0.0

    def test_fast_movement_reads_as_narrative_flow(self):
        # 0.1 -> 0.9 over 20 points: slope 0.042/pt > 0.01 = "moving", and a
        # uniform ramp stays under 2σ (z_max -> √3), so it is flow, not
        # anomaly — that is exactly why the threshold is 2.0, not 1.5.
        values = compute_zeta_values(_series([0.1 + 0.042 * i for i in range(20)]))
        assert values["narrative_flow"] == 1.0
        assert values["identity_continuity"] == 0.0
        assert values["temporal_coherence"] == 1.0, "a uniform ramp is not an anomaly"

    def test_spike_drops_coherence_on_that_pair_only(self):
        ts = TemporalState(max_size=500)
        spike = [0.5] * 20 + [0.95] + [0.5] * 19
        for i, value in enumerate(spike):
            ts.record({"timestamp": f"t{i}", "alpha": {"energy": value}, "beta": {"focus": 0.5}})
        values = compute_zeta_values(ts)
        # alpha spikes (anomalous), beta stays flat (stable): 1 of 2 pairs.
        assert values["temporal_coherence"] == 0.5
        assert values["identity_continuity"] == 0.5
        assert values["narrative_flow"] == 0.0

    def test_memory_depth_is_the_window_fill_ratio(self):
        values = compute_zeta_values(_series([0.5] * 7))
        assert values["memory_depth"] == 7 / 50


class TestStateMatrixDrivesZeta:
    def test_cold_matrix_keeps_defaults_unobserved(self):
        matrix = StateMatrix4D()
        assert matrix.zeta_observed_fields == frozenset()
        defaults = dict(matrix.zeta.values)
        matrix.update_alpha(energy=0.8)  # 1 observation: not enough yet
        assert matrix.zeta_observed_fields == frozenset()
        assert matrix.zeta.values == defaults, "unobserved keys must stay untouched (D11)"

    def test_second_observation_computes_all_four_keys(self):
        matrix = StateMatrix4D()
        matrix.update_alpha(energy=0.8, comfort=0.6)
        matrix.update_beta(focus=0.9, curiosity=0.7)
        assert matrix.zeta_observed_fields == frozenset(ZETA_KEYS)
        # Exactly 2 snapshots -> memory_depth = min(1, 2 / 50).
        assert matrix.zeta.values["memory_depth"] == 2 / 50
        assert set(matrix.zeta.values) >= ZETA_KEYS

    def test_history_and_temporal_stay_in_lockstep(self):
        matrix = StateMatrix4D()
        for i in range(10):
            matrix.update_alpha(energy=(i % 7) / 10)
        assert len(matrix.history) == 10
        assert matrix._get_temporal_state().size() == 10

    def test_recompute_does_not_route_through_post_update(self):
        # If the recompute went through _post_update() it would append a
        # second snapshot (and recurse); update_count is the direct witness
        # of how many _post_update() runs actually happened.
        matrix = StateMatrix4D()
        for i in range(5):
            matrix.update_alpha(energy=(i % 3) / 10)
        assert matrix.update_count == 5
        assert len(matrix.history) == 5

    def test_zeta_update_is_not_an_observation(self):
        matrix = StateMatrix4D()
        matrix.update_alpha(energy=0.7)
        matrix.update_alpha(energy=0.8)
        assert matrix._get_temporal_state().size() == 2
        history_before = len(matrix.history)
        matrix.update_zeta(memory_depth=0.6)
        # The manual write stands (no self-supersede within the same call)…
        assert matrix.zeta.values["memory_depth"] == 0.6
        # …and ζ itself added no observation: the snapshot would be an
        # axis-identical duplicate that poisons trend/anomaly windows.
        assert matrix._get_temporal_state().size() == 2

    def test_manual_write_is_superseded_by_the_next_observation(self):
        matrix = StateMatrix4D()
        matrix.update_zeta(memory_depth=0.6)  # explicit write, temporal empty
        assert matrix.zeta.values["memory_depth"] == 0.6
        matrix.update_alpha(energy=0.5)  # 1st observation: still nothing to compute
        assert matrix.zeta.values["memory_depth"] == 0.6
        matrix.update_alpha(energy=0.6)  # 2nd observation: computed value wins
        assert matrix.zeta.values["memory_depth"] == 2 / 50

    def test_observed_fields_property_is_an_immutable_view(self):
        matrix = StateMatrix4D()
        matrix.update_alpha(energy=0.7)
        matrix.update_beta(focus=0.6)
        view = matrix.zeta_observed_fields
        assert isinstance(view, frozenset)
        assert view == frozenset(ZETA_KEYS)
