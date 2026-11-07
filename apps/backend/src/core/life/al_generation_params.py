# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [A] [L0-L11]
# =============================================================================
"""C-param：讓 AL 的相位進入**生成參數**，而不只是系統自己的決定。

到目前為止，內生節律影響的是本系統內部（心跳節拍、記憶編碼權重）。那證明
「節律有功能」，但沒有證明它碰到生成。這一層是最小的一步：同一個 prompt，
在不同相位送出去時，`temperature` 與 `max_tokens` 不同。

為什麼是這兩個、不是 logits
--------------------------
`temperature` 在解碼時直接改下一個 token 的分布（`p_i ∝ exp(z_i/T)`），
`max_tokens` 改的是生成長度的上限。兩者都是送給模型的**請求參數**，所以
「AL 的狀態改變了模型的取樣條件」這件事在這一層是可驗證的、且不需要碰
模型的內部。

它仍然只是 C-param：耦合發生在「請求的參數」上，不是在「模型的狀態」上。
字面上的「同一個模型」（C-state）需要模型那邊有可被外部調制的狀態——本模組
不假裝有。

三條紀律：純函數（給定輸入與快照，輸出相同）；快照只讀；`rhythm` 缺席 →
原值不動（D11：未觀測不改現行規則）。
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 相位拉滿時的擺幅。刻意小：43 s 的緩慢調制不該蓋過路由/提示詞的決定。
TEMPERATURE_SWING = 0.15
TOKENS_FRACTION = 0.10

# 與 router 的界限一致（`_apply_negotiator_bias` 用 0.1–1.5）；同一組界線，
# 免得兩個地方各自夾出不同範圍。
TEMPERATURE_MIN = 0.1
TEMPERATURE_MAX = 1.5
TOKENS_MIN = 64
TOKENS_MAX = 8192


@dataclass(frozen=True)
class GenerationParams:
    """調制後的請求參數＋逐項歸因（I9：說得出是誰改的、改了多少）。"""

    temperature: float
    max_tokens: int
    applied: Dict[str, float] = field(default_factory=dict)
    source: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "applied": dict(self.applied),
            "source": self.source,
        }


def _activation(snapshot: Any) -> Optional[float]:
    """讀 ``snapshot.rhythm.activation``；壞型別/缺席一律當未觀測。

    ``activation=0.0`` 是「在谷底」的**觀測**，與「沒量到」不同：前者要把
    temperature 壓低，後者什麼都不做。
    """
    try:
        rhythm = getattr(snapshot, "rhythm", None)
    except Exception:  # noqa: BLE001 - 狀態來源壞掉不該把例外帶進生成路徑
        logger.debug("AL rhythm unavailable on snapshot; leaving params untouched", exc_info=True)
        return None
    if not isinstance(rhythm, dict):
        return None
    value = rhythm.get("activation")
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return min(max(number, 0.0), 1.0)


def modulate(
    temperature: float,
    max_tokens: int,
    snapshot: Any,
    *,
    swing: float = TEMPERATURE_SWING,
    tokens_fraction: float = TOKENS_FRACTION,
) -> GenerationParams:
    """把內生相位加成到請求參數上。無相位 → 原值（逐位相同，不是近似）。"""
    activation = _activation(snapshot)
    if activation is None:
        return GenerationParams(
            temperature=float(temperature),
            max_tokens=int(max_tokens),
            applied={},
            source=None,
        )

    # 以 0.5（極限環中點）為中性：相位在上半圈 → 稍高溫，下半圈 → 稍低溫。
    offset = 2.0 * (activation - 0.5)  # [-1, 1]
    new_temperature = min(
        max(float(temperature) + swing * offset, TEMPERATURE_MIN), TEMPERATURE_MAX
    )
    new_tokens = int(round(max_tokens * (1.0 + tokens_fraction * offset)))
    new_tokens = min(max(new_tokens, TOKENS_MIN), TOKENS_MAX)

    return GenerationParams(
        temperature=round(new_temperature, 4),
        max_tokens=new_tokens,
        applied={
            "temperature_delta": round(new_temperature - float(temperature), 4),
            "max_tokens_delta": new_tokens - int(max_tokens),
            "activation": round(activation, 4),
        },
        source="core.life.al_oscillator",
    )
