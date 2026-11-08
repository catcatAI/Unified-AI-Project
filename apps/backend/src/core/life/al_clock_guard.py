# =============================================================================
# ANGELA-MATRIX: [L2] [αβ] [B] [L2]
# =============================================================================
"""AL 的時鐘存疑：對「現在幾點」有自己的估計與不確定度。

到目前為止 AL 對時間是**照單全收**的：`al_arousal` 吃注入的 `clock`，時鐘
倒退就當作沒有經過時間（值凍結），時鐘前跳就整段衰減。這在行為上分辨不出
「被偽造的時鐘」與「真的過了很久」，而 review §11.3 把這件事列為機制證據
的第一項：**一個有自己時間估計的系統，應該對外部給的時間存疑。**

判準（可執行，不靠宣稱）：

- 系統有兩個時間來源。`time.monotonic()` **不能**被偽造或跳躍（它只會單調
  前進）；`time.time()` 可以（NTP 校時、時區、使用者改鐘、注入的假時鐘）。
- 每一次取樣，用單調時鐘算「實際經過多久」（`expected`），用 wall-clock 算
  「聲稱經過多久」（`observed`）。
- 兩者不一致超過容忍度 → `suspicion`。容忍度取 `max(abs_tolerance,
  rel_tolerance * expected)`：間隔很短時要求絕對誤差，間隔長時允許比例誤差。
- 漂移用 EWMA 追蹤（`rate`），所以「一直慢一點」的正常漂移不會被當成偽造，
  只有**突變**才會。

邊界（誠實標記）：

- 同時偽造兩個來源的攻擊，這裡偵測不到——因為沒有第三個時間來源可用。這不
  是缺陷，是系統邊界的定義（review §11.6）。
- 這個模組**不改轉移**、不落盤、不做 I/O；它只回答「這個讀數可不可信」。
  存疑之後要不要凍結狀態，是呼叫者的決定（目前 `AffectTracker` 仍然照舊
  推進，但會把狀態記在 `clock_status()` 上，供上層與稽核讀取）。

用法::

    guard = ClockGuard()
    verdict = guard.sample(now=time.time(), monotonic=time.monotonic())
    if verdict.suspicion:
        logger.warning("clock looks wrong: %s", verdict.reason)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

# 容忍度：短間隔看絕對值（秒），長間隔看比例。實測的正常漂移遠小於此。
DEFAULT_ABS_TOLERANCE_S = 5.0
DEFAULT_REL_TOLERANCE = 0.25

# 漂移 EWMA 的平滑係數：0.2 表示約 5 個樣本追上，足夠慢到不被單一異常帶走。
DEFAULT_DRIFT_ALPHA = 0.2

# 單次樣本最多相信多少秒的間隔（再長就沒有估計意義，只更新基準）。
MAX_MEASURED_INTERVAL_S = 6 * 3600.0


@dataclass(frozen=True)
class ClockVerdict:
    """一次取樣的判讀結果。

    - ``ok``：沒有異常（也包含「第一次取樣，無從比較」）。
    - ``suspicion``：本次讀數與單調時鐘不一致；``reason`` 說明是哪一種。
    - ``disagreement``：``observed - expected``（秒）。正值＝wall-clock 跑得
      比實際快（前跳或偽造），負值＝跑得比實際慢（倒退）。
    - ``rate``：本次 ``observed / expected``；``drift`` 是它的 EWMA。
    - ``samples``：累積樣本數。
    """

    ok: bool
    suspicion: bool
    reason: str
    observed: Optional[float]
    expected: Optional[float]
    disagreement: Optional[float]
    rate: Optional[float]
    drift: Optional[float]
    samples: int


class ClockGuard:
    """追蹤 wall-clock 與單調時鐘的偏差，對突變存疑。

    純記憶體、執行緒不安全（呼叫端自己鎖）；沒有 I/O，所以測試可以完全不
    碰真實時鐘。``drift`` 是「wall-clock 相對單調時鐘的速率」，1.0 表示一致。
    """

    def __init__(
        self,
        *,
        abs_tolerance_s: float = DEFAULT_ABS_TOLERANCE_S,
        rel_tolerance: float = DEFAULT_REL_TOLERANCE,
        drift_alpha: float = DEFAULT_DRIFT_ALPHA,
    ) -> None:
        if abs_tolerance_s < 0.0 or rel_tolerance < 0.0:
            raise ValueError("tolerances must be non-negative")
        if not 0.0 < drift_alpha <= 1.0:
            raise ValueError("drift_alpha must be in (0, 1]")
        self._abs_tol = abs_tolerance_s
        self._rel_tol = rel_tolerance
        self._alpha = drift_alpha
        self._last_now: Optional[float] = None
        self._last_mono: Optional[float] = None
        self._drift: Optional[float] = None
        self._samples = 0

    # -- 讀 ------------------------------------------------------------------
    @property
    def drift(self) -> Optional[float]:
        return self._drift

    @property
    def samples(self) -> int:
        return self._samples

    def reset(self) -> None:
        """清空基準（時鐘被判定為不可信、準備換一個來源時用）。"""
        self._last_now = None
        self._last_mono = None
        self._drift = None
        self._samples = 0

    # -- 判讀 ----------------------------------------------------------------
    def sample(self, now: float, monotonic: float) -> ClockVerdict:
        """吃一組讀數並判讀。

        第一筆只建立基準（``ok=True``、``suspicion=False``）。之後每一筆都與
        單調時鐘對照。
        """
        if not (math.isfinite(now) and math.isfinite(monotonic)):
            return ClockVerdict(
                ok=False,
                suspicion=True,
                reason="non-finite clock reading",
                observed=None,
                expected=None,
                disagreement=None,
                rate=None,
                drift=self._drift,
                samples=self._samples,
            )

        if self._last_now is None or self._last_mono is None:
            self._last_now, self._last_mono = now, monotonic
            self._samples = 1
            return ClockVerdict(
                ok=True,
                suspicion=False,
                reason="baseline",
                observed=None,
                expected=None,
                disagreement=None,
                rate=None,
                drift=None,
                samples=self._samples,
            )

        expected = monotonic - self._last_mono
        observed = now - self._last_now
        self._samples += 1

        # 基準一律前進：即使本次可疑，下一次仍要與「現在」比較，否則一個
        # 假時鐘會永久污染後續所有判斷。
        self._last_now, self._last_mono = now, monotonic

        if expected <= 0.0:
            # 單調時鐘不動（同一毫秒內連讀）：沒有可比資訊，不判。
            return self._verdict(
                suspicion=False,
                reason="no elapsed reference",
                observed=observed,
                expected=expected,
                disagreement=None,
                rate=None,
            )

        if expected > MAX_MEASURED_INTERVAL_S:
            # 太久沒取樣：漂移估計已經沒有意義，只重建基準。
            self._drift = None
            return self._verdict(
                suspicion=False,
                reason="sample gap too long to compare",
                observed=observed,
                expected=expected,
                disagreement=None,
                rate=None,
            )

        # ``expected <= 0`` returned above, so the ratio always exists here.
        rate = observed / expected
        disagreement = observed - expected
        tolerance = max(self._abs_tol, self._rel_tol * expected)

        reference = self._drift if self._drift is not None else 1.0
        deviation = abs(rate - reference)
        suspicious = abs(disagreement) > tolerance or deviation > self._rel_tol

        if suspicious:
            reason = "clock went backwards" if observed < 0 else "clock rate jumped"
        else:
            reason = "ok"
            # 只有正常樣本才更新漂移：否則攻擊會把基準一起帶走。
            if self._drift is None:
                self._drift = rate
            else:
                self._drift = (1 - self._alpha) * self._drift + self._alpha * rate

        return self._verdict(
            suspicion=suspicious,
            reason=reason,
            observed=observed,
            expected=expected,
            disagreement=disagreement,
            rate=rate,
        )

    def _verdict(
        self,
        *,
        suspicion: bool,
        reason: str,
        observed: Optional[float],
        expected: Optional[float],
        disagreement: Optional[float],
        rate: Optional[float],
    ) -> ClockVerdict:
        return ClockVerdict(
            ok=not suspicion,
            suspicion=suspicion,
            reason=reason,
            observed=observed,
            expected=expected,
            disagreement=disagreement,
            rate=rate,
            drift=self._drift,
            samples=self._samples,
        )


# =============================================================================
# 進程級單例：讓 AffectTracker 不必自己管理一個 guard
# =============================================================================
_GUARD: Optional[ClockGuard] = None


def get_clock_guard() -> ClockGuard:
    global _GUARD
    if _GUARD is None:
        _GUARD = ClockGuard()
    return _GUARD


def set_clock_guard(guard: Optional[ClockGuard]) -> None:
    """測試隔離用；生產不呼叫。"""
    global _GUARD
    _GUARD = guard
