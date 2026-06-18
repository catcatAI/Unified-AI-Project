"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
VisionHandler — processes image analysis intents.
"""

import asyncio
import base64
import logging
import mimetypes
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class VisionHandler:
    """Handles image analysis intents: describe, OCR, identify."""

    def __init__(self, model_bus: Any = None):
        self._model_bus = model_bus

    async def handle(self, text: str, intent: str = "vision") -> str:
        image_path = self._extract_image_path(text)
        if not image_path:
            return "（視覺分析）請提供圖片路徑或附帶圖片。"
        target = Path(image_path)
        if not await asyncio.to_thread(target.exists):
            return f"（視覺分析）圖片不存在：{image_path}"
        if not await asyncio.to_thread(target.is_file):
            return f"（視覺分析）不是檔案：{image_path}"
        mime_type = mimetypes.guess_type(str(target))[0]
        if not mime_type or not mime_type.startswith("image/"):
            return f"（視覺分析）不支援的圖片格式：{mime_type}"
        try:
            image_data = await asyncio.to_thread(target.read_bytes)
            b64 = base64.b64encode(image_data).decode()
            if self._model_bus and hasattr(self._model_bus, "execute_handler"):
                result = await self._model_bus.execute_handler(
                    "vision", text, {"image_path": str(target), "image_b64": b64, "mime_type": mime_type}
                )
                if result.get("success"):
                    return f"（視覺分析）{result.get('result', '無結果')}"
            return self._local_describe(target, mime_type)
        except Exception as e:
            logger.error(f"VisionHandler error: {e}", exc_info=True)
            return f"（視覺分析）分析失敗：{e}"

    def _extract_image_path(self, text: str) -> Optional[str]:
        m = re.search(r"```(?:image|img|pic)?\s*\n(.*?)```", text, re.DOTALL)
        if m:
            path = m.group(1).strip().split("\n")[0].strip()
            if path:
                return path
        m = re.search(r"`([^`]+\.(?:png|jpg|jpeg|gif|bmp|webp|svg))`", text, re.IGNORECASE)
        if m:
            return m.group(1)
        m = re.search(r"([\w\\/:.\-]+\.(?:png|jpg|jpeg|gif|bmp|webp|svg))", text, re.IGNORECASE)
        if m:
            return m.group(1)
        prefixes = ["分析圖片", "看看圖片", "描述圖片", "圖片", "analyze image", "describe image", "look at"]
        for p in prefixes:
            if text.lower().startswith(p):
                rest = text[len(p):].strip().strip(":：").strip()
                if rest:
                    return rest
        return text.strip() if "." in text else None

    def _local_describe(self, target: Path, mime_type: str) -> str:
        size = target.stat().st_size
        size_str = f"{size} bytes" if size < 1024 else f"{size // 1024}KB"
        return (
            f"（視覺分析）圖片資訊：\n"
            f"  檔案：{target.name}\n"
            f"  格式：{mime_type}\n"
            f"  大小：{size_str}\n"
            f"  注意：本機描述模式，需要 LLM 後端才能進行深度分析。"
        )


__all__ = ["VisionHandler"]
