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
