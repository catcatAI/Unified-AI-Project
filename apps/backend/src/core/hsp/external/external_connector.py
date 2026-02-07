import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ExternalConnector:
    """
    Connects to external HSP nodes. 
    (Stubbed to fix corruption)
    """
    def __init__(self, ai_id=None, config=None, **kwargs):
        self.config = config or {}
        self.ai_id = ai_id
        logger.info(f"ExternalConnector (Stub) initialized. Ignored kwargs: {kwargs.keys()}")

    async def connect(self):
        logger.info("ExternalConnector Stub: Connected.")
        return True

    async def send(self, message: Dict[str, Any]):
        logger.info(f"ExternalConnector Stub: Sending message: {message.get('message_id')}")
        return True
