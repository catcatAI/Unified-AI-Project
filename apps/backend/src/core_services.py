"""
Standalone CLI mode — real services are loaded when running the backend server.
CLI handlers gracefully degrade with "not available" messages.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_OPERATIONAL_CONFIGS = {}


class _Services:
    def __init__(self):
        self._service_registry: Dict[str, Any] = {}

    def register(self, name: str, instance: Any) -> None:
        self._service_registry[name] = instance

    def get(self, key: str, default: Any = None) -> Any:
        return self._service_registry.get(key, default)

    def __contains__(self, key: object) -> bool:
        return key in self._service_registry

    def list_services(self) -> List[str]:
        return list(self._service_registry.keys())


_services = _Services()


async def initialize_services(config=None, ai_id=None, use_mock_ham=False, operational_configs=None) -> None:
    """Initialize all services."""
    cfg = config or {}
    logger.info("CLI standalone mode: registering basic services")

    class LoggerService:
        def info(self, msg: str) -> None:
            logger.info(msg)
        def debug(self, msg: str) -> None:
            logger.debug(msg)
        def error(self, msg: str) -> None:
            logger.error(msg)

    class ConfigService:
        def __init__(self, conf: dict):
            self._conf = conf
        def get(self, key: str, default: Any = None) -> Any:
            return self._conf.get(key, default)
        def all(self) -> dict:
            return self._conf

    _services.register("logger", LoggerService())
    _services.register("config", ConfigService(cfg))

    if ai_id:
        logger.info(f"CLI configured with AI ID: {ai_id}")
        _services.register("ai_id", ai_id)

    if use_mock_ham:
        logger.info("Mock HAM service requested but not available — use_mock_ham=True has no effect")


def get_services() -> _Services:
    return _services


async def shutdown_services() -> None:
    logger.info("CLI standalone mode: clearing service registry")
    _services._service_registry.clear()
