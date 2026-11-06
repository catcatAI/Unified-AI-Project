# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [A] [L0-L11]
# =============================================================================
"""內生節律源：讓「自發」從一句話變成一個可量測的機制。

上一輪量到的事實是：心跳間隔是 ``(stress, arousal)`` 的無記憶純函數，
輸入不變則間隔不變，所以它**不會自己振盪**。那是一個否定結果，但否定的是
「現有這條路」，不是「自發節律不可能」。要往前走，缺的是一個**自己會動**
的來源；本模組補上它，並且刻意讓它的週期**不是查表、不是寫死的秒數**。

機制：Van der Pol 型鬆弛振盪器

    dx/dt = v
    dv/dt = μ(1 − x²)·v − ω²·x + drive

這是二階非線性 ODE，沒有閉式解。它的極限環**振幅與週期都是從積分裡長出來
的**，不是參數直接指定的：改 μ 會改變波形與週期，改 ω 會整體縮放，而輸出
永遠收斂到同一條極限環（不論初值）。這正是它可被證偽的地方——

- 若程式其實是「每 N 秒輸出一次」，把 μ 改掉週期不會照規律變；
- 若積分沒有收斂，把 ``max_step`` 減半週期會漂移；
- 若它忽略擾動，施加脈衝後相位不會被推走。

三件事本模組都要在 ``scripts/al_rhythm_source.py`` 裡被量，而不是被宣稱。

**它證明什麼、不證明什麼**：這證明「系統內部存在一個不依賴輸入的自持週期，
且該週期是狀態的一部分（可跨重啟接續）」。它**不**證明生命——振盪器本身
只是節律的必要條件，不是生命證據；生命證據仍要過階梯（r1–r7）與偽造品預算。

三條紀律沿用 ``al_state`` / ``al_arousal``：轉移是純函數、無 I/O、無 ``ai.*``；
``activation`` 是投影（不落盤）；落盤的是 fast 狀態 ``(x, v, at)``。
"""

from __future__ import annotations

import json
import logging
import math
import os
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from core.data_config import get_data_root

logger = logging.getLogger(__name__)

OSC_STATE_VERSION = 1

# μ：非線性強度。越大 → 越鬆弛（波形越像方波），週期越長。
DEFAULT_MU = 1.8
# ω：線性部分的角頻率（rad/s）。小 → 慢。
DEFAULT_OMEGA = 0.30
# 積分步長上限。是**精度**參數，不是隱藏的時鐘：內部一律以 ≤ max_step
# 的步長積分，所以對外看起來「任意取樣頻率結果相同」。這條被
# ``test_period_is_not_a_timestep_artifact`` 直接量。
MAX_STEP_S = 0.02

# 重啟後最多補算多少秒。超過就不假裝知道相位（stale=True），因為在
# cpu 上積分一年既慢又沒有意義；寧可誠實標記，不要編一個相位出來。
MAX_CATCHUP_S = 600.0


def _clamp01(value: float) -> float:
    return 0.0 if value < 0.0 else 1.0 if value > 1.0 else value


@dataclass(frozen=True)
class OscState:
    """落盤的 fast 狀態。相位資訊全在 (x, v) 裡，``at`` 是它對應的時刻。"""

    x: float = 0.0
    v: float = 1.0
    at: float = 0.0

    def as_dict(self) -> dict:
        return {"version": OSC_STATE_VERSION, "x": self.x, "v": self.v, "at": self.at}


class Oscillator:
    """二階非線性振盪器。狀態是 ``(x, v)``，積分用 RK4。

    刻意**沒有** `phase` 欄位：相位是 ``(x, v)`` 在極限環上的位置，另外存一份
    只會讓兩者不同步。
    """

    def __init__(
        self,
        mu: float = DEFAULT_MU,
        omega: float = DEFAULT_OMEGA,
        *,
        max_step: float = MAX_STEP_S,
        x: float = 0.0,
        v: float = 1.0,
    ) -> None:
        if mu <= 0.0 or omega <= 0.0:
            raise ValueError("mu and omega must be positive")
        self.mu = float(mu)
        self.omega = float(omega)
        self.max_step = float(max_step)
        self.x = float(x)
        self.v = float(v)

    # --- 轉移（純函數的部分）------------------------------------------------
    def _accel(self, x: float, v: float, drive: float) -> float:
        return self.mu * (1.0 - x * x) * v - self.omega * self.omega * x + drive

    def _rk4(self, dt: float, drive: float) -> None:
        x, v, a = self.x, self.v, self._accel
        k1x, k1v = v, a(x, v, drive)
        k2x, k2v = v + 0.5 * dt * k1v, a(x + 0.5 * dt * k1x, v + 0.5 * dt * k1v, drive)
        k3x, k3v = v + 0.5 * dt * k2v, a(x + 0.5 * dt * k2x, v + 0.5 * dt * k2v, drive)
        k4x, k4v = v + dt * k3v, a(x + dt * k3x, v + dt * k3v, drive)
        self.x = x + dt * (k1x + 2.0 * k2x + 2.0 * k3x + k4x) / 6.0
        self.v = v + dt * (k1v + 2.0 * k2v + 2.0 * k3v + k4v) / 6.0

    def step(self, dt: float, drive: float = 0.0) -> float:
        """前進 ``dt`` 秒（可為 0，不可為負），回傳當下的 activation。"""
        if dt < 0.0:
            raise ValueError("dt must be non-negative")
        remaining = float(dt)
        while remaining > 0.0:
            h = min(self.max_step, remaining)
            self._rk4(h, drive)
            remaining -= h
        return self.activation

    @property
    def phase(self) -> float:
        """極限環上的相位，[0, 1)。

        取相平面的角度：``atan2(−v/ω, x)``。這是無因次量（0..1 就是一圈），
        與週期無關，所以改 μ 時「相位」的意義不變。選這個定義而不是「距離上次
        穿越幾個週期」是因為後者需要一個歷史，而 (x, v) 已經帶著它。
        """
        angle = math.atan2(-self.v / self.omega, self.x)
        return (angle % (2.0 * math.pi)) / (2.0 * math.pi)

    @property
    def activation(self) -> float:
        """0..1 的驅動量。極限環的振幅約 ±2，這裡固定映射，不做自適應正規化。

        自適應正規化會讓「振幅變小」看起來像「振幅正常」，也就抹掉了極限環
        是否還在的那個訊號，所以不用。
        """
        return _clamp01((self.x + 2.0) / 4.0)


def natural_period(
    mu: float = DEFAULT_MU,
    omega: float = DEFAULT_OMEGA,
    *,
    max_step: float = MAX_STEP_S,
    settle_s: float = 60.0,
    measure_s: float = 600.0,
) -> float:
    """量出極限環的週期（秒）。從 ``x=0, v=1`` 起跑，先讓它收斂再量。

    單調上升穿越 ``x = 0`` 的間隔平均。這是「量」不是「算」：沒有任何地方寫
    著週期應該是多少。
    """
    osc = Oscillator(mu=mu, omega=omega, max_step=max_step)
    osc.step(settle_s)
    prev_x = osc.x
    crossings = []
    t = 0.0
    h = 0.05
    while t < measure_s:
        osc.step(h)
        t += h
        if prev_x < 0.0 <= osc.x:
            crossings.append(t)
        prev_x = osc.x
    if len(crossings) < 2:
        raise RuntimeError("oscillator did not produce two cycles")
    diffs = [b - a for a, b in zip(crossings, crossings[1:])]
    return sum(diffs) / len(diffs)


class RhythmTracker:
    """把振盪器的狀態接上時鐘與磁碟：重啟後相位接得上，不是重新起跑。

    與 ``AffectTracker`` 同一套紀律：注入 clock，讀值時才推進，落盤 fast 狀態。
    """

    def __init__(
        self,
        path: Optional[Path] = None,
        *,
        clock: Callable[[], float] = time.time,
        mu: float = DEFAULT_MU,
        omega: float = DEFAULT_OMEGA,
        max_step: float = MAX_STEP_S,
    ) -> None:
        self._clock = clock
        self._lock = threading.Lock()
        self.stale = False
        self._path = (
            Path(path) if path is not None else get_data_root() / "life" / "al_rhythm_state.json"
        )
        self._osc = Oscillator(mu=mu, omega=omega, max_step=max_step)
        loaded = self._load()
        if loaded is None:
            self._osc.step(0.0)
        self._last = loaded if loaded is not None else self._clock()

    # --- 內部 ---------------------------------------------------------------
    def _load(self) -> Optional[float]:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("rhythm state unreadable (%s); starting fresh", exc)
            return None
        if not isinstance(raw, dict) or raw.get("version") != OSC_STATE_VERSION:
            return None
        try:
            self._osc.x = float(raw["x"])
            self._osc.v = float(raw["v"])
            at = float(raw["at"])
        except (KeyError, TypeError, ValueError):
            logger.warning("rhythm state malformed; starting fresh")
            return None
        if not (math.isfinite(self._osc.x) and math.isfinite(self._osc.v) and math.isfinite(at)):
            return None
        return at

    def _save(self) -> None:
        payload = OscState(x=self._osc.x, v=self._osc.v, at=self._last).as_dict()
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=str(self._path.parent), suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh)
            os.replace(tmp, self._path)
        except OSError as exc:
            logger.warning("rhythm state not persisted: %s", exc)

    # --- 公開介面 -----------------------------------------------------------
    def activation(self, now: Optional[float] = None) -> float:
        """推進到 ``now`` 並回傳 0..1 的內生驅動量。"""
        with self._lock:
            now = self._clock() if now is None else float(now)
            dt = now - self._last
            if dt < 0.0:
                # 時鐘倒退：不往前推算，保留狀態（與 ClockGuard 的立場一致）。
                dt = 0.0
            if dt > MAX_CATCHUP_S:
                dt = MAX_CATCHUP_S
                self.stale = True
            self._last = now
            value = self._osc.step(dt)
            self._save()
            return value

    def phase(self) -> float:
        """當下相位 [0, 1)，不推進（與 ``activation`` 不同，這是純讀）。"""
        with self._lock:
            return self._osc.phase

    def activation_preview(self) -> float:
        """當下的驅動量，**不推進、不落盤**。

        ``activation()`` 會推進振盪器並每次 `_save()`，那是給「一次對話一個
        樣本」用的。學習路徑（GARDEN 的 Hebbian 更新）每個樣本都要讀一次
        gain，用 `activation()` 等於每個樣本寫一次磁碟；這裡只讀 (x, v) 的
        現值，代價是一次鎖。
        """
        with self._lock:
            return self._osc.activation

    def state(self) -> dict:
        with self._lock:
            return {
                "x": self._osc.x,
                "v": self._osc.v,
                "at": self._last,
                "phase": self._osc.phase,
                "stale": self.stale,
            }


_tracker: Optional[RhythmTracker] = None
_tracker_lock = threading.Lock()


def get_rhythm_tracker() -> RhythmTracker:
    """生產用的單例。"""
    global _tracker
    with _tracker_lock:
        if _tracker is None:
            _tracker = RhythmTracker()
        return _tracker


def set_rhythm_tracker(tracker: Optional[RhythmTracker]) -> None:
    """測試/量測替換用（傳 None 即清除）。"""
    global _tracker
    with _tracker_lock:
        _tracker = tracker
