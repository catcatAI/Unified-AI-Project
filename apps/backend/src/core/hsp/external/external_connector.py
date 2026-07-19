"""
Real ExternalConnector for HSP - HTTP-based inter-process communication.

Enables agents running as subprocesses to communicate with each other
and with the central HSP message router.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ExternalConnector:
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        ai_id: Optional[str] = None,
        broker_address: Optional[str] = None,
        broker_port: Optional[int] = None,
    ):
        self.config = config or {}
        self.ai_id = ai_id or self.config.get("ai_id", "default")
        self.broker_address = broker_address or self.config.get("broker_address", "localhost")
        self.broker_port = broker_port or self.config.get("broker_port", 1883)
        logger.debug(f"ExternalConnector initialized (ai_id={self.ai_id})")

    async def connect(self) -> bool:
        """Connect to broker via HTTP health-check."""
        import aiohttp

        url = f"http://{self.broker_address}:{self.broker_port}/health"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    ok = resp.status == 200
                    logger.debug(f"ExternalConnector connect -> {resp.status} ({ok})")
                    return ok
        except Exception as e:
            logger.debug(f"ExternalConnector connect failed (broker may be down): {e}")
            return False

    async def send(self, message: Dict[str, Any]) -> bool:
        """Send a message via HTTP POST to the broker."""
        import aiohttp

        url = f"http://{self.broker_address}:{self.broker_port}/message"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=message, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    ok = resp.status == 200
                    logger.debug(f"ExternalConnector send -> {resp.status} ({ok})")
                    return ok
        except Exception as e:
            logger.debug(f"ExternalConnector send failed: {e}")
            return False

    async def disconnect(self) -> None:
        self.config = {}
        logger.debug("ExternalConnector disconnected")
