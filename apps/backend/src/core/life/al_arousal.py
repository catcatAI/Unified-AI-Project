# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [A] [L0-L11]
# =============================================================================
"""AL 第一個「真有時間」的欄位：``emotion.arousal``（契約 §3.2 fast 欄位）。

AL 垂直切片（2026-10-30）。契約 §0 說 AL 底層只有四件事：時鐘、狀態、
轉移、錨；此前快照上的欄位不是讀別人的現值（intensity/tendency），就是
恆 ``None``（emotion）。這裡把一個欄位從頭到尾做完整，證明「時間作用在
狀態上」這件事在 AL 內部成立，而不是靠文字塞進 prompt：

1. **事件只改 target，不直接改 v**（§5）：觀測到的喚醒度設定 ``target``，
   ``arousal`` 以 ``τ_rise`` 逼近 ``target``；``target`` 自己以 ``τ_fall``
   回落到基線。兩級都是 §5 唯一算子 ``v ← target + (v−target)·e^(−dt/τ)``，
   串接後有閉式解，所以 **任意取樣頻率得到同一結果**（§4.2：多迴圈只是
   取樣頻率，不是時間基準；可重放，I6）。
2. **跨重啟連續**（§4.4）：狀態連同時間戳落盤；重啟後讀回、再按實際經過
   的時間衰減，不是歸零、也不是凍結。
3. **未觀測一律 ``None``**（D11）：沒收過任何事件前，``arousal()`` 是
   ``None``，不是 0.0，也不是基線。
4. **時鐘注入**：``AffectTracker(clock=...)``。轉移是純函式，吃明確的
   ``now``；測試餵假時鐘，不睡覺、不碰 wall-clock。

**與契約 §4 的一處偏離（需決策）**：§4.1 要求所有衰減的 ``dt`` 由 tick 推進
計算。但 ``al_state.advance_tick`` 目前**沒有任何生產呼叫者**（``ticks``
永遠停在 0），沒有 tick 可供換算。本切片因此以注入的時鐘作為 ``dt`` 的
供應者（生產預設 ``time.time``，跨重啟需要可比的時間軸）。tick 來源接上後，
只需換掉注入的 clock，轉移函式不用動。

**喚醒度的觀測源是關鍵字推斷**（``EmotionAnalyzer``，非量測）：事件 payload
由生產者標 ``source``，本模組只負責「類別＋強度 → 喚醒度」的單一映射。

三條紀律（同 ``al_state``）：轉移是純函式、無 I/O、無 ``ai.*``（I8）；
``derived`` 不落盤（這裡落盤的是 fast 狀態，不是投影）；對狀態的寫只經
``al_state.submit_event``（I7），本模組不提供第二條寫路徑給外部。
"""

from __future__ import annotations

import dataclasses
import json
import logging
import math
import os
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional, Union

from core.data_config import get_data_root
from core.system.config.magic_numbers import threshold_value

logger = logging.getLogger(__name__)

AFFECT_STATE_VERSION = 1

# 靜息喚醒度。不是配置鍵：記憶策略（al_memory_policy）以它為中性點，兩邊
# 必須同值，所以放常數而非可調鍵。
AROUSAL_BASELINE = 0.3

# τ：fast 欄位屬「秒～分」級（§3.1）。走配置鍵（§7.2 慣例）。
DEFAULT_TAU_RISE_S = 20.0  # arousal 逼近 target
DEFAULT_TAU_FALL_S = 300.0  # target 回落到基線
TAU_RISE_KEY = "al_arousal_tau_rise_s"
TAU_FALL_KEY = "al_arousal_tau_fall_s"

# 類別 → 滿強度時的喚醒度（PAD 的 A 軸，0..1）。類別名與
# ``services.llm.emotion_analyzer`` 的七類一致；未知類別 → 不觀測（D11）。
CATEGORY_AROUSAL: Dict[str, float] = {
    "angry": 0.85,
    "fear": 0.85,
    "surprise": 0.75,
    "happy": 0.65,
    "curious": 0.5,
    "sad": 0.35,
    "calm": 0.1,
}

Clock = Callable[[], float]
PathLike = Union[str, Path]


# =========================================================================
# 純函式：§5 算子與串接轉移
# =========================================================================
def _clamp01(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def _finite(value: object) -> Optional[float]:
    """有限浮點，否則 ``None``；``bool`` 也擋（True 不是 1.0 的觀測）。"""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def relax(value: float, target: float, dt: float, tau: float) -> float:
    """§5 唯一算子：``target + (value − target)·e^(−dt/τ)``。

    ``dt ≤ 0`` 或不是有限數 → 原值（時鐘倒退不產生負衰減）；
    ``τ ≤ 0`` → 立即到位。
    """
    if not math.isfinite(dt) or dt <= 0.0:
        return value
    if tau <= 0.0:
        return target
    return target + (value - target) * math.exp(-dt / tau)


@dataclass(frozen=True)
class AffectState:
    """arousal 的完整狀態：現值、目標、上次更新的時鐘讀數。"""

    arousal: float
    target: float
    at: float


def advance(
    state: AffectState,
    now: float,
    *,
    baseline: float = AROUSAL_BASELINE,
    tau_rise: float = DEFAULT_TAU_RISE_S,
    tau_fall: float = DEFAULT_TAU_FALL_S,
) -> AffectState:
    """把狀態推進到 ``now``（無事件，只有時間）。

    兩級一階濾波串接的**閉式解**：target 以 ``τ_fall`` 回落到 ``baseline``，
    arousal 以 ``τ_rise`` 追 target。閉式解讓結果與取樣頻率無關：
    ``advance(advance(s, t1), t2) == advance(s, t2)``（半群性，測試釘住）。
    """
    dt = now - state.at
    if not math.isfinite(dt) or dt <= 0.0:
        return state

    d0 = state.target - baseline
    u0 = state.arousal - baseline
    ef = math.exp(-dt / tau_fall) if tau_fall > 0.0 else 0.0

    if tau_rise <= 0.0:
        u = d0 * ef  # 立即跟上 target
    elif tau_fall <= 0.0:
        u = u0 * math.exp(-dt / tau_rise)  # target 立即回基線，只剩 u0 的衰減
    else:
        er = math.exp(-dt / tau_rise)
        if abs(tau_fall - tau_rise) <= 1e-9 * max(tau_fall, tau_rise):
            u = (u0 + d0 * dt / tau_rise) * er  # τ 相等的極限形式
        else:
            u = u0 * er + d0 * tau_fall / (tau_fall - tau_rise) * (ef - er)

    return AffectState(
        arousal=_clamp01(baseline + u),
        target=_clamp01(baseline + d0 * ef),
        at=now,
    )


def observe(
    state: Optional[AffectState],
    level: float,
    now: float,
    *,
    baseline: float = AROUSAL_BASELINE,
    tau_rise: float = DEFAULT_TAU_RISE_S,
    tau_fall: float = DEFAULT_TAU_FALL_S,
) -> AffectState:
    """吃一筆觀測：先推進到 ``now``，**只改 target**（§5「事件只改 target」）。

    第一筆觀測前沒有狀態：以靜息基線起算（一個剛醒來的生命從靜息開始，
    喚醒度要由後續的時間逼近 target，而不是一步跳到觀測值）。
    """
    if state is None:
        current = AffectState(arousal=baseline, target=baseline, at=now)
    else:
        current = advance(state, now, baseline=baseline, tau_rise=tau_rise, tau_fall=tau_fall)
    return dataclasses.replace(current, target=_clamp01(level), at=max(current.at, now))


def arousal_level(
    emotion: object, intensity: object, baseline: float = AROUSAL_BASELINE
) -> Optional[float]:
    """分類結果 → 喚醒度觀測值；無法觀測回 ``None``（D11）。

    強度 0 = 沒有訊號 → 基線；強度 1 = 該類別的滿喚醒度；中間線性內插。
    """
    category = CATEGORY_AROUSAL.get(str(emotion).strip().lower()) if emotion is not None else None
    strength = _finite(intensity)
    if category is None or strength is None:
        return None
    return _clamp01(baseline + (category - baseline) * _clamp01(strength))


# =========================================================================
# 有狀態的包裝：落盤、時鐘注入、鎖
# =========================================================================
def _tau(key: str, default: float) -> float:
    value = _finite(threshold_value(key, default))
    return value if value is not None and value >= 0.0 else default


class AffectTracker:
    """持有一份 :class:`AffectState`，負責落盤與時鐘。

    對外只有讀：``arousal()``。寫入口是 ``al_state.submit_event``（I7），
    它再呼叫 :meth:`observe_level`。
    """

    def __init__(self, path: Optional[PathLike] = None, clock: Clock = time.time) -> None:
        self._path = Path(path) if path is not None else get_data_root() / "al_affect.json"
        self._clock = clock
        self._lock = threading.Lock()
        self._state: Optional[AffectState] = self._load()

    # -- 參數（每次讀配置，改鍵立即生效）-------------------------------
    @staticmethod
    def _params() -> Dict[str, float]:
        return {
            "baseline": AROUSAL_BASELINE,
            "tau_rise": _tau(TAU_RISE_KEY, DEFAULT_TAU_RISE_S),
            "tau_fall": _tau(TAU_FALL_KEY, DEFAULT_TAU_FALL_S),
        }

    # -- 讀 ----------------------------------------------------------------
    def arousal(self) -> Optional[float]:
        """現在的喚醒度；從未觀測 → ``None``（D11）。純讀，不落盤。"""
        with self._lock:
            if self._state is None:
                return None
            return advance(self._state, self._clock(), **self._params()).arousal

    # -- 寫（只給 al_state.submit_event 呼叫）--------------------------------
    def observe_level(self, level: float) -> None:
        with self._lock:
            self._state = observe(self._state, level, self._clock(), **self._params())
            self._save(self._state)

    # -- 落盤 --------------------------------------------------------------
    def _load(self) -> Optional[AffectState]:
        if not self._path.is_file():
            return None
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("[ALAffect] unreadable state file %s: %s", self._path, exc)
            return None
        if not isinstance(data, dict) or data.get("version") != AFFECT_STATE_VERSION:
            logger.warning(
                "[ALAffect] unrecognised state file %s; treating as unobserved", self._path
            )
            return None
        arousal, target, at = (_finite(data.get(k)) for k in ("arousal", "target", "at"))
        if arousal is None or target is None or at is None:
            logger.warning("[ALAffect] malformed state in %s; treating as unobserved", self._path)
            return None
        return AffectState(arousal=_clamp01(arousal), target=_clamp01(target), at=at)

    def _save(self, state: AffectState) -> None:
        payload = {
            "version": AFFECT_STATE_VERSION,
            "arousal": state.arousal,
            "target": state.target,
            "at": state.at,
        }
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(
                dir=self._path.parent, prefix=".al_affect.", suffix=".tmp"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(payload, fh)
                os.replace(tmp_name, self._path)
            except BaseException:
                if os.path.exists(tmp_name):
                    os.unlink(tmp_name)
                raise
        except OSError as exc:
            # 落盤失敗不拖垮對話，但要留下聲音：跨重啟連續性此刻失效。
            logger.warning("[ALAffect] could not persist %s: %s", self._path, exc)


_TRACKER: Optional[AffectTracker] = None
_TRACKER_LOCK = threading.Lock()


def get_affect_tracker() -> AffectTracker:
    """進程級單例（首次使用才建，路徑取當時的 data root）。"""
    global _TRACKER
    with _TRACKER_LOCK:
        if _TRACKER is None:
            _TRACKER = AffectTracker()
        return _TRACKER


def set_affect_tracker(tracker: Optional[AffectTracker]) -> None:
    """換掉（或清掉）單例 —— 測試隔離用；生產不呼叫。"""
    global _TRACKER
    with _TRACKER_LOCK:
        _TRACKER = tracker
