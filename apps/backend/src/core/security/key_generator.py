# =============================================================================
# ANGELA-MATRIX: 密鑰生成工具
# =============================================================================
# 職責: 生成強隨機系統密鑰並更新環境變量
# =============================================================================

import secrets
import string
from typing import Optional


class KeyGenerator:
    """Secure cryptographic key generator.

    Generates strong random system keys using the `secrets` module
    and supports updating .env files with generated keys.
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}

    @staticmethod
    def generate_secure_key(length: int = 32) -> str:
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(chars) for _ in range(length))

    def update_env_file(self, keys: dict, env_path: str) -> None:
        import os

        existing = {}
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        existing[k.strip()] = v.strip()
        existing.update(keys)
        with open(env_path, "w", encoding="utf-8") as f:
            for k, v in existing.items():
                f.write(f"{k}={v}\n")
