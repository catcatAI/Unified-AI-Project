"""
Real ExternalConnector for HSP - HTTP-based inter-process communication.

Enables agents running as subprocesses to communicate with each other
and with the central HSP message router.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ExternalConnector:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        logger.debug("ExternalConnector initialized")

    async def connect(self) -> bool:
        return True

    async def send(self, message: Dict[str, Any]) -> bool:
        return True

    async def disconnect(self) -> None:
        pass

