"""身份漂移（`core/life/identity_drift.py`）的數學與語義契約（契約 §6）。

本檔釘住六件事：

1. **時間係數住在配置裡**（§7.2「τ 是配置鍵」）—— 模組預設值與
   `configs/standard/behavior/behavior.default.yaml` 必須一致，防再變成
   無讀者的死鍵（同區那批 `identity_continuity_*` 就是前車之鑑）。
2. **注入漂移 → 指標單調上升**（契約 §13.2 驗收判據 4）。
3. **相關係數不能反證漂移**：r 對位移不變，錨是常數時 `dx/dy` 退化，
   倉內 `TemporalState.correlation` 會回 `0.0`（偽裝成「無關」）——
   這條測試就是「為什麼本模組不放 r」的證據。
4. **偏離錨但已平息 ≠ 漂移中**：長成新的人格不該被判成病態（`moving` 閘）。
5. **未觀測不裝觀測**（D11）：點數不足 → `observed=False`、`worst_*` 回 `None`。
6. **純性與可重放**（I6）：同輸入同輸出，與時間順序無關（會自行排序）。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_SRC = Path(__file__).resolve().parents[2] / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from core.life.identity_drift import (  # noqa: E402
    ANCHOR_NONE,
    ANCHOR_ORIGIN,
    ANCHOR_SUPPLIED,
    MIN_POINTS,
    TAU_FAST,
    TAU_SLOW,
    Z_THRESHOLD,
    identity_drift,
    worst_identity_drift,
)
from core.state.temporal import TemporalState  # noqa: E402


def _history(values, *, dimension: str = "mu", start: float = 0.0):
    return [(start + i, {dimension: value}) for i, value in enumerate(values)]


class TestTimeConstantsLiveInConfig:
    def test_configured_values_are_reachable(self):
        """讀得到配置 = 鍵有讀者（不是死鍵）。失敗即表示接線漏了。

        τ 用 `lifecycle_value` 而非 `timing_value` —— 後者乘硬體倍率，
        會讓同一份配置在不同機器上量出不同的人格時間常數。
        """
        from core.system.config.magic_numbers import (
            lifecycle_value,
            limit_value,
            threshold_value,
        )

        assert lifecycle_value("identity_tau_slow", 999.0) == TAU_SLOW
        assert lifecycle_value("identity_tau_fast", 999.0) == TAU_FAST
        assert threshold_value("identity_z_threshold", 999.0) == Z_THRESHOLD
        assert limit_value("identity_min_points", 999) == MIN_POINTS

    @pytest.mark.parametrize("tau", [0.0, -1.0, float("nan"), float("inf")])
    def test_non_positive_time_constant_is_rejected(self, tau):
        history = _history([0.5] * 10)
        with pytest.raises(ValueError):
            identity_drift(history, "mu", tau_slow=tau)
        with pytest.raises(ValueError):
            identity_drift(history, "mu", tau_fast=tau)


class TestAnchoredDistance:
    def test_origin_anchor_is_the_first_observation(self):
        history = _history([0.5] * 40 + [0.5 + 0.4 * i / 39 for i in range(40)])
        evidence = identity_drift(history, "mu")
        assert evidence.anchor_source == ANCHOR_ORIGIN
        assert evidence.anchor == pytest.approx(0.5)

    def test_supplied_anchor_replaces_the_origin(self):
        history = _history([0.7] * 40)
        evidence = identity_drift(history, "mu", anchor=0.5)
        assert evidence.anchor_source == ANCHOR_SUPPLIED
        assert evidence.anchor == pytest.approx(0.5)
        assert evidence.distance == pytest.approx(0.2)

    def test_unobservable_supplied_anchor_withholds_the_measurement(self):
        """供給的錨不可觀測 → 沒有錨就沒有距離，不拿第一筆冒充（D11）。"""
        evidence = identity_drift(_history([0.7] * 40), "mu", anchor=float("nan"))
        assert evidence.observed is False
        assert evidence.anchor_source == ANCHOR_NONE
        assert evidence.drift == 0.0

    def test_zero_variance_reports_z_as_none(self):
        """零方差 → 沒有噪聲尺度，z 未定義；絕不偽裝成 0.0 或很大的數。"""
        evidence = identity_drift(_history([0.7] * 40), "mu", anchor=0.5)
        assert evidence.z is None
        assert evidence.distance == pytest.approx(0.2)
        assert evidence.confirmed is False, "偏離但沒有任何移動 = 已經平息"


class TestDriftIsMonotone:
    def test_injected_drift_raises_the_metric_monotonically(self):
        """契約 §13.2-4：注入漂移 → 指標單調上升。"""
        previous = -1.0
        for shift in (0.0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5):
            values = [0.5] * 40 + [0.5 + shift * i / 39 for i in range(40)]
            evidence = identity_drift(_history(values), "mu")
            assert evidence.confirmed or shift == 0.0
            assert evidence.drift >= previous - 1e-12, f"drift 不單調於 shift={shift}"
            previous = evidence.drift
        assert previous > 0.0, "0.5 的注入漂移必須被量到"

    def test_drift_stays_inside_the_unit_interval(self):
        values = [0.0] * 40 + [1.0] * 40
        evidence = identity_drift(_history(values), "mu", anchor=-5.0)
        assert 0.0 <= evidence.drift <= 1.0


class TestCorrelationCannotRefuteDrift:
    def test_constant_anchor_correlation_degrades_to_a_fake_zero(self):
        """錨是常數 → `dy = 0`，倉內實作回 0.0；同一批資料我們量到真漂移。"""
        values = [0.5] * 40 + [0.5 + 0.4 * i / 39 for i in range(40)]
        timeline = TemporalState()
        for i, value in enumerate(values):
            timeline.record({"self": {"mu": value}, "anchor": {"mu": 0.5}})

        shape_only = timeline.correlation("self", "mu", "anchor", "mu")
        assert shape_only.correlation is None, "常數錨 → r 未定義（回 0.0 會被讀成『無關』）"
        assert shape_only.p_value is None, "沒做顯著性檢定就不給 p 值（舊值恆 1.0 是假值）"

        evidence = identity_drift(_history(values), "mu")
        assert evidence.confirmed is True
        assert evidence.drift > 0.2, "距離錨的量測看得見相關係數看不見的位移"


class TestMovementGate:
    def test_settled_far_from_the_anchor_is_not_active_drift(self):
        """離錨很遠但已平息 = 長成了新的人格，不是漂移中。"""
        evidence = identity_drift(_history([0.5] * 10 + [0.9] * 120), "mu")
        assert evidence.distance is not None and evidence.distance > 0.3
        assert evidence.z is not None and evidence.z >= Z_THRESHOLD
        assert evidence.moving is False
        assert evidence.confirmed is False
        assert evidence.drift == 0.0

    def test_fast_noise_around_the_anchor_does_not_confirm(self):
        values = [0.5 + 0.15 * (-1) ** i for i in range(120)]
        evidence = identity_drift(_history(values), "mu")
        assert evidence.confirmed is False
        assert evidence.drift == 0.0


class TestObservationGate:
    def test_too_few_points_is_unobserved(self):
        evidence = identity_drift(_history([0.5, 0.9, 0.1]), "mu")
        assert evidence.observed is False
        assert evidence.points == 3
        assert evidence.z is None
        assert evidence.drift == 0.0

    def test_missing_dimension_and_non_finite_values_are_skipped(self):
        history = [(i, {"other": 1.0}) for i in range(20)]
        history += [(20 + i, {"mu": float("nan")}) for i in range(5)]
        assert identity_drift(history, "mu").observed is False

    def test_worst_returns_none_when_nothing_is_observed(self):
        assert worst_identity_drift(_history([0.5] * 3)) is None
        assert worst_identity_drift([]) is None

    def test_worst_picks_the_largest_confirmed_drift(self):
        history = [
            (
                i,
                {
                    "steady": 0.5,
                    "walking": 0.5 + 0.4 * i / 59,
                },
            )
            for i in range(60)
        ]
        worst = worst_identity_drift(history)
        assert worst is not None
        dimension, evidence = worst
        assert dimension == "walking"
        assert evidence.confirmed and evidence.drift > 0.0

    def test_worst_still_reports_an_observed_stable_state(self):
        """都觀測到但沒在漂 → 回一維、drift=0.0（量到了，與未觀測不同）。"""
        worst = worst_identity_drift(_history([0.5] * 40))
        assert worst is not None
        _, evidence = worst
        assert evidence.observed is True
        assert evidence.drift == 0.0


class TestPurity:
    def test_replay_is_deterministic(self):
        values = [0.5 + 0.01 * i for i in range(30)]
        history = _history(values)
        first = identity_drift(history, "mu")
        second = identity_drift(list(history), "mu")
        assert first == second

    def test_order_of_the_history_does_not_matter(self):
        values = [0.5 + 0.01 * i for i in range(30)]
        shuffled = list(reversed(_history(values)))
        assert identity_drift(shuffled, "mu") == identity_drift(_history(values), "mu")

    def test_evidence_carries_no_side_effects_on_the_history(self):
        history = _history([0.5] * 40)
        snapshot = list(history)
        identity_drift(history, "mu")
        assert history == snapshot
