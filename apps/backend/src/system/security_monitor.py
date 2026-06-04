"""
Angela AI v6.0 - Security & Communication Monitor
密鑰生成與加密通訊監控器

實現 A/B/C 密鑰體系：
- Key A: 後端控制密鑰 (Backend Control)
- Key B: 行動端通訊密鑰 (Mobile-Backend Comm)
- Key C: 桌面端/跨裝置同步密鑰 (Desktop/Sync)

包含系統匣監控功能，可常駐並啟停後端服務。
"""

import os
import logging
import secrets
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ABCKeyManager:
    """A/B/C 密鑰管理器 — 生成和提供三種通訊密鑰。"""

    def __init__(self) -> None:
        self._keys: Dict[str, str] = {
            "KeyA": secrets.token_hex(32),
            "KeyB": secrets.token_hex(32),
            "KeyC": secrets.token_hex(32),
        }
        # Allow override via environment
        for k in self._keys:
            env_val = os.environ.get(k)
            if env_val:
                self._keys[k] = env_val
        logger.info("ABCKeyManager initialized (keys generated)")

    def get_key(self, key_name: str) -> Optional[str]:
        """Get a key by name (KeyA, KeyB, KeyC)."""
        return self._keys.get(key_name)

    def rotate_key(self, key_name: str) -> Optional[str]:
        """Rotate a single key."""
        if key_name in self._keys:
            self._keys[key_name] = secrets.token_hex(32)
            logger.info(f"Key {key_name} rotated")
            return self._keys[key_name]
        return None

