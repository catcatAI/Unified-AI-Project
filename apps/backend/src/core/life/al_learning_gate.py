# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [A] [L0-L11]
# =============================================================================
"""C-learn：讓 AL 的相位改變**可塑性**，也就是「這次經歷會被記得多深」。

前面三級改的都是當下的計算：請求參數（C-param）、輸出分布（C-logit）、發火
閾值（C-state）。它們都不改變模型明天是什麼樣子。這一層改的是**權重會被推向
哪裡**——同一個模型、同一批資料、同一個順序，只因為經歷它們時的內生相位不同，
留下來的結構就不同。

為什麼可塑性算「內部狀態」而不是「超參數」：`lr` 是設定（同一份程式裡固定），
可塑性增益是**當下體質**——它隨振盪器走，一次一個樣本。把增益換成常數，行為
就回到未接線時（逐位相同），這是本模組的紀律。

語義映射（不是任意常數）：相位高（喚醒高）→ 此刻的共現更容易固化（增益
1.6）；相位低 → 同樣的共現幾乎不留痕（0.4）。這與「疲勞時不易形成新記憶」
是同一件事，也與 `al_memory_policy.py`（寫入權重）方向一致，但作用在不同
的機制上：那個決定要不要存，這個決定存得多牢。

純函數、無 I/O。`activation` 缺席或壞型別 → 增益恰為 1.0。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Optional

# 相位拉滿時的可塑性擺幅：峰 1.6×、谷 0.4×。比 C-state 的閾值擺幅大，因為
# 權重更新是線性累積——擺幅太小會被 decay 與 top-k 的雜訊淹掉（量測前也
# 是這樣假設的，實測見 scripts/al_c_learn.py）。
DEFAULT_PLASTICITY_SPAN = 0.6
MIN_GAIN = 0.05
MAX_GAIN = 3.0


@dataclass(frozen=True)
class PlasticityGain:
    """交給學習步驟的一次性可塑性增益（帶 provenance，I9）。"""

    gain: float = 1.0
    activation: Optional[float] = None
    source: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "gain": self.gain,
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


def learning_gain(activation: Any, *, span: float = DEFAULT_PLASTICITY_SPAN) -> PlasticityGain:
    """activation → 可塑性增益。0.5 給 1.0（中性），兩端 0.4–1.6。"""
    value = _coerce(activation)
    if value is None:
        return PlasticityGain(gain=1.0, activation=None, source=None)
    offset = 2.0 * (value - 0.5)  # [-1, 1]
    gain = 1.0 + span * offset
    gain = min(max(gain, MIN_GAIN), MAX_GAIN)
    return PlasticityGain(
        gain=round(gain, 6),
        activation=value,
        source="core.life.al_oscillator",
    )


def sanitize_gain(raw: Any) -> float:
    """呼叫端傳進來的增益 → 可用的正有限值；壞值一律 1.0（逐位不變）。"""
    if raw is None or isinstance(raw, bool):
        return 1.0
    try:
        number = float(raw)
    except (TypeError, ValueError):
        return 1.0
    if not math.isfinite(number) or number <= 0.0:
        return 1.0
    return min(max(number, MIN_GAIN), MAX_GAIN)
