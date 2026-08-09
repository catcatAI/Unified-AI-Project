# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""CNS domain 訂閱同步器測試（§11.3 #4 步驟 B10）。"""

import pytest
from core.backbone.subscriptions import CORE_DOMAIN, CNSDomainSync


class _FakeBackboneState:
    """輕量 BackboneState 門面假實作（記錄 subscribe/unsubscribe/update/emit）。"""

    def __init__(self, store=None):
        self.store = store
        self._writes = []
        self._emits = []
        self._subscribed = []
        self._callbacks = {}

    def subscribe(self, domain, callback):
        self._subscribed.append(domain)
        self._callbacks[domain] = callback
        return True

    def unsubscribe(self, domain, callback):
        self._subscribed = [d for d in self._subscribed if d != domain]
        self._callbacks.pop(domain, None)
        return True

    def update(self, domain, data, notify=True):
        self._writes.append((domain, data))
        return True

    def emit_event(self, event_type, data):
        self._emits.append((event_type, data))
        return True

    def write_axis(self, axis, key, value):
        self._writes.append((axis, key, value))
        return True


class _FakeMatrix:
    """記錄 write_axis 呼叫的假主狀態矩陣。"""

    pass


# 上面是輔助，以下用 FakeBackboneState 直接測 CNSDomainSync。


@pytest.fixture
def sync_ctx():
    state = _FakeBackboneState()
    matrix = _FakeMatrix()
    sync = CNSDomainSync(state=state, matrix=matrix)
    return sync, state


class TestCNSDomainSync:
    def test_subscribe_core_domain(self, sync_ctx):
        sync, state = sync_ctx
        assert sync.subscribe(CORE_DOMAIN)
        assert "core" in sync.subscribed_domains()
        assert "core" in state._subscribed

    def test_subscribe_idempotent(self, sync_ctx):
        sync, state = sync_ctx
        assert sync.subscribe("core")
        assert sync.subscribe("core")
        assert len(state._subscribed) == 1

    def test_subscribe_custom_callback(self, sync_ctx):
        sync, state = sync_ctx
        calls = []

        def cb(domain, data):
            calls.append(domain)

        assert sync.subscribe_with("custom", cb)
        # 觸發下層 callback
        state._callbacks["custom"]("custom", {"a": 1})
        assert calls == ["custom"]

    def test_unsubscribe(self, sync_ctx):
        sync, state = sync_ctx
        sync.subscribe("core")
        assert sync.subscribe("core")
        assert sync.unsubscribe("core")
        assert "core" not in sync.subscribed_domains()
        assert "core" not in state._subscribed

    def test_subscribe_no_state_returns_false(self):
        sync = CNSDomainSync(state=None)
        assert not sync.subscribe("core")

    def test_domain_change_writes_axis_to_matrix(self, sync_ctx):
        """CNS core domain 含軸字典變更 → 同步寫回主矩陣。"""
        _, state = sync_ctx
        sync, _ = sync_ctx
        sync.subscribe("core")
        # 模擬下層 CNS 觸發 domain callback（domain, data）
        state._callbacks["core"]("core", {"alpha": {"focus": 0.8, "energy": 0.6}})
        # write_axis 被呼叫（記錄在 state._writes）
        writes = [w for w in state._writes if w[0] == "alpha"]
        assert ("alpha", "focus", 0.8) in writes
        assert ("alpha", "energy", 0.6) in writes

    def test_domain_change_non_axis_data_ignored(self, sync_ctx):
        _, state = sync_ctx
        sync, _ = sync_ctx
        sync.subscribe("core")
        state._callbacks["core"]("core", {"plain_key": "value"})
        assert ("plain_key", "value") not in state._writes

    def test_emit_event_delegates(self, sync_ctx):
        sync, state = sync_ctx
        assert sync.emit_event("custom.event", {"x": 1})
        assert ("custom.event", {"x": 1}) in state._emits


class TestBackboneStateSubscription:
    def test_backbone_state_sync_integration(self):
        """真實 GlobalStateStore + StateMatrix4D：CNS domain 訂閱寫回矩陣。"""
        from core.backbone import get_backbone, reset_backbone
        from core.engine.state_matrix import StateMatrix4D
        from core.system.state_store.global_store import GlobalStateStore

        reset_backbone()
        bb = get_backbone()
        store = GlobalStateStore()
        # 先註冊 domain 讓 subscribe 有 domain-specific 列表
        store.update_state("core", {}, notify=False)
        bb.bind_state_store(store)
        sm = StateMatrix4D()
        bb.register_matrix("primary", sm)
        bb.state_sync.bind_matrix(sm)

        assert sm.theta.values.get("novelty") == 0.5
        assert bb.state_sync.subscribe("core")
        store.update_state("core", {"theta": {"novelty": 0.9}}, notify=True)
        assert sm.theta.values.get("novelty") == 0.9
        reset_backbone()