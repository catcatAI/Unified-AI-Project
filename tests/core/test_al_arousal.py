"""AL 垂直切片 — ``emotion.arousal``：事件改 target、時間逼近、跨重啟連續。

這個檔案要回答的一個問題：**時間是否真的作用在狀態上？** 判準不是「欄位有值」，
而是下面三件事同時成立：

1. 同一個快照時刻、同一條記憶，**不同歷史 → 不同決定**（`TestHistoryMatters`）。
   決定由 `retention_policy(weight)` 做出，輸入是 AL 內部狀態，不經任何文字。
2. 重啟之後狀態**接著衰減**，不是歸零、也不是凍結（`TestSurvivesRestart`）。
3. 轉移與取樣頻率無關（半群性）、與閉式解/數值積分一致（`TestTransition`）。

所有時間都來自注入的 `FakeClock`：不睡覺、不碰 wall-clock，結果完全可重放（I6）。

ANGELA-MATRIX: [L3] [αβγδ] [A] [L0-L11]
"""

import dataclasses
import math
import sys
import time
from pathlib import Path

import pytest

BACKEND_SRC = Path(__file__).resolve().parents[2] / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from core.life import al_arousal, al_state  # noqa: E402
from core.life.al_arousal import (  # noqa: E402
    AROUSAL_BASELINE,
    CATEGORY_AROUSAL,
    DEFAULT_TAU_FALL_S,
    DEFAULT_TAU_RISE_S,
    AffectState,
    AffectTracker,
    advance,
    arousal_level,
    observe,
    relax,
    set_affect_tracker,
)
from core.life.al_memory_policy import retention_policy  # noqa: E402
from core.life.al_state import EventType, submit_event  # noqa: E402

B = AROUSAL_BASELINE


class FakeClock:
    """可手動撥動的時鐘；``tick(dt)`` 前進 dt 秒。"""

    def __init__(self, start: float = 1_000_000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def tick(self, dt: float) -> None:
        self.now += dt


@pytest.fixture(autouse=True)
def _isolated():
    """事件緩衝與單例追蹤器不外漏：每個案例都從沒有歷史開始。"""
    al_state.clear_events()
    set_affect_tracker(None)
    yield
    set_affect_tracker(None)
    al_state.clear_events()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def tracker(tmp_path, clock) -> AffectTracker:
    t = AffectTracker(path=tmp_path / "al_affect.json", clock=clock)
    set_affect_tracker(t)
    return t


def _angry(intensity: float = 0.9) -> None:
    submit_event(
        EventType.AFFECT_OBSERVED,
        {"emotion": "angry", "intensity": intensity, "source": "keyword_inference"},
    )


def _weight_now(**snapshot_overrides) -> float:
    """固定其他欄位，只讓 emotion 由 AL 內部狀態決定，取記憶策略的編碼權重。"""
    fields = dict(drift=None, intensity=0.5, life_phase=None)
    fields.update(snapshot_overrides)
    return retention_policy(dataclasses.replace(al_state.get_al_state(), **fields)).weight


# =========================================================================
class TestOperator:
    """§5 唯一算子。"""

    def test_zero_dt_is_identity(self):
        assert relax(0.2, 0.9, 0.0, 10.0) == 0.2

    def test_matches_the_closed_form(self):
        got = relax(0.2, 0.8, 7.0, 10.0)
        assert got == pytest.approx(0.8 + (0.2 - 0.8) * math.exp(-0.7))

    def test_moves_monotonically_toward_target_without_overshoot(self):
        values = [relax(0.1, 0.9, dt, 25.0) for dt in (0, 1, 5, 25, 100, 1000)]
        assert values == sorted(values)
        assert all(0.1 <= v <= 0.9 for v in values)

    def test_clock_going_backwards_does_not_decay_negatively(self):
        assert relax(0.4, 0.9, -5.0, 10.0) == 0.4
        assert relax(0.4, 0.9, float("nan"), 10.0) == 0.4

    def test_non_positive_tau_snaps_to_target(self):
        assert relax(0.1, 0.9, 1.0, 0.0) == 0.9


# =========================================================================
class TestTransition:
    """兩級串接的閉式解：與取樣頻率無關、與數值積分一致。"""

    S0 = AffectState(arousal=B, target=0.8, at=0.0)

    def test_sampling_frequency_does_not_change_the_result(self):
        """半群性：一步走 70 秒 == 一百步各走 0.7 秒（§4.2）。"""
        one = advance(self.S0, 70.0)
        state = self.S0
        for i in range(1, 101):
            state = advance(state, 0.7 * i)
        assert state.arousal == pytest.approx(one.arousal, abs=1e-9)
        assert state.target == pytest.approx(one.target, abs=1e-9)

    def test_agrees_with_brute_force_integration(self):
        """用最笨的小步長歐拉法獨立驗證閉式解，不是拿同一條公式驗自己。"""
        v, target, dt = self.S0.arousal, self.S0.target, 0.001
        for _ in range(60_000):  # 60 秒
            dv = (target - v) / DEFAULT_TAU_RISE_S
            dtarget = (B - target) / DEFAULT_TAU_FALL_S
            v += dv * dt
            target += dtarget * dt
        got = advance(self.S0, 60.0)
        assert got.arousal == pytest.approx(v, abs=2e-3)
        assert got.target == pytest.approx(target, abs=2e-3)

    def test_equal_taus_branch_is_continuous_with_the_general_case(self):
        equal = advance(self.S0, 40.0, tau_rise=30.0, tau_fall=30.0)
        nearby = advance(self.S0, 40.0, tau_rise=30.0, tau_fall=30.0 * (1 + 1e-6))
        assert equal.arousal == pytest.approx(nearby.arousal, abs=1e-4)

    def test_arousal_rises_then_falls_back_to_baseline(self):
        """上升再回落：這是「有時間」的最小可觀察形狀。"""
        path = [advance(self.S0, t).arousal for t in (0, 20, 60, 120, 600, 3600, 86_400)]
        peak = max(path)
        assert peak > B + 0.1  # 真的上去了
        assert path[0] == pytest.approx(B)
        assert path.index(peak) not in (0, len(path) - 1)  # 峰值在中間
        assert path[-1] == pytest.approx(B, abs=1e-6)  # 一天後回到靜息

    def test_an_event_only_moves_the_target_never_the_value(self):
        """§5「事件只改 target」：觀測當下 arousal 不跳變。"""
        before = AffectState(arousal=0.4, target=0.4, at=100.0)
        after = observe(before, 0.9, 100.0)
        assert after.arousal == before.arousal
        assert after.target == 0.9

    def test_first_observation_starts_from_rest_not_from_the_observed_value(self):
        state = observe(None, 0.9, 50.0)
        assert state.arousal == B and state.target == 0.9


# =========================================================================
class TestLevelMapping:
    """類別＋強度 → 喚醒度；無法觀測就是 None（D11）。"""

    def test_zero_intensity_carries_no_signal(self):
        assert arousal_level("angry", 0.0) == pytest.approx(B)

    def test_full_intensity_reaches_the_category_arousal(self):
        for name, a in CATEGORY_AROUSAL.items():
            assert arousal_level(name, 1.0) == pytest.approx(a)

    def test_calm_pulls_below_baseline_angry_pushes_above(self):
        assert arousal_level("calm", 0.9) < B < arousal_level("angry", 0.9)

    def test_category_is_case_insensitive_and_intensity_is_clamped(self):
        assert arousal_level(" Angry ", 5.0) == pytest.approx(CATEGORY_AROUSAL["angry"])

    @pytest.mark.parametrize(
        "emotion,intensity",
        [
            ("no-such-emotion", 0.8),
            (None, 0.8),
            ("angry", None),
            ("angry", True),  # bool 不是 1.0 的觀測
            ("angry", float("nan")),
            ("angry", float("inf")),
            ("angry", "high"),
        ],
    )
    def test_unobservable_input_is_none_not_a_guess(self, emotion, intensity):
        assert arousal_level(emotion, intensity) is None


# =========================================================================
class TestUnobservedStaysUnobserved:
    """D11：沒量過就是 None，不是 0.0、也不是基線。"""

    def test_fresh_tracker_reports_none(self, tracker):
        assert tracker.arousal() is None

    def test_snapshot_emotion_is_none_until_an_event_arrives(self, tracker):
        snap = al_state.get_al_state()
        assert snap.emotion is None and snap.source["emotion"] is None

    def test_an_unobservable_event_is_recorded_but_changes_nothing(self, tracker):
        submit_event(EventType.AFFECT_OBSERVED, {"emotion": "bewildered", "intensity": 0.9})
        assert [e["type"] for e in al_state.recent_events()] == ["affect_observed"]
        assert tracker.arousal() is None

    def test_the_policy_is_untouched_while_nothing_was_observed(self, tracker):
        """沒有喚醒度觀測 → 權重＝舊公式 ``0.5 + intensity``，行為與切片前一致。"""
        assert _weight_now() == pytest.approx(1.0)


# =========================================================================
class TestHistoryMatters:
    """切片的主張：同一刻、同一條記憶，歷史不同，決定就不同。"""

    def test_a_recent_outburst_makes_the_memory_weigh_more_than_a_calm_history(
        self, tracker, clock
    ):
        # 歷史 A：30 秒前有一次強烈憤怒
        _angry(0.9)
        clock.tick(30.0)
        weight_after_outburst = _weight_now()

        # 歷史 B：全新的生命，沒有任何情緒觀測（對照組）
        set_affect_tracker(AffectTracker(path=tracker._path.with_name("b.json"), clock=clock))
        weight_no_history = _weight_now()

        # 歷史 C：30 秒前是一段平靜
        set_affect_tracker(AffectTracker(path=tracker._path.with_name("c.json"), clock=clock))
        submit_event(EventType.AFFECT_OBSERVED, {"emotion": "calm", "intensity": 0.9})
        clock.tick(30.0)
        weight_after_calm = _weight_now()

        assert weight_after_calm < weight_no_history < weight_after_outburst
        assert weight_no_history == pytest.approx(1.0)

    def test_the_same_outburst_matters_less_as_time_passes(self, tracker, clock):
        _angry(0.9)
        weights = []
        for wait in (30.0, 120.0, 600.0, 3600.0):
            clock.tick(wait)
            weights.append(_weight_now())
        peak = max(weights)
        assert weights[-1] == pytest.approx(1.0, abs=1e-3)  # 一小時後回到中性
        assert peak > 1.01  # 中途確實加權過
        assert weights.index(peak) < len(weights) - 1

    def test_the_decision_comes_from_state_not_from_text(self, tracker, clock):
        """政策函式的簽名裡沒有文字：兩個快照只差 emotion 欄，權重就不同。"""
        base = dataclasses.replace(al_state.get_al_state(), drift=None, intensity=0.5)
        hot = dataclasses.replace(base, emotion={"arousal": 0.9})
        cold = dataclasses.replace(base, emotion={"arousal": 0.05})
        assert retention_policy(hot).weight > retention_policy(cold).weight
        assert retention_policy(hot).source["weight"] == "state"


# =========================================================================
class TestSurvivesRestart:
    """§4.4 跨重啟連續：接著衰減，不歸零、不凍結。"""

    def test_a_restarted_tracker_continues_from_where_time_left_it(self, tmp_path, clock):
        path = tmp_path / "al_affect.json"
        first = AffectTracker(path=path, clock=clock)
        set_affect_tracker(first)
        _angry(0.9)
        clock.tick(45.0)
        before_restart = first.arousal()
        assert before_restart is not None and before_restart > B + 0.05

        reborn = AffectTracker(path=path, clock=clock)  # 「進程重啟」
        assert reborn.arousal() == pytest.approx(before_restart, abs=1e-9)

    def test_downtime_counts_and_a_long_absence_returns_to_rest(self, tmp_path, clock):
        path = tmp_path / "al_affect.json"
        set_affect_tracker(AffectTracker(path=path, clock=clock))
        _angry(0.9)
        clock.tick(10.0)

        clock.tick(3 * 86_400.0)  # 離線三天
        assert AffectTracker(path=path, clock=clock).arousal() == pytest.approx(B, abs=1e-6)

    def test_it_is_neither_reset_to_zero_nor_frozen(self, tmp_path, clock):
        path = tmp_path / "al_affect.json"
        set_affect_tracker(AffectTracker(path=path, clock=clock))
        _angry(0.9)
        clock.tick(40.0)
        at_save = AffectTracker(path=path, clock=clock).arousal()

        clock.tick(60.0)
        later = AffectTracker(path=path, clock=clock).arousal()
        assert at_save is not None and later is not None
        assert later != pytest.approx(at_save, abs=1e-6)  # 沒凍結
        assert later > 0.0 and at_save > 0.0  # 沒歸零

    @pytest.mark.parametrize(
        "content",
        [
            "not json at all",
            "[]",
            '{"version": 99, "arousal": 0.5, "target": 0.5, "at": 1}',
            '{"version": 1, "arousal": "x", "target": 0.5, "at": 1}',
            '{"version": 1, "arousal": 0.5, "target": NaN, "at": 1}',
            '{"version": 1, "arousal": 0.5}',
        ],
    )
    def test_a_damaged_file_means_unobserved_not_a_crash(self, tmp_path, clock, content):
        path = tmp_path / "al_affect.json"
        path.write_text(content, encoding="utf-8")
        assert AffectTracker(path=path, clock=clock).arousal() is None

    def test_saving_leaves_no_temp_files_behind(self, tmp_path, clock):
        set_affect_tracker(AffectTracker(path=tmp_path / "al_affect.json", clock=clock))
        for _ in range(5):
            _angry(0.5)
            clock.tick(1.0)
        assert sorted(p.name for p in tmp_path.iterdir()) == ["al_affect.json"]


# =========================================================================
class TestClockDiscipline:
    """時間只從注入的時鐘來（I4 的精神）。"""

    def test_decay_never_reads_the_wall_clock(self, tracker, clock, monkeypatch):
        def boom():
            raise AssertionError("wall-clock read during state transition")

        monkeypatch.setattr(time, "time", boom)
        tracker.observe_level(0.8)
        clock.tick(25.0)
        assert tracker.arousal() is not None

    def test_a_clock_that_goes_backwards_does_not_corrupt_the_state(self, tracker, clock):
        tracker.observe_level(0.8)
        clock.tick(30.0)
        forward = tracker.arousal()
        clock.now -= 500.0  # 系統時間被調回去
        assert tracker.arousal() == pytest.approx(B)  # 回到觀測當下：還沒逼近
        clock.now += 530.0
        assert tracker.arousal() is not None and forward is not None

    def test_tau_comes_from_configuration(self, tmp_path, clock, monkeypatch):
        fast = AffectTracker(path=tmp_path / "fast.json", clock=clock)
        slow = AffectTracker(path=tmp_path / "slow.json", clock=clock)

        def configured(key, default=0.0):
            return 2_000.0 if key == al_arousal.TAU_RISE_KEY else default

        for t in (fast, slow):
            t.observe_level(0.9)
        clock.tick(20.0)
        default_rise = fast.arousal()
        monkeypatch.setattr(al_arousal, "threshold_value", configured)
        slower_rise = slow.arousal()
        assert default_rise is not None and slower_rise is not None
        assert slower_rise < default_rise  # τ_rise 拉長 → 20 秒後離靜息更近

    def test_a_malformed_tau_falls_back_to_the_default(self, monkeypatch):
        monkeypatch.setattr(al_arousal, "threshold_value", lambda key, default=0.0: float("nan"))
        assert al_arousal._tau(al_arousal.TAU_RISE_KEY, 20.0) == 20.0
        monkeypatch.setattr(al_arousal, "threshold_value", lambda key, default=0.0: -5.0)
        assert al_arousal._tau(al_arousal.TAU_RISE_KEY, 20.0) == 20.0


# =========================================================================
class TestSnapshotContract:
    """契約面：快照欄位、歸因、I7 唯一寫入口。"""

    def test_snapshot_carries_only_the_observed_component_with_provenance(self, tracker, clock):
        _angry(0.9)
        clock.tick(20.0)
        snap = al_state.get_al_state()  # 內含 validate_snapshot（I1/I2/I9）
        assert set(snap.emotion) == {"arousal"}  # P、D 未觀測 → 鍵缺席，不寫 0.0
        assert snap.source["emotion"] == "core.life.al_arousal"
        assert 0.0 <= snap.emotion["arousal"] <= 1.0

    def test_emotion_still_cannot_be_registered_as_a_provider(self):
        """I7/I8：唯一寫入口是事件通道，不是 provider 登記簿。"""
        with pytest.raises(al_state.ALValidationError):
            al_state.register_al_source("emotion", lambda: {"arousal": 1.0})

    def test_the_only_production_caller_of_the_writer_is_the_event_path(self):
        """I7 的機械版：全 src 中呼叫 ``.observe_level(`` 的只有 ``al_state``。"""
        import re

        callers = {
            p.relative_to(BACKEND_SRC).as_posix()
            for p in BACKEND_SRC.rglob("*.py")
            if re.search(r"\.observe_level\(", p.read_text(encoding="utf-8", errors="ignore"))
        }
        assert callers == {"core/life/al_state.py"}

    def test_the_tracker_public_surface_is_one_reader_and_one_writer(self):
        public = {n for n in dir(AffectTracker) if not n.startswith("_")}
        assert public == {"arousal", "observe_level"}
