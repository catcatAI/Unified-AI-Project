"""
VisionCaptionService — LLM Vision API captioning for semantic image understanding.

Uses existing Google (Gemini Pro Vision) and OpenAI (GPT-4V) API keys
to generate semantic descriptions of images. Supports Chinese and English.

P39: First semantic understanding layer for the vision pipeline.
Allows Angela to answer "你看到了什麼？" with actual semantic content.

Usage:
  svc = VisionCaptionService()
  result = await svc.caption(image_bytes, prompt="描述這張圖片")
  # -> {"caption": "...", "backend": "gemini", "language": "zh", "time_ms": 1234}
"""

import asyncio
import base64
import logging
import mimetypes
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from core.system.config.network_defaults import (
    GOOGLE_API_BASE,
    OPENAI_API_BASE,
    GOOGLE_TIMEOUT,
    OPENAI_TIMEOUT,
)

logger = logging.getLogger(__name__)

# Default prompt templates
CAPTION_PROMPT_ZH = "请用中文详细描述这张图片的内容，包括物体、场景、颜色、动作和整体氛围。"
CAPTION_PROMPT_EN = "Describe this image in detail in English, including objects, scene, colors, actions, and overall atmosphere."


class VisionCaptionService:
    """Generate semantic descriptions of images using LLM Vision APIs.

    Supports multiple backends with automatic fallback:
      1. Gemini Pro Vision (Google, free tier up to 60 req/min)
      2. GPT-4 Vision (OpenAI, if API key configured)

    Lazy-loads API keys from environment (no hard dependencies).
    """

    GEMINI_VISION_MODEL: str = "gemini-1.5-flash"  # Fast, free tier, multimodal
    GPT4V_MODEL: str = "gpt-4o-mini"  # Cost-effective vision model

    def __init__(self):
        self._gemini_key: Optional[str] = None
        self._openai_key: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._available_backends: List[str] = []
        self._initialized: bool = False

    async def initialize(self) -> bool:
        """Check which backends are available by reading env vars.

        Returns True if at least one backend is configured.
        """
        self._gemini_key = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
        self._openai_key = os.environ.get("OPENAI_API_KEY", "")

        self._available_backends = []
        if self._gemini_key and "your_" not in self._gemini_key and "PLACEHOLDER" not in self._gemini_key:
            self._available_backends.append("gemini")
        if self._openai_key and "your_" not in self._openai_key and "PLACEHOLDER" not in self._openai_key:
            self._available_backends.append("openai")

        self._initialized = True
        if self._available_backends:
            logger.info("VisionCaptionService initialized with backends: %s", self._available_backends)
            return True
        logger.warning("VisionCaptionService: no LLM Vision API keys configured (GEMINI_API_KEY / OPENAI_API_KEY)")
        return False

    def _get_session(self) -> aiohttp.ClientSession:
        """Lazy-init HTTP session with connection pooling."""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=5, keepalive_timeout=30)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    async def close(self) -> None:
        """Close the HTTP session. Call during shutdown."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    @property
    def is_available(self) -> bool:
        return self._initialized and len(self._available_backends) > 0

    @property
    def backends(self) -> List[str]:
        return list(self._available_backends)

    # --- Main caption method ---

    async def caption(
        self,
        image_data: bytes,
        prompt: Optional[str] = None,
        language: str = "zh",
        preferred_backend: Optional[str] = None,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """Generate a semantic caption for the given image.

        Args:
            image_data: Raw image bytes (PNG/JPEG)
            prompt: Optional custom prompt (default: language-appropriate template)
            language: "zh" for Chinese, "en" for English
            preferred_backend: "gemini", "openai", or None for auto
            timeout: API call timeout in seconds

        Returns:
            dict with:
              - caption (str): The generated description
              - backend (str): Which backend was used ("gemini", "openai", "none")
              - language (str): Language of the caption
              - time_ms (float): Processing time
              - error (str, optional): Error message if failed
        """
        if not self._initialized:
            await self.initialize()

        if not self.is_available:
            return {
                "caption": "",
                "backend": "none",
                "language": language,
                "error": "No LLM Vision API keys configured",
                "time_ms": 0.0,
            }

        if not image_data:
            return {"caption": "", "backend": "none", "language": language, "error": "Empty image data", "time_ms": 0.0}

        t0 = time.time()
        caption_text = ""
        backend_used = "none"
        mime_type = self._detect_mime_type(image_data)

        # Determine caption prompt
        caption_prompt = prompt or (CAPTION_PROMPT_ZH if language == "zh" else CAPTION_PROMPT_EN)

        # Try backends in order: preferred -> gemini -> openai
        backends_to_try = []
        if preferred_backend and preferred_backend in self._available_backends:
            backends_to_try.append(preferred_backend)
        for b in ["gemini", "openai"]:
            if b in self._available_backends and b not in backends_to_try:
                backends_to_try.append(b)

        for backend in backends_to_try:
            try:
                if backend == "gemini":
                    caption_text = await self._caption_gemini(image_data, caption_prompt, mime_type, timeout)
                elif backend == "openai":
                    caption_text = await self._caption_openai(image_data, caption_prompt, mime_type, timeout)

                if caption_text:
                    backend_used = backend
                    break
            except Exception as e:
                logger.warning("VisionCaption %s failed: %s", backend, e, exc_info=True)
                continue

        elapsed = (time.time() - t0) * 1000
        result: Dict[str, Any] = {
            "caption": caption_text,
            "backend": backend_used,
            "language": language,
            "time_ms": round(elapsed, 1),
        }
        if not caption_text:
            result["error"] = f"All backends failed: {', '.join(backends_to_try)}"
        return result

    # --- Gemini Vision ---

    async def _caption_gemini(
        self, image_data: bytes, prompt: str, mime_type: str, timeout: float
    ) -> str:
        """Generate caption using Gemini Pro Vision API."""
        session = self._get_session()
        b64 = base64.b64encode(image_data).decode("utf-8")

        payload = {
            "contents": [{
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": b64}},
                    {"text": prompt},
                ]
            }],
            "generationConfig": {
                "maxOutputTokens": 256,
                "temperature": 0.4,
                "topP": 0.9,
            },
        }

        url = f"{GOOGLE_API_BASE.rstrip('/')}/models/{self.GEMINI_VISION_MODEL}:generateContent"
        async with session.post(
            url,
            params={"key": self._gemini_key},
            json=payload,
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as resp:
            if resp.status != 200:
                err_text = await resp.text()
                logger.error("Gemini Vision error: HTTP %d: %s", resp.status, err_text[:200])
                return ""
            data = await resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return ""
            return parts[0].get("text", "").strip()

    # --- OpenAI GPT-4 Vision ---

    async def _caption_openai(
        self, image_data: bytes, prompt: str, mime_type: str, timeout: float
    ) -> str:
        """Generate caption using GPT-4 Vision API."""
        session = self._get_session()
        b64 = base64.b64encode(image_data).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64}"

        payload = {
            "model": self.GPT4V_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url, "detail": "auto"}},
                    ],
                }
            ],
            "max_tokens": 256,
            "temperature": 0.4,
        }

        url = f"{OPENAI_API_BASE.rstrip('/')}/chat/completions"
        async with session.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {self._openai_key}", "Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as resp:
            if resp.status != 200:
                err_text = await resp.text()
                logger.error("OpenAI Vision error: HTTP %d: %s", resp.status, err_text[:200])
                return ""
            data = await resp.json()
            choices = data.get("choices", [])
            if not choices:
                return ""
            return choices[0].get("message", {}).get("content", "").strip()

    # --- Utility ---

    @staticmethod
    def _detect_mime_type(image_data: bytes) -> str:
        """Guess MIME type from image bytes header."""
        if image_data[:4] == b"\x89PNG":
            return "image/png"
        if image_data[:2] in (b"\xff\xd8",):
            return "image/jpeg"
        if image_data[:4] == b"RIFF":
            return "image/webp"
        if image_data[:6] in (b"GIF87a", b"GIF89a"):
            return "image/gif"
        if image_data[:4] == b"<svg" or b"<svg" in image_data[:100]:
            return "image/svg+xml"
        return "image/png"  # Default fallback


# --- Global singleton ---

_VISION_CAPTION: Optional[VisionCaptionService] = None
_VISION_CAPTION_LOCK = asyncio.Lock()


async def get_vision_caption_service() -> VisionCaptionService:
    """Get or create the global VisionCaptionService singleton."""
    global _VISION_CAPTION
    if _VISION_CAPTION is None:
        async with _VISION_CAPTION_LOCK:
            if _VISION_CAPTION is None:
                svc = VisionCaptionService()
                await svc.initialize()
                _VISION_CAPTION = svc
    return _VISION_CAPTION


__all__ = [
    "VisionCaptionService",
    "get_vision_caption_service",
]
