"""Tests for the fixed scoring protocol (``scripts/al_downstream_protocol.py``).

The protocol exists so the mechanism question cannot be answered by picking a
regime after the fact. Only two things need pinning: the overall verdict must
refuse to conclude from a single informative regime, and the cell evaluation must
keep the arms gain-matched.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "al_downstream_protocol.py"


@pytest.fixture(scope="module")
def protocol():
    spec = importlib.util.spec_from_file_location("al_downstream_protocol_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["al_downstream_protocol_test"] = module
    spec.loader.exec_module(module)
    return module


def _cell(verdict, informative=True):
    return {"informative": informative, "cell": {"verdict": verdict}}


class TestOverallVerdict:
    def test_one_informative_regime_is_not_enough(self, protocol):
        cells = [_cell("phase-beats-matched-mean"), _cell("whatever", informative=False)]
        assert protocol.overall_verdict(cells) == "insufficient-informative-regimes"

    def test_same_direction_everywhere_is_a_claim(self, protocol):
        cells = [_cell("phase-beats-matched-mean"), _cell("phase-beats-matched-mean")]
        assert protocol.overall_verdict(cells) == "mechanism-benefit-consistent"

    def test_consistent_absence_of_benefit_is_also_a_claim(self, protocol):
        cells = [_cell("no-downstream-difference"), _cell("timing-does-not-matter-only-gain")]
        assert protocol.overall_verdict(cells) == "no-mechanism-benefit-consistent"

    def test_consistent_harm_is_its_own_claim(self, protocol):
        # 一致的負結果不能退化成「沒贏」，否則反例會被記成空白。
        cells = [_cell("phase-loses-to-matched-mean")] * 3
        assert protocol.overall_verdict(cells) == "mechanism-harm-consistent"

    def test_harm_counts_as_no_benefit_when_mixed(self, protocol):
        cells = [_cell("phase-loses-to-matched-mean"), _cell("no-downstream-difference")]
        assert protocol.overall_verdict(cells) == "no-mechanism-benefit-consistent"

    def test_opposite_directions_make_no_claim(self, protocol):
        cells = [_cell("phase-beats-matched-mean"), _cell("no-downstream-difference")]
        assert protocol.overall_verdict(cells) == "regime-dependent-no-claim"


class TestProtocolConstants:
    def test_readout_is_the_one_that_can_rank(self, protocol):
        assert protocol.READOUT == "potential"

    def test_calibration_seeds_do_not_leak_into_evaluation(self, protocol):
        # 共用種子等於先看答案再出題：難度校準會優待評估用的那幾個種子。
        assert set(protocol.CALIBRATION_SEEDS).isdisjoint(protocol.SEEDS)
        assert len(protocol.CALIBRATION_SEEDS) >= 3

    def test_regime_matrix_is_not_a_single_regime(self, protocol):
        assert len(protocol.EPOCHS_MATRIX) >= 2

    def test_there_is_more_than_one_task_family(self, protocol):
        # v3 的改動是增加獨立維度：只換 regime 不足以判斷機制。
        assert len(protocol.FAMILIES) >= 2

    def test_each_family_ladder_starts_easy(self, protocol):
        for steps in protocol.FAMILIES.values():
            sizes = [int(step["pairs"]) for step in steps]
            assert sizes == sorted(sizes)


class TestCell:
    def test_cell_keeps_the_arms_gain_matched(self, protocol):
        cell = protocol.evaluate_cell(
            "hard",
            {"step": {"pairs": 48, "noise_bits": 3, "shared": True}, "lr": 0.03},
            epochs=1,
        )
        assert cell["gain_matched"] is True
        means = {name: cell["arms"][name]["gain_mean"] for name in cell["arms"]}
        assert abs(means["phase"] - means["neutral"]) <= 0.05
        assert abs(means["shuffled"] - means["neutral"]) <= 0.05

    def test_cell_reports_every_arm(self, protocol):
        cell = protocol.evaluate_cell(
            "hard", {"step": {"pairs": 48, "noise_bits": 3, "shared": True}, "lr": 0.03}, epochs=1
        )
        assert set(cell["arms"]) == {"neutral", "phase", "shuffled"}


class TestSeedRobustness:
    """平均差要站得住：7/12 的「贏」是擲硬幣，不是機制。"""

    def test_sign_test_minimum_for_twelve_seeds(self, protocol):
        assert protocol.SIGN_TEST_MIN == 10

    def _wins(self, over_neutral, over_shuffled, seeds=12):
        return {
            "seeds": seeds,
            "phase_over_neutral_hit": over_neutral,
            "phase_over_shuffled_hit": over_shuffled,
        }

    def test_strong_claim_survives(self, protocol):
        verdict, downgrade = protocol._seed_robust("phase-beats-matched-mean", self._wins(11, 10))
        assert verdict == "phase-beats-matched-mean"
        assert downgrade is None

    def test_claim_on_a_coin_flip_is_downgraded(self, protocol):
        # 這就是 v7 hard ep5 的形狀：對 neutral 11/12，對 shuffled 7/12。
        verdict, downgrade = protocol._seed_robust("phase-beats-matched-mean", self._wins(11, 7))
        assert verdict == "timing-does-not-matter-only-gain"
        assert "7/12" in downgrade

    def test_weak_harm_is_not_called_harm(self, protocol):
        verdict, downgrade = protocol._seed_robust(protocol.HARM, self._wins(2, 5))
        assert verdict == "no-downstream-difference"
        assert "harm not seed-robust" in downgrade

    def test_consistent_harm_survives(self, protocol):
        verdict, _ = protocol._seed_robust(protocol.HARM, self._wins(1, 2))
        assert verdict == protocol.HARM


class TestCalibrationDoesNotRetunePerEpoch:
    def test_families_share_one_step_across_the_epochs_axis(self, protocol):
        """v6 的混淆：逐格校準讓 ep1 與 ep5 落在不同難度，epochs 軸就不只改訓練量。

        現在校正只回傳單一 step，矩陣套用它；測試釘住「校準函式不再吃 epochs 參數」。
        """
        import inspect

        params = inspect.signature(protocol.calibrate_family).parameters
        assert "epochs" not in params
        assert "epochs" not in params or "step" in params

    def test_each_ladder_has_a_rung_between_the_extremes(self, protocol):
        # 只有最易與最難兩級時，找不到「ep1 不低於 0.30、ep5 不高於 0.70」的組合。
        for family, steps in protocol.FAMILIES.items():
            assert len(steps) >= 3, family


class TestCalibrationMargin:
    """第一個合格的候選永遠貼著邊界，而三個校準種子的餘裕和噪音同量級。"""

    def test_margin_is_five_points(self, protocol):
        assert protocol.HIT_MARGIN == 0.05

    def test_centred_needs_headroom_on_every_epoch(self, protocol):
        assert protocol._is_centred({1: 0.36, 3: 0.45, 5: 0.60}) is True

    def test_boundary_adjacent_candidate_is_not_centred(self, protocol):
        # 就是 v8 選中的 0.306／0.333。
        assert protocol._is_centred({1: 0.306, 3: 0.361, 5: 0.583}) is False
        assert protocol._is_centred({1: 0.333, 3: 0.384, 5: 0.63}) is False

    def test_partial_measurement_is_not_centred(self, protocol):
        # 校準在中途爆掉就 break，剩下沒量到的格不能當成合格。
        assert protocol._is_centred({1: 0.5}) is False

    def test_many_to_one_ladder_has_a_centred_rung(self, protocol):
        rungs = protocol.FAMILIES["many_to_one"]
        assert any(rung.get("pairs") == 72 and rung.get("target_group") == 12 for rung in rungs)


class TestConfirmationSeeds:
    def test_three_seed_sets_are_pairwise_disjoint(self, protocol):
        scan = set(protocol.CALIBRATION_SEEDS)
        confirm = set(protocol.CONFIRMATION_SEEDS)
        evaluate = set(protocol.SEEDS)
        assert scan.isdisjoint(evaluate)
        assert confirm.isdisjoint(evaluate)
        assert confirm.isdisjoint(scan)

    def test_confirmation_uses_more_seeds_than_the_scan(self, protocol):
        # 掃描值偏樂觀 0.055 就是因為只有三個種子；確認要明顯更寬。
        assert len(protocol.CONFIRMATION_SEEDS) >= 2 * len(protocol.CALIBRATION_SEEDS)
