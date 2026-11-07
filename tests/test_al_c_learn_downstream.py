"""Tests for the downstream experiment (``scripts/al_c_learn_downstream.py``).

Two things are worth pinning: the verdict must be able to say "the timing matters",
"only the total gain mattered" and "no difference at all", and the run itself must
keep the three arms gain-matched -- otherwise the comparison silently becomes about
how much was learned instead of when.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "al_c_learn_downstream.py"


@pytest.fixture(scope="module")
def gate():
    spec = importlib.util.spec_from_file_location("al_c_learn_downstream_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["al_c_learn_downstream_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report(gate):
    return gate.run(seeds=(11, 23, 37))


def _rows(phase, neutral, shuffled):
    return {
        "phase": [{"margin": m, "hit_rate": 0.5} for m in phase],
        "neutral": [{"margin": m, "hit_rate": 0.5} for m in neutral],
        "shuffled": [{"margin": m, "hit_rate": 0.5} for m in shuffled],
    }


class TestVerdict:
    def test_phase_winning_both_arms_counts(self, gate):
        rows = _rows([0.30, 0.31, 0.29], [0.10, 0.11, 0.10], [0.09, 0.10, 0.11])
        assert gate._verdict(rows) == "phase-beats-matched-mean"

    def test_winning_neutral_but_not_shuffled_is_about_gain(self, gate):
        rows = _rows([0.30, 0.31, 0.29], [0.10, 0.11, 0.10], [0.30, 0.29, 0.31])
        assert gate._verdict(rows) == "timing-does-not-matter-only-gain"

    def test_margin_gain_with_worse_top1_is_not_a_win(self, gate):
        rows = {
            "phase": [{"margin": 0.30, "hit_rate": 0.45}],
            "neutral": [{"margin": 0.10, "hit_rate": 0.50}],
            "shuffled": [{"margin": 0.09, "hit_rate": 0.50}],
        }
        assert gate._verdict(rows) == "margin-gain-without-hit-gain"

    def test_a_clear_loss_is_reported_as_a_loss(self, gate):
        # phase 兩項都明顯更差、且多數種子同時輸給兩個臂：這是負結果，不是「沒差」。
        rows = {
            "phase": [{"margin": -0.10, "hit_rate": 0.20}] * 3,
            "neutral": [{"margin": 0.10, "hit_rate": 0.55}] * 3,
            "shuffled": [{"margin": 0.10, "hit_rate": 0.55}] * 3,
        }
        assert gate._verdict(rows) == "phase-loses-to-matched-mean"

    def test_a_small_deficit_stays_a_non_result(self, gate):
        rows = {
            "phase": [{"margin": 0.10, "hit_rate": 0.50}] * 3,
            "neutral": [{"margin": 0.10, "hit_rate": 0.50}, {"margin": 0.30, "hit_rate": 0.50}]
            + [{"margin": 0.10, "hit_rate": 0.50}],
            "shuffled": [{"margin": 0.10, "hit_rate": 0.50}] * 3,
        }
        assert gate._verdict(rows) == "no-downstream-difference"

    def test_no_separation_is_reported_as_none(self, gate):
        rows = _rows([0.10, 0.11, 0.10], [0.10, 0.11, 0.10], [0.10, 0.11, 0.10])
        assert gate._verdict(rows) == "no-downstream-difference"


class TestArms:
    def test_the_three_arms_are_gain_matched(self, report):
        arms = report["arms"]
        assert abs(arms["phase"]["gain_mean"] - arms["neutral"]["gain_mean"]) <= 0.05
        assert abs(arms["shuffled"]["gain_mean"] - arms["neutral"]["gain_mean"]) <= 0.05
        assert report["gain_matched"] is True

    def test_shuffled_reuses_the_phase_gain_multiset(self, report):
        # 打亂只換順序：兩臂的平均增益必須完全相同，否則不是同一個實驗。
        assert report["arms"]["shuffled"]["gain_mean"] == report["arms"]["phase"]["gain_mean"]

    def test_every_arm_produces_a_margin_per_seed(self, report):
        for name in ("neutral", "phase", "shuffled"):
            assert len(report["per_seed_margin"][name]) == len(report["seeds"])


class TestSchedule:
    """調制頻率必須與 epochs 無關，否則「訓練量」與「頻率」是同一個開關。"""

    def test_step_per_period_fixes_the_rate(self, gate):
        period = gate.natural_period()
        one = gate._schedule(period, 48, step_per_period=48)
        five = gate._schedule(period, 48 * 5, step_per_period=48)
        # 同樣的每樣本速度：每一輪都走完一個週期（容許極限環的微量漂移）。
        for cycle in range(5):
            assert five[48 * cycle : 48 * (cycle + 1)] == pytest.approx(one, abs=0.02)
        # 5 輪是同一個週期重複 5 次，不是把一個週期拉長成 5 倍。
        stretched = gate._schedule(period, 48 * 5)
        assert stretched[48:96] != pytest.approx(one, abs=0.02)

    def test_default_still_stretches_one_period_over_the_whole_run(self, gate):
        one = gate._schedule(6.0, 48)
        five = gate._schedule(6.0, 48 * 5)
        assert five[:48] != pytest.approx(one)


class TestScoring:
    """候選集必須由目標 label 決定；用 pair 索引拼字串會把命中率截半。"""

    def test_a_label_is_never_its_own_rival(self, gate):
        margin, hit = gate._score({"t00": 0.5, "t01": 0.1}, ["t00", "t01"], "t00")
        assert hit is True
        assert margin == pytest.approx(0.4)

    def test_missing_labels_are_not_rivals(self, gate):
        # 沒學到的 label 不在 out 裡，不該被當成 0 分的對手而讓 margin 虛胖。
        margin, hit = gate._score({"t00": 0.5}, ["t00", "t01"], "t00")
        assert hit is False
        assert margin == 0.0

    def test_many_to_one_can_score_every_pair(self, gate, monkeypatch):
        # 24 個 label、48 個 pair：舊寫法讓索引 >= 24 的 pair rivals 全空，
        # 命中率被硬性截在 0.5；正確的評分要能在同樣權重上拿到 1.0。
        task = dict(gate.TASKS["many_to_one"])
        pairs = gate._pairs(task)
        targets = gate._candidate_targets(pairs)
        assert len(pairs) == 48 and len(targets) == 24
        wanted = {tuple(inputs): target for inputs, target in pairs}

        def perfect(core, inputs, readout):
            assert readout == "potential"
            target = wanted[tuple(inputs)]
            return {label: 1.0 for label in targets} | {target: 2.0}

        monkeypatch.setattr(gate._readouts, "_forward", perfect)
        report = gate._evaluate(None, task)
        assert report["hit_rate"] == 1.0
        assert report["margin"] == pytest.approx(1.0)


class TestHeldoutIsCheckedByContent:
    """舊檢查用 ``id()``，兩邊是不同物件，永遠不會相等——那道斷言不可能失敗。"""

    def test_a_reused_cue_is_caught(self, gate):
        train = [(["cue00", "n1"], "t00"), (["cue01", "n2"], "t01")]
        held = [(["cue01", "n2"], "t01")]
        with pytest.raises(AssertionError, match="重疊"):
            gate._assert_disjoint(train, held)

    def test_the_old_id_check_would_have_passed_here(self, gate):
        # 同一個「內容」但是新物件：id() 不同，內容相同。這正是原斷言漏掉的情形。
        train = [(["cue00"], "t00")]
        held = [(["cue00"], "t00")]
        assert not (set(id(p) for p in held) & set(id(p) for p in train))
        with pytest.raises(AssertionError):
            gate._assert_disjoint(train, held)

    def test_disjoint_cues_pass(self, gate):
        gate._assert_disjoint([(["cue00"], "t00")], [(["cue01"], "t00")])

    @pytest.mark.parametrize("family", ["easy", "hard", "conflict", "structured", "many_to_one"])
    def test_every_real_family_passes_the_check(self, gate, family):
        task = gate.TASKS[family]
        gate._assert_disjoint(gate._pairs(task), gate._heldout_pairs(task))


class TestTop1GainWithoutMarginGain:
    """margin 幾乎不動時，top-1 仍可能大幅移動——只判 margin 會寫成「沒有差別」。"""

    def test_top1_gain_alone_is_not_called_no_difference(self, gate):
        rows = {
            "phase": [{"margin": 0.100, "hit_rate": 0.70}] * 5,
            "neutral": [{"margin": 0.101, "hit_rate": 0.52}] * 5,
            # shuffled 更高：好處贏得過 neutral，但贏不過同散佈的隨機順序。
            "shuffled": [{"margin": 0.102, "hit_rate": 0.75}] * 5,
        }
        assert gate._verdict(rows) == "hit-gain-without-margin-gain"

    def test_top1_gain_over_both_arms_is_flagged_for_a_human(self, gate):
        rows = {
            "phase": [{"margin": 0.100, "hit_rate": 0.70}] * 5,
            "neutral": [{"margin": 0.101, "hit_rate": 0.52}] * 5,
            "shuffled": [{"margin": 0.102, "hit_rate": 0.60}] * 5,
        }
        assert gate._verdict(rows) == "hit-gain-over-both-arms"

    def test_a_minority_of_seeds_gaining_is_not_enough(self, gate):
        rows = {
            "phase": [
                {"margin": 0.100, "hit_rate": 0.90},
                {"margin": 0.100, "hit_rate": 0.30},
                {"margin": 0.100, "hit_rate": 0.30},
            ],
            "neutral": [{"margin": 0.101, "hit_rate": 0.50}] * 3,
            "shuffled": [{"margin": 0.102, "hit_rate": 0.62}] * 3,
        }
        assert gate._verdict(rows) == "no-downstream-difference"


class TestHitGainUsesTheBinomialThreshold:
    """「多數」不是證據：8/12 的單尾機率是 0.19。"""

    @staticmethod
    def _rows(wins: int, n: int = 12):
        phase, neutral, shuffled = [], [], []
        for i in range(n):
            phase.append({"margin": 0.100, "hit_rate": 0.70 if i < wins else 0.52})
            neutral.append({"margin": 0.101, "hit_rate": 0.52})
            shuffled.append({"margin": 0.102, "hit_rate": 0.75})
        return {"phase": phase, "neutral": neutral, "shuffled": shuffled}

    def test_eight_of_twelve_is_not_enough_at_the_binomial_threshold(self, gate):
        assert gate._verdict(self._rows(8), need=10) == "no-downstream-difference"

    def test_ten_of_twelve_is_enough(self, gate):
        assert gate._verdict(self._rows(10), need=10) == "hit-gain-without-margin-gain"

    def test_the_default_is_a_strict_majority_not_a_coin_flip(self, gate):
        # 沒有傳門檻時（單獨跑腳本）只要求嚴格多數，但文件已寫明那不是檢定。
        assert gate._verdict(self._rows(7)) == "hit-gain-without-margin-gain"
