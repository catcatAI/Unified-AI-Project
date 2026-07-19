# ANGELA-MATRIX: L3 [γ] [B] [L0]
"""LLM backend abstract base class"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

import aiohttp
from core.interfaces.protocols import LLMResponse

logger = logging.getLogger(__name__)


class BaseLLMBackend(ABC):
    """LLM 後端抽象基類"""

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    def _get_session(self) -> aiohttp.ClientSession:
        """Return the long-lived ClientSession (lazy-init, enables connection pooling)."""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=10, keepalive_timeout=30)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    async def close(self) -> None:
        """Close the HTTP session. Call during shutdown."""
        session = getattr(self, "_session", None)
        if session and not session.closed:
            await session.close()
            self._session = None

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """生成回應"""

    @abstractmethod
    async def check_health(self) -> bool:
        """檢查後端健康狀態"""
