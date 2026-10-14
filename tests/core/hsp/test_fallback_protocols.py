# =============================================================================
# ANGELA-MATRIX: [L4] [δ] [B] [L6+]
# =============================================================================
"""Tests for the restored HSP fallback protocols.

The monorepo migration left an 80-line stub whose ``HTTPProtocol.post``
returned ``{"status": "ok"}`` unconditionally, whose constructor signature
did not match the connector's call, and whose manager was never assigned —
so ``fallback_manager`` was permanently ``None`` and every fallback branch
was dead code. These tests pin the restored contracts: protocol round-trips,
manager rotation/retry, the connector's degraded-send path, and the four
bug fixes documented in fallback_protocols.py.
"""

import asyncio
import glob
import json
import os
import tempfile

import pytest
from core.hsp.fallback.fallback_protocols import (
    FallbackMessage,
    FallbackProtocolManager,
    FileBasedProtocol,
    InMemoryProtocol,
    MessagePriority,
    ProtocolStatus,
    get_fallback_manager,
)

# asyncio mark 應只套用到 async 測試——原模組級 pytestmark 誤標
# TestFallbackMessage 的 2 個同步測試（pytest-asyncio 警告噪音）。
# 改為逐 async class 套用。


class TestFallbackMessage:
    def test_roundtrip_dict(self):
        msg = FallbackMessage(
            id="m1",
            sender_id="a",
            recipient_id="b",
            message_type="hsp_message",
            payload={"k": "v"},
            timestamp=123.0,
            priority=MessagePriority.HIGH,
            correlation_id="c1",
        )
        restored = FallbackMessage.from_dict(msg.to_dict())
        assert restored.id == "m1"
        assert restored.priority == MessagePriority.HIGH
        assert restored.payload == {"k": "v"}
        assert restored.correlation_id == "c1"

    def test_ttl_expiry(self):
        msg = FallbackMessage(
            id="m",
            sender_id="a",
            recipient_id="b",
            message_type="t",
            payload={},
            timestamp=0.0,
            ttl=0.01,
        )
        assert msg.is_expired() is True
        msg2 = FallbackMessage(
            id="m",
            sender_id="a",
            recipient_id="b",
            message_type="t",
            payload={},
            timestamp=0.0,
            ttl=None,
        )
        assert msg2.is_expired() is False


class TestInMemoryProtocol:
    pytestmark = pytest.mark.asyncio

    async def test_send_listener_handler_roundtrip(self):
        proto = InMemoryProtocol()
        assert await proto.initialize()
        received = []

        async def handler(msg):
            received.append(msg)

        proto.register_handler("hsp_message", handler)
        await proto.start_listening()
        try:
            msg = FallbackMessage(
                id="m1",
                sender_id="s",
                recipient_id="r",
                message_type="hsp_message",
                payload={"n": 1},
                timestamp=0.0,
            )
            assert await proto.send_message(msg) is True
            await asyncio.sleep(0.05)
            assert len(received) == 1
            assert received[0].payload == {"n": 1}
            assert proto.stats["messages_sent"] == 1
            assert proto.stats["messages_received"] == 1
        finally:
            await proto.stop_listening()

    async def test_health_check_does_not_require_running(self):
        """The circular gate bug: health_check required running=True, but
        running is only set by start_listening which the manager calls after
        a health check passes — the protocol could never become active."""
        proto = InMemoryProtocol()
        assert await proto.initialize()
        assert await proto.health_check() is True
        assert proto.running is False

    async def test_expired_message_dropped(self):
        proto = InMemoryProtocol()
        await proto.initialize()
        received = []

        async def handler(msg):
            received.append(msg)

        proto.register_handler("t", handler)
        msg = FallbackMessage(
            id="old",
            sender_id="s",
            recipient_id="r",
            message_type="t",
            payload={},
            timestamp=0.0,
            ttl=0.01,
        )
        await proto.handle_message(msg)
        assert received == []


class TestFileBasedProtocol:
    pytestmark = pytest.mark.asyncio

    async def test_outbox_inbox_roundtrip(self):
        base = tempfile.mkdtemp()
        proto = FileBasedProtocol(base_path=base)
        assert await proto.initialize()
        assert os.path.isdir(proto.inbox_path)
        assert os.path.isdir(proto.outbox_path)

        received = []

        async def handler(msg):
            received.append(msg)

        proto.register_handler("hsp_message", handler)
        await proto.start_listening()
        try:
            msg = FallbackMessage(
                id="f1",
                sender_id="s",
                recipient_id="r",
                message_type="hsp_message",
                payload={"file": True},
                timestamp=0.0,
            )
            assert await proto.send_message(msg) is True
            outbox = glob.glob(os.path.join(proto.outbox_path, "*.json"))
            assert len(outbox) == 1
            # Simulate a peer process picking it up into our inbox.
            os.rename(outbox[0], os.path.join(proto.inbox_path, os.path.basename(outbox[0])))
            await asyncio.sleep(1.2)
            assert len(received) == 1
            assert received[0].payload == {"file": True}
            # Handled files are consumed (deleted).
            assert glob.glob(os.path.join(proto.inbox_path, "*.json")) == []
        finally:
            await proto.stop_listening()

    async def test_health_check_requires_dirs(self):
        proto = FileBasedProtocol(base_path=tempfile.mkdtemp())
        assert await proto.health_check() is False  # not initialized yet
        await proto.initialize()
        assert await proto.health_check() is True


class TestFallbackProtocolManager:
    pytestmark = pytest.mark.asyncio

    async def test_send_rotates_past_failing_protocol(self):
        """A protocol that fails sends must not block delivery forever;
        the manager rotates to the next healthy one."""

        class FailingProto(InMemoryProtocol):
            async def send_message(self, message) -> bool:
                self.stats["errors"] += 1
                return False

        manager = get_fallback_manager()
        failing = FailingProto()
        healthy = InMemoryProtocol()
        # Higher priority number = preferred; failing one is preferred first.
        manager.add_protocol(failing, priority=3)
        manager.add_protocol(healthy, priority=1)
        assert await manager.initialize()

        received = []

        async def handler(msg):
            received.append(msg)

        manager.register_handler("hsp_message", handler)
        await manager.start()
        try:
            ok = await manager.send_message(
                recipient_id="r", message_type="hsp_message", payload={"rotated": True}
            )
            assert ok is True
            await asyncio.sleep(0.05)
            assert len(received) == 1
            assert failing.stats["errors"] >= 1
        finally:
            await manager.shutdown()

    async def test_send_fails_when_all_protocols_fail(self):
        class FailingProto(InMemoryProtocol):
            async def send_message(self, message) -> bool:
                return False

        manager = get_fallback_manager()
        manager.add_protocol(FailingProto(), priority=1)
        assert await manager.initialize()
        await manager.start()
        try:
            ok = await manager.send_message(
                recipient_id="r",
                message_type="t",
                payload={},
            )
            assert ok is False
        finally:
            await manager.shutdown()

    async def test_get_status_shape(self):
        manager = get_fallback_manager()
        manager.add_protocol(InMemoryProtocol(), priority=1)
        assert await manager.initialize()
        status = manager.get_status()
        assert status["active_protocol"] == "in_memory"
        assert status["protocols"][0]["name"] == "in_memory"
        assert status["protocols"][0]["status"] == "active"
        await manager.shutdown()

    async def test_no_double_delivery_via_wildcard(self):
        """Typed handler must fire exactly once per message (the manager
        must not also register a "*" catch-all that double-delivers)."""
        manager = get_fallback_manager()
        manager.add_protocol(InMemoryProtocol(), priority=1)
        assert await manager.initialize()
        received = []

        async def handler(msg):
            received.append(msg)

        manager.register_handler("hsp_message", handler)
        await manager.start()
        try:
            await manager.send_message(recipient_id="r", message_type="hsp_message", payload={})
            await asyncio.sleep(0.05)
            assert len(received) == 1
        finally:
            await manager.shutdown()


class TestConnectorFallbackIntegration:
    pytestmark = pytest.mark.asyncio

    async def test_connect_initializes_fallback_and_degraded_send(self):
        from core.hsp.connector import HSPConnector

        connector = HSPConnector(ai_id="angela_test", mock_mode=True, enable_fallback=True)
        try:
            assert await connector.connect() is True
            assert connector.fallback_initialized is True
            status = connector.get_communication_status()
            assert status["fallback_initialized"] is True
            assert status["fallback_status"]["active_protocol"] in ("in_memory", "file_based")

            envelope = {
                "message_id": "m1",
                "sender_ai_id": "angela_test",
                "recipient_ai_id": "peer",
                "correlation_id": "c1",
                "qos_parameters": {},
            }
            assert await connector._send_via_fallback("hsp/test", envelope, qos=1) is True

            health = await connector.health_check()
            assert health["fallback_healthy"] is True
        finally:
            await connector.disconnect()
        assert connector.fallback_initialized is False

    async def test_connect_without_fallback_flag(self):
        from core.hsp.connector import HSPConnector

        connector = HSPConnector(ai_id="angela_nofb", mock_mode=True, enable_fallback=False)
        try:
            await connector.connect()
            assert connector.fallback_initialized is False
            assert connector.fallback_manager is None
        finally:
            await connector.disconnect()

    async def test_degraded_send_uses_keyword_signature(self):
        """Regression: the pre-monorepo call passed sender_id as the first
        positional against a recipient_id-first signature (TypeError on every
        degraded send). The connector must pass keywords."""
        from core.hsp.connector import HSPConnector

        connector = HSPConnector(ai_id="angela_kw", mock_mode=True, enable_fallback=True)
        try:
            await connector.connect()
            manager = connector.fallback_manager
            assert manager is not None
            seen = []
            original = manager.send_message

            async def spy(*args, **kwargs):
                seen.append((args, kwargs))
                return await original(*args, **kwargs)

            manager.send_message = spy
            envelope = {
                "message_id": "m2",
                "sender_ai_id": "angela_kw",
                "recipient_ai_id": "peer2",
                "correlation_id": "c2",
                "qos_parameters": {"priority": "high"},
            }
            assert await connector._send_via_fallback("t", envelope, qos=1) is True
            args, kwargs = seen[0]
            assert args == ()  # no positional args at all
            assert kwargs["recipient_id"] == "peer2"
            assert kwargs["priority"] == MessagePriority.HIGH
        finally:
            await connector.disconnect()
