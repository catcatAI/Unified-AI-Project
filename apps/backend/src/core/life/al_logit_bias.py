# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [A] [L0-L11]
# =============================================================================
"""C-logit：讓 AL 的相位進入**模型的 logits**，而不是只進入請求參數。

C-param（`al_generation_params`）改的是取樣條件：temperature/max_tokens。那
一層的問題是「換一個模型，耦合就消失」——因為狀態從來沒有碰到模型的輸出。

這一層直接改模型在解碼時的 logits：

    scores[t] += bias(t)    對 t ∈ 一組語意詞彙

相位高 → 提高「高喚醒」詞的 logit、壓低「低喚醒」詞；相位低則反之。因為
softmax 對 logits 是單調的，這**直接改變模型對下一個 token 的機率**。

誠實邊界
--------
這仍然是外部施加的偏移（debiased decoding / logit_bias 那一類），不是模型
自身狀態的調制。字面上的「同一個模型」要到 C-state（hidden state / KV /
adapter 由 AL 狀態驅動）才算，而那是另一件事。這裡可以誠實主張的是：

- 耦合點在**模型的輸出分布**上，不在請求的參數上；
- 因此它與 C-param 在性質上不同：同樣的 temperature，分布已經不一樣了。

紀律：純函數（給定 activation 與詞彙 id，輸出同一組偏移）；不 import 任何
模型/框架（`llama_cpp` 只在量測腳本裡出現，本模組只產生 id→偏移）。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional, Sequence

# 相位拉滿時的偏移量（logit 單位）。1.0 的偏移約等於 e 倍的機率比，
# 4.0 足以讓一個詞從「可能」變成「明顯偏好」，又不會把分布壓成 argmax。
DEFAULT_STRENGTH = 4.0


@dataclass(frozen=True)
class LogitBias:
    """一組 token→偏移，附上它是怎麼來的（I9 逐項歸因）。"""

    biases: Dict[int, float] = field(default_factory=dict)
    activation: Optional[float] = None
    source: Optional[str] = None

    @property
    def is_empty(self) -> bool:
        return not self.biases

    def as_dict(self) -> dict:
        return {
            "biases": dict(self.biases),
            "activation": self.activation,
            "source": self.source,
            "max_abs": max((abs(v) for v in self.biases.values()), default=0.0),
        }


def _coerce_activation(value: object) -> Optional[float]:
    """壞型別/NaN → 未觀測（不是 0.0：0.0 是「在谷底」的觀測）。"""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return min(max(number, 0.0), 1.0)


def phase_bias(
    activation: object,
    energy_ids: Iterable[int],
    calm_ids: Iterable[int],
    *,
    strength: float = DEFAULT_STRENGTH,
) -> LogitBias:
    """activation → 對兩組詞彙的反向偏移。

    ``activation = 0.5`` 時偏移恰好為 0（neutral），所以「沒有相位偏好」與
    「相位在中點」在這層不可區分——這是刻意的：中點就是無偏好。
    """
    value = _coerce_activation(activation)
    if value is None:
        return LogitBias(biases={}, activation=None, source=None)

    offset = 2.0 * (value - 0.5)  # [-1, 1]
    biases: Dict[int, float] = {}
    for token_id in energy_ids:
        biases[int(token_id)] = round(strength * offset, 6)
    for token_id in calm_ids:
        biases[int(token_id)] = round(-strength * offset, 6)
    return LogitBias(biases=biases, activation=value, source="core.life.al_oscillator")


def apply_to(scores: Sequence[float], bias: LogitBias) -> list:
    """回傳套用偏移後的分數（不就地修改輸入）。

    只是 ``scores[t] + bias(t)``；不做正規化，因為正規化會抹掉 softmax 之前的
    差異——而那正是要被量測的東西。
    """
    out = list(scores)
    for token_id, delta in bias.biases.items():
        if 0 <= token_id < len(out):
            out[token_id] += delta
    return out
