"""Phase 2 item 1 of the three-core plan — the single AL state surface.

Contract §3–§4 (schema + clock) and §9 (read goes through one snapshot).
The schema holds before the remaining fields are wired to real
computation (schema-first per the plan, then one field per commit); the
one field already wired — `age` (item 2, birth adopts the persisted
clock) — is asserted at the bottom.

1. **Schema matches the contract**: the nine v2 fields with their
   §3.1 class tags, `maturity` excluded per D9, `drift` the only
   `derived` field — and `derived` can never reach disk (I3 is enforced
   by `_persist()` refusing, not by remembering).
2. **The clock survives restarts**: `born_at`/`ticks` are loaded before
   anything is initialised, never rebuilt from wall-clock (§4.4), so
   `age` stops resetting to zero on every process restart.
3. **Attribution is always present** (I9): version + effective +
   components + weights + source, with I1 (Σw = 1 ± ε) and I2
   (w_self ≥ floor) validated at the snapshot exit.
4. **I8 boundary**: this module's own imports stay inside stdlib +
   `core.*` — it never reaches out to `ai.*`/`api.*`/`services.*`.
   Sources held by the api layer are injected via the provider registry;
   `emotion` is unobservable in v1 by design (§8 event channel later).
5. **§8 event write path** (item ④): `submit_event()` is the only write
   into AL — unknown types raise `ALValidationError`, non-mapping
   payloads are rejected, the payload is copied (callers can't mutate
   the record), the buffer is bounded at 100 with oldest evicted, and
   nothing persists (v1 skips window aggregation per §14).
"""

import ast
import dataclasses
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import pytest

BACKEND_SRC = Path(__file__).resolve().parents[2] / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from core.life import al_state  # noqa: E402
from core.life.al_state import (  # noqa: E402
    AL_STATE_VERSION,
    DERIVED_FIELDS,
    FIELD_CLASSES,
    PARAM_SOURCES,
    ALSnapshot,
    ALValidationError,
    EventType,
    advance_tick,
    clear_events,
    get_al_state,
    init_clock,
    load_clock,
    recent_events,
    register_al_source,
    submit_event,
    validate_snapshot,
    validate_weights,
)

# 契約 §3.2 的 v2 欄位集（9 個；v2 = v1 八欄 + life_cycle_state）
CONTRACT_FIELDS = {
    "born_at",
    "ticks",
    "life_phase",
    "life_cycle_state",
    "health",
    "intensity",
    "emotion",
    "tendency",
    "drift",
}


@pytest.fixture(autouse=True)
def _isolated_source_registry():
    """provider 登記簿是模組級共享狀態 — 每測試前後清空。"""
    al_state.clear_al_sources()
    yield
    al_state.clear_al_sources()


class TestSchemaMatchesContract:
    def test_v2_field_set_is_the_contract_nine(self):
        # v2 = §3.2 八欄 + life_cycle_state（Phase 3 item 3 的 voter 輸入）
        assert set(FIELD_CLASSES) == CONTRACT_FIELDS
        assert len(FIELD_CLASSES) == 9

    def test_field_classes_match_contract_table(self):
        # §3.2: born_at/ticks/life_phase/life_cycle_state=invariant,
        # health/emotion=fast, intensity/tendency=slow, drift=derived
        assert FIELD_CLASSES["born_at"] == "invariant"
        assert FIELD_CLASSES["ticks"] == "invariant"
        assert FIELD_CLASSES["life_phase"] == "invariant"
        assert FIELD_CLASSES["life_cycle_state"] == "invariant"
        assert FIELD_CLASSES["health"] == "fast"
        assert FIELD_CLASSES["emotion"] == "fast"
        assert FIELD_CLASSES["intensity"] == "slow"
        assert FIELD_CLASSES["tendency"] == "slow"
        assert FIELD_CLASSES["drift"] == "derived"

    def test_maturity_is_not_in_schema(self):
        # D9: maturity 不進 schema（後端階梯已刪、前端階梯與 AL 無關）
        assert "maturity" not in FIELD_CLASSES

    def test_only_drift_is_derived(self):
        assert DERIVED_FIELDS == frozenset({"drift"})

    def test_persist_rejects_derived_field(self, tmp_path):
        # I3 機械保證：derived 想落盤直接拋，不靠「記得不要寫」
        target = tmp_path / "al_state.json"
        with pytest.raises(ALValidationError, match="I3"):
            al_state._persist({"born_at": 1.0, "drift": {"zeta": 0.1}}, path=target)
        assert not target.exists()

    def test_persist_writes_only_clock_keys(self, tmp_path):
        target = tmp_path / "al_state.json"
        init_clock(now=1000.0, path=target)
        written = json.loads(target.read_text(encoding="utf-8"))
        assert set(written) == {"version", "born_at", "ticks"}
        assert not set(written) & DERIVED_FIELDS


class TestWeightsGuards:
    def test_default_weights_pass_i1_and_i2(self):
        validate_weights(dict(al_state.DEFAULT_WEIGHTS))  # 不拋即過

    def test_reject_unnormalized_weights(self):
        with pytest.raises(ALValidationError, match="I1"):
            validate_weights({"ai": 0.7, "user": 0.4})

    def test_reject_self_weight_below_floor(self):
        with pytest.raises(ALValidationError, match="I2"):
            validate_weights(
                {"ai": 0.2, "user": 0.5, "group_fast": 0.2, "group_slow": 0.1},
                w_self_min=0.5,
            )

    def test_reject_unknown_source(self):
        with pytest.raises(ALValidationError, match="I1"):
            validate_weights({"ai": 1.0, "stranger": 0.0})


class TestClockSurvivesRestart:
    def test_missing_file_is_unobserved(self, tmp_path):
        assert load_clock(path=tmp_path / "none.json") == (None, None)

    def test_init_clock_is_sticky_across_restart(self, tmp_path):
        target = tmp_path / "al_state.json"
        born, ticks = init_clock(now=1000.0, path=target)
        assert (born, ticks) == (1000.0, 0)
        # 模擬重啟後再次初始化：now 不同，但舊時鐘勝出（§4.4 不得以當前時間重建）
        born_again, ticks_again = init_clock(now=9999.0, path=target)
        assert (born_again, ticks_again) == (1000.0, 0)
        # 真正的「重啟」＝只讀不建
        assert load_clock(path=target) == (1000.0, 0)

    def test_advance_tick_persists_and_reloads(self, tmp_path):
        target = tmp_path / "al_state.json"
        init_clock(now=1000.0, path=target)
        assert advance_tick(path=target) == 1
        assert advance_tick(path=target) == 2
        assert load_clock(path=target) == (1000.0, 2)
        # 推進後的 ticks 在檔案裡（§4.1 每次推進持久化）
        written = json.loads(target.read_text(encoding="utf-8"))
        assert written["ticks"] == 2
        assert written["born_at"] == 1000.0

    def test_advance_without_init_starts_clock_now(self, tmp_path):
        target = tmp_path / "al_state.json"
        assert advance_tick(path=target) == 1
        born, ticks = load_clock(path=target)
        assert born is not None and ticks == 1


class TestSnapshotAttribution:
    def test_snapshot_carries_i9_fields(self):
        snap = get_al_state()
        payload = snap.as_dict()
        for key in ("version", "effective", "components", "weights", "source"):
            assert key in payload, f"I9: snapshot must carry {key}"
        assert set(payload["components"]) == set(PARAM_SOURCES)

    def test_snapshot_version_and_validation(self):
        snap = get_al_state()
        assert snap.version == AL_STATE_VERSION
        validate_snapshot(snap)  # 不拋即過

    def test_validate_snapshot_rejects_bad_weights(self):
        snap = get_al_state()
        broken = dataclasses.replace(snap, weights={"ai": 0.2, "user": 0.9})
        with pytest.raises(ALValidationError):
            validate_snapshot(broken)


class TestAggregationReadPath:
    def test_returns_versioned_snapshot(self):
        snap = get_al_state()
        assert isinstance(snap, ALSnapshot)
        assert snap.version == AL_STATE_VERSION
        # 時鐘未由本測試初始化 → 要麼 None（D11）要麼從既有檔案讀到
        assert snap.born_at is None or isinstance(snap.born_at, float)

    def test_intensity_and_tendency_are_observed(self):
        snap = get_al_state()
        assert isinstance(snap.intensity, float)
        assert snap.source["intensity"] == ("core.life_intensity_formula.peek_life_intensity")
        assert isinstance(snap.tendency, dict) and snap.tendency
        assert all(isinstance(v, float) for v in snap.tendency.values())
        assert snap.source["tendency"] == ("core.life.life_essence.get_all_blended_tendencies")

    def test_unregistered_sources_are_none(self):
        # health/life_phase/life_cycle_state/drift 的實例握在 api 側
        # （I8 禁 AL 自己伸手）→ 未經 provider 登記 = 未觀測 = None（D11），
        # source 同步 None
        snap = get_al_state()
        assert snap.life_phase is None
        assert snap.life_cycle_state is None
        assert snap.health is None
        assert snap.drift is None
        assert snap.source["life_phase"] is None
        assert snap.source["life_cycle_state"] is None
        assert snap.source["health"] is None
        assert snap.source["drift"] is None

    def test_emotion_is_always_unobserved(self):
        # I8：情緒在 ai/alignment，AL 出站 import 即違規；v1 恆 None
        snap = get_al_state()
        assert snap.emotion is None
        assert snap.source["emotion"] is None
        assert "emotion" not in al_state.PROVIDABLE_SOURCES

    def test_registered_source_flows_into_snapshot(self):
        register_al_source("health", lambda: 0.42)
        snap = get_al_state()
        assert snap.health == 0.42
        assert snap.source["health"] == "provider:health"

    def test_life_cycle_state_enum_flows_in_as_name(self):
        # DLI 的 LifeCycleState 是 Enum —— 快照照 _phase_str 規則取 .name，
        # voter 端拿到的是 "MATURE" 這種字串（與 router 舊注入同詞彙）。
        from enum import Enum

        class _Cycle(Enum):
            MATURE = "mature"

        register_al_source("life_cycle_state", lambda: _Cycle.MATURE)
        snap = get_al_state()
        assert snap.life_cycle_state == "MATURE"
        assert snap.source["life_cycle_state"] == "provider:life_cycle_state"

    def test_failing_source_degrades_to_none(self):
        def boom():
            raise RuntimeError("sensor offline")

        register_al_source("health", boom)
        snap = get_al_state()
        assert snap.health is None
        assert snap.source["health"] is None

    def test_register_rejects_unknown_source_name(self):
        with pytest.raises(ALValidationError, match="unknown AL source"):
            register_al_source("emotion", lambda: None)


class TestBirthAdoptsSingleClock:
    """item 2（age）：私有出生時鐘 → 單一持久化 ``born_at``（§4）。

    舊 bug：``LifeStats`` / ``SelfModel`` 都是
    ``default_factory=datetime.now`` —— 每次重建 = 新生 = age 歸零、
    身份自述的誕生日每次重啟漂移。
    """

    @staticmethod
    def _freeze_clock(monkeypatch, tmp_path, born=1000.0):
        """起鐘於過去某刻，並把模組時鐘檔導向 tmp（不碰真資料目錄）。"""
        target = tmp_path / "al_state.json"
        init_clock(now=born, path=target)
        monkeypatch.setattr(
            al_state,
            "_clock_path",
            lambda path=None: Path(path) if path is not None else target,
        )
        return target

    def test_dli_birth_time_comes_from_persisted_clock(self, tmp_path, monkeypatch):
        self._freeze_clock(monkeypatch, tmp_path)
        from core.life.digital_life_integrator import DigitalLifeIntegrator

        dli = DigitalLifeIntegrator(config={"enable_formula_integration": False})
        assert dli.life_stats.birth_time == datetime.fromtimestamp(1000.0)
        # 1970 年出生 → age 以千天計；舊 bug 恆 0（now - now）
        assert dli.get_age().days > 1000

    def test_cyber_identity_birth_comes_from_persisted_clock(self, tmp_path, monkeypatch):
        self._freeze_clock(monkeypatch, tmp_path)
        from core.life.cyber_identity import CyberIdentity

        identity = CyberIdentity()
        assert identity.self_model.birth_date == datetime.fromtimestamp(1000.0)
        assert identity.get_self_summary()["age_days"] > 1000


class TestI8Boundary:
    BANNED_ROOTS = ("ai", "services", "api", "integrations")

    def test_module_imports_stay_inside_stdlib_and_core(self):
        source = Path(al_state.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
        violations = [name for name in imported if name.split(".")[0] in self.BANNED_ROOTS]
        assert violations == [], f"I8: AL outbound imports are forbidden: {violations}"


class TestEventWritePath:
    """§8 寫路徑（item ④ 種子）：對 AL 的寫只經 ``submit_event``（I7）。"""

    @pytest.fixture(autouse=True)
    def _clean_buffer(self):
        """事件緩衝是模組級共享狀態 — 每測試前後清空。"""
        clear_events()
        yield
        clear_events()

    def test_records_shape(self):
        submit_event(EventType.MEMORY_RESULT, {"mem_id": "exp_1", "pruned": 3})
        events = recent_events()
        assert len(events) == 1
        record = events[0]
        assert record["type"] == "memory_result"
        assert isinstance(record["at"], float)
        assert record["payload"] == {"mem_id": "exp_1", "pruned": 3}

    def test_accepts_the_enum_member_and_its_plain_string_value(self):
        submit_event(EventType.MEMORY_RESULT, {"a": 1})
        submit_event("memory_result", {"b": 2})
        assert [e["payload"] for e in recent_events()] == [{"a": 1}, {"b": 2}]

    def test_unknown_type_raises(self):
        # 打錯字靜默失效比崩潰更貴 — 與 register_al_source 同款
        with pytest.raises(ALValidationError, match="unknown event type"):
            submit_event("memory_reuslt", {"typo": True})

    def test_non_mapping_payload_raises(self):
        with pytest.raises(TypeError, match="mapping"):
            submit_event(EventType.MEMORY_RESULT, ["not", "a", "mapping"])

    def test_payload_is_copied_not_linked(self):
        payload = {"count": 1}
        submit_event(EventType.MEMORY_RESULT, payload)
        payload["count"] = 999
        assert recent_events()[-1]["payload"]["count"] == 1

    def test_buffer_is_bounded_and_evicts_oldest(self):
        for index in range(105):
            submit_event(EventType.MEMORY_RESULT, {"i": index})
        events = recent_events()
        assert len(events) == 100, "bounded buffer: oldest evicted, never grows"
        assert events[0]["payload"]["i"] == 5  # 前 5 筆被淘汰
        assert events[-1]["payload"]["i"] == 104

    def test_limit_semantics(self):
        for index in range(3):
            submit_event(EventType.MEMORY_RESULT, {"i": index})
        assert len(recent_events()) == 3
        assert [e["payload"]["i"] for e in recent_events(limit=2)] == [1, 2]
        assert recent_events(limit=0) == []
