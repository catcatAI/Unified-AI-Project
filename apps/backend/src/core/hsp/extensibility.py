import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class HSPMessageRegistry:
    handlers: Dict[str, Callable] = field(default_factory=dict)

    def register(self, message_type: str, handler: Callable) -> None:
        self.handlers[message_type] = handler

    def get_handler(self, message_type: str) -> Optional[Callable]:
        return self.handlers.get(message_type)


class HSPExtensionManager:
    def __init__(self):
        self._extensions: Dict[str, Any] = {}
        self.registry = HSPMessageRegistry()
        logger.debug("HSPExtensionManager initialized")

    def register_extension(self, name: str, extension: Any) -> None:
        self._extensions[name] = extension

    def get_extension(self, name: str) -> Optional[Any]:
        return self._extensions.get(name)
