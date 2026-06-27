"""
Angela AI v6.0 - Security & Communication Monitor
Consolidated from system.security_monitor.
"""

import logging
import os
import secrets
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ABCKeyManager:
    def __init__(self) -> None:
        self._keys: Dict[str, str] = {
            "KeyA": secrets.token_hex(32),
            "KeyB": secrets.token_hex(32),
            "KeyC": secrets.token_hex(32),
        }
        for k in self._keys:
            env_val = os.environ.get(k)
            if env_val:
                self._keys[k] = env_val
        logger.info("ABCKeyManager initialized (keys generated)")

    def get_key(self, key_name: str) -> Optional[str]:
        return self._keys.get(key_name)

    def rotate_key(self, key_name: str) -> Optional[str]:
        if key_name in self._keys:
            self._keys[key_name] = secrets.token_hex(32)
            logger.info(f"Key {key_name} rotated")
            return self._keys[key_name]
        return None
