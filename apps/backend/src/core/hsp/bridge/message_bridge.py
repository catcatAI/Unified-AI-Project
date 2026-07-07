import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class MessageBridge:
    source: str = ""
    target: str = ""
    config: Dict[str, Any] = field(default_factory=dict)

    def bridge_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return message

    def handle_external_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.bridge_message(message)