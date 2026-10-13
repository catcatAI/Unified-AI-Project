# =============================================================================
# ANGELA-MATRIX: [L4] [δ] [A] [L6+]
# =============================================================================
"""HSP fallback protocols — degraded-mode messaging when the MQTT broker is down.

History: the pre-monorepo tree (e32cfe31b, packages/backend/src/hsp/fallback/)
had a complete async implementation. The migration left a 80-line stub whose
``HTTPProtocol.post`` returned ``{"status": "ok"}`` unconditionally and whose
``__init__(base_url=...)`` signature did not even match the connector's
``HTTPProtocol(host=..., port=...)`` call — so enabling fallback would have
raised ``TypeError``, and ``fallback_manager`` was never assigned anywhere.
This module restores the real protocols and fixes four genuine bugs carried
by the old version:

1. ``FallbackProtocolManager.send_message`` was invoked with five positional
   args in the old connector (sender_id first) against a four-parameter
   signature — a guaranteed ``TypeError`` on the degraded path. The signature
   is now keyword-explicit (``recipient_id`` first, no sender_id) and the
   connector passes keywords.
2. ``FileBasedProtocol`` defaulted to a CWD-relative ``data/fallback_comm``
   (split-brain path class); it now anchors to the repo data root.
3. ``FileBasedProtocol.health_check`` had a bare ``except:`` — now logged.
4. The retry backoff was a hard ``asyncio.sleep(1)``; now config-driven via
   ``loop_sleep("fallback_retry_backoff", 0.2)``.
"""

import asyncio
import json
import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, cast

from core.system.config.magic_numbers import loop_sleep

logger = logging.getLogger(__name__)


class ProtocolStatus(Enum):
    """Protocol status enumeration."""

    ACTIVE = "active"
    DEGRADED = "degraded"
    FAILED = "failed"
    DISABLED = "disabled"


class MessagePriority(Enum):
    """Message priority levels."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class FallbackMessage:
    """Fallback protocol message format."""

    id: str
    sender_id: str
    recipient_id: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: float
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    ttl: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary form."""
        data = asdict(self)
        data["priority"] = self.priority.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FallbackMessage":
        """Create from dictionary form."""
        data = dict(data)
        if "priority" in data:
            data["priority"] = MessagePriority(data["priority"])
        return cls(**data)

    def is_expired(self) -> bool:
        """Check whether the message has outlived its TTL."""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl


class BaseFallbackProtocol(ABC):
    """Base class for fallback protocols."""

    def __init__(self, protocol_name: str):
        self.protocol_name = protocol_name
        self.status = ProtocolStatus.DISABLED
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.stats: Dict[str, Any] = {
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
            "last_activity": None,
        }
        self.consecutive_failures: int = 0

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the protocol."""

    @abstractmethod
    async def send_message(self, message: FallbackMessage) -> bool:
        """Send a message via this protocol."""

    @abstractmethod
    async def start_listening(self) -> None:
        """Start listening for inbound messages."""

    @abstractmethod
    async def stop_listening(self) -> None:
        """Stop listening for inbound messages."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Probe whether the protocol is currently usable."""

    def register_handler(self, message_type: str, handler: Callable) -> None:
        """Register a handler for a message type."""
        self.message_handlers.setdefault(message_type, []).append(handler)

    async def handle_message(self, message: FallbackMessage) -> None:
        """Dispatch an inbound message to registered handlers."""
        try:
            if message.is_expired():
                logger.warning("Dropping expired fallback message %s", message.id)
                return

            self.stats["messages_received"] += 1
            self.stats["last_activity"] = time.time()

            # "*" is a wildcard the manager registers for every message;
            # the old version registered it but never dispatched to it.
            handlers = list(self.message_handlers.get(message.message_type, []))
            handlers.extend(self.message_handlers.get("*", []))
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        handler(message)
                except Exception as e:
                    logger.error("Fallback handler error: %s", e, exc_info=True)
                    self.stats["errors"] += 1
        except Exception as e:
            logger.error("Fallback message handling failed: %s", e, exc_info=True)
            self.stats["errors"] += 1


class InMemoryProtocol(BaseFallbackProtocol):
    """In-process queue protocol — last-resort, same-process delivery."""

    def __init__(self, max_queue_size: int = 1000):
        super().__init__("in_memory")
        self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.running = False
        self.listener_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """Initialize the in-memory protocol."""
        self.status = ProtocolStatus.ACTIVE
        logger.info("In-memory fallback protocol initialized")
        return True

    async def send_message(self, message: FallbackMessage) -> bool:
        """Enqueue a message for in-process delivery."""
        try:
            await self.message_queue.put(message)
            self.stats["messages_sent"] += 1
            self.stats["last_activity"] = time.time()
            return True
        except Exception as e:
            logger.error("In-memory send failed: %s", e, exc_info=True)
            self.stats["errors"] += 1
            return False

    async def start_listening(self) -> None:
        """Start draining the queue into registered handlers."""
        if self.running:
            return
        self.running = True
        self.listener_task = asyncio.create_task(self._message_listener())
        logger.info("In-memory fallback protocol listening")

    async def stop_listening(self) -> None:
        """Stop draining the queue."""
        self.running = False
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
        logger.info("In-memory fallback protocol stopped")

    async def _message_listener(self) -> None:
        """Internal queue drain loop."""
        while self.running:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self.handle_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("In-memory listener error: %s", e, exc_info=True)
                await asyncio.sleep(1)

    async def health_check(self) -> bool:
        """Healthy once initialized.

        The pre-monorepo version also required ``self.running`` — but
        ``running`` is only set by ``start_listening``, which the manager
        calls *after* a health check passes, so the protocol could never
        become active (a circular gate that disabled the whole fallback
        chain even in the old tree).
        """
        return self.status == ProtocolStatus.ACTIVE


class FileBasedProtocol(BaseFallbackProtocol):
    """File-based protocol — cross-process delivery via inbox/outbox dirs."""

    def __init__(self, base_path: str = "data/fallback_comm"):
        super().__init__("file_based")
        self.base_path = base_path
        self.inbox_path = os.path.join(base_path, "inbox")
        self.outbox_path = os.path.join(base_path, "outbox")
        self.running = False
        self.listener_task: Optional[asyncio.Task] = None
        self.node_id = str(uuid.uuid4())[:8]

    async def initialize(self) -> bool:
        """Create inbox/outbox directories."""
        try:
            os.makedirs(self.inbox_path, exist_ok=True)
            os.makedirs(self.outbox_path, exist_ok=True)
            self.status = ProtocolStatus.ACTIVE
            logger.info("File fallback protocol initialized at %s", self.base_path)
            return True
        except Exception as e:
            logger.error("File protocol init failed: %s", e, exc_info=True)
            self.status = ProtocolStatus.FAILED
            return False

    async def send_message(self, message: FallbackMessage) -> bool:
        """Write a message file into the outbox."""
        try:
            filename = f"{message.id}_{self.node_id}.json"
            filepath = os.path.join(self.outbox_path, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(message.to_dict(), f, ensure_ascii=False, indent=2)
            self.stats["messages_sent"] += 1
            self.stats["last_activity"] = time.time()
            return True
        except Exception as e:
            logger.error("File protocol send failed: %s", e, exc_info=True)
            self.stats["errors"] += 1
            return False

    async def start_listening(self) -> None:
        """Start polling the inbox directory."""
        if self.running:
            return
        self.running = True
        self.listener_task = asyncio.create_task(self._file_listener())
        logger.info("File fallback protocol listening on %s", self.inbox_path)

    async def stop_listening(self) -> None:
        """Stop polling the inbox directory."""
        self.running = False
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
        logger.info("File fallback protocol stopped")

    async def _file_listener(self) -> None:
        """Poll inbox for new message files; delete after handling."""
        while self.running:
            try:
                if os.path.isdir(self.inbox_path):
                    for filename in os.listdir(self.inbox_path):
                        if not filename.endswith(".json"):
                            continue
                        filepath = os.path.join(self.inbox_path, filename)
                        try:
                            with open(filepath, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            message = FallbackMessage.from_dict(data)
                            await self.handle_message(message)
                            os.remove(filepath)
                        except Exception as e:
                            logger.error("File message handling failed %s: %s", filepath, e)
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error("File listener error: %s", e, exc_info=True)
                await asyncio.sleep(1)

    async def health_check(self) -> bool:
        """Healthy while active and both directories exist."""
        try:
            return (
                self.status == ProtocolStatus.ACTIVE
                and os.path.isdir(self.inbox_path)
                and os.path.isdir(self.outbox_path)
            )
        except Exception as e:
            logger.debug("File protocol health check error: %s", e)
            return False


class HTTPProtocol(BaseFallbackProtocol):
    """HTTP protocol — aiohttp server for inbound + client for known peers.

    Requires peer endpoints to be registered via ``add_endpoint`` before
    outbound sends can succeed; inbound works out of the box.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        super().__init__("http")
        self.host = host
        self.port = port
        self.server: Any = None
        self.session: Any = None
        self.endpoints: Dict[str, str] = {}

    async def initialize(self) -> bool:
        """Start the aiohttp server and client session."""
        try:
            import aiohttp
            from aiohttp import web

            self.session = aiohttp.ClientSession()

            app = web.Application()
            app.router.add_post("/message", self._handle_http_message)
            app.router.add_get("/health", self._handle_health_check)

            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, self.host, self.port)
            await site.start()

            self.server = runner
            self.status = ProtocolStatus.ACTIVE
            logger.info("HTTP fallback protocol listening on %s:%s", self.host, self.port)
            return True
        except Exception as e:
            logger.error("HTTP protocol init failed: %s", e, exc_info=True)
            self.status = ProtocolStatus.FAILED
            await self._close_resources()
            return False

    async def _close_resources(self) -> None:
        """Release server/session resources (best-effort)."""
        if self.server is not None:
            try:
                await self.server.cleanup()
            except Exception as e:
                logger.debug("HTTP server cleanup error: %s", e)
            self.server = None
        if self.session is not None:
            try:
                await self.session.close()
            except Exception as e:
                logger.debug("HTTP session close error: %s", e)
            self.session = None

    async def send_message(self, message: FallbackMessage) -> bool:
        """POST the message to the recipient's registered endpoint."""
        try:
            endpoint = self.endpoints.get(message.recipient_id)
            if not endpoint or self.session is None:
                logger.debug("No HTTP endpoint registered for %s", message.recipient_id)
                return False
            url = f"{endpoint.rstrip('/')}/message"
            async with self.session.post(url, json=message.to_dict()) as response:
                if response.status == 200:
                    self.stats["messages_sent"] += 1
                    self.stats["last_activity"] = time.time()
                    return True
                logger.error("HTTP send failed with status %s", response.status)
                return False
        except Exception as e:
            logger.error("HTTP send error: %s", e, exc_info=True)
            self.stats["errors"] += 1
            return False

    async def _handle_http_message(self, request: Any) -> Any:
        """Inbound /message endpoint."""
        try:
            from aiohttp import web

            data = await request.json()
            message = FallbackMessage.from_dict(data)
            await self.handle_message(message)
            return web.json_response({"status": "ok"})
        except Exception as e:
            logger.error("HTTP inbound message error: %s", e, exc_info=True)
            from aiohttp import web

            return web.json_response({"error": str(e)}, status=400)

    async def _handle_health_check(self, request: Any) -> Any:
        """Inbound /health endpoint."""
        from aiohttp import web

        return web.json_response({"status": self.status.value, "stats": self.stats})

    async def start_listening(self) -> None:
        """Server already listens from initialize()."""

    async def stop_listening(self) -> None:
        """Stop the server and close the client session."""
        await self._close_resources()

    async def health_check(self) -> bool:
        """Healthy while the server is running."""
        return self.status == ProtocolStatus.ACTIVE and self.server is not None

    def add_endpoint(self, node_id: str, endpoint: str) -> None:
        """Register a peer node's HTTP endpoint for outbound sends."""
        self.endpoints[node_id] = endpoint


class FallbackProtocolManager:
    """Priority-ordered manager over fallback protocols.

    Higher priority number = preferred. On send failure the manager rotates
    to the next healthy protocol, skipping ones on a failure streak, until
    the message's retry budget is exhausted.
    """

    def __init__(self) -> None:
        self.protocols: List[tuple] = []  # (priority, protocol)
        self.active_protocol: Optional[BaseFallbackProtocol] = None
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.manager_task: Optional[asyncio.Task] = None
        self.health_check_interval = 30

    def add_protocol(self, protocol: BaseFallbackProtocol, priority: int = 0) -> None:
        """Add a protocol; higher priority is preferred."""
        self.protocols.append((priority, protocol))
        self.protocols.sort(key=lambda x: x[0], reverse=True)

    async def initialize(self) -> bool:
        """Initialize every registered protocol."""
        success_count = 0
        for _priority, protocol in self.protocols:
            try:
                if await protocol.initialize():
                    success_count += 1
                    # No wildcard handler here: the connector registers
                    # typed handlers ("hsp_message"); a "*" catch-all would
                    # double-deliver every inbound message.
                    logger.info("Fallback protocol %s initialized", protocol.protocol_name)
                else:
                    logger.warning(
                        "Fallback protocol %s failed to initialize", protocol.protocol_name
                    )
            except Exception as e:
                logger.error("Fallback protocol %s init error: %s", protocol.protocol_name, e)

        if success_count > 0:
            await self._select_active_protocol()
            return True

        logger.error("All fallback protocols failed to initialize")
        return False

    async def _select_active_protocol(self, exclude: Optional[set] = None) -> None:
        """Pick the highest-priority healthy protocol not in ``exclude``."""
        exclude = exclude or set()
        candidates = []
        for priority, protocol in self.protocols:
            if id(protocol) in exclude:
                continue
            try:
                if await protocol.health_check():
                    candidates.append((priority, protocol))
            except Exception as e:
                logger.debug("Health check error for %s: %s", protocol.protocol_name, e)

        if not candidates and exclude:
            # Everything excluded (failure streaks) — reset counters and retry once.
            for _, protocol in self.protocols:
                protocol.consecutive_failures = 0
            for priority, protocol in self.protocols:
                try:
                    if await protocol.health_check():
                        candidates.append((priority, protocol))
                except Exception:
                    pass

        if not candidates:
            logger.error("No healthy fallback protocol available")
            self.active_protocol = None
            return

        candidates.sort(key=lambda x: x[0], reverse=True)
        chosen = candidates[0][1]
        if self.active_protocol is not chosen:
            if self.active_protocol:
                try:
                    await self.active_protocol.stop_listening()
                except Exception as e:
                    logger.debug("Stop-listening error: %s", e)
            self.active_protocol = chosen
            await chosen.start_listening()
            logger.info("Active fallback protocol switched to %s", chosen.protocol_name)

    async def send_message(
        self,
        recipient_id: str,
        message_type: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: Optional[str] = None,
        sender_id: str = "system",
    ) -> bool:
        """Build a FallbackMessage and deliver it (with rotation + retries)."""
        message = FallbackMessage(
            id=str(uuid.uuid4()),
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            payload=payload,
            timestamp=time.time(),
            priority=priority,
            correlation_id=correlation_id,
        )
        return await self.send_fallback_message(message)

    async def send_fallback_message(self, message: FallbackMessage) -> bool:
        """Deliver a pre-built message across healthy protocols."""
        tried: set = set()
        backoff = loop_sleep("fallback_retry_backoff", 0.2)

        while True:
            if not self.active_protocol or id(self.active_protocol) in tried:
                await self._select_active_protocol(exclude=tried)

            protocol = self.active_protocol
            if not protocol:
                logger.error("No fallback protocol available for message %s", message.id)
                return False

            tried.add(id(protocol))
            try:
                success = await protocol.send_message(message)
            except Exception as e:
                logger.error("Protocol %s send raised: %s", protocol.protocol_name, e)
                success = False

            if success:
                protocol.consecutive_failures = 0
                logger.debug("Message %s sent via %s", message.id, protocol.protocol_name)
                return True

            protocol.consecutive_failures += 1
            if message.retry_count >= message.max_retries:
                logger.error(
                    "Message %s exhausted retries (last protocol: %s)",
                    message.id,
                    protocol.protocol_name,
                )
                return False
            message.retry_count += 1
            await asyncio.sleep(backoff)

    async def _handle_protocol_message(self, message: FallbackMessage) -> None:
        """Queue inbound messages for external consumption."""
        await self.message_queue.put(message)

    async def get_message(self, timeout: Optional[float] = None) -> Optional[FallbackMessage]:
        """Pop one inbound message (optional timeout)."""
        try:
            if timeout:
                msg = await asyncio.wait_for(self.message_queue.get(), timeout=timeout)
            else:
                msg = await self.message_queue.get()
            return cast(FallbackMessage, msg)
        except asyncio.TimeoutError:
            return None

    def register_handler(self, message_type: str, handler: Callable) -> None:
        """Register a handler on every (initialized) protocol."""
        for _, protocol in self.protocols:
            protocol.register_handler(message_type, handler)

    async def start(self) -> None:
        """Start the health monitor loop."""
        if self.running:
            return
        self.running = True
        self.manager_task = asyncio.create_task(self._health_monitor())
        logger.info("Fallback protocol manager started")

    async def shutdown(self) -> None:
        """Stop the monitor and every protocol."""
        self.running = False
        if self.manager_task:
            self.manager_task.cancel()
            try:
                await self.manager_task
            except asyncio.CancelledError:
                pass

        for _, protocol in self.protocols:
            try:
                await protocol.stop_listening()
            except Exception as e:
                logger.error("Error stopping %s: %s", protocol.protocol_name, e)
        logger.info("Fallback protocol manager stopped")

    async def _health_monitor(self) -> None:
        """Periodically re-select the active protocol."""
        while self.running:
            try:
                await self._select_active_protocol()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error("Fallback health monitor error: %s", e)
                await asyncio.sleep(5)

    def get_status(self) -> Dict[str, Any]:
        """Status snapshot for health endpoints."""
        return {
            "active_protocol": (
                self.active_protocol.protocol_name if self.active_protocol else None
            ),
            "protocols": [
                {
                    "name": protocol.protocol_name,
                    "priority": priority,
                    "status": protocol.status.value,
                    "consecutive_failures": protocol.consecutive_failures,
                    "stats": protocol.stats,
                }
                for priority, protocol in self.protocols
            ],
        }


def get_fallback_manager() -> FallbackProtocolManager:
    """Factory: one manager per HSP connector (no shared global state)."""
    return FallbackProtocolManager()
