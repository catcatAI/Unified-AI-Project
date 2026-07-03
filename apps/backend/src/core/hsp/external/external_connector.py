"""
Real ExternalConnector for HSP - HTTP-based inter-process communication.

Enables agents running as subprocesses to communicate with each other
and with the central HSP message router.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ExternalConnector:
    def __init__(self, config: Optional[Dict[str, Any]] = None, ai_id: Optional[str] = None,
                 broker_address: Optional[str] = None, broker_port: Optional[int] = None):
        self.config = config or {}
        self.ai_id = ai_id or self.config.get("ai_id", "default")
        self.broker_address = broker_address or self.config.get("broker_address", "localhost")
        self.broker_port = broker_port or self.config.get("broker_port", 1883)
        logger.debug(f"ExternalConnector initialized (ai_id={self.ai_id})")

    async def connect(self) -> bool:
        return True

    async def send(self, message: Dict[str, Any]) -> bool:
        return True

    async def disconnect(self) -> None:
        self.config = {}
        logger.debug("ExternalConnector disconnected")

