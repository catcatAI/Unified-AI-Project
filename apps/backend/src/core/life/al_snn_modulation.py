# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [A] [L0-L11]
# =============================================================================
"""C-state：讓 AL 的相位改變**模型內部的動力學**，而不只是它的輸入或輸出。

前三個層級都可以說是「從外面推」：

- C-param：改請求參數（temperature）→ 換一個模型就沒了；
- C-logit：改輸出分布（logit 偏移）→ 分布被推，但模型內部完全不知道；
- **C-state**（本模組）：改模型自己的**參數/狀態**——這裡是 GARDEN SNN 的
  發火閾值。同樣的輸入、同樣的權重，因為內部興奮度不同，脈衝樣式就不同。

為什麼閾值算「內部狀態」而不是「輸入」：輸入 `input_keys` 決定哪個神經元被
點亮，權重 `W` 決定誰影響誰，而閾值決定**這台網路多容易被點起來**。它不屬於
任何一種輸入，換掉它等於換掉這個模型當下的體質。

語義映射（不是任意常數）：activation 高 → 閾值低 → 同一個線索更容易擴散到
下游概念。這與「喚醒度高時聯想更活躍」是同一件事。

紀律：純函數、無 I/O；`activation` 缺席或壞型別 → 倍率恰為 1.0（呼叫端行為
與未接線時逐位相同）。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Optional

# 相位拉滿時的閾值擺幅：峰 0.5×、谷 1.5×。取 0.5 是因為 GARDEN 的 top-k
# 競爭只看相對大小，閾值再低就變成「全部點亮」，訊號被自己淹掉。
DEFAULT_THRESHOLD_SPAN = 0.5
MIN_MULTIPLIER = 0.4
MAX_MULTIPLIER = 1.6


@dataclass(frozen=True)
class SNNModulation:
    """交給模型的一次性內部調制（帶 provenance，I9）。"""

    threshold_multiplier: float = 1.0
    activation: Optional[float] = None
    source: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "threshold_multiplier": self.threshold_multiplier,
            "activation": self.activation,
            "source": self.source,
        }


def _coerce(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return min(max(number, 0.0), 1.0)


def modulate(activation: Any, *, span: float = DEFAULT_THRESHOLD_SPAN) -> SNNModulation:
    """activation → 閾值倍率。0.5 給 1.0（中性），兩端 0.5–1.5。"""
    value = _coerce(activation)
    if value is None:
        return SNNModulation(threshold_multiplier=1.0, activation=None, source=None)
    offset = 2.0 * (value - 0.5)  # [-1, 1]
    multiplier = 1.0 - span * offset
    multiplier = min(max(multiplier, MIN_MULTIPLIER), MAX_MULTIPLIER)
    return SNNModulation(
        threshold_multiplier=round(multiplier, 6),
        activation=value,
        source="core.life.al_oscillator",
    )
