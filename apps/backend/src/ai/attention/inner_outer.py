# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""內外注意力機制原型（E2）：內聚鎖死動力學 + 狀態增益搶回注意力。

誠實邊界：這是機制原型（numpy 玩具動力學），不是 Gemma 注意力頭的量測。
它把假設寫成可證偽的數值預測——內聚閾值、逃逸增益、劑量單調性——真頭量測
（llama_cpp 注意力張量 + 3.35GB CPU 推理）是設門的後續實驗，不在本輪。

模型：
- 外（recent）：近窗 token 親和力；內（anchors）：長程錨點親和力。
- 無狀態時每步自增強（argmax 富者愈富）→ 質量向近窗坍縮 → 不動點 = 卡重複。
- 狀態增益 g 每步加到錨點側；g 足夠大時 argmax 翻到錨點側 → 逃逸。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Sequence


@dataclass
class Allocation:
    """單步分配結果：近窗與錨點的權重、內聚度。"""

    recent_weights: List[float]
    anchor_weights: List[float]
    inwardness: float


def _softmax(scores: Sequence[float]) -> List[float]:
    """數值穩定的 softmax（減 max 防溢出）。"""
    if not scores:
        raise ValueError("softmax needs at least one score")
    peak = max(scores)
    exps = [math.exp(s - peak) for s in scores]
    total = sum(exps)
    return [e / total for e in exps]


def attention_inwardness(weights: Sequence[float], recent_k: int = 8) -> float:
    """真頭內聚度：查詢位置對最近 recent_k 個鍵的注意力質量佔比。

    `weights` 為單步單頭（或已平均）的鍵分佈（和為 1）；`recent_k <= 0`
    報錯。短前綴（len <= k）時全質量皆算近期，迴圈早期不低估。
    """
    if recent_k <= 0:
        raise ValueError("recent_k must be positive")
    if not weights:
        raise ValueError("weights must not be empty")
    return sum(weights[-recent_k:])


def attention_sink_mass(weights: Sequence[float], sink_k: int = 4) -> float:
    """匯質量：查詢位置對最初 sink_k 個鍵（含 BOS）的注意力質量佔比。

    與內聚度互補：低熵延續若把質量沉向句首，此值在 loop 組更高。
    `sink_k <= 0` 或空分佈報錯（與內聚度同樣的 fail-closed）。
    """
    if sink_k <= 0:
        raise ValueError("sink_k must be positive")
    if not weights:
        raise ValueError("weights must not be empty")
    return sum(weights[:sink_k])


@dataclass
class InnerOuterAttention:
    """內外注意力分配器與內聚動力學。

    Args:
        inward_threshold: 內聚度超過此值記為鎖死傾向。
        loop_steps: 連續超標步數達此值記為 loop_entry。
        reinforcement: 每步自增強係數（貪婪解碼鎖定的玩具模型）。
    """

    inward_threshold: float = 0.8
    loop_steps: int = 3
    reinforcement: float = 0.5

    def allocate(
        self, recent: Sequence[float], anchors: Sequence[float], state_gain: float = 0.0
    ) -> Allocation:
        """單步分配：錨點側加狀態增益後聯合 softmax，內聚度=近窗質量。"""
        if not recent:
            raise ValueError("recent window must not be empty")
        if not anchors:
            raise ValueError("anchors must not be empty")
        boosted = list(recent) + [a + state_gain for a in anchors]
        weights = _softmax(boosted)
        recent_weights = weights[: len(recent)]
        anchor_weights = weights[len(recent) :]
        return Allocation(
            recent_weights=recent_weights,
            anchor_weights=anchor_weights,
            inwardness=sum(recent_weights),
        )

    def iterate(
        self,
        recent: Sequence[float],
        anchors: Sequence[float],
        state_gain: float = 0.0,
        steps: int = 8,
    ) -> List[Allocation]:
        """自增強迭代：每步給當前 argmax 加 reinforcement 後重分配。

        無狀態增益時 argmax 鎖在近窗 → 內聚度趨 1（卡重複不動點）；
        錨點增益足夠時 argmax 翻轉 → 逃逸。
        """
        trace: List[Allocation] = []
        current = list(recent)
        for _ in range(steps):
            step = self.allocate(current, anchors, state_gain)
            trace.append(step)
            peak = max(range(len(current)), key=lambda i: current[i])
            current = [
                v + (self.reinforcement if i == peak else 0.0) for i, v in enumerate(current)
            ]
        return trace

    def loop_entry(self, trace: Sequence[Allocation]) -> bool:
        """trace 尾段連續超標達 loop_steps 即記 loop_entry。"""
        streak = 0
        for step in trace:
            streak = streak + 1 if step.inwardness > self.inward_threshold else 0
            if streak >= self.loop_steps:
                return True
        return False

    def dose_response(
        self, recent: Sequence[float], anchors: Sequence[float], gains: Sequence[float]
    ) -> List[float]:
        """劑量反應曲線：各增益下終態內聚度（應隨增益非增）。"""
        out = []
        for gain in gains:
            trace = self.iterate(recent, anchors, state_gain=gain)
            out.append(trace[-1].inwardness)
        return out

    def min_escape_gain(
        self, recent: Sequence[float], anchors: Sequence[float], gains: Sequence[float]
    ) -> float | None:
        """回傳首個使終態內聚度跌破閾值的增益；全不逃逸回傳 None。"""
        for gain in gains:
            trace = self.iterate(recent, anchors, state_gain=gain)
            if trace[-1].inwardness < self.inward_threshold:
                return gain
        return None
