# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""E2 機制原型測試：內聚鎖死、狀態逃逸、劑量單調、逃逸增益。

配對邏輯即 E2 接受門的縮影：同一組親和力，無狀態鎖死、有狀態逃逸。
數值斷言分兩層——結構性質（單調、和為 1、逃逸可重驗）優先，
魔法數字只釘特徵點（0.987 鎖死、3.0 首逃）。
"""

from __future__ import annotations

import pytest
from ai.attention.inner_outer import Allocation, InnerOuterAttention

RECENT = [2.0, 1.0, 0.5]
ANCHORS = [0.5, 0.5]
GAINS = [0.0, 1.0, 3.0, 5.0, 10.0]


def test_allocate_splits_mass_and_sums_to_one() -> None:
    module = InnerOuterAttention()
    alloc = module.allocate(RECENT, ANCHORS, state_gain=0.0)
    assert isinstance(alloc, Allocation)
    assert len(alloc.recent_weights) == 3
    assert len(alloc.anchor_weights) == 2
    assert sum(alloc.recent_weights) + sum(alloc.anchor_weights) == pytest.approx(1.0)
    assert alloc.inwardness == pytest.approx(sum(alloc.recent_weights))


def test_allocate_rejects_empty_sides() -> None:
    module = InnerOuterAttention()
    with pytest.raises(ValueError, match="recent window"):
        module.allocate([], ANCHORS)
    with pytest.raises(ValueError, match="anchors"):
        module.allocate(RECENT, [])


def test_softmax_rejects_empty_directly() -> None:
    from ai.attention.inner_outer import _softmax

    with pytest.raises(ValueError, match="at least one score"):
        _softmax([])


def test_allocate_is_numerically_stable() -> None:
    module = InnerOuterAttention()
    alloc = module.allocate([1000.0, 999.0], [998.0], state_gain=0.0)
    assert sum(alloc.recent_weights) + sum(alloc.anchor_weights) == pytest.approx(1.0)
    assert 0.0 < alloc.inwardness < 1.0


def test_no_state_locks_in() -> None:
    """無狀態：內聚度趨 1，loop_entry 為真（卡重複不動點）。"""
    module = InnerOuterAttention()
    trace = module.iterate(RECENT, ANCHORS, state_gain=0.0)
    assert trace[-1].inwardness == pytest.approx(0.9869, abs=1e-3)
    assert module.loop_entry(trace) is True


def test_state_gain_escapes() -> None:
    """同組親和力 + 增益 5：內聚度跌破閾值，無 loop_entry。"""
    module = InnerOuterAttention()
    trace = module.iterate(RECENT, ANCHORS, state_gain=5.0)
    assert trace[-1].inwardness < module.inward_threshold
    assert module.loop_entry(trace) is False


def test_dose_response_is_monotone_non_increasing() -> None:
    """劑量反應曲線隨增益非增（狀態越多，內聚越少）。"""
    module = InnerOuterAttention()
    curve = module.dose_response(RECENT, ANCHORS, GAINS)
    assert len(curve) == len(GAINS)
    assert all(b <= a for a, b in zip(curve, curve[1:]))
    assert curve[0] > curve[-1]


def test_min_escape_gain_is_exact_and_reverifiable() -> None:
    """首逃增益 3.0，且在該增益重跑確實逃逸、前一檔確實不逃。"""
    module = InnerOuterAttention()
    gain = module.min_escape_gain(RECENT, ANCHORS, GAINS)
    assert gain == 3.0
    assert module.iterate(RECENT, ANCHORS, state_gain=gain)[-1].inwardness < 0.8
    assert module.iterate(RECENT, ANCHORS, state_gain=1.0)[-1].inwardness >= 0.8


def test_min_escape_gain_none_when_never() -> None:
    module = InnerOuterAttention()
    assert module.min_escape_gain(RECENT, ANCHORS, [0.0]) is None
    assert module.min_escape_gain(RECENT, ANCHORS, []) is None


def test_loop_entry_needs_consecutive_streak() -> None:
    """非連續超標不算 loop（單點毛刺不誤報）。"""
    module = InnerOuterAttention(loop_steps=3)
    lone_spike = [Allocation([0.9], [0.1], 0.9)]
    assert module.loop_entry(lone_spike) is False
    locked = module.iterate(RECENT, ANCHORS, state_gain=0.0)
    assert module.loop_entry(locked) is True
    assert module.loop_entry([]) is False
