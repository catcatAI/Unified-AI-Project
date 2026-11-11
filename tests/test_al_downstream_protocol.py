"""Tests for the fixed scoring protocol (``scripts/al_downstream_protocol.py``).

The protocol exists so the mechanism question cannot be answered by picking a
regime after the fact. Only two things need pinning: the overall verdict must
refuse to conclude from a single informative regime, and the cell evaluation must
keep the arms gain-matched.
"""

from __future__ import annotations

import importlib.util
import math
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

    def test_sign_test_minimum_follows_the_seed_count(self, protocol):
        # 門檻由 n 導出：12 → 10（p≈0.019）、40 → 26（p≈0.040）。寫死任一個都會讓
        # 「加種子」悄悄放寬判詞。
        assert len(protocol.SEEDS) == 40
        assert protocol.SIGN_TEST_MIN == 26
        assert protocol._sign_test_minimum(12) == 10
        assert protocol.SIGN_TEST_MIN == protocol._sign_test_minimum(len(protocol.SEEDS))

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


class TestDetectableEffectSize:
    """「沒有差別」要說得出解析度：符號門檻在 12 個種子上能偵測到的最小差。"""

    def test_paired_stats_only_count_direction(self, protocol):
        rows = {
            "a": [{"h": 0.5}, {"h": 0.4}, {"h": 0.6}],
            "b": [{"h": 0.4}, {"h": 0.4}, {"h": 0.2}],
        }
        stats = protocol._paired_stats(rows, "a", "b", "h")
        assert stats["wins"] == 2
        assert stats["n"] == 3
        assert abs(stats["mean"] - 0.16667) < 1e-4

    def test_minimum_detectable_delta_matches_the_sign_gate(self, protocol):
        # σ=0.10、12 個種子、門檻 10/12：80% 檢定力需要 δ≈0.11。門檻要和 n 一起取——
        # 用 module 常數（現在是 26/40）配 n=12 是「要求 12 個種子裡 26 個同向」，必然 None。
        mde = protocol._min_detectable_delta(0.10, 12, protocol._sign_test_minimum(12))
        assert mde is not None
        assert 0.09 < mde < 0.14

    def test_more_seeds_can_detect_smaller_effects(self, protocol):
        few = protocol._min_detectable_delta(0.10, 12, protocol._sign_test_minimum(12))
        many = protocol._min_detectable_delta(0.10, 40, protocol._sign_test_minimum(40))
        assert few is not None and many is not None
        assert many < few / 2

    def test_no_spread_means_no_estimate(self, protocol):
        assert protocol._min_detectable_delta(0.0, 12, 10) is None


class TestLabelShuffleControl:
    """量具控制：輸入不變、標籤打亂。若仍拿中段，量到的就不是學習。"""

    def test_shuffle_is_much_worse_than_trained(self, protocol):
        control = protocol._label_shuffle_baseline("conflict", (0, 1), readout="direct")
        assert control["chance"] == 0.125
        # 打亂後模型把錯誤的對應學得很牢，真標籤永遠輸：比亂猜還低。
        assert control["train"] < control["chance"]
        assert control["heldout"] < control["chance"]

    def test_shuffle_control_reports_chance_for_each_family(self, protocol):
        for family, targets in (("conflict", 8), ("many_to_one", 24)):
            control = protocol._label_shuffle_baseline(family, (0,), readout="direct")
            assert control["chance"] == round(1.0 / targets, 3)


class TestSeedCountControlsTheGate:
    """種子可以加，但門檻必須跟著 n 走，否則判詞會悄悄變鬆。"""

    def test_gate_uses_the_reported_seed_count(self, protocol):
        base = {"phase_over_neutral_hit": 20, "phase_over_shuffled_hit": 20, "seeds": 40}
        verdict, downgrade = protocol._seed_robust("phase-beats-matched-mean", base)
        assert verdict == "timing-does-not-matter-only-gain"
        assert downgrade is not None and "need 26/40" in downgrade

        strong = {
            "phase_over_neutral_hit": 27,
            "phase_over_shuffled_hit": 27,
            "seeds": 40,
        }
        assert protocol._seed_robust("phase-beats-matched-mean", strong) == (
            "phase-beats-matched-mean",
            None,
        )

    def test_twelve_seeds_still_need_ten(self, protocol):
        weak = {"phase_over_neutral_hit": 8, "phase_over_shuffled_hit": 8, "seeds": 12}
        assert protocol._seed_robust("phase-beats-matched-mean", weak)[0] != (
            "phase-beats-matched-mean"
        )

    def test_calibration_seeds_cannot_be_reused(self, protocol):
        with pytest.raises(ValueError):
            protocol.run(readout="direct", seeds=(11, 23, 211), families=["conflict"])


class TestGainMatchingHasPower:
    """均值容差不可能失敗（排程剛好走完整週期），所以閘門必須驗分佈與順序。"""

    def test_mean_delta_is_exactly_zero_by_construction(self, protocol):
        gains = protocol._downstream._schedule(
            protocol._downstream.natural_period(), 96, step_per_period=96
        )
        match = protocol._gains_matched(gains, gains[::-1])
        # 實測 3.7e-5：均值不是精確 1.0，但任何 0.01 以上的容差都不會綁定。
        assert abs(match["mean_delta"]) < 1e-3
        assert abs(match["mean_delta"]) < protocol.GAIN_MATCH_TOL
        assert match["multiset_match"] is True

    def test_a_copy_is_not_a_shuffle(self, protocol):
        gains = protocol._downstream._schedule(
            protocol._downstream.natural_period(), 96, step_per_period=96
        )
        # 同一條排程當「打亂臂」等於兩臂相同：順序沒有不同，閘門必須擋下來。
        assert protocol._gains_matched(gains, gains)["order_differs"] is False

    def test_a_reversed_schedule_is_a_legal_shuffle(self, protocol):
        gains = protocol._downstream._schedule(
            protocol._downstream.natural_period(), 96, step_per_period=96
        )
        assert protocol._gains_matched(gains, gains[::-1])["order_differs"] is True

    def test_unequal_multisets_are_rejected(self, protocol):
        gains = [0.4, 1.0, 1.6]
        match = protocol._gains_matched(gains, [0.4, 1.0, 1.0])
        assert match["multiset_match"] is False


class TestHeldoutChanceBoundIsDerivedFromCount:
    """``2 / len(targets)`` 的係數 2 沒有來源，也不看 held-out 有幾條。"""

    def test_the_bound_tightens_as_heldout_grows(self):
        def bound(chance, pairs):
            return chance + 2 * math.sqrt(chance * (1 - chance) / pairs)

        assert bound(0.042, 96) < bound(0.042, 48)
        # 舊的平準門檻 0.0833 對 24 條 held-out 而言太嚴、對 400 條而言太鬆。
        assert bound(0.042, 24) > 2 * 0.042
        assert bound(0.042, 400) < 2 * 0.042

    def test_the_point_gain_of_a_top1_only_case_is_not_hidden(self, protocol):
        # hit-gain-without-margin-gain 算「機制沒有好處」，但 top-1 的移動要看得到。
        assert "hit-gain-without-margin-gain" in protocol.NO_BENEFIT
        # top-1 同時贏過兩個臂是詞彙裡沒有的格，不能自動歸進「沒好處」。
        assert "hit-gain-over-both-arms" not in protocol.NO_BENEFIT


class TestCalibrationFailureSaysWhichFailure:
    """``ladder-exhausted`` 同時蓋住「階梯不夠長」與「這一族沒有中段」兩件不同的事。"""

    @staticmethod
    def _trial(hits):
        return {"neutral_hit_by_epoch": {str(epoch): hit for epoch, hit in hits.items()}}

    def test_every_rung_on_the_ceiling_is_not_a_ladder_problem(self, protocol):
        trials = [self._trial({1: 1.0}), self._trial({1: 1.0})]
        assert protocol._exhaustion_reason(trials) == "task-at-ceiling"

    def test_the_reason_reads_int_keys_as_well_as_json_string_keys(self, protocol):
        # `calibrate_family` 回傳的是 int 鍵，存成 JSON 後變成字串。只認一種就會把
        # 天花板誤報成 ladder-exhausted（v21 第一次重跑就是這樣）。
        int_keys = [{"neutral_hit_by_epoch": {1: 1.0}}, {"neutral_hit_by_epoch": {1: 1.0}}]
        assert protocol._exhaustion_reason(int_keys) == "task-at-ceiling"

    def test_every_rung_on_the_floor_is_not_a_ladder_problem_either(self, protocol):
        trials = [self._trial({1: 0.0}), self._trial({1: 0.042})]
        assert protocol._exhaustion_reason(trials) == "task-at-floor"

    def test_a_rung_that_centres_then_saturates_is_a_ladder_problem(self, protocol):
        # structured 的 lr 0.01：ep1/ep3 都在中段，ep5 升到 0.806 → 換一個更長的階梯有意義。
        trials = [self._trial({1: 1.0}), self._trial({1: 0.583, 3: 0.583, 5: 0.806})]
        assert protocol._exhaustion_reason(trials) == "ladder-exhausted"

    def test_no_measurements_at_all_is_not_a_ceiling_claim(self, protocol):
        assert protocol._exhaustion_reason([]) == "ladder-exhausted"

    def test_the_reason_reaches_the_report(self, protocol, monkeypatch):
        monkeypatch.setattr(
            protocol,
            "calibrate_family",
            lambda family, readout=None: {"informative": False, "reason": "task-at-ceiling"},
        )
        control = {"train": 0.02, "heldout": 0.02, "chance": 0.02}
        monkeypatch.setattr(protocol, "_label_shuffle_baseline", lambda *a, **k: dict(control))
        cells = protocol.run(families=("hard",))["cells"]
        assert {cell["reason"] for cell in cells} == {"task-at-ceiling"}
        # 沒有可下結論的格 → 整體不能給判詞。
        assert protocol.overall_verdict(cells) == "insufficient-informative-regimes"


class TestUnmeasuredFamiliesAreNamed:
    """量不到的族必須具名登記，並且只能變少。

    WHY：v21 之前，`hard`／`easy`／`structured` 三族從未產出可下結論的格，它們就只是
    「沒有 cell」——報告上看起來跟「量過、沒差」一樣。未爆彈是這樣留下來的：訓練後
    才發現某一族其實從頭到尾沒被量到。
    """

    def test_every_registered_family_exists(self, protocol):
        assert set(protocol.UNMEASURED_FAMILIES) <= set(protocol.FAMILIES)

    def test_registry_is_a_ratchet(self, protocol):
        # 預算在 scripts/al_unmeasured_budget.txt：只能往下（族真的被量到了就下調）。
        assert len(protocol.UNMEASURED_FAMILIES) == protocol._unmeasured_budget()

    def test_each_registered_family_says_why(self, protocol):
        for reason in protocol.UNMEASURED_FAMILIES.values():
            assert len(reason) > 20, "「量不到」必須寫出結構原因，不能只寫『測不出來』"

    def test_an_unregistered_unmeasurable_family_blocks_the_verdict(self, protocol):
        cells = [_cell("phase-beats-matched-mean") for _ in range(3)]
        assert protocol.overall_verdict(cells, ["brand-new-family"]) == "unmeasured-unregistered"

    def test_the_report_names_each_unmeasured_family(self, protocol, monkeypatch):
        monkeypatch.setattr(
            protocol,
            "calibrate_family",
            lambda family, readout=None: {"informative": False, "reason": "task-at-ceiling"},
        )
        monkeypatch.setattr(
            protocol,
            "_label_shuffle_baseline",
            lambda *a, **k: {"train": 0.02, "heldout": 0.02, "chance": 0.02},
        )
        report = protocol.run(families=("structured", "conflict"))

        assert report["unmeasured"]["structured"].startswith("ep1 完全遷移")
        # conflict 沒登記，卻量不到 → 不得假裝整體有結論
        assert report["unregistered_unmeasured"] == ["conflict"]
        assert report["verdict"] == "unmeasured-unregistered"
        # 兩族都量不到 → 沒有「登記了卻量到」的過期項。
        assert report["stale_unmeasured"] == []

    def test_a_registered_family_that_is_measured_is_stale(self, protocol):
        """反方向也要響：登記為量不到、但每一格都量到了＝登記簿過期。

        v23 就是這樣抓到 `hard` 的：12 個種子下它看起來量不到（ep1 neutral 0.333、sd 0），
        40 個種子下三格全部可下結論。只擋一個方向的登記簿會一直長大，然後冒充「未知」。
        """
        cells = [_cell("no-downstream-difference") for _ in range(3)]
        for cell in cells:
            cell["family"] = "hard"
        assert protocol._stale_registrations(cells, {"hard": "x"}) == ["hard"]
        # 只要還有一格量不到，就不是過期——那是真的量不到。
        cells[1]["informative"] = False
        cells[1]["reason"] = "task-at-ceiling"
        assert protocol._stale_registrations(cells, {"hard": "x"}) == []
        # 沒跑到的族（沒有 cell）不算過期，也不算漏登記：這次沒量它。
        assert protocol._stale_registrations(cells[:0], {"hard": "x"}) == []


class TestWithinCueProbe:
    """同一個 cue 底下兩個 target 競爭：唯一對分佈敏感、又不受讀出尺度影響的量法。

    top-1 只能問「這批權重最像哪個 target」，而強弱住的是「同一個 cue 內部相對誰大」——後者在
    任何正數縮放下都不變（歸一化也保得住），所以這個量表在三個讀出下都應該拿到同一個答案。
    """

    def test_design_gives_every_cue_two_distinct_targets(self, protocol):
        design = protocol._ambiguous_design()
        assert len(design) == protocol.AMBIGUOUS_CUES
        strong = [s for _, s, _ in design]
        weak = [w for _, _, w in design]
        assert len(set(strong + weak)) == 2 * len(design)
        for _, hi, lo in design:
            assert hi != lo

    def test_stream_gives_every_pair_the_same_number_of_visits(self, protocol):
        """等次數是這個量法的前提：不然強弱有一部分來自「出現得多」，四個臂都靠它得分。"""
        visits = protocol._ambiguous_stream(6, seed=3, epochs=4)
        assert len(visits) == 6 * 4
        for index in range(6):
            assert visits.count(index) == 4

    def test_report_is_paired_against_the_shuffled_control(self, protocol):
        report = protocol.within_cue_probe(readout="direct", seeds=(1, 2), epochs=3)
        assert report["verdict"] in {
            "within-cue-strength-anchored",
            "within-cue-strength-not-anchored",
        }
        assert set(report["arms"]) == {"flat", "graded", "matched", "speed"}
        assert report["cues"] == protocol.AMBIGUOUS_CUES
        assert 0.0 <= report["arms"]["graded"]["win_rate_mean"] <= 1.0
        assert report["sign_test_min"] == protocol._sign_test_minimum(2)

    def test_unknown_readout_is_rejected(self, protocol):
        with pytest.raises(AssertionError):
            protocol.within_cue_probe(readout="softmax", seeds=(1,), epochs=1)

    def test_combined_verdict_cannot_hide_an_unanchored_probe(self, protocol):
        """「定點有帶強弱、但綁錯關聯」不能被跨族判詞吃掉。"""
        probes = [
            {
                "weights_verdict": "fixed-point-carries-strength",
                "ordering_verdict": "ordering-carries-across-tiers",
                "readout_verdict": "readout-better",
            }
        ]
        loose = {"verdict": "within-cue-strength-not-anchored"}
        verdict = protocol._strength_verdict(probes, loose)
        assert verdict.endswith("within-cue-strength-not-anchored")
        assert "anchored" not in verdict.replace("not-anchored", "")

    def test_probe_verdict_is_named_even_without_a_ladder_probe(self, protocol):
        assert (
            protocol._strength_verdict([], {"verdict": "within-cue-strength-anchored"})
            == "no-strength-probe/within-cue-strength-anchored"
        )
        # 沒跑就不能用空白冒充「沒問題」。
        assert protocol._strength_verdict([], None) == "no-strength-probe"


class TestNormalizedReadout:
    """`normalized` 讀出：把來源列（cue token）歸一化成對 target 的分佈。

    它存在的理由是可檢定的：定點用權重大小編碼頻率，所以罕見配對的絕對權重天生小，任何直接
    比大小的讀出都會把「罕見」讀成「證據弱」。歸一化後讀出對頻率尺度不敏感——所以「分級
    掉一半」是尺度問題而不是學錯問題。但方向很容易寫反（除到 target 的列總量就完全沒用了），
    所以下面兩條把它釘死。
    """

    @staticmethod
    def _trained(protocol):
        readouts = protocol._downstream._readouts
        core = protocol._downstream.TensorSNNCore(threshold=0.25, timesteps=readouts.TIMESTEPS)
        for i in range(3):
            core.hebbian_update(
                {f"c{i}": 1.0, "n0": 1.0},
                {f"t{i}": 1.0},
                lr=0.2,
                target_strength=0.35,
            )
        return core, readouts

    def test_it_normalizes_the_source_row_not_the_target_column(self, protocol):
        core, readouts = self._trained(protocol)
        V = core.vocab_size
        W = core._W[:V, :V]
        row_sums = W.sum(dim=1)
        inputs = {k: 1.0 for k in ("c1", "n0")}

        got = readouts._forward(core, inputs, "normalized")
        expected = {}
        for target in ("t0", "t1", "t2"):
            j = core._key_to_idx[target]
            expected[target] = sum(
                float(W[core._key_to_idx[key], j]) / float(row_sums[core._key_to_idx[key]])
                for key in inputs
                if float(row_sums[core._key_to_idx[key]]) > 0
            )

        for target, value in expected.items():
            assert got.get(target, 0.0) == pytest.approx(value, abs=1e-5), target

    def test_rescaling_a_row_does_not_change_what_is_read(self, protocol):
        """頻率不變性：每個 cue 名下的權重整體多大不重要，重要的是分佈在哪個 target。"""
        core, readouts = self._trained(protocol)
        V = core.vocab_size
        W = core._W[:V, :V].clone()
        inputs = {k: 1.0 for k in ("c1", "n0")}
        baseline = readouts._forward(core, inputs, "normalized")
        direct = readouts._forward(core, inputs, "direct")

        # 每一列乘上不同的正數：等於模擬「這些 cue 出現得比較多／比較少」。
        for i in range(V):
            core._W[i, :V] = W[i] * (1.0 + i % 7)
        rescaled = readouts._forward(core, inputs, "normalized")
        direct_rescaled = readouts._forward(core, inputs, "direct")

        for key, value in baseline.items():
            assert rescaled[key] == pytest.approx(value, abs=1e-5), key
        # 對照：直接比大小的讀出會被這個縮放整批改掉，所以它才看不到「罕見」之後的東西。
        assert any(abs(direct_rescaled[key] - value) > 1e-4 for key, value in direct.items())


class TestStrengthProbe:
    """G1（定點 = target_strength·gate）在 12 格階梯上結構上量不到，這裡釘住探針本身。

    階梯每一筆樣本都是 `{key: 1.0}`，`gate` 恆為 1，所以不管規則怎麼改，所有配對都停在同一個
    定點。要有東西可量，輸入端必須真的帶強弱——探針用「出現次數」分層（真實語料的共現頻率就是
    這樣分佈的），四個臂共用同一條訓練流，只改信心怎麼進 ``hebbian_update``。
    """

    @staticmethod
    def _task(protocol, pairs=8):
        return {"pairs": pairs, "noise_bits": 2, "shared": False, "lr": 0.05, "threshold": 0.25}

    def test_spearman_extremes_and_no_spread(self, protocol):
        assert protocol._spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
        assert protocol._spearman([1, 2, 3, 4], [40, 30, 20, 10]) == pytest.approx(-1.0)
        # 全平不是「完美相關」：那種情況該回 None，讓報表說「量不到」而不是說 1.0。
        assert protocol._spearman([1, 1, 1, 1], [1, 2, 3, 4]) is None

    def test_tier_assignment_is_fixed_not_resampled(self, protocol):
        pairs = [(f"c{i}", "t00") for i in range(10)]
        tiers = protocol._tier_of_pairs(pairs)

        assert sorted(set(tiers)) == [1, 3]
        assert tiers.count(3) == 5
        # 固定種子：哪個配對是強層不能每次跑都不一樣，否則跨臂比較會混到抽樣差異。
        assert tiers == protocol._tier_of_pairs(pairs)

    def test_the_stream_repeats_each_pair_by_its_tier(self, protocol):
        tiers = [3, 1, 1]
        stream = protocol._strength_stream([("c", "t")] * 3, tiers, seed=1, epochs=2)

        assert len(stream) == 2 * sum(tiers)
        for index, tier in enumerate(tiers):
            assert stream.count(index) == 2 * tier

    def test_the_fixed_point_carries_the_tier_and_the_flat_arm_does_not(self, protocol):
        """跑到接近定點才分得開：flat 的弱層只是 decay 不平衡，graded 的弱層停在 T·gate。"""
        task = self._task(protocol)
        pairs = protocol._downstream._pairs(task)
        tiers = protocol._tier_of_pairs(pairs)
        stream = protocol._strength_stream(pairs, tiers, seed=11, epochs=40)
        conf = [tiers[i] / float(max(protocol.STRENGTH_TIERS)) for i in stream]

        flat = protocol._run_strength_arm(
            task, pairs, tiers, stream, [1.0] * len(stream), 11, "flat"
        )
        graded = protocol._run_strength_arm(task, pairs, tiers, stream, conf, 11, "graded")

        assert graded["weight_weak"] < flat["weight_weak"] * 0.8
        assert graded["tier_gap"] > flat["tier_gap"]

    def test_equilibrium_reports_the_ratio_and_a_verdict(self, protocol):
        task = self._task(protocol)
        calibration = {
            "step": {k: task[k] for k in ("pairs", "noise_bits", "shared")},
            "lr": task["lr"],
        }

        report = protocol.strength_equilibrium("easy", calibration, seeds=(11, 23, 37), epochs=20)

        assert report["verdict"] in {"fixed-point-carries-strength", "fixed-point-inert"}
        assert (
            report["arms"]["graded"]["weak_over_strong_mean"]
            < report["arms"]["flat"]["weak_over_strong_mean"]
        )
        assert report["graded_below_flat"] == report["seeds"]

    def test_the_probe_records_which_readout_produced_the_numbers(self, protocol):
        """讀出是待測變因之一，所以報告必須帶上是哪一個——不然兩份數字分不出差在讀出。

        v24 的兩難就是「讀出有訊號的區域還沒走到定點、定點看得見的區域讀出已經飽和」，
        換讀出（``potential`` → ``direct``）若不留痕，這兩個結論會互相冒充。
        """
        task = self._task(protocol)
        calibration = {
            "step": {k: task[k] for k in ("pairs", "noise_bits", "shared")},
            "lr": task["lr"],
        }

        probe = protocol.strength_probe(
            "easy", calibration, readout="direct", seeds=(11, 23), epochs=1
        )

        assert probe["readout"] == "direct"
        # 預設沒指定時仍是 potential：既有報告要能逐位重現。
        default = protocol.strength_probe("easy", calibration, seeds=(11,), epochs=1)
        assert default["readout"] == protocol.READOUT == "potential"

    def test_the_readout_cannot_change_the_weights(self, protocol):
        """不變量：讀出只決定「怎麼看」，不得影響「學到什麼」。

        這條會被試探出來：換讀出必須重跑校準，而校準會挑不同的 ``lr``／``step``，於是「讀出
        差異」很容易混進「任務參數差異」。把權重釘死，就分得出哪一部分真的是讀出造成的。
        """
        task = self._task(protocol)
        pairs = protocol._downstream._pairs(task)
        tiers = protocol._tier_of_pairs(pairs)
        stream = protocol._strength_stream(pairs, tiers, seed=11, epochs=2)
        conf = [tiers[i] / float(max(protocol.STRENGTH_TIERS)) for i in stream]

        potential = protocol._run_strength_arm(
            task, pairs, tiers, stream, conf, 11, "graded", readout="potential"
        )
        direct = protocol._run_strength_arm(
            task, pairs, tiers, stream, conf, 11, "graded", readout="direct"
        )

        for key in ("weight_strong", "weight_weak", "tier_gap", "spearman", "distinct_levels"):
            assert potential[key] == direct[key], key
        assert potential["readout"] == "potential" and direct["readout"] == "direct"

    def test_unknown_readout_is_rejected_instead_of_silently_defaulting(self, protocol):
        task = self._task(protocol)
        calibration = {
            "step": {k: task[k] for k in ("pairs", "noise_bits", "shared")},
            "lr": task["lr"],
        }

        with pytest.raises(AssertionError, match="unknown readout"):
            protocol.strength_probe(
                "easy", calibration, readout="spike_count", seeds=(11,), epochs=1
            )

    def test_equilibrium_answers_the_readout_question_at_the_fixed_point(self, protocol):
        """定點區的 top-1 是「讀出飽和」假設的拷問：``potential`` 下全 0，換讀出才有內容。"""
        task = self._task(protocol)
        calibration = {
            "step": {k: task[k] for k in ("pairs", "noise_bits", "shared")},
            "lr": task["lr"],
        }

        report = protocol.strength_equilibrium(
            "easy", calibration, seeds=(11, 23, 37), epochs=20, readout="direct"
        )

        assert report["readout"] == "direct"
        assert report["readout_verdict"] in {
            "readout-better",
            "readout-worse",
            "readout-no-difference",
        }
        assert (
            report["graded_over_matched_hit"] + report["graded_under_matched_hit"]
            <= report["seeds"]
        )
        # 每個臂都有定點區的命中率，即使它是 0.000（「量到 0」與「沒量」要分得開）。
        for arm in ("flat", "graded", "matched", "speed"):
            assert 0.0 <= report["arms"][arm]["hit_rate_mean"] <= 1.0

    def test_equilibrium_refuses_calibration_seeds(self, protocol):
        task = self._task(protocol)
        calibration = {
            "step": {k: task[k] for k in ("pairs", "noise_bits", "shared")},
            "lr": task["lr"],
        }

        with pytest.raises(ValueError, match="calibration seeds"):
            protocol.strength_equilibrium("easy", calibration, seeds=protocol.CALIBRATION_SEEDS)

    @pytest.mark.parametrize(
        "better, worse, expected",
        [
            # 40 個種子 ⇒ need 26：只有「同向且超過門檻」才算有方向。
            (40, 0, "readout-better"),
            (7, 27, "readout-worse"),
            (20, 19, "readout-no-difference"),  # 望遠鏡兩端都不夠，不能報方向
            (13, 20, "readout-no-difference"),
            # 兩個方向都過門檻（不可能同時發生，但別讓程式默默選一邊）
            (30, 30, "readout-no-difference"),
        ],
    )
    def test_readout_direction_needs_a_sign_test(self, protocol, better, worse, expected):
        need = protocol._sign_test_minimum(40)
        assert need == 26
        assert protocol._readout_verdict(better, worse, need) == expected


class TestWeightAttribution:
    """權重比量具讀的是誰的格子——沒有這一格，判詞就分不出「模型不帶強弱」與「量具把十個寫入者平均掉」。"""

    def test_a_family_with_one_pair_per_target_is_fully_attributable(self, protocol):
        task = dict(protocol._downstream.TASKS["hard"])
        pairs = protocol._downstream._pairs(task)
        attribution = protocol._attribution(pairs, protocol._tier_of_pairs(pairs))

        assert attribution["single_tier_fraction"] == 1.0
        assert attribution["writers_per_cell"] == 1.0

    def test_a_family_that_shares_a_target_pins_the_ratio_near_one(self, protocol):
        """96 個 cue 共用 8 個 target：每個格子平均十個寫入者，兩層各佔一半。

        那種格子讀出來的比例不可能反映 tier，所以那一族的 ``fixed-point-inert`` 不是對模型的
        宣稱，是量具的產物。
        """
        task = dict(protocol._downstream.TASKS["conflict"])
        pairs = protocol._downstream._pairs(task)
        attribution = protocol._attribution(pairs, protocol._tier_of_pairs(pairs))

        assert attribution["single_tier_fraction"] < 0.1
        assert attribution["writers_per_cell"] > 5

    def test_a_verdict_must_carry_its_contamination(self, protocol):
        clean = {"single_tier_fraction": 1.0, "writers_per_cell": 1.0}
        mixed = {"single_tier_fraction": 0.05, "writers_per_cell": 10.4}

        assert protocol._caveated("fixed-point-inert", clean) == "fixed-point-inert"
        assert (
            protocol._caveated("fixed-point-inert", mixed)
            == "fixed-point-inert (cells-shared 0.05)"
        )

    def test_the_caveat_cannot_be_laundered_by_the_cross_family_verdict(self, protocol):
        """混合族的結論進到跨族判詞後，仍然看得出它是混合的。"""
        probes = [
            {
                "weights_verdict": "fixed-point-inert (cells-shared 0.05)",
                "ordering_verdict": "ordering-not-separated-from-distribution",
                "readout_verdict": "readout-no-difference",
            }
        ]

        verdict = protocol._strength_verdict(probes)

        assert "cells-shared 0.05" in verdict
        assert "fixed-point-carries-strength" not in verdict


class TestRankCredit:
    """§46–§48 的三種讀出都只看勝負或絕對尺度；名次信用是唯一能說「差一點」的既有量具。

    它自己也會說謊，而且撒謊的方式跟 §50 同型：在前提不成立的地方講話。這裡把兩道前提釘住。
    """

    def test_credit_is_one_over_rank(self, protocol):
        out = {"t_a": 5.0, "t_b": 3.0, "t_c": 1.0}

        assert protocol._rank_credit(out, ["t_a", "t_b", "t_c"], "t_a") == 1.0
        assert protocol._rank_credit(out, ["t_a", "t_b", "t_c"], "t_b") == pytest.approx(0.5)
        assert protocol._rank_credit(out, ["t_a", "t_b", "t_c"], "t_c") == pytest.approx(1 / 3)

    def test_never_scored_target_earns_nothing(self, protocol):
        assert protocol._rank_credit({"t_a": 1.0}, ["t_a", "t_b"], "t_b") == 0.0

    def test_a_tie_counts_as_beating_us(self, protocol):
        # 並列被當成證據會讓「什麼都沒學」看起來像有排序，所以保守處理。
        out = {"t_a": 2.0, "t_b": 2.0}

        assert protocol._rank_credit(out, ["t_a", "t_b"], "t_a") == pytest.approx(0.5)

    def test_averaging_over_both_tiers_punishes_grading_by_construction(self, protocol):
        """ratchet：全體平均會讓「把弱層壓低」的臂看起來比較差，所以判詞不准用它。

        這條測試就是在把那個陷阱寫成不變量——`graded` 的強層若排得更前、弱層排得更後，
        平均可以是負的。判詞因此只看強層。
        """
        strong_tier, weak_tier = max(protocol.STRENGTH_TIERS), min(protocol.STRENGTH_TIERS)
        graded = {strong_tier: [1.0, 1.0], weak_tier: [0.125, 0.125]}
        flat = {strong_tier: [0.9, 0.9], weak_tier: [0.6, 0.6]}

        def mean(per_tier):
            values = [v for tier in per_tier for v in per_tier[tier]]
            return sum(values) / len(values)

        assert mean(graded) < mean(flat)  # 平均看起來「分級較差」
        assert sum(graded[strong_tier]) > sum(flat[strong_tier])  # 但強層其實較好

    def test_both_arms_must_name_the_right_answer(self, protocol):
        """只有一邊點得出答案時，另一邊的名次只是「所有東西都贏過我」，不是排序資訊。"""
        assert protocol._rank_interpretable(0.42, 0.46) is True
        assert protocol._rank_interpretable(0.0, 0.0) is False
        assert protocol._rank_interpretable(0.0, 0.203) is False

    def test_the_verdict_refuses_to_read_a_dead_readout(self, protocol):
        # 四臂 top-1 全 0＝讀出連正確 target 都點不出來，名次在那裡只是雜訊排列。
        assert protocol._rank_verdict(40, 0, 26, interpretable=False) == (
            "rank-credit-readout-degenerate"
        )
        assert protocol._rank_verdict(40, 0, 26, interpretable=True) == "rank-credit-favours-graded"
        assert protocol._rank_verdict(0, 40, 26) == "rank-credit-favours-matched"
        assert protocol._rank_verdict(14, 25, 26) == "rank-credit-no-difference"

    def test_the_rank_verdict_joins_the_cross_family_verdict_only_when_measured(self, protocol):
        base = {
            "weights_verdict": "fixed-point-carries-strength",
            "ordering_verdict": "ordering-carries-across-tiers",
            "readout_verdict": "readout-better",
        }
        unmeasured = protocol._strength_verdict([dict(base)])
        measured = protocol._strength_verdict(
            [dict(base, rank_verdict="rank-credit-no-difference")]
        )

        # 沒跑就不能用空白冒充「沒問題」：句子長度本身是證據。
        assert unmeasured.count("/") == 2
        assert measured.endswith("/rank-credit-no-difference")
