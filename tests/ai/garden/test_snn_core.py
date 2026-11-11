# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [C] [L0]
# =============================================================================
"""
Tests for GARDEN TensorSNNCore.
"""

import os
import tempfile

import numpy as np
import pytest
from ai.garden.snn_core import (
    DEFAULT_DECAY,
    DEFAULT_LEAK,
    DEFAULT_THRESHOLD,
    DEFAULT_TIMESTEPS,
    HormonalModulator,
    TensorSNNCore,
    _get_backend,
)


class TestHormonalModulator:
    """Tests for the hormone-based threshold modulator."""

    def test_init(self):
        m = HormonalModulator()
        assert "cortisol" in m.hormones
        assert "serotonin" in m.hormones
        assert "dopamine" in m.hormones
        assert m.hormones["cortisol"] == 0.5
        assert m.hormones["serotonin"] == 0.5

    def test_set_hormone_clamps(self):
        m = HormonalModulator()
        m.set_hormone("cortisol", 2.0)
        assert m.hormones["cortisol"] == 1.0
        m.set_hormone("serotonin", -0.5)
        assert m.hormones["serotonin"] == 0.0

    def test_threshold_multiplier_normal(self):
        m = HormonalModulator()
        mult = m.get_threshold_multiplier()
        assert 0.4 <= mult <= 1.6

    def test_threshold_multiplier_stressed(self):
        m = HormonalModulator()
        m.set_hormone("cortisol", 1.0)
        m.set_hormone("adrenaline", 1.0)
        mult = m.get_threshold_multiplier()
        assert mult < 1.0  # Stress lowers threshold (more reactive)

    def test_threshold_multiplier_calm(self):
        m = HormonalModulator()
        m.set_hormone("serotonin", 1.0)
        mult = m.get_threshold_multiplier()
        assert mult > 0.95  # Calm raises threshold

    def test_profile_summary(self):
        m = HormonalModulator()
        profile = m.get_profile_summary()
        assert isinstance(profile, dict)
        assert len(profile) >= 6

    def test_sync_from_endocrine_live_values(self):
        """R87 死路徑 #11 回歸：sync_from_endocrine 必須能吃下真實
        get_hormonal_profile 形狀（hormones 鍵 = en_name）。

        歷史 bug 三層壞：(1) HormoneType.NORADRENALINE 不存在
        （真名 NOREPINEPHRINE）；(2) 用 enum 物件查 en_name 字串鍵；
        (3) fallback 用 ht.name（"CORTISOL"）也查不到。AttributeError
        被 except 吞掉 → live 同步從未成功。
        """
        m = HormonalModulator()

        class _FakeEndocrine:
            def get_hormonal_profile(self):
                return {
                    "hormones": {
                        "Cortisol": {"current": 0.9, "base": 0.5, "normalized": 0.8},
                        "Serotonin": {"current": 0.2, "base": 0.5, "normalized": 0.25},
                        "Norepinephrine": {"current": 0.7, "base": 0.3, "normalized": 0.6},
                    },
                }

        m.connect_endocrine_system(_FakeEndocrine())
        m.sync_from_endocrine()  # 修復前這裡 AttributeError
        assert m.hormones["cortisol"] == 0.8
        assert m.hormones["serotonin"] == 0.25
        assert m.hormones["noradrenaline"] == 0.6
        assert m._last_sync > 0


class TestTensorSNNCoreInit:
    """Tests for SNN core construction."""

    def test_init_defaults(self):
        core = TensorSNNCore()
        assert core.leak == DEFAULT_LEAK
        assert core.base_threshold == DEFAULT_THRESHOLD
        assert core.timesteps == DEFAULT_TIMESTEPS
        assert core.decay == DEFAULT_DECAY
        assert core.vocab_size == 0
        assert core._W is None

    def test_init_custom(self):
        core = TensorSNNCore(leak=0.1, threshold=0.5, timesteps=10, decay=0.8)
        assert core.leak == 0.1
        assert core.base_threshold == 0.5
        assert core.timesteps == 10
        assert core.decay == 0.8


class TestTensorSNNCoreKeyRegistry:
    """Tests for key registration and vocabulary management."""

    def test_register_key(self, snn_core: TensorSNNCore):
        core = snn_core
        before = core.vocab_size
        idx = core._register_key("new_key")
        assert core.vocab_size == before + 1
        assert idx == before  # New key gets next index

    def test_register_duplicate(self, snn_core: TensorSNNCore):
        core = snn_core
        idx1 = core._register_key("g1")
        idx2 = core._register_key("g1")
        assert idx1 == idx2
        assert core.vocab_size == 6  # As defined in conftest

    def test_grow_matrix(self, snn_core: TensorSNNCore):
        core = snn_core
        old_v = core.vocab_size
        core._register_key("very_new_key")
        # Amortized (doubling) growth: matrix capacity grows to >= old_v + 1,
        # while the live region always matches vocab_size.
        assert core._W.shape[0] >= old_v + 1
        assert core._W.shape[1] >= old_v + 1
        assert core._W.shape[0] == core._W.shape[1]

    def test_vocab_size_property(self, snn_core: TensorSNNCore):
        assert snn_core.vocab_size == 6


class TestTensorSNNCoreRelations:
    """Tests for relation management."""

    def test_add_relation(self, snn_core: TensorSNNCore):
        core = snn_core
        core.add_relation("g1", "e1", weight=0.8, bidirectional=True)
        i = core._key_to_idx["g1"]
        j = core._key_to_idx["e1"]
        assert core._W[i, j] == 0.8
        assert core._W[j, i] == 0.8

    def test_add_relation_directed(self, snn_core: TensorSNNCore):
        core = snn_core
        core.add_relation("g1", "e1", weight=0.8, bidirectional=False)
        i = core._key_to_idx["g1"]
        j = core._key_to_idx["e1"]
        assert core._W[i, j] == 0.8
        assert core._W[j, i] == 0.0

    def test_add_relation_accumulates(self, snn_core: TensorSNNCore):
        core = snn_core
        core.add_relation("g1", "e1", weight=0.5, bidirectional=True)
        core.add_relation("g1", "e1", weight=0.5, bidirectional=True)
        i = core._key_to_idx["g1"]
        j = core._key_to_idx["e1"]
        assert core._W[i, j] == 1.0  # Clamped to 1.0

    def test_add_relations_from_entry(self, snn_core: TensorSNNCore):
        core = snn_core
        relations = {"synonym": ["e1"], "mapping": ["r1"]}
        core.add_relations_from_entry("g1", relations)
        i = core._key_to_idx["g1"]
        j = core._key_to_idx["e1"]
        k = core._key_to_idx["r1"]
        # Synonym: 0.9, Mapping: 0.7
        assert core._W[i, j] >= 0.9
        assert core._W[i, k] >= 0.7


class TestTensorSNNCoreForward:
    """Tests for the LIF multi-step forward pass."""

    def test_forward_known_input(self, snn_core: TensorSNNCore):
        core = snn_core
        result = core.forward({"g1": 1.0})
        assert isinstance(result, dict)
        assert len(result) >= 1

    def test_forward_empty_keys(self, snn_core: TensorSNNCore):
        core = snn_core
        assert core.forward({}) == {}

    def test_forward_unregistered_keys(self, snn_core: TensorSNNCore):
        core = snn_core
        assert core.forward({"nonexistent": 1.0}) == {}

    def test_forward_propagates(self, snn_core: TensorSNNCore):
        """Input 'g1' should propagate to 'g5' (synonym) and 'r1'/'r2'."""
        core = snn_core
        result = core.forward({"g1": 1.0})
        assert "g5" in result
        # g5 connects to r1, so r1 should be activated (2 hops)
        assert "r1" in result

    def test_forward_scores_normalized(self, snn_core: TensorSNNCore):
        core = snn_core
        result = core.forward({"g1": 1.0})
        for score in result.values():
            assert 0.0 <= score <= 1.0

    def test_forward_with_context(self, snn_core: TensorSNNCore):
        core = snn_core
        result = core.forward({"g1": 1.0}, context={"mode": "test"})
        assert isinstance(result, dict)
        assert len(result) >= 1

    def test_forward_hormonal_modulation(self, snn_core: TensorSNNCore):
        core = snn_core
        # Set high stress
        core.modulator.set_hormone("cortisol", 1.0)
        core.modulator.set_hormone("adrenaline", 1.0)
        result = core.forward({"g1": 1.0})
        assert isinstance(result, dict)

    def test_forward_no_w_matrix(self):
        core = TensorSNNCore()
        result = core.forward({"g1": 1.0})
        assert result == {}


class TestTensorSNNCoreHebbian:
    """Tests for Hebbian learning."""

    def test_hebbian_update(self, snn_core: TensorSNNCore):
        core = snn_core
        delta = core.hebbian_update({"g1": 1.0}, {"e1": 1.0}, lr=0.1, target_strength=0.8)
        assert delta > 0
        i = core._key_to_idx["g1"]
        j = core._key_to_idx["e1"]
        assert core._W[i, j] > 0
        assert core._W[j, i] > 0

    def test_hebbian_empty_input(self, snn_core: TensorSNNCore):
        core = snn_core
        assert core.hebbian_update({}, {"e1": 1.0}) == 0.0

    def test_hebbian_empty_target(self, snn_core: TensorSNNCore):
        core = snn_core
        assert core.hebbian_update({"g1": 1.0}, {}) == 0.0

    def test_hebbian_tracks_updates(self, snn_core: TensorSNNCore):
        core = snn_core
        before = core.total_hebbian_updates
        core.hebbian_update({"g1": 1.0}, {"e1": 1.0})
        assert core.total_hebbian_updates == before + 1

    def test_hebbian_symmetric(self, snn_core: TensorSNNCore):
        core = snn_core
        core.hebbian_update({"g1": 1.0}, {"e1": 1.0}, lr=0.5, target_strength=0.9)
        i = core._key_to_idx["g1"]
        j = core._key_to_idx["e1"]
        assert core._W[i, j] == core._W[j, i]


class TestTensorSNNCorePersistence:
    """Tests for save/load."""

    def test_save_load(self, snn_core: TensorSNNCore):
        core = snn_core
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "snn.pt")
            core.save(path)
            core2 = TensorSNNCore()
            core2.load(path)
        assert core2.vocab_size == core.vocab_size
        assert core2.leak == core.leak
        assert core2.base_threshold == core.base_threshold
        assert core2.timesteps == core.timesteps

    def test_save_load_preserves_weights(self, snn_core: TensorSNNCore):
        core = snn_core
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "snn.pt")
            core.save(path)
            core2 = TensorSNNCore()
            core2.load(path)
        i = core._key_to_idx["g1"]
        j = core._key_to_idx["g5"]
        i2 = core2._key_to_idx["g1"]
        j2 = core2._key_to_idx["g5"]
        assert core._W[i, j] == core2._W[i2, j2]

    def test_save_load_hebbian_history(self, snn_core: TensorSNNCore):
        core = snn_core
        core.hebbian_update({"g1": 1.0}, {"e1": 1.0})
        core.total_steps = 42
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "snn.pt")
            core.save(path)
            core2 = TensorSNNCore()
            core2.load(path)
        assert core2.total_steps == 42
        assert core2.total_hebbian_updates >= 0

    def test_torch_save_loads_on_torchless_runtime(self, snn_core: TensorSNNCore, monkeypatch):
        """Regression (H1-a): a torch-saved .pt checkpoint must load on a
        torch-less runtime via the numpy sidecar (.npz sparse / .json meta)
        instead of raising FileNotFoundError."""
        core = snn_core
        xp, is_torch = _get_backend()
        if not is_torch:
            pytest.skip("torch backend not active; nothing to cross-backend test")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "snn.pt")
            core.hebbian_update({"g1": 1.0}, {"g2": 0.9}, lr=0.05)
            core.save(path)
            # Sidecar files must exist next to the .pt.
            assert os.path.exists(path + ".npz"), "torch save must write .npz sidecar"
            assert os.path.exists(tmp + "/snn.json"), "torch save must write .json meta"
            # Simulate torch-less runtime: force the numpy backend for load.
            import ai.garden.snn_core as S

            orig = S._get_backend
            S._get_backend = lambda: (np, False)
            try:
                state = S._load_checkpoint(path)
            finally:
                S._get_backend = orig
            assert state["W"] is not None
            assert "g1" in state["key_to_idx"] and "g2" in state["key_to_idx"]
            assert "last_used_by_key" in state
            # Weight values must survive the sparse densify roundtrip.
            i = state["key_to_idx"]["g1"]
            j = state["key_to_idx"]["g2"]
            assert state["W"][i, j] > 0.0


class TestTensorSNNCoreStats:
    """Tests for status/introspection."""

    def test_get_stats_empty(self):
        core = TensorSNNCore()
        s = core.get_stats()
        assert s["vocab_size"] == 0
        assert s["weight_matrix_shape"] == []
        assert s["matrix_density"] == 0.0

    def test_get_stats_with_data(self, snn_core: TensorSNNCore):
        s = snn_core.get_stats()
        assert s["vocab_size"] == 6
        assert s["weight_matrix_shape"] == [6, 6]
        assert s["matrix_density"] > 0
        assert s["matrix_memory_bytes"] == 6 * 6 * 4
        assert "hormones" in s


class TestStrengthProportionalWeights:
    """G1: the Hebbian fixed point must carry the co-activation strength.

    The old rule pulled every pair toward the same ``target_strength``, so the
    confidence product only changed *how fast* a pair got there: after enough
    updates a strength-0.4 association and a strength-1.0 association held the
    same weight, and everything downstream that wanted to rank edges found a
    flat matrix (external review G1; ``scripts/garden_readout_variants.py`` and
    the AL roadmap both papered over it). The fixed point is now
    ``target_strength * gate``.
    """

    @staticmethod
    def _weight(core, a, b):
        return float(core._W[core._key_to_idx[a], core._key_to_idx[b]])

    def test_reference_rule_matches_the_implementation(self, snn_core: TensorSNNCore):
        """Independent scalar recurrence — fails if the patch drifts from it."""
        lr, target, gate = 0.1, 0.35, 0.6
        expected = 0.0
        for _ in range(50):
            snn_core.hebbian_update(
                {"a": gate}, {"b": 1.0}, lr=lr, target_strength=target, weight_decay=0.0
            )
            expected = min(1.0, max(0.0, expected + lr * gate * (target * gate - expected)))
        # abs tolerance covers float32 storage in the weight matrix, nothing more.
        assert self._weight(snn_core, "a", "b") == pytest.approx(expected, abs=1e-6)

    def test_the_fixed_point_scales_with_the_gate(self, snn_core: TensorSNNCore):
        target = 0.35
        pairs = (("s1", "t1", 1.0), ("s2", "t2", 0.5))
        for _ in range(120):
            for src, tgt, gate in pairs:
                snn_core.hebbian_update({src: gate}, {tgt: 1.0}, lr=0.1, target_strength=target)
        strong = self._weight(snn_core, "s1", "t1")
        weak = self._weight(snn_core, "s2", "t2")
        assert strong > weak * 1.8, "a gate of 1.0 must not settle near a gate of 0.5"
        assert weak > 0.0

    def test_many_updates_keep_the_ordering(self, snn_core: TensorSNNCore):
        """The regression this guards: everything converging to one constant."""
        target = 0.35
        gates = (("p1", "q1", 1.0), ("p2", "q2", 0.7), ("p3", "q3", 0.4))
        for _ in range(200):
            for src, tgt, gate in gates:
                snn_core.hebbian_update(
                    {src: gate},
                    {tgt: 1.0},
                    lr=0.1,
                    target_strength=target,
                    weight_decay=0.0,
                )
        w = [self._weight(snn_core, s, t) for s, t, _ in gates]
        assert w[0] > w[1] > w[2], f"ordering lost after 200 updates: {w}"
        assert min(w[0] - w[1], w[1] - w[2]) > 0.05, f"ordering too shallow: {w}"
        for value, (_, _, gate) in zip(w, gates):
            assert value == pytest.approx(target * gate, abs=0.01)

    def test_full_confidence_behaviour_is_unchanged(self, snn_core: TensorSNNCore):
        """gate = 1 must reproduce the old rule exactly (no retraining needed)."""
        target, lr = 0.35, 0.1
        snn_core.hebbian_update(
            {"f": 1.0}, {"g": 1.0}, lr=lr, target_strength=target, weight_decay=0.0
        )
        old_rule = min(1.0, max(0.0, 0.0 + lr * 1.0 * (target - 0.0)))
        assert self._weight(snn_core, "f", "g") == pytest.approx(old_rule, abs=1e-6)


class TestRateAndFixedPointAreSeparable:
    """AL §55 applied to the production core: confidence is charged once.

    The pair's product already sets the destination (``0.35 * gate``). Charging
    it again in the step made a 0.5 x 0.5 association learn 16x slower than a
    crisp one *while* settling at half the height. ``rate_exponent`` keeps the
    destination and softens only the rate: 1.0 is the historical rule, 0.5 makes
    the rate follow the geometric mean (one confidence per side) — the ``c`` the
    AL arms measured against ``c²``.
    """

    @staticmethod
    def _weight(core, a, b):
        return float(core._W[core._key_to_idx[a], core._key_to_idx[b]])

    def test_the_default_reproduces_the_historical_rate(self):
        """Without the new argument nothing may move — old callers stay identical."""
        # Own core: the shared fixture may already hold weight on these keys, and
        # this test compares against a recurrence that starts from zero.
        core = TensorSNNCore(threshold=0.5)
        lr, target, gate = 0.05, 0.35, 0.25
        expected = 0.0
        for _ in range(8):
            # b at full confidence: the pair's gate is then exactly ``gate``,
            # which is what the scalar recurrence below models.
            core.hebbian_update(
                {"a": gate}, {"b": 1.0}, lr=lr, target_strength=target, weight_decay=0.0
            )
            expected = expected + lr * gate * (target * gate - expected)
        assert self._weight(core, "a", "b") == pytest.approx(expected, abs=1e-6)

    def test_a_soft_rate_accumulates_faster_without_raising_the_ceiling(self):
        gate = 0.25
        fast = TensorSNNCore(threshold=0.5)
        slow = TensorSNNCore(threshold=0.5)
        for _ in range(8):
            fast.hebbian_update(
                {"a": gate}, {"b": 1.0}, lr=0.05, weight_decay=0.0, rate_exponent=0.5
            )
            slow.hebbian_update({"a": gate}, {"b": 1.0}, lr=0.05, weight_decay=0.0)
        fast_w, slow_w = self._weight(fast, "a", "b"), self._weight(slow, "a", "b")
        assert fast_w > slow_w * 1.5, "the soft rate must actually soften the slowdown"
        # The destination is the product's job; softening the rate must not raise it.
        assert fast_w < 0.35 * gate

    def test_the_fixed_point_does_not_depend_on_the_rate(self):
        weights = []
        for exponent in (1.0, 0.5):
            core = TensorSNNCore(threshold=0.5)
            for _ in range(400):
                core.hebbian_update(
                    {"a": 0.25},
                    {"b": 1.0},
                    lr=0.05,
                    weight_decay=0.0,
                    rate_exponent=exponent,
                )
            weights.append(self._weight(core, "a", "b"))
        for value in weights:
            assert value == pytest.approx(0.35 * 0.25, abs=2e-3)


class TestRowDecayReachesCellsItDidNotWrite:
    """Roadmap §56: the late slide is row-wide decay, not a dead readout.

    ``_decay_touched_rows`` multiplies the *whole* touched row by
    ``(1 - weight_decay)`` and prunes below 0.01, so an association that happens
    to live in a row somebody else keeps touching loses weight on their updates.
    Measured on the AL `conflict` family (12 seeds, decay 0.002 vs 0.0): every arm
    declines from ep40 to ep80 with decay on while its weights still rise, and
    12/12 seeds improve with decay off — while the readout-free weight ranking
    declines too, which rules out readout saturation. These two tests pin the
    mechanism at unit scale, so a change to decay scope cannot pass silently.
    """

    @staticmethod
    def _weight(core, a, b):
        return float(core._W[core._key_to_idx[a], core._key_to_idx[b]])

    def test_a_quiet_cell_loses_weight_when_its_row_is_touched(self):
        core = TensorSNNCore(threshold=0.5)
        for _ in range(30):
            core.hebbian_update({"a": 1.0}, {"b": 1.0}, lr=0.1, weight_decay=0.0)
        before = self._weight(core, "a", "b")
        assert before > 0.3, "the cell under test must start well above the prune floor"

        # A different target now shares the same source row; (a, b) is never
        # written here, yet it is decayed because its row was touched.
        for _ in range(60):
            core.hebbian_update({"a": 1.0}, {"c": 1.0}, lr=0.1, weight_decay=0.002)
        after = self._weight(core, "a", "b")
        assert after < before * 0.95, f"row decay did not reach the quiet cell: {before} -> {after}"

    def test_a_quiet_cell_under_the_floor_is_pruned_to_zero(self):
        core = TensorSNNCore(threshold=0.5)
        core.hebbian_update({"a": 0.05}, {"b": 0.05}, lr=0.01, weight_decay=0.0)
        tiny = self._weight(core, "a", "b")
        assert 0.0 < tiny < 0.01
        # Default decay touches row `a`; the entry is not protected because this
        # call did not write it, so it is erased rather than faded.
        core.hebbian_update({"a": 1.0}, {"c": 1.0}, lr=0.05)
        assert self._weight(core, "a", "b") == 0.0
