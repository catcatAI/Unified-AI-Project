# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [A] [L0-L11]
# =============================================================================
"""§10 與記憶的介面：AL 輸出 retention/decay policy（策略，不是內容）。

三分法 Phase 2 item ④。本模組只有一件事：**由唯讀快照算出一份保留策略**
—— ``retention_policy(snapshot) -> RetentionPolicy``。記憶層（HAM）執行
三個量並經 ``submit_event`` 回報結果事件（契約 §10 的完整往返）。

三個量與觀測源（語義映射 2026-10-27 使用者裁決）：

- **該記多久 ``retention_seconds`` ← ``drift{zeta,eta}``**：系統變動越快，
  舊記憶越快過時 → 留短。取**已觀測鍵的最大值**（漂移的語義是「變化最快
  的那一面」），線性壓縮、10% 為地板（再怎麼動盪，剛存下的經驗也該活過
  最短的一段時間）。觀測源是 2b/2c 接好的 ζ（異常對佔比）與 η（模組組成
  對稱差）——policy 直接消費本計畫前幾項的真值。
- **多重 ``weight`` ← ``intensity``**：生命強度越高，編碼越該加權
  —— ``weight = 0.5 + intensity ∈ [0.5, 1.5]``（中強度 0.5 → 1.0 中性）。
- **該固化嗎 ``consolidate`` ← ``life_phase == "CONSOLIDATION"``**：鞏固
  階段才定型；其他階段與未觀測都不固化。

**D11**：任一觀測源缺席 → 該量退基準值，``source`` 標 ``"default"``；
執行側只對 ``"state"`` 的量改變記憶行為——未觀測不動現行規則。

三條紀律（同 ``al_state``）：純函式、無 I/O、無 ``ai.*``（I8）；
同快照 → 同策略（I6 可重放）；快照只讀。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict

from core.life.al_state import ALSnapshot

# 基準保留期 30 天 —— 與 HAM `_RETENTION_DAYS_LOW` 同尺度（該層自己的註解：
# 「一年沒用過的低重要性記憶是噪聲」；30 天是記憶層現行的低階保留期）。
BASE_RETENTION_SECONDS = 30.0 * 86400.0
# 漂移拉滿（drift = 1）時的地板：基準的 10%（3 天）。
RETENTION_FLOOR_RATIO = 0.1
# weight = WEIGHT_BASE + WEIGHT_GAIN * intensity → [0.5, 1.5]，中性點 1.0。
WEIGHT_BASE = 0.5
WEIGHT_GAIN = 1.0
# 固化只認這個階段名（``LifePhase.name`` 經 ``_phase_str`` 序列化）。
CONSOLIDATION_PHASE = "CONSOLIDATION"

_SOURCE_STATE = "state"
_SOURCE_DEFAULT = "default"


@dataclass(frozen=True)
class RetentionPolicy:
    """§10 的交換量：記憶層執行的三個決定＋逐量歸因（I9/D11）。

    ``source`` 每量一鍵（``retention`` / ``weight`` / ``consolidate``）：
    ``"state"`` ＝由觀測驅動、執行側照辦；``"default"`` ＝觀測缺席退
    基準、執行側不動記憶的現行規則。
    """

    retention_seconds: float
    weight: float
    consolidate: bool
    source: Dict[str, str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "retention_seconds": self.retention_seconds,
            "weight": self.weight,
            "consolidate": self.consolidate,
            "source": dict(self.source),
        }


def _finite_float(value: Any) -> float | None:
    """Coerce to a finite float; None/NaN/inf → ``None``（不可觀測）。"""
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def retention_policy(snapshot: ALSnapshot) -> RetentionPolicy:
    """純函式：唯讀快照 → 保留策略（無 I/O、可重放，§5 同款紀律）。

    只讀 ``drift`` / ``intensity`` / ``life_phase`` 三個觀測欄；其餘欄位
    不看（策略不由健康分、年齡等欄位驅動 —— 每加一個觀測源要先在契約
    記語義，不默認接）。
    """
    # --- 該記多久 ← drift（max of observed keys, clamped [0, 1]）---------
    retention_seconds = BASE_RETENTION_SECONDS
    retention_source = _SOURCE_DEFAULT
    drift_observed = None
    if isinstance(snapshot.drift, dict) and snapshot.drift:
        # 0.0 是合法觀測（量到穩定），只濾不可觀測（None/NaN/inf）
        values = [
            v for v in (_finite_float(raw) for raw in snapshot.drift.values()) if v is not None
        ]
        if values:
            drift_observed = min(max(max(values), 0.0), 1.0)
    if drift_observed is not None:
        retention_seconds = max(
            BASE_RETENTION_SECONDS * (1.0 - drift_observed),
            BASE_RETENTION_SECONDS * RETENTION_FLOOR_RATIO,
        )
        retention_source = _SOURCE_STATE

    # --- 多重 ← intensity ---------------------------------------------------
    weight = 1.0
    weight_source = _SOURCE_DEFAULT
    intensity = _finite_float(snapshot.intensity)
    if intensity is not None:
        intensity = min(max(intensity, 0.0), 1.0)
        weight = WEIGHT_BASE + WEIGHT_GAIN * intensity
        weight_source = _SOURCE_STATE

    # --- 該固化嗎 ← life_phase --------------------------------------------
    consolidate = False
    consolidate_source = _SOURCE_DEFAULT
    if snapshot.life_phase is not None:
        consolidate = str(snapshot.life_phase).upper() == CONSOLIDATION_PHASE
        consolidate_source = _SOURCE_STATE

    return RetentionPolicy(
        retention_seconds=retention_seconds,
        weight=weight,
        consolidate=consolidate,
        source={
            "retention": retention_source,
            "weight": weight_source,
            "consolidate": consolidate_source,
        },
    )
