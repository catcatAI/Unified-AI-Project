# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""學習協調器測試（§5.5.2 步驟 B5 — CNS 事件驅動取代 chat_service 內嵌觸發）。"""

import asyncio

import pytest
from core.backbone.contracts import Envelope, EnvelopeKind
from core.backbone.learning import LEARNING_EVENT, LearningCoordinator


class _FakePairs:
    """輕量假 PairScheduler：記錄 submit/resolve/fail。"""

    def __init__(self):
        self.submitted = []
        self.resolved = []
        self.failed = []
        self._counter = 0

    def submit(self, envelope, timeout=None, kind=None):
        self._counter += 1
        pid = f"p{self._counter}"
        self.submitted.append((pid, envelope, timeout, kind))
        return pid

    def resolve(self, pid, output):
        self.resolved.append((pid, output))

    def fail(self, pid, reason=None):
        self.failed.append((pid, reason))


class _FakeStateStore:
    """輕量假 CNS state store：記錄 subscribe/unsubscribe。"""

    def __init__(self):
        self.subscribed = []
        self.unsubscribed = []

    def subscribe_event(self, event_type, callback, priority=0):
        self.subscribed.append((event_type, callback))

    def unsubscribe_event(self, event_type, callback):
        self.unsubscribed.append((event_type, callback))


@pytest.fixture
def fake_pairs():
    return _FakePairs()


@pytest.fixture
def fake_store():
    return _FakeStateStore()


class TestLearningCoordinator:
    def test_register_and_trigger(self, fake_pairs):
        coordinator = LearningCoordinator(pair_scheduler=fake_pairs)
        calls = []

        async def learner(user_message, response, context):
            calls.append((user_message, response, context))
            return {"ok": True}

        coordinator.register_learning("continuous", learner)
        assert coordinator.names() == ["continuous"]
        assert coordinator.has("continuous")

        async def run():
            return await coordinator.trigger("hi", "hello", {"k": 1})

        results = asyncio.run(run())
        assert results["continuous"]["status"] == "PAIRED"
        assert calls == [("hi", "hello", {"k": 1})]
        # 成對排程: submit → resolve (kind=learning)
        assert fake_pairs.submitted
        assert fake_pairs.resolved
        assert fake_pairs.submitted[0][3] == EnvelopeKind.LEARNING

    def test_learner_failure_marks_error(self, fake_pairs):
        coordinator = LearningCoordinator(pair_scheduler=fake_pairs)

        async def bad_learner(user_message, response, context):
            raise RuntimeError("boom")

        coordinator.register_learning("bad", bad_learner)

        async def run():
            return await coordinator.trigger("hi", "hello")

        results = asyncio.run(run())
        assert results["bad"]["status"] == "ERROR"
        assert "boom" in results["bad"]["error"]
        # 失敗 → fail() 但其它 learner 不受影響
        assert fake_pairs.failed

    def test_one_failure_does_not_block_others(self, fake_pairs):
        coordinator = LearningCoordinator(pair_scheduler=fake_pairs)
        ran = []

        async def bad_learner(u, r, c):
            raise ValueError("x")

        async def good_learner(u, r, c):
            ran.append(u)
            return {"ok": True}

        coordinator.register_learning("bad", bad_learner)
        coordinator.register_learning("good", good_learner)

        async def run():
            return await coordinator.trigger("hi", "hello")

        results = asyncio.run(run())
        assert results["bad"]["status"] == "ERROR"
        assert results["good"]["status"] == "PAIRED"
        assert ran == ["hi"]

    def test_unregister(self):
        coordinator = LearningCoordinator()

        async def learner(u, r, c):
            return None

        coordinator.register_learning("a", learner)
        assert coordinator.unregister("a")
        assert not coordinator.has("a")
        assert not coordinator.unregister("a")

    def test_clear(self):
        coordinator = LearningCoordinator()

        async def learner(u, r, c):
            return None

        coordinator.register_learning("a", learner)
        coordinator.register_learning("b", learner)
        coordinator.clear()
        assert coordinator.names() == []


class TestLearningCNSSubscription:
    def test_subscribe_events(self, fake_store):
        coordinator = LearningCoordinator()
        assert coordinator.subscribe(fake_store)
        assert fake_store.subscribed == [(LEARNING_EVENT, coordinator._on_response_generated)]
        assert coordinator._subscribed

    def test_unsubscribe(self, fake_store):
        coordinator = LearningCoordinator()
        coordinator.subscribe(fake_store)
        assert coordinator.unsubscribe()
        assert fake_store.unsubscribed == [(LEARNING_EVENT, coordinator._on_response_generated)]
        assert not coordinator._subscribed

    def test_subscribe_no_store(self):
        coordinator = LearningCoordinator()
        assert not coordinator.subscribe(None)

    def test_callback_missing_response_skips(self, fake_pairs, fake_store):
        coordinator = LearningCoordinator(pair_scheduler=fake_pairs)
        coordinator.subscribe(fake_store)
        # 無 response payload → 直接返回，不建立 task
        coordinator._on_response_generated(LEARNING_EVENT, {"user_message": "hi"})
        assert fake_pairs.submitted == []

    def test_backbone_integration(self):
        """backbone.register_learning + trigger_learning 經主幹線接線。"""
        from core.backbone import get_backbone, reset_backbone

        reset_backbone()
        bb = get_backbone()
        calls = []

        async def learner(u, r, c):
            calls.append((u, r))
            return {"ok": True}

        bb.register_learning("test", learner)
        assert "test" in bb.learning.names()

        async def run():
            return await bb.trigger_learning("q", "a", {"x": 1})

        results = asyncio.run(run())
        assert results["test"]["status"] == "PAIRED"
        assert calls == [("q", "a")]
        reset_backbone()

    def test_subscribe_learning_delegation(self):
        from core.backbone import get_backbone, reset_backbone

        reset_backbone()
        bb = get_backbone()
        store = _FakeStateStore()
        assert bb.subscribe_learning(store)
        assert store.subscribed[0][0] == LEARNING_EVENT
        reset_backbone()
