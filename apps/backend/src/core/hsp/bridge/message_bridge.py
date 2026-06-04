import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MessageBridge:
    source: str = ""
    target: str = ""
    config: Dict[str, Any] = field(default_factory=dict)

    def bridge_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return message