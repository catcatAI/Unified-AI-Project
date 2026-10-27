# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [A] [L0-L11]
# =============================================================================
"""身份漂移：漂移 = 距離錨，而且要零假設才談得上「反證」（契約 §6、§7.2）。

三件事，全部純函式（無 I/O、無 ``ai.*``、同快照同結果，可重放）：

1. **時間係數**：慢層 ``tau_slow`` 與快層 ``tau_fast`` 各自濾波，權重
   ``w_i = exp(-Δt/τ)`` —— 契約 §5 的同一個一階濾波算子。單一時間常數會把
   一時的波動與跨世代的沉澱當成同一件事，正是 §7.2「佔比綁 τ」的理由。
   τ 的單位是 LifeEssence 的世代（epoch，契約 §4.3 三種時間尺度之一）。
2. **距離錨**：``distance = 慢層加權值 − 錨``。錨取序列的第一筆觀測
   （``anchor_source="origin"``＝第 0 代祖先核心），**不是預設值** —— 沒有
   觀測背後的錨不算錨（D11）。錨也可以由呼叫方供給（``anchor_source="supplied"``）。
3. **反證**：``z = distance / SE``，SE 由加權有效樣本數
   ``n_eff = (Σw)² / Σw²`` 得出。**本模組刻意不放相關係數 r**：r 對位移不變
   —— 狀態停在離錨 0.4 的常數位置時 r 仍是 1（形狀沒變、位置變了）；錨是
   常數時 ``dx = 0``，倉內 ``TemporalState.correlation`` 回 ``0.0``（假值，
   不是「無關」）。拿 r 反證漂移會得到「沒有漂移」的錯覺，所以相關只能當
   形狀報告，不能當證據（`tests/core/test_identity_drift.py` 釘住這條）。

**``confirmed`` 要同時滿足兩件事，缺一不可**：

* 慢層偏離錨在統計上站得住（``|z| >= z_threshold``；零方差退化為「偏離非零
  即成立」——沒有噪聲可言）；
* 快層正在拉離慢層（``moving``）—— **還在動**。

第二條是刻意的：**偏離錨但已經平息 = 長成了新的人格，不是「漂移中」**。
把「離初始很遠」誤讀成「正在漂」會讓穩定成長的傾向永遠被當成病態。
只有「離開錨 **且** 仍在動」才確認，``drift`` 因此回 ``0.0``（觀測到、無確認漂移）。

**修正參數集**沿用既有的 ``al_memory_policy.RetentionPolicy``（§10），本模組
只負責把觀測算成 ``drift["identity"]`` 這第三個觀測鍵：

* ``retention``：``retention_policy`` 對已觀測鍵取最大 —— 只有在真的漂移時
  這個鍵才 > 0，語義仍是「正在變動的那一面」→ 留短；
* ``consolidate``：``identity > 0`` 時固化被擋下 —— **還沒定型的自我，不該把
  記憶永久保護起來**（噪音固化成人格，正是衰減/固化邊界要防的那一格）。

兩者都受 D11 約束：觀測不足（< ``min_points``）→ 鍵不進 dict，行為一概不動。

**這套機制穩定的是傾向，不是智能**：核心分 0.00/10、生產路徑 0 句回覆由模型
產生（`MEASUREMENT_MAP` 2026-10-24 實測）。錨與閘能讓傾向不亂飄，但替系統
長不出能力 —— 不要把「穩定」讀成「智能」。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

# 時間係數（世代）：生產接線讀配置（configs/standard/behavior/behavior.default.yaml
# 的 identity_* 鍵，用法由 tests/core/test_identity_drift.py 釘住，防再次變成
# 無讀者的死鍵）；這裡的預設值是無配置時的退路，與 compute_zeta_values(window=50)
# 同一款慣例。調參演算法（τ 自身怎麼學）仍是契約 Q5，未做。
TAU_SLOW = 20.0
TAU_FAST = 5.0
# 與 anomalies() 的 2σ 同一檔 —— 不另立閾值尺度。
Z_THRESHOLD = 2.0
MIN_POINTS = 6

ANCHOR_ORIGIN = "origin"
ANCHOR_SUPPLIED = "supplied"
ANCHOR_NONE = "none"


@dataclass(frozen=True)
class IdentityDriftEvidence:
    """一維傾向的漂移證據。未觀測的量一律 ``None``/``0.0``，絕不偽裝（D11）。"""

    observed: bool
    dimension: str
    points: int
    anchor: Optional[float]
    anchor_source: str
    slow: Optional[float]
    fast: Optional[float]
    distance: Optional[float]
    z: Optional[float]
    moving: bool
    confirmed: bool
    drift: float

    def as_dict(self) -> Dict[str, object]:
        return {
            "observed": self.observed,
            "dimension": self.dimension,
            "points": self.points,
            "anchor": self.anchor,
            "anchor_source": self.anchor_source,
            "slow": self.slow,
            "fast": self.fast,
            "distance": self.distance,
            "z": self.z,
            "moving": self.moving,
            "confirmed": self.confirmed,
            "drift": self.drift,
        }


def _finite(value: Any) -> Optional[float]:
    """轉有限浮點；``None``/NaN/inf/非數字 → ``None``（不可觀測）。"""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _weights(times: Sequence[float], tau: float, end: float) -> List[float]:
    """``w_i = exp(-Δt/τ)`` —— 契約 §5 一階濾波的權重形式（同一個 τ）。"""
    return [math.exp(-(end - t) / tau) for t in times]


def _ewm(values: Sequence[float], weights: Sequence[float]) -> Tuple[float, float, float]:
    """加權均值、標準誤（含 ``n_eff`` 修正）與有效樣本數。

    ``n_eff = (Σw)² / Σw²``：指數加權下舊點不等權，直接用 n 會把不確定度
    估得太小 → z 虛高 → 假的「顯著」。
    """
    total = sum(weights)
    if total <= 0:
        raise ValueError("weights must sum to a positive number")
    mean = sum(w * v for w, v in zip(weights, values)) / total
    variance = sum(w * (v - mean) ** 2 for w, v in zip(weights, values)) / total
    sum_sq = sum(w * w for w in weights)
    n_eff = (total * total) / sum_sq if sum_sq > 0 else 0.0
    se = math.sqrt(variance / n_eff) if n_eff > 0 else 0.0
    return mean, se, n_eff


def _unobserved(
    dimension: str, points: int, anchor: object, anchor_source: str
) -> IdentityDriftEvidence:
    supplied = _finite(anchor)
    return IdentityDriftEvidence(
        observed=False,
        dimension=dimension,
        points=points,
        anchor=supplied,
        anchor_source=(
            anchor_source if supplied is not None or anchor_source == ANCHOR_ORIGIN else ANCHOR_NONE
        ),
        slow=None,
        fast=None,
        distance=None,
        z=None,
        moving=False,
        confirmed=False,
        drift=0.0,
    )


def identity_drift(
    history: Sequence[Tuple[object, object]],
    dimension: str,
    *,
    anchor: Optional[float] = None,
    tau_slow: float = TAU_SLOW,
    tau_fast: float = TAU_FAST,
    z_threshold: float = Z_THRESHOLD,
    min_points: int = MIN_POINTS,
) -> IdentityDriftEvidence:
    """量一個維度的身份漂移（純函式，同輸入同輸出）。

    ``history`` 是 ``(時間, {維度: 值})`` 序列（``LifeEssence.mu_history()`` 的
    形狀）；時間可缺、值可缺（缺值的點直接跳過），序列會由本函式排序。

    回傳的 ``drift ∈ [0,1]``：**只有確認中的漂移才有非零值**（偏離錨且仍在動），
    觀測到但未確認 = ``0.0``；觀測不足則 ``observed=False``，呼叫方不該把
    ``drift`` 讀成「量到零」。
    """
    if (
        not (tau_slow > 0)
        or not (tau_fast > 0)
        or not (math.isfinite(tau_slow) and math.isfinite(tau_fast))
    ):
        raise ValueError(
            f"time constants must be finite and positive, got {tau_slow=!r} {tau_fast=!r}"
        )
    if not (z_threshold > 0):
        raise ValueError(f"z_threshold must be positive, got {z_threshold!r}")

    supplied_anchor = _finite(anchor)
    anchor_source = ANCHOR_SUPPLIED if anchor is not None else ANCHOR_ORIGIN

    series: List[Tuple[float, float]] = []
    for entry in history or ():
        if not isinstance(entry, (tuple, list)) or len(entry) != 2:
            continue
        when, row = entry
        if not isinstance(row, Mapping):
            continue
        time_value = _finite(when)
        point = _finite(row.get(dimension))
        if time_value is None or point is None:
            continue
        series.append((time_value, point))
    series.sort(key=lambda item: item[0])

    if len(series) < max(int(min_points), 2):
        return _unobserved(dimension, len(series), anchor, anchor_source)

    times = [t for t, _ in series]
    values = [v for _, v in series]
    end = times[-1]

    if supplied_anchor is None:
        if anchor is not None:
            # 供給的錨不可觀測 → 沒有錨就沒有距離（不拿第一筆冒充供給值）
            return _unobserved(dimension, len(series), anchor, ANCHOR_NONE)
        base = values[0]
        anchor_source = ANCHOR_ORIGIN
    else:
        base = supplied_anchor

    slow, se_slow, _ = _ewm(values, _weights(times, tau_slow, end))
    fast, _, _ = _ewm(values, _weights(times, tau_fast, end))

    distance = slow - base
    z = distance / se_slow if se_slow > 0 else None
    gap = fast - slow
    # 「還在動」＝快層的當下水位已經拉離慢層，且差距大過**長程噪聲尺度**
    # （se_slow）。用 se_fast 做門會退化：一段平息後的序列其快窗變異趨近 0，
    # 任何殘留差距都會被讀成「在動」——那會把已經長成的新人格永遠當成病態。
    if se_slow > 0:
        moving = abs(gap) >= z_threshold * se_slow
    else:
        moving = gap != 0.0

    anchor_significant = abs(z) >= z_threshold if z is not None else distance != 0.0
    confirmed = bool(anchor_significant and moving)
    drift = min(1.0, max(0.0, abs(distance))) if confirmed else 0.0

    return IdentityDriftEvidence(
        observed=True,
        dimension=dimension,
        points=len(series),
        anchor=base,
        anchor_source=anchor_source,
        slow=slow,
        fast=fast,
        distance=distance,
        z=z,
        moving=moving,
        confirmed=confirmed,
        drift=drift,
    )


def worst_identity_drift(
    history: Sequence[Tuple[object, object]],
    *,
    dimensions: Optional[Sequence[str]] = None,
    anchor: Optional[float] = None,
    tau_slow: float = TAU_SLOW,
    tau_fast: float = TAU_FAST,
    z_threshold: float = Z_THRESHOLD,
    min_points: int = MIN_POINTS,
) -> Optional[Tuple[str, IdentityDriftEvidence]]:
    """逐維度量，回「最嚴重的那一面」（與 ``retention_policy`` 取最大同款語義）。

    全部維度都觀測不足 → ``None``（D11：整個量未觀測，呼叫方一個鍵都不寫）。
    都觀測到但無確認漂移 → 回其中一維，其 ``drift`` 為 ``0.0`` —— 這是
    「量到了、沒在漂」，與未觀測不同。
    """
    if dimensions is None:
        dimensions = sorted(
            {
                name
                for _, row in history or ()
                if isinstance(row, Mapping)
                for name in row
                if _finite(row.get(name)) is not None
            }
        )
    best: Optional[Tuple[str, IdentityDriftEvidence]] = None
    for name in dimensions:
        evidence = identity_drift(
            history,
            name,
            anchor=anchor,
            tau_slow=tau_slow,
            tau_fast=tau_fast,
            z_threshold=z_threshold,
            min_points=min_points,
        )
        if not evidence.observed:
            continue
        if best is None:
            best = (name, evidence)
            continue
        best_key = (best[1].drift, abs(best[1].distance or 0.0))
        candidate_key = (evidence.drift, abs(evidence.distance or 0.0))
        if candidate_key > best_key:
            best = (name, evidence)
    return best


__all__ = [
    "ANCHOR_NONE",
    "ANCHOR_ORIGIN",
    "ANCHOR_SUPPLIED",
    "IdentityDriftEvidence",
    "MIN_POINTS",
    "TAU_FAST",
    "TAU_SLOW",
    "Z_THRESHOLD",
    "identity_drift",
    "worst_identity_drift",
]
