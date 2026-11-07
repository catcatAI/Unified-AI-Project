"""``RhythmTracker.activation_preview`` 必須回答「這一刻」，不是「上次推進那一刻」。

GARDEN 的 Hebbian 更新每個樣本讀一次可塑性增益，而讀值走的是 preview（不落盤）。
如果 preview 只回傳 `_osc.activation`，那麼沒有對話在推振盪器時，學習會一直用
第一次推進的相位——「覺醒高時記得牢」就退化成「開機時記得牢」。
"""

from __future__ import annotations

import math

import pytest

from core.life.al_oscillator import MAX_CATCHUP_S, Oscillator, RhythmTracker


class _Clock:
    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def _tracker(tmp_path, clock):
    return RhythmTracker(tmp_path / "rhythm.json", clock=clock)


def test_preview_moves_with_the_clock(tmp_path):
    clock = _Clock()
    tracker = _tracker(tmp_path, clock)
    stale = tracker.activation_preview()
    clock.now += 0.9  # 同一個週期內的不同位置，不是半個週期後的巧合
    assert tracker.activation_preview() != pytest.approx(stale, abs=1e-9)


def test_preview_matches_what_advancing_would_give(tmp_path):
    clock = _Clock()
    tracker = _tracker(tmp_path, clock)
    clock.now += 0.7
    previewed = tracker.activation_preview()
    advanced = tracker.activation()
    assert previewed == pytest.approx(advanced, abs=1e-9)


def test_preview_advances_nothing_and_persists_nothing(tmp_path):
    clock = _Clock()
    tracker = _tracker(tmp_path, clock)
    before = tracker.state()
    clock.now += 3.0
    tracker.activation_preview()
    after = tracker.state()
    assert after["x"] == before["x"]
    assert after["v"] == before["v"]
    assert after["at"] == before["at"]
    assert not (tmp_path / "rhythm.json").exists()


def test_preview_caps_a_long_absence_instead_of_an_expensive_catch_up(tmp_path):
    clock = _Clock()
    tracker = _tracker(tmp_path, clock)
    fresh = Oscillator()
    fresh.step(MAX_CATCHUP_S)
    clock.now += MAX_CATCHUP_S * 50.0
    previewed = tracker.activation_preview()
    assert math.isfinite(previewed)
    assert 0.0 <= previewed <= 1.0
    assert previewed == pytest.approx(fresh.activation, abs=1e-6)


def test_a_backwards_clock_does_not_rewind_the_oscillator(tmp_path):
    clock = _Clock()
    tracker = _tracker(tmp_path, clock)
    clock.now += 1.0
    tracker.activation()  # 推進一次，記下真實狀態
    state = tracker.state()
    clock.now -= 5.0
    expected = min(max((state["x"] + 2.0) / 4.0, 0.0), 1.0)
    assert tracker.activation_preview() == pytest.approx(expected, abs=1e-9)
    assert tracker.state()["x"] == state["x"]
    assert tracker.state()["at"] == state["at"]
