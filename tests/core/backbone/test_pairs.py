# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""Stability Core 成對排程測試（§5.0.2 / §5.0.3）。

覆蓋：
- submit/resolve/cancel/retry 基本生命週期
- 先入先配（輸出永不早於輸入處理）
- 同對單執行（衝突防範）
- 逾時 → ORPHAN（永不靜默）
- 配對狀態查詢（status/pending/orphans/by_kind）
"""

import time

import pytest
from core.backbone.contracts import Envelope, PairPattern, PairStatus
from core.backbone.pairs import (
    PairConflictError,
    PairScheduler,
    PairState,
    get_pair_scheduler,
    reset_pair_scheduler,
)


@pytest.fixture(autouse=True)
def _fresh_scheduler():
    reset_pair_scheduler()
    yield
    reset_pair_scheduler()


@pytest.fixture
def scheduler():
    return PairScheduler()


def _env(payload="x", kind="chat", correlation_id=None):
    return Envelope(payload=payload, kind=kind, correlation_id=correlation_id)


# ---------------------------------------------------------------------------
# 基本生命週期
# ---------------------------------------------------------------------------
class TestBasicLifecycle:
    def test_submit_returns_pair_id(self, scheduler):
        pid = scheduler.submit(_env(kind="chat"))
        assert isinstance(pid, str) and pid
        status = scheduler.status(pid)
        assert status["status"] == PairStatus.QUEUED

    def test_submit_resolve_paired(self, scheduler):
        env = _env(kind="external")
        pid = scheduler.submit(env)
        scheduler.resolve(
            pid, Envelope(payload="result", direction="up", correlation_id=env.correlation_id)
        )
        assert scheduler.status(pid)["status"] == PairStatus.PAIRED
        assert scheduler.status(pid)["output_message_id"] is not None

    def test_cancel(self, scheduler):
        pid = scheduler.submit(_env())
        scheduler.cancel(pid)
        assert scheduler.status(pid)["status"] == PairStatus.CANCELLED

    def test_retry_from_error(self, scheduler):
        pid = scheduler.submit(_env())
        scheduler.start(pid)
        scheduler.fail(pid, reason="boom")
        assert scheduler.status(pid)["status"] == PairStatus.ERROR
        scheduler.retry(pid)
        status = scheduler.status(pid)
        assert status["status"] == PairStatus.QUEUED
        assert status["schedule"]["retries"] == 1

    def test_unknown_pair_id_raises_keyerror(self, scheduler):
        with pytest.raises(KeyError):
            scheduler.resolve("nope", _env())


# ---------------------------------------------------------------------------
# 衝突防範（§5.0.2 同對單執行）
# ---------------------------------------------------------------------------
class TestConflictPrevention:
    def test_duplicate_pending_pair_conflict(self, scheduler):
        env = _env(correlation_id="corr-1")
        scheduler.submit(env)
        with pytest.raises(PairConflictError):
            scheduler.submit(_env(correlation_id="corr-1"))

    def test_duplicate_after_terminal_allowed(self, scheduler):
        env = _env(correlation_id="corr-2")
        pid = scheduler.submit(env)
        scheduler.resolve(pid, Envelope(payload="r", direction="up"))
        # 終態後可重複提交相同 correlation_id
        pid2 = scheduler.submit(_env(correlation_id="corr-2"))
        assert scheduler.status(pid2)["status"] == PairStatus.QUEUED

    def test_double_resolve_conflict(self, scheduler):
        env = _env()
        pid = scheduler.submit(env)
        scheduler.resolve(pid, Envelope(payload="r", direction="up"))
        with pytest.raises(PairConflictError):
            scheduler.resolve(pid, Envelope(payload="r2", direction="up"))

    def test_illegal_transition_raises(self, scheduler):
        pid = scheduler.submit(_env())
        scheduler.cancel(pid)
        with pytest.raises(PairConflictError):
            scheduler.start(pid)

    def test_run_pair_async_conflict_same_pair(self, scheduler):
        env = _env(kind="external")
        pid = scheduler.submit(env)
        lock = scheduler._get_lock(pid)
        assert lock.acquire(blocking=False)
        try:
            with pytest.raises(PairConflictError):
                scheduler.run_pair_async(pid, lambda e: "x")
        finally:
            lock.release()


# ---------------------------------------------------------------------------
# 逾時 → ORPHAN（§5.0.5：永不靜默）
# ---------------------------------------------------------------------------
class TestTimeoutOrphan:
    def test_orphan_after_deadline(self, scheduler):
        env = _env(kind="external")
        pid = scheduler.submit(env, timeout=0.05)
        time.sleep(0.1)
        orphans = scheduler.orphans()
        assert any(o["pair_id"] == pid for o in orphans)

    def test_sweep_marks_orphan(self, scheduler):
        env = _env(kind="external")
        pid = scheduler.submit(env, timeout=0.05)
        time.sleep(0.1)
        swept = scheduler.sweep()
        assert pid in swept
        assert scheduler.status(pid)["status"] == PairStatus.ORPHAN

    def test_orphan_never_silent(self, scheduler):
        env = _env(kind="external")
        pid = scheduler.submit(env, timeout=0.05)
        time.sleep(0.1)
        scheduler.sweep()
        # ORPHAN 可被診斷：不會靜默消失
        assert scheduler.status(pid) is not None
        assert scheduler.status(pid)["status"] in (PairStatus.ORPHAN,)

    def test_retry_orphan_back_to_queued(self, scheduler):
        env = _env(kind="external")
        pid = scheduler.submit(env, timeout=0.05)
        time.sleep(0.1)
        scheduler.sweep()
        scheduler.retry(pid)
        assert scheduler.status(pid)["status"] == PairStatus.QUEUED


# ---------------------------------------------------------------------------
# 先入先配（§5.0.2）
# ---------------------------------------------------------------------------
class TestFirstInFirstPaired:
    def test_pairs_submitted_in_order(self, scheduler):
        p1 = scheduler.submit(_env(kind="a"), timeout=0.5)
        p2 = scheduler.submit(_env(kind="b"), timeout=0.5)
        p3 = scheduler.submit(_env(kind="c"), timeout=0.5)
        log = scheduler.all()
        log.sort(key=lambda d: d["schedule"]["submitted_at"])
        assert [d["pair_id"] for d in log] == [p1, p2, p3]

    def test_output_cannot_precede_input(self, scheduler):
        env = _env(kind="external")
        pid = scheduler.submit(env)
        # 未 submit 的 pair_id 無法 resolve（輸出必屬某 pair_id）
        with pytest.raises(KeyError):
            scheduler.resolve("not-submitted", Envelope(payload="r", direction="up"))
        assert scheduler.status(pid)["status"] == PairStatus.QUEUED


# ---------------------------------------------------------------------------
# 配對狀態查詢（§5.0.3）
# ---------------------------------------------------------------------------
class TestPairStateQueries:
    def test_pending(self, scheduler):
        scheduler.submit(_env(kind="a"))
        scheduler.submit(_env(kind="b"))
        assert len(scheduler.pending()) == 2

    def test_by_kind(self, scheduler):
        scheduler.submit(_env(kind="external"))
        scheduler.submit(_env(kind="external"))
        scheduler.submit(_env(kind="learning"))
        assert len(scheduler.by_kind("external")) == 2
        assert len(scheduler.by_kind("learning")) == 1

    def test_pair_state_facade(self, scheduler):
        state = PairState(scheduler)
        pid = scheduler.submit(_env(kind="external"))
        assert state.status(pid)["status"] == PairStatus.QUEUED
        assert len(state.pending()) == 1
        scheduler.sweep()
        state.adjust_deadline(pid, 10.0)
        state.cancel(pid)
        assert state.status(pid)["status"] == PairStatus.CANCELLED

    def test_correlation_id_indexed(self, scheduler):
        env = _env(kind="chat", correlation_id="hsp-correlation-42")
        pid = scheduler.submit(env)
        status = scheduler.status(pid)
        assert status["correlation_id"] == "hsp-correlation-42"


# ---------------------------------------------------------------------------
# 全域單例
# ---------------------------------------------------------------------------
class TestSingleton:
    def test_get_pair_scheduler_singleton(self):
        s1 = get_pair_scheduler()
        s2 = get_pair_scheduler()
        assert s1 is s2

    def test_backbone_io_pair_endpoint(self):
        from core.backbone import get_backbone

        bb = get_backbone()
        pid = bb.submit(_env(kind="external"), timeout=0.5)
        assert bb.io_pairs.status(pid)["status"] == PairStatus.QUEUED
        bb.resolve(pid, Envelope(payload="ok", direction="up"))
        assert bb.io_pairs.status(pid)["status"] == PairStatus.PAIRED
