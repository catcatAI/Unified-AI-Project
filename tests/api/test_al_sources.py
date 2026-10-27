"""Phase 2 item ③ — lifespan 統一註冊 AL provider（I8：AL 不出站伸手）。

item 1 的契約：``life_phase`` / ``health`` / ``drift`` 的實例握在 api 側，
``register_al_source()`` 當時零生產呼叫者 —— 讀路徑建好了，但沒人注入，
快照三欄恆 ``None``。本檔釘住四件事：

1. 啟動序列真的呼叫 ``_register_al_sources()``，且在 backbone 註冊之後
   （自檢 log 才能報 ``al_state_on_backbone``）；
2. 三個 provider 解析出真值，``source`` 逐欄標 ``provider:*``（I9 歸因）；
3. D11 閘：心跳沒重算過 → ``health=None``（預設 0.5 沒有觀測背後）；
   drift 兩鍵皆未觀測 → 整欄 ``None``，不是 ``{}``；
4. AL 聚合器（``core.life.al_state`` 模組）註冊進既有 backbone，不新造。

server 執行下的 dump 面是 ``GET /api/v1/system/status/detailed`` 的
``al_state`` 段（``_detailed_al_state``），本檔從同一条讀路徑驗證。
item ④ 另加 ``al_events`` 段（§8 事件寫路徑的 dump 面）。
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

BACKEND_SRC = Path(__file__).resolve().parents[2] / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

import api.lifespan as lifespan  # noqa: E402
from core.life.al_state import (  # noqa: E402
    EventType,
    clear_al_sources,
    clear_events,
    get_al_state,
    submit_event,
)


class _FakeHeartbeat:
    """``get_system_health()`` 的最小替身（真物件會在 start() 起背景迴圈）。"""

    def __init__(self, update_count: int = 3, score: float = 0.77):
        self._update_count = update_count
        self._score = score

    def get_system_health(self):
        return {"system_health": self._score, "health_update_count": self._update_count}


@pytest.fixture(autouse=True)
def isolated_al_registry(monkeypatch):
    """乾淨的 provider 登記簿 + 事件緩衝 + sentinel 生命單例（不起真物件）。"""
    clear_al_sources()
    clear_events()
    monkeypatch.setattr(lifespan, "_lifecycle_instance", SimpleNamespace(current_phase="EMERGENCE"))
    monkeypatch.setattr(lifespan, "_heartbeat_instance", _FakeHeartbeat())
    yield
    clear_al_sources()
    clear_events()


def _patch_drift_upstream(monkeypatch, *, eta_observed: bool, zeta_coherence):
    """把 ``_al_drift`` 的兩個 canonical getter 指到可控替身（2c 同款讀法）。"""
    import api.routes.chat_routes as chat_routes

    monkeypatch.setattr(
        chat_routes,
        "_get_eta_axis",
        lambda: SimpleNamespace(
            active_modules=["m"],
            execution_count=0,
            success_rate=1.0,
            structural_drift=0.125 if eta_observed else 0.0,
            structural_drift_observed=eta_observed,
        ),
    )
    observed = frozenset() if zeta_coherence is None else frozenset({"temporal_coherence"})
    values = {} if zeta_coherence is None else {"temporal_coherence": zeta_coherence}
    monkeypatch.setattr(
        chat_routes,
        "_get_state_matrix",
        lambda: SimpleNamespace(
            zeta=SimpleNamespace(values=values),
            zeta_observed_fields=observed,
        ),
    )


class TestProviderRegistration:
    def test_startup_sequence_registers_al_sources_after_backbone(self):
        """釘住呼叫與順序 — 漏接線時這裡紅，而不是靜默 None。"""
        import inspect

        source = inspect.getsource(lifespan._startup_services)
        assert "_register_al_sources()" in source
        assert source.index("_preinit_backbone") < source.index("_register_al_sources")

    def test_registered_sources_reach_the_snapshot(self, monkeypatch):
        _patch_drift_upstream(monkeypatch, eta_observed=True, zeta_coherence=0.75)
        lifespan._register_al_sources()

        snap = get_al_state()
        assert snap.life_phase == "EMERGENCE"
        assert snap.source["life_phase"] == "provider:life_phase"
        assert snap.health == pytest.approx(0.77)
        assert snap.source["health"] == "provider:health"
        # zeta 值漂移 = 異常對佔比 = 1 - temporal_coherence（2b 同一觀測源）
        assert snap.drift == {"eta": 0.125, "zeta": 0.25}
        assert snap.source["drift"] == "provider:drift"

    def test_health_is_withheld_until_the_heartbeat_recomputed(self, monkeypatch):
        monkeypatch.setattr(lifespan, "_heartbeat_instance", _FakeHeartbeat(update_count=0))
        lifespan._register_al_sources()

        snap = get_al_state()
        assert snap.health is None, "default 0.5 has no observation behind it"
        assert snap.source["health"] is None

    def test_drift_is_none_when_both_sources_are_unobserved(self, monkeypatch):
        _patch_drift_upstream(monkeypatch, eta_observed=False, zeta_coherence=None)
        lifespan._register_al_sources()

        snap = get_al_state()
        assert snap.drift is None, "both keys unobserved → the whole field is withheld"
        assert snap.source["drift"] is None

    def test_life_phase_enum_serialises_to_its_name(self):
        from core.life.al_state import _phase_str
        from core.life.autonomous_life_cycle import LifePhase

        # LifePhase.value 是 (cn, en) tuple — str() 會吐 tuple 字面量
        assert _phase_str(LifePhase.EMERGENCE) == "EMERGENCE"
        assert _phase_str(None) is None
        assert _phase_str("plain") == "plain"


class TestAlStateOnBackbone:
    def test_backbone_registration_carries_the_al_state_module(self, monkeypatch):
        """Phase 2 item ③：聚合器註冊進既有 backbone（不新造第二個）。"""
        import core.backbone as cb

        registered = {}

        class _Count:
            def count(self):
                return len(registered)

        class _Memories:
            def names(self):
                return []

        class FakeBackbone:
            registries = type("R", (), {"modules": _Count(), "matrices": _Count()})()
            memories = _Memories()

            def register_module(self, key, obj):
                registered[key] = obj

            def register_matrix(self, key, obj):
                registered[key] = obj

            def register_memory(self, key, obj):
                registered[key] = obj

            def register_dictionary(self, key, obj):
                registered[key] = obj

        monkeypatch.setattr(cb, "get_backbone", lambda: FakeBackbone())
        # 重元件不建：這個測試只關心 al_state 聚合器有沒有上主幹線
        monkeypatch.setattr(lifespan, "get_digital_life", lambda: None)
        monkeypatch.setattr(lifespan, "get_causal_reasoning", lambda: None)
        monkeypatch.setattr(lifespan, "get_crisis_system", lambda: None)
        monkeypatch.setattr(lifespan, "get_agent_manager", lambda: None)
        monkeypatch.setattr(lifespan, "get_desktop_interaction", lambda: None)
        monkeypatch.setattr(lifespan, "get_training_coordinator", lambda: None)
        monkeypatch.setattr(lifespan, "_chat_service_instance", None)

        lifespan._register_backbone()

        from core.life import al_state

        assert registered.get("al_state") is al_state, "AL aggregate must be the registered object"


class TestDetailedEndpointDump:
    def test_detailed_al_state_is_the_snapshot_dump(self):
        """``/status/detailed`` 的 al_state 段 = §9 快照原樣（I9 歸因可取證）。"""
        from api.routes.system_routes import _detailed_al_state

        lifespan._register_al_sources()
        data = _detailed_al_state()

        assert data["version"] == 1
        assert data["life_phase"] == "EMERGENCE"
        assert data["source"]["life_phase"] == "provider:life_phase"
        assert data["source"]["health"] == "provider:health"
        # 歸因紅線：參數層未接線 → effective 恆 None（item 1 D11）
        assert data["effective"] is None

    def test_detailed_al_events_is_the_recent_event_list(self):
        """``/status/detailed`` 的 al_events 段 = §8 事件（舊→新，item ④）。"""
        from api.routes.system_routes import _detailed_al_events

        submit_event(EventType.MEMORY_RESULT, {"mem_id": "exp_1", "pruned": 2})
        submit_event(EventType.MEMORY_RESULT, {"mem_id": "exp_2", "pruned": 0})

        data = _detailed_al_events()
        assert [e["payload"]["mem_id"] for e in data] == ["exp_1", "exp_2"]
        assert all(e["type"] == "memory_result" for e in data)

    def test_empty_buffer_reads_as_nothing_observed(self):
        from api.routes.system_routes import _detailed_al_events

        assert _detailed_al_events() == [], "空＝沒觀測到事件，不是資料丟了"

    def test_detailed_endpoint_wires_the_al_events_key(self):
        """釘住接線 — 漏了 key，helper 就成了零呼叫孤兒。"""
        import inspect

        from api.routes.system_routes import system_status_detailed

        source = inspect.getsource(system_status_detailed)
        assert 'result["al_events"]' in source
        assert "_detailed_al_events()" in source
