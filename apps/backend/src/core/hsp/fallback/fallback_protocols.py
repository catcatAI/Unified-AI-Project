import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class InMemoryProtocol:
    data: Dict[str, Any] = field(default_factory=dict)

    def store(self, key: str, value: Any) -> None:
        self.data[key] = value

    def retrieve(self, key: str) -> Optional[Any]:
        return self.data.get(key)


class FileBasedProtocol:
    def __init__(self, base_path: str = "/tmp"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _sanitize_key(self, key: str) -> str:
        import re

        sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", key)
        return sanitized.replace("..", "_")

    def save(self, key: str, value: Any) -> bool:
        try:
            key = self._sanitize_key(key)
            file_path = os.path.join(self.base_path, f"{key}.json")
            if os.path.commonpath([os.path.abspath(file_path), os.path.abspath(self.base_path)]) != os.path.abspath(
                self.base_path
            ):
                logger.warning(f"Invalid key for FileBasedProtocol.save: {key}")
                return False
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(value, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.warning(f"FileBasedProtocol.save failed: {e}", exc_info=True)
            return False

    def load(self, key: str) -> Optional[Any]:
        try:
            key = self._sanitize_key(key)
            file_path = os.path.join(self.base_path, f"{key}.json")
            if os.path.commonpath([os.path.abspath(file_path), os.path.abspath(self.base_path)]) != os.path.abspath(
                self.base_path
            ):
                logger.warning(f"Invalid key for FileBasedProtocol.load: {key}")
                return None
            if not os.path.exists(file_path):
                return None
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"FileBasedProtocol.load failed: {e}", exc_info=True)
            return None


class HTTPProtocol:
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url

    async def get(self, path: str) -> Optional[Dict[str, Any]]:
        return None

    async def post(self, path: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return {"status": "ok"}
