#!/usr/bin/env python3
"""
Angela AI - Environment Configuration Validator
环境配置验证器

验证所有必需的环境变量是否正确配置，提供清晰的错误提示。
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Required environment variables with descriptions
REQUIRED_VARS: Dict[str, str] = {
    "ANGELA_HOME": "Angela AI home directory",
}

OPTIONAL_VARS: Dict[str, str] = {
    "ANGELA_LOG_LEVEL": "Log level (DEBUG, INFO, WARNING, ERROR)",
    "ANGELA_CONFIG_DIR": "Configuration directory override",
    "ANGELA_DATA_DIR": "Data directory override",
    "ANGELA_LLM_API_KEY": "LLM API key",
    "ANGELA_LLM_BASE_URL": "LLM API base URL",
}

# Required config keys with descriptions
REQUIRED_CONFIG_KEYS: Dict[str, str] = {
    "version": "Configuration version",
    "name": "Configuration name",
}


class ConfigValidator:
    """Validates environment configuration."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._errors: List[str] = []
        self._warnings: List[str] = []

    def validate_environment(self) -> bool:
        """Validate required environment variables."""
        self._errors.clear()
        self._warnings.clear()
        all_ok = True
        for var, desc in REQUIRED_VARS.items():
            if not os.environ.get(var):
                self._errors.append(f"Missing required env var: {var} ({desc})")
                all_ok = False
        for var, desc in OPTIONAL_VARS.items():
            if not os.environ.get(var):
                logger.debug(f"Optional env var not set: {var} ({desc})")
        return all_ok

    def validate_config(self) -> bool:
        """Validate config dictionary has required keys."""
        self._errors.clear()
        all_ok = True
        for key, desc in REQUIRED_CONFIG_KEYS.items():
            if key not in self.config:
                self._errors.append(f"Missing required config key: {key} ({desc})")
                all_ok = False
        return all_ok

    def get_errors(self) -> List[str]:
        return list(self._errors)

    def get_warnings(self) -> List[str]:
        return list(self._warnings)


def validate_environment() -> Tuple[bool, List[str]]:
    """Quick one-shot environment validation."""
    validator = ConfigValidator()
    ok = validator.validate_environment()
    return ok, validator.get_errors()


def validate_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Quick one-shot config validation."""
    validator = ConfigValidator(config)
    ok = validator.validate_config()
    return ok, validator.get_errors()


__all__ = ["ConfigValidator", "validate_environment", "validate_config"]
