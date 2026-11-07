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


class TestHeldOutIsNotTrainingData:
    """根問題：`_train` 與 `_evaluate` 共用同一批 pair，所以分數是「記得快」不是「學會」。"""

    @pytest.fixture(scope="class")
    def downstream(self):
        return self._module()

    def _module(self):
        import importlib.util

        script = REPO_ROOT / "scripts" / "al_c_learn_downstream.py"
        spec = importlib.util.spec_from_file_location("al_downstream_test", script)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules["al_downstream_test"] = module
        spec.loader.exec_module(module)
        return module

    def test_heldout_cues_are_all_new(self, downstream):
        task = {"pairs": 48, "noise_bits": 3, "shared": True, "lr": 0.03, "threshold": 0.25}
        train = {tuple(cue) for cue, _ in downstream._pairs(task)}
        held = {tuple(cue) for cue, _ in downstream._heldout_pairs(task)}
        assert len(held) == 48
        assert train.isdisjoint(held)

    def test_heldout_keeps_the_label_set(self, downstream):
        task = {"pairs": 48, "noise_bits": 3, "shared": True, "lr": 0.03, "threshold": 0.25}
        train_targets = set(downstream._candidate_targets(downstream._pairs(task)))
        held_targets = {target for _, target in downstream._heldout_pairs(task)}
        assert held_targets <= train_targets

    def test_heldout_is_at_chance_for_a_trained_core(self, downstream):
        """釘住根缺陷本身：訓練到訓練集 1.0，沒訓過的 cue 仍是亂猜。

        這條測試不是在慶祝能力，是在防止有人把「訓練集命中率」講成「學會了」。
        """
        task = {"pairs": 48, "noise_bits": 3, "shared": True, "lr": 0.03, "threshold": 0.25}
        core = downstream._train([1.0] * 48, 11, task, 3)
        on_train = downstream._evaluate(core, task)["hit_rate"]
        off_train = downstream._evaluate(core, task, downstream._heldout_pairs(task))["hit_rate"]
        assert on_train > 0.9
        assert off_train <= 0.10


class TestStructuredTaskOffersRealHeldOut:
    """共用 feature token 才讓 held-out 有意義——但這個模型訓久了會壓成同分。"""

    @pytest.fixture(scope="class")
    def downstream(self):
        import importlib.util

        script = REPO_ROOT / "scripts" / "al_c_learn_downstream.py"
        spec = importlib.util.spec_from_file_location("al_downstream_structured_test", script)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules["al_downstream_structured_test"] = module
        spec.loader.exec_module(module)
        return module

    def test_feature_token_is_shared_between_train_and_heldout(self, downstream):
        task = downstream.TASKS["structured"]
        for cue, target in downstream._pairs(task):
            assert f"feat{target}" in cue
        for cue, target in downstream._heldout_pairs(task):
            assert f"feat{target}" in cue

    def test_one_epoch_transfers_to_unseen_cues(self, downstream):
        task = downstream.TASKS["structured"]
        core = downstream._train([1.0] * 48, 11, task, 1)
        on_train = downstream._evaluate(core, task)["hit_rate"]
        off_train = downstream._evaluate(core, task, downstream._heldout_pairs(task))["hit_rate"]
        assert on_train > 0.9
        assert off_train > 0.9

    def test_more_epochs_flatten_the_readout(self, downstream):
        """訓練更久會把所有 target 的電位壓成同分，top-1 崩掉——epochs 不是學習曲線。

        這是模型行為，不是測試環境問題；寫成測試是為了讓它不能被悄悄忽略。
        """
        task = downstream.TASKS["structured"]
        one = downstream._train([1.0] * 48, 11, task, 1)
        three = downstream._train([1.0] * 48 * 3, 11, task, 3)
        assert downstream._evaluate(one, task)["hit_rate"] > 0.9
        assert downstream._evaluate(three, task)["hit_rate"] <= 0.1


class TestReadoutIsWhereTheCollapseLives:
    """權重沒塌，是 16 步膜電位擴散把整個連通分量填平。"""

    @pytest.fixture(scope="class")
    def downstream(self):
        import importlib.util

        script = REPO_ROOT / "scripts" / "al_c_learn_downstream.py"
        spec = importlib.util.spec_from_file_location("al_downstream_readout_test", script)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules["al_downstream_readout_test"] = module
        spec.loader.exec_module(module)
        return module

    def test_direct_readout_survives_training_that_flattens_potential(self, downstream):
        task = downstream.TASKS["structured"]
        core = downstream._train([1.0] * 48 * 3, 11, task, 3)
        potential = downstream._evaluate(core, task)["hit_rate"]
        direct = downstream._evaluate(core, task, readout="direct")["hit_rate"]
        assert potential <= 0.1
        assert direct > 0.9

    def test_direct_readout_also_holds_on_unseen_cues(self, downstream):
        task = downstream.TASKS["structured"]
        core = downstream._train([1.0] * 48 * 5, 11, task, 5)
        held = downstream._heldout_pairs(task)
        potential = downstream._evaluate(core, task, held)["hit_rate"]
        direct = downstream._evaluate(core, task, held, readout="direct")["hit_rate"]
        assert potential <= 0.1
        assert direct > 0.9

    def test_direct_readout_ranks_the_target_from_direct_edges(self, downstream):
        task = downstream.TASKS["structured"]
        pairs = downstream._pairs(task)
        targets = downstream._candidate_targets(pairs)
        core = downstream._train([1.0] * 48 * 3, 11, task, 3)
        out = downstream._readouts._forward(core, {k: 1.0 for k in pairs[0][0]}, "direct")
        ranked = sorted(((out[label], label) for label in targets), reverse=True)
        assert ranked[0][1] == pairs[0][1]


class TestConflictTaskHasAMiddleBand:
    """舊任務只有唯一 token，命中率只能 1.0 或 0；衝突證據才有中段。"""

    @pytest.fixture(scope="class")
    def downstream(self):
        import importlib.util

        script = REPO_ROOT / "scripts" / "al_c_learn_downstream.py"
        spec = importlib.util.spec_from_file_location("al_downstream_conflict_test", script)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules["al_downstream_conflict_test"] = module
        spec.loader.exec_module(module)
        return module

    def test_no_cue_token_belongs_to_a_single_target(self, downstream):
        task = downstream.TASKS["conflict"]
        owners = {}
        for cue, target in downstream._pairs(task):
            for token in cue:
                owners.setdefault(token, set()).add(target)
        assert min(len(targets) for targets in owners.values()) >= 2

    def test_conflict_heldout_combines_seen_features(self, downstream):
        task = downstream.TASKS["conflict"]
        train = {tuple(cue) for cue, _ in downstream._pairs(task)}
        held = downstream._heldout_pairs(task)
        assert train.isdisjoint({tuple(cue) for cue, _ in held})
        seen = {token for cue, _ in downstream._pairs(task) for token in cue}
        assert all(token in seen for cue, _ in held for token in cue)

    def test_conflict_lands_in_the_middle_band(self, downstream):
        task = downstream.TASKS["conflict"]
        core = downstream._train([1.0] * 96, 11, task, 1)
        hit = downstream._evaluate(core, task, readout="direct")["hit_rate"]
        assert 0.2 < hit < 0.8, hit

    def test_conflict_transfers_to_unseen_combinations(self, downstream):
        task = downstream.TASKS["conflict"]
        core = downstream._train([1.0] * 96 * 5, 11, task, 5)
        on_train = downstream._evaluate(core, task, readout="direct")["hit_rate"]
        off_train = downstream._evaluate(
            core, task, downstream._heldout_pairs(task), readout="direct"
        )["hit_rate"]
        assert on_train > 0.3
        # held-out 與訓練集同步，差距不超過 0.2——這是組合證據，不是背誦。
        assert abs(on_train - off_train) < 0.2
