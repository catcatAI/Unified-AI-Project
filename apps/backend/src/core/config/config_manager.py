import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Central configuration manager.

    Handles loading configuration defaults and validating configuration
    dictionaries against expected schema.
    """

    def __init__(self):
        self._config: Dict[str, Any] = {}

    async def load_defaults(self, *args, **kwargs) -> Dict[str, Any]:
        """Load default configuration values.

        Returns a dict of default config values. Subclasses may override
        to load from files or environment.
        """
        defaults = {
            "debug": False,
            "log_level": "INFO",
            "timeout": 30,
            "max_retries": 3,
        }
        self._config.update(defaults)
        return dict(self._config)

    async def validate(self, *args, **kwargs) -> bool:
        """Validate the current configuration.

        Returns True if valid, False otherwise. Logs warnings for
        invalid or missing keys.
        """
        required_keys = {"debug", "log_level"}
        missing = required_keys - set(self._config.keys())
        if missing:
            logger.warning("ConfigManager: missing required keys: %s", missing)
            return False
        return True

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value
