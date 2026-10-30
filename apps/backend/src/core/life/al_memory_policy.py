# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [A] [L0-L11]
# =============================================================================
"""§10 與記憶的介面：AL 輸出 retention/decay policy（策略，不是內容）。

三分法 Phase 2 item ④。本模組只有一件事：**由唯讀快照算出一份保留策略**
—— ``retention_policy(snapshot) -> RetentionPolicy``。記憶層（HAM）執行
三個量並經 ``submit_event`` 回報結果事件（契約 §10 的完整往返）。

三個量與觀測源（語義映射 2026-10-27 使用者裁決）：

- **該記多久 ``retention_seconds`` ← ``drift{zeta,eta,identity}``**：系統變動越快，
  舊記憶越快過時 → 留短。取**已觀測鍵的最大值**（漂移的語義是「變化最快
  的那一面」），線性壓縮、10% 為地板（再怎麼動盪，剛存下的經驗也該活過
  最短的一段時間）。觀測源是 2b/2c 接好的 ζ（異常對佔比）、η（模組組成
  對稱差）與 ``identity``（身份離開錨**且仍在動**的量，2026-10-28 起）——
  ``identity`` 只在確認漂移時才 > 0，所以它進最大值時語義仍是「正在變動」，
  不會把「穩定地長離了初始」誤當成動盪。
- **多重 ``weight`` ← ``intensity`` ×``emotion.arousal``**：生命強度越高，
  編碼越該加權 —— ``0.5 + intensity ∈ [0.5, 1.5]``（中強度 0.5 → 1.0 中性）；
  再乘喚醒度因子 ``1 + 0.4·(a − 0.3) ∈ [0.88, 1.28]``（以靜息基線為中性，
  2026-10-30；只有 ``emotion.arousal`` 被觀測到才乘，未觀測不動現行規則）。
- **該固化嗎 ``consolidate`` ← ``life_phase == "CONSOLIDATION"``，且
  ``drift["identity"] == 0``**：鞏固階段才定型；**身份正在離開錨且仍在動時
  不固化**（2026-10-28 的固化閘，觀測源 ``core/life/identity_drift.py``）——
  閘只延後保護，不改寫任何狀態值，所以不碰契約 Q3「修正過頭會抹平生命」。
  其他階段與未觀測都不固化。

**D11**：任一觀測源缺席 → 該量退基準值，``source`` 標 ``"default"``；
執行側只對 ``"state"`` 的量改變記憶行為——未觀測不動現行規則。

三條紀律（同 ``al_state``）：純函式、無 I/O、無 ``ai.*``（I8）；
同快照 → 同策略（I6 可重放）；快照只讀。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict

from core.life.al_arousal import AROUSAL_BASELINE
from core.life.al_state import ALSnapshot

# 基準保留期 30 天 —— 與 HAM `_RETENTION_DAYS_LOW` 同尺度（該層自己的註解：
# 「一年沒用過的低重要性記憶是噪聲」；30 天是記憶層現行的低階保留期）。
BASE_RETENTION_SECONDS = 30.0 * 86400.0
# 漂移拉滿（drift = 1）時的地板：基準的 10%（3 天）。
RETENTION_FLOOR_RATIO = 0.1
# weight = WEIGHT_BASE + WEIGHT_GAIN * intensity → [0.5, 1.5]，中性點 1.0。
WEIGHT_BASE = 0.5
WEIGHT_GAIN = 1.0
# 喚醒度對編碼加權的調節（2026-10-30，AL 垂直切片）：``factor = 1 + GAIN·(a − baseline)``，
# 以靜息基線為中性點（平靜時不動現行規則），a ∈ [0,1] → factor ∈ [0.88, 1.28]。
# 語義：喚醒度高時發生的事該記得更牢；觀測源是 ``emotion.arousal``（時間上
# 逼近 target 的 fast 狀態），所以同一句話在不同「歷史」下會得到不同權重。
AROUSAL_GAIN = 0.4
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
    """Coerce to a finite float; None/NaN/inf/bool/非數字 → ``None``（不可觀測）。

    ``bool`` 也擋：``True`` 進 float 欄位是型別錯，被讀成 1.0 會讓一個
    沒量過的量看起來「拉滿」（D11 的同一件事：壞型別 = 未觀測）。
    """
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def retention_policy(snapshot: ALSnapshot) -> RetentionPolicy:
    """純函式：唯讀快照 → 保留策略（無 I/O、可重放，§5 同款紀律）。

    只讀 ``drift`` / ``intensity`` / ``life_phase`` / ``emotion.arousal`` 四個觀測欄；其餘欄位
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

    # --- 多重 ← intensity ×（喚醒度調節）-----------------------------------
    weight = 1.0
    weight_source = _SOURCE_DEFAULT
    intensity = _finite_float(snapshot.intensity)
    if intensity is not None:
        intensity = min(max(intensity, 0.0), 1.0)
        weight = WEIGHT_BASE + WEIGHT_GAIN * intensity
        weight_source = _SOURCE_STATE
    arousal = (
        _finite_float(snapshot.emotion.get("arousal"))
        if isinstance(snapshot.emotion, dict)
        else None
    )
    if arousal is not None:
        arousal = min(max(arousal, 0.0), 1.0)
        weight *= 1.0 + AROUSAL_GAIN * (arousal - AROUSAL_BASELINE)
        weight_source = _SOURCE_STATE

    # --- 該固化嗎 ← life_phase + 身份漂移閘 -------------------------------
    consolidate = False
    consolidate_source = _SOURCE_DEFAULT
    if snapshot.life_phase is not None:
        consolidate = str(snapshot.life_phase).upper() == CONSOLIDATION_PHASE
        consolidate_source = _SOURCE_STATE

    # 固化閘（2026-10-28）：``drift["identity"] > 0`` ＝ 身份正在離開錨**且仍在
    # 動**（`core/life/identity_drift.py` 的 confirmed 條件，兩者缺一不可）。
    # 還沒定型的自我不該把記憶永久保護起來 —— 噪音固化成人格，正是衰減/固化
    # 邊界要防的那一格。鍵缺席（未觀測）或 0.0（觀測到沒在漂）→ 不動原判定；
    # 被閘擋下時決定來自觀測 → source 標 state（D11/I9 逐量歸因）。
    identity_drift = (
        _finite_float(snapshot.drift.get("identity")) if isinstance(snapshot.drift, dict) else None
    )
    if identity_drift is not None and identity_drift > 0.0:
        consolidate = False
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
