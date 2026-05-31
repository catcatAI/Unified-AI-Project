"""
ANGELA-MATRIX: [L3] [β] [B] [L2]
MessageLoggerHandler — C3 on_message handler that logs and annotates user messages.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_message_counter = 0


async def message_logger_handler(data: dict) -> dict:
    """Log incoming message and annotate with metadata."""
    global _message_counter
    _message_counter += 1
    user_text = data.get("user_message", "")
    model_id = data.get("model_id", "unknown")
    logger.info(
        "[Plugin:MessageLogger] message #%d | model=%s | len=%d",
        _message_counter, model_id, len(user_text),
    )
    data["plugin_logged_at"] = datetime.utcnow().isoformat()
    data["plugin_message_seq"] = _message_counter
    return data


class MessageLoggerHandler:
    """Handler class wrapping message_logger_handler for registration."""

    def __init__(self):
        self.counter = 0

    async def __call__(self, data: dict) -> dict:
        self.counter += 1
        user_text = data.get("user_message", "")
        model_id = data.get("model_id", "unknown")
        logger.info(
            "[Plugin:MessageLogger] message #%d | model=%s | len=%d",
            self.counter, model_id, len(user_text),
        )
        data["plugin_logged_at"] = datetime.utcnow().isoformat()
        data["plugin_message_seq"] = self.counter
        return data
