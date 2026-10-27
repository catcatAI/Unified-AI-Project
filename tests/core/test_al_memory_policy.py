"""Phase 2 item ④ — §10 retention/decay policy 的純函式契約（AL 側）。

`retention_policy(snapshot) -> RetentionPolicy` 只由唯讀快照算出三個量
（該記多久／多重／該固化嗎），本檔釘住四件事：

1. **未觀測 → 基準 + `source="default"`**（D11）；觀測到 0 也算觀測
   （`{"zeta": 0.0}` 是「量到穩定」，不是沒量）；NaN/inf/壞型別同
   未觀測，不炸。
2. **語義映射**（2026-10-27 使用者裁決）：保留期 ← drift 取已觀測鍵
   最大值、線性壓縮、10% 地板；權重 ← intensity（`0.5 + i`，界限
   [0.5, 1.5]）；固化 ← `life_phase == "CONSOLIDATION"`，**且身份不在漂移中**
   （2026-10-28 的固化閘，見 `TestConsolidationIdentityGate`）。
3. **逐量歸因獨立**（I9）：三個 `source` 各記各的，一個觀測缺席不牽連
   另外兩個。
4. **純性**（I6 可重放）：同快照同策略、快照不被修改、只讀三個觀測欄
   —— `health` 等其他欄位怎麼變都不影響策略。
"""

import dataclasses
import sys
from pathlib import Path

import pytest

BACKEND_SRC = Path(__file__).resolve().parents[2] / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from core.life import al_state  # noqa: E402
from core.life.al_memory_policy import (  # noqa: E402
    BASE_RETENTION_SECONDS,
    RETENTION_FLOOR_RATIO,
    retention_policy,
)

BASE_DAYS = BASE_RETENTION_SECONDS / 86400.0  # 基準 30 天


def _snap(**overrides):
    """受控快照：三個觀測欄預設全 None（全未觀測）。

    不直接吃環境快照 —— test env 的 ``intensity`` 恆有觀測，寫死會讓
    「未觀測退基準」的斷言隨環境漂移。其他欄位（health/tendency/...）
    保留環境真值，因此也能用來驗「其他欄位不影響策略」。
    """
    fields = dict(drift=None, intensity=None, life_phase=None)
    fields.update(overrides)
    return dataclasses.replace(al_state.get_al_state(), **fields)


class TestUnobservedFallsBackToDefaults:
    def test_all_unobserved_returns_base_policy(self):
        policy = retention_policy(_snap())
        assert policy.retention_seconds == BASE_RETENTION_SECONDS
        assert policy.weight == 1.0
        assert policy.consolidate is False
        assert policy.source == {
            "retention": "default",
            "weight": "default",
            "consolidate": "default",
        }

    @pytest.mark.parametrize(
        ("bad_drift", "bad_intensity"),
        [
            ({"zeta": float("nan")}, float("inf")),
            ({"zeta": None}, float("nan")),
            ({"zeta": "not-a-number"}, "also-not"),
        ],
    )
    def test_non_finite_or_badly_typed_observation_is_unobserved(self, bad_drift, bad_intensity):
        # 壞觀測不能把策略炸掉，也不該被當成「觀測到了」（D11）
        policy = retention_policy(_snap(drift=bad_drift, intensity=bad_intensity))
        assert policy.retention_seconds == BASE_RETENTION_SECONDS
        assert policy.weight == 1.0
        assert policy.source["retention"] == "default"
        assert policy.source["weight"] == "default"

    def test_non_dict_drift_field_is_unobserved(self):
        policy = retention_policy(_snap(drift="corrupted"))
        assert policy.source["retention"] == "default"


class TestRetentionFromDrift:
    @pytest.mark.parametrize(
        ("drift", "expect_days"),
        [
            (0.0, 30.0),  # 量到穩定 → 滿期；0 也是觀測（source 必須 state）
            (0.25, 22.5),
            (0.5, 15.0),
            (0.75, 7.5),
            (1.0, 3.0),  # 拉滿 → 10% 地板
            (2.0, 3.0),  # 超上界 → clamp 後落地板
            (-0.5, 30.0),  # 負值 → clamp 到 0
        ],
    )
    def test_linear_compression_with_floor(self, drift, expect_days):
        policy = retention_policy(_snap(drift={"zeta": drift}))
        assert policy.retention_seconds / 86400.0 == pytest.approx(expect_days)
        assert policy.source["retention"] == "state"

    def test_floor_is_never_crossed(self):
        policy = retention_policy(_snap(drift={"zeta": 1.0}))
        assert policy.retention_seconds == pytest.approx(
            BASE_RETENTION_SECONDS * RETENTION_FLOOR_RATIO
        )

    @pytest.mark.parametrize("values", [{"zeta": 0.8, "eta": 0.1}, {"zeta": 0.1, "eta": 0.8}])
    def test_takes_max_of_observed_keys(self, values):
        # drift 的語義是「變化最快的那一面」→ 兩鍵取大
        policy = retention_policy(_snap(drift=values))
        assert policy.retention_seconds / 86400.0 == pytest.approx(6.0)
        assert policy.source["retention"] == "state"

    def test_dict_of_only_unobserved_keys_counts_as_unobserved(self):
        policy = retention_policy(_snap(drift={"zeta": float("nan"), "eta": None}))
        assert policy.source["retention"] == "default"


class TestWeightFromIntensity:
    @pytest.mark.parametrize(
        ("intensity", "expect"),
        [
            (0.0, 0.5),
            (0.25, 0.75),
            (0.5, 1.0),
            (1.0, 1.5),
            (1.4, 1.5),  # clamp 上界
            (-0.3, 0.5),  # clamp 下界
        ],
    )
    def test_weight_is_base_plus_clamped_intensity(self, intensity, expect):
        policy = retention_policy(_snap(intensity=intensity))
        assert policy.weight == pytest.approx(expect)
        assert policy.source["weight"] == "state"

    @pytest.mark.parametrize("intensity", [-10.0, -0.001, 0.0, 0.5, 1.0, 10.0])
    def test_weight_stays_within_bounds(self, intensity):
        policy = retention_policy(_snap(intensity=intensity))
        assert 0.5 <= policy.weight <= 1.5


class TestConsolidationFromPhase:
    def test_consolidation_phase_consolidates(self):
        policy = retention_policy(_snap(life_phase="CONSOLIDATION"))
        assert policy.consolidate is True
        assert policy.source["consolidate"] == "state"

    @pytest.mark.parametrize("phase", ["EMERGENCE", "EXPLORATION", "TRANSCENDENCE", "COEXISTENCE"])
    def test_every_other_phase_does_not_consolidate(self, phase):
        policy = retention_policy(_snap(life_phase=phase))
        assert policy.consolidate is False
        assert policy.source["consolidate"] == "state", "觀測到了，只是不固化"

    def test_phase_match_ignores_case(self):
        # `_phase_str` 保證 uppercase，但 plain 字串 provider 可能給小寫
        policy = retention_policy(_snap(life_phase="consolidation"))
        assert policy.consolidate is True

    def test_unobserved_phase_never_consolidates(self):
        policy = retention_policy(_snap(life_phase=None))
        assert policy.consolidate is False
        assert policy.source["consolidate"] == "default"


class TestPurityAndScope:
    def test_attribution_is_per_quantity(self):
        # 只有 drift 觀測 → 只有 retention 標 state（I9 逐量歸因）
        policy = retention_policy(_snap(drift={"zeta": 0.5}))
        assert policy.source == {
            "retention": "state",
            "weight": "default",
            "consolidate": "default",
        }

    def test_same_snapshot_yields_identical_policy(self):
        snap = _snap(drift={"zeta": 0.4}, intensity=0.6, life_phase="CONSOLIDATION")
        assert retention_policy(snap) == retention_policy(snap)

    def test_snapshot_is_not_mutated(self):
        snap = _snap(drift={"zeta": 0.4}, intensity=0.6, life_phase="CONSOLIDATION")
        before = dataclasses.asdict(snap)
        retention_policy(snap)
        assert dataclasses.asdict(snap) == before

    def test_other_observed_fields_do_not_influence_policy(self):
        # 只讀 drift/intensity/life_phase —— health 怎麼變都不改變策略
        low = retention_policy(_snap(health=0.1))
        high = retention_policy(_snap(health=0.9))
        assert low == high

    def test_as_dict_carries_all_four_keys(self):
        payload = retention_policy(_snap()).as_dict()
        assert set(payload) == {"retention_seconds", "weight", "consolidate", "source"}
        assert isinstance(payload["source"], dict)


class TestConsolidationIdentityGate:
    """固化閘（2026-10-28）：`drift["identity"] > 0` ＝ 身份正在離開錨且仍在動。

    觀測源是 `core/life/identity_drift.py`（契約 §6 距離錨）。還沒定型的自我
    不該把記憶永久保護起來 —— 噪音固化成人格，正是衰減/固化邊界要防的那一格。
    鍵缺席（未觀測）或 0.0（量到沒在漂）一律不動原判定（D11）。
    """

    def test_confirmed_identity_drift_blocks_consolidation(self):
        policy = retention_policy(_snap(life_phase="CONSOLIDATION", drift={"identity": 0.42}))
        assert policy.consolidate is False
        assert policy.source["consolidate"] == "state", "決定來自觀測，不是預設"

    def test_observed_zero_identity_drift_does_not_block(self):
        policy = retention_policy(_snap(life_phase="CONSOLIDATION", drift={"identity": 0.0}))
        assert policy.consolidate is True

    def test_unobserved_identity_key_leaves_the_phase_rule_alone(self):
        policy = retention_policy(_snap(life_phase="CONSOLIDATION", drift={"zeta": 0.9}))
        assert policy.consolidate is True, "鍵缺席 = 未觀測，不動原判定（D11）"

    @pytest.mark.parametrize("bad", [float("nan"), float("inf"), None, "oops", True])
    def test_non_finite_identity_key_is_treated_as_unobserved(self, bad):
        policy = retention_policy(_snap(life_phase="CONSOLIDATION", drift={"identity": bad}))
        assert policy.consolidate is True

    def test_identity_key_participates_in_the_retention_max(self):
        """`identity` 只在確認漂移時 > 0，所以它進最大值時語義仍是「正在變動」。"""
        policy = retention_policy(_snap(drift={"identity": 0.5}))
        assert policy.retention_seconds == pytest.approx(BASE_RETENTION_SECONDS * 0.5)
        assert policy.source["retention"] == "state"
