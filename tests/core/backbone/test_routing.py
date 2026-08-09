# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""信封路由測試（§6 io.py — send_down / send_up + backbone.io 成對入口）。"""

import pytest
from core.backbone.contracts import Envelope, PairStatus
from core.backbone.io import BackboneIO


def _env(payload="x", kind="chat", correlation_id=None):
    return Envelope(payload=payload, kind=kind, correlation_id=correlation_id)


def _make_io():
    from core.backbone import get_backbone

    return get_backbone().io


class TestSendDown:
    def test_send_down_calls_handler_and_pairs(self):
        io = _make_io()
        io.register_down("chat", lambda e, **kw: {"reply": "hi"})
        result = io.send_down(_env(kind="chat"))
        assert result == {"reply": "hi"}
        # send_down 自動建立 IOPair 且自動配對
        pairs = io.pending()
        assert pairs == []

    def test_send_down_auto_pair_with_envelope_result(self):
        io = _make_io()

        def handler(e, **kw):
            return Envelope(payload="reply", direction="up", correlation_id=e.correlation_id)

        io.register_down("chat", handler)
        result = io.send_down(_env(kind="chat"))
        assert isinstance(result, Envelope)

    def test_send_down_no_handler_raises(self):
        io = _make_io()
        with pytest.raises(ValueError):
            io.send_down(_env(kind="unknown"))

    def test_send_down_handler_error_marks_pair_error(self):
        io = _make_io()

        def boom(e, **kw):
            raise RuntimeError("handler crash")

        io.register_down("chat", boom)
        with pytest.raises(RuntimeError):
            io.send_down(_env(kind="chat"))
        # 失敗對已標記 ERROR，不靜默
        errored = [p for p in io.pairs.all() if p["status"] == PairStatus.ERROR]
        assert len(errored) >= 1

    def test_default_down_handler(self):
        io = _make_io()
        io.set_default_down(lambda e, **kw: "default-result")
        assert io.send_down(_env(kind="whatever")) == "default-result"


class TestSendUp:
    def test_send_up_pairs_by_meta(self):
        io = _make_io()
        env = _env(kind="chat")
        pid = io.submit(env, timeout=1.0)
        out = Envelope(payload="resp", direction="up", correlation_id=env.correlation_id)
        out.meta["pair_id"] = pid
        io.send_up(out)
        assert io.status(pid)["status"] == PairStatus.PAIRED

    def test_send_up_no_handler_returns_envelope(self):
        io = _make_io()
        out = _env(kind="chat", correlation_id="c")
        out.direction = "up"
        assert io.send_up(out) is out

    def test_send_up_calls_handler(self):
        io = _make_io()
        io.register_up("chat", lambda e, **kw: "handled-up")
        out = _env(kind="chat")
        out.direction = "up"
        assert io.send_up(out) == "handled-up"


class TestBackboneIOIntegration:
    def test_backbone_io_submit_resolve(self):
        from core.backbone import get_backbone

        bb = get_backbone()
        pid = bb.io.submit(_env(kind="external"), timeout=1.0)
        bb.io.resolve(pid, Envelope(payload="out", direction="up"))
        assert bb.io.status(pid)["status"] == PairStatus.PAIRED

    def test_io_orphan_queries(self):
        import time

        io = _make_io()
        io.submit(_env(kind="external"), timeout=0.05)
        time.sleep(0.1)
        assert len(io.orphans()) == 1
        io.sweep()
        assert io.status is not None

    def test_send_down_no_pair_tracking_if_scheduler_off(self):
        io = BackboneIO(pair_scheduler=None)
        io.register_down("chat", lambda e, **kw: "no-pair")
        assert io.send_down(_env(kind="chat")) == "no-pair"
        with pytest.raises(RuntimeError):
            io.submit(_env())
