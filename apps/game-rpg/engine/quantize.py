# -*- coding: utf-8 -*-
"""萬物皆軸引擎 — step 量化吸附 + 定點整數模式（計畫 §6.2/§6.3 M2）。

- ``quantize(v, step)``：``round_half_away(v/step)*step``，以 step 十進位
  寬度清洗表示誤差 → **0.01 step 往返無漂移**（idempotent、結果落在格點）。
- ``step<=0`` → 原值不動（**0=連續不量化**）；step<0 → ValueError。
- 半遠離零（half-away-from-zero）：2.5@step1 → 3（非 banker's 的 2）。
- 定點整數模式：``quantize_fixed(v, step)`` 回整數格索引、``from_fixed``
  還原；``quantize_auto(..., fixed=True)`` 為模式開關（§6.2「定點整數模式」）。
- ``quantize_axis(value, spec, override_step)``：**軸級覆寫**——覆寫值優先於
  ``AxisSpec.step``（含 0=對該軸關閉量化）；fsm/非數值原樣通過。
"""

from __future__ import annotations

import math
from typing import Optional, Union

from engine.axes import AxisSpec

Number = Union[int, float]


def _round_half_away(x: float) -> int:
    """半遠離零取整（正 x+0.5 後 floor；負對稱）。"""
    if x >= 0:
        return int(math.floor(x + 0.5))
    return -int(math.floor(-x + 0.5))


def _step_decimals(step: float) -> int:
    """step 的十進位位數（repr 判讀；指數型取 -exp；上限 12 防失控）。"""
    r = repr(float(step))
    if "e" in r or "E" in r:
        mantissa, _, exp = r.replace("E", "e").partition("e")
        decimals = -int(exp)
        if decimals < 0:
            return 0
        if "." in mantissa:
            decimals += len(mantissa.split(".", 1)[1])
        return min(decimals, 12)
    if "." in r:
        frac = r.split(".", 1)[1]
        return min(len(frac), 12)
    return 0


def quantize(value: float, step: float) -> float:
    """step 量化吸附；step==0（連續）原樣；step<0 raise ValueError。"""
    if step < 0:
        raise ValueError(f"step must be >= 0, got {step}")
    if step == 0:
        return float(value)
    index = _round_half_away(float(value) / step)
    return round(index * step, _step_decimals(step))


def quantize_fixed(value: float, step: float) -> int:
    """定點模式：回整數格索引 ``round_half_away(v/step)``；step<=0 raise。"""
    if step <= 0:
        raise ValueError(f"fixed-point quantize requires step > 0, got {step}")
    return _round_half_away(float(value) / step)


def from_fixed(index: int, step: float) -> float:
    """格索引 → 值（同 quantize 的清洗，保證落格無漂移）。"""
    if step <= 0:
        raise ValueError(f"from_fixed requires step > 0, got {step}")
    return round(int(index) * step, _step_decimals(step))


def quantize_auto(value: float, step: float, fixed: bool = False) -> Union[float, int]:
    """模式開關：fixed=False 回量化值（float）、True 回格索引（int）。"""
    if fixed:
        return quantize_fixed(value, step)
    return quantize(value, step)


def quantize_axis(
    value: float, spec: AxisSpec, override_step: Optional[float] = None
) -> Union[float, int]:
    """軸級量化：``override_step`` 優先於 ``spec.step``（0=對該軸關閉）。

    fsm 軸或非數值（含 bool）原樣通過——FSM 狀態不做數值吸附。
    """
    step = spec.step if override_step is None else override_step
    if step < 0:
        raise ValueError(f"override_step must be >= 0, got {step}")
    if spec.kind == "fsm" or isinstance(value, bool) or not isinstance(value, (int, float)):
        return value
    return quantize(float(value), step)
