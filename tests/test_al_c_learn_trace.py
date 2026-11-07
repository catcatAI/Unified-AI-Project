"""Tests for the prune-floor fix and the cue-level trace (``scripts/al_c_learn_trace.py``).

The trace exposed a real defect: ``hebbian_update`` pruned, in the same call, any
weight whose single increment landed under the 0.01 floor. With ``lr`` 0.03 and any
``plasticity`` below 1 the increment is 0.0105 * plasticity, so a whole sample could
be learned and erased forever. These tests pin the fix, pin that decay still prunes,
and pin the trace's ability to name the cause.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

from ai.garden.snn_core import TensorSNNCore  # noqa: E402

SCRIPT = REPO_ROOT / "scripts" / "al_c_learn_trace.py"


@pytest.fixture(scope="module")
def trace():
    spec = importlib.util.spec_from_file_location("al_c_learn_trace_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["al_c_learn_trace_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def core():
    return TensorSNNCore(threshold=0.25, timesteps=16)


def _weight(core, src: str, tgt: str) -> float:
    return float(core._W[core._key_to_idx[src], core._key_to_idx[tgt]])


class TestPruneFloor:
    def test_increment_below_the_floor_survives_the_same_call(self, core):
        # lr 0.01 * target 0.35 = 0.0035, well under the 0.01 prune floor.
        core.hebbian_update({"a": 1.0}, {"b": 1.0}, lr=0.01, target_strength=0.35)
        assert _weight(core, "a", "b") > 0.0

    def test_repeated_small_steps_accumulate(self, core):
        # 修好之前：每一步都被剪回 0，這個樣本永遠學不到東西。
        for _ in range(8):
            core.hebbian_update({"a": 1.0}, {"b": 1.0}, lr=0.01, target_strength=0.35)
        assert _weight(core, "a", "b") > 0.01

    def test_low_plasticity_still_learns(self, core):
        # plasticity 0.4 讓增量掉到 0.0042 —— 這是相位調制實際會遇到的區間。
        for _ in range(8):
            core.hebbian_update(
                {"a": 1.0}, {"b": 1.0}, lr=0.03, target_strength=0.35, plasticity=0.4
            )
        assert _weight(core, "a", "b") > 0.01

    def test_decay_still_prunes_weights_it_did_not_touch(self, core):
        # 同一列但不同欄（這次沒寫到的）仍然照舊被衰減剪掉。
        core.hebbian_update({"a": 1.0}, {"z": 1.0}, lr=0.05)
        row, col = core._key_to_idx["a"], core._key_to_idx["z"]
        core._W[row, col] = 0.005  # 舊的、快消失的權重
        core.hebbian_update({"a": 1.0}, {"b": 1.0}, lr=0.05)
        assert float(core._W[row, col]) == 0.0


class TestThresholdIsReachable:
    """門檻必須落在增益的實際範圍內，否則那個判詞是一條死路。"""

    def test_low_gain_threshold_splits_the_real_schedule(self, trace):
        period = trace._downstream.natural_period()
        gains = trace._downstream._schedule(period, 48)
        below = [g for g in gains if g < trace.LOW_GAIN]
        above = [g for g in gains if g >= trace.LOW_GAIN]
        assert below, "門檻太高：沒有任何樣本算低增益"
        assert above, "門檻太低：所有樣本都算低增益"
        # 舊的 0.2 低於整個擺幅（0.4–1.6），所以永遠觸發不了。
        assert min(gains) > 0.2

    def test_report_exposes_the_base_rate(self, trace):
        report = trace.run(seed=11)
        assert 0.0 <= report["gain"]["below_low_base_rate"] <= 1.0
        # 沒有基準率，就分不清「翻轉的多半低增益」和「大部分樣本都低增益」。
        assert report["gain"]["low_gain_threshold"] == trace.LOW_GAIN


class TestVerdict:
    def _rows(self, gains, deltas):
        return [
            {"gain": gain, "margin_delta": delta, "phase_margin": delta}
            for gain, delta in zip(gains, deltas)
        ]

    def test_low_gain_losers_are_named(self, trace):
        rows = self._rows([0.1, 0.15, 0.9, 1.0], [-0.01, -0.02, 0.01, 0.02])
        assert trace._verdict(rows, [0, 1]) == "low-gain-samples-are-the-losers"

    def test_flips_outside_low_gain_are_not_blamed_on_gain(self, trace):
        rows = self._rows([0.9, 1.0, 1.4, 1.5], [-0.01, -0.02, 0.01, 0.02])
        assert trace._verdict(rows, [0, 1]) == "flips-not-explained-by-gain"

    def test_no_flips_says_nothing(self, trace):
        rows = self._rows([0.4, 1.0], [0.0, 0.0])
        assert trace._verdict(rows, []) == "no-flips"


class TestTraceReport:
    def test_no_target_row_is_left_at_zero(self, trace):
        # 這一條就是那個缺陷的回歸測試：修好之後，沒有任何 cue 的目標列是空的。
        report = trace.run(seed=11)
        assert report["phase_rows_at_zero"] == 0

    def test_report_names_its_own_cause(self, trace):
        report = trace.run(seed=11)
        assert report["verdict"] in {
            "low-gain-samples-are-the-losers",
            "flips-not-explained-by-gain",
            "no-flips",
        }
