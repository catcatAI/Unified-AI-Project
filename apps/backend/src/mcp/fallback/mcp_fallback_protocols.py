# ANGELA-MATRIX: L0[基础层] [A] L1

"""MCP Fallback Protocols - 备选通信协议实现"""

import asyncio
import logging
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class FallbackProtocolType(Enum):
    """备选通信协议类型"""

    IN_PROCESS = "in_process"
    SHARED_MEMORY = "shared_memory"
    FILE_BASED = "file_based"
    LOOPBACK = "loopback"


class FallbackProtocol:
    """备选通信协议基类"""

    def __init__(self, protocol_type: FallbackProtocolType):
        self.protocol_type = protocol_type
        self._handlers: Dict[str, Callable[..., Awaitable[Any]]] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()

    def register_handler(self, command: str, handler: Callable[..., Awaitable[Any]]) -> None:
        self._handlers[command] = handler

    async def send_message(self, target: str, command: str, payload: Dict[str, Any]) -> bool:
        await self._message_queue.put({"target": target, "command": command, "payload": payload})
        return True

    async def process_messages(self) -> int:
        count = 0
        while not self._message_queue.empty():
            msg = await self._message_queue.get()
            handler = self._handlers.get(msg["command"])
            if handler:
                try:
                    await handler(msg["payload"])
                    count += 1
                except Exception as e:
                    logger.error(f"[FallbackProtocol] Handler error for {msg['command']}: {e}")
        return count


async def initialize_fallback_protocols(is_multiprocess: bool = False) -> bool:
    """初始化所有备选通信协议"""
    logger.info(f"[MCP-Fallback] Initializing protocols (multiprocess={is_multiprocess})...")
    protocols = {
        FallbackProtocolType.IN_PROCESS: FallbackProtocol(FallbackProtocolType.IN_PROCESS),
    }
    if is_multiprocess:
        protocols[FallbackProtocolType.SHARED_MEMORY] = FallbackProtocol(
            FallbackProtocolType.SHARED_MEMORY
        )
    logger.info(f"[MCP-Fallback] {len(protocols)} protocol(s) initialized")
    return True
