# ANGELA-MATRIX: L3 [γ] [B] [L0]
"""Google Gemini API LLM backend"""

import logging
import time
from typing import Any

import aiohttp
from core.interfaces.protocols import LLMResponse
from core.system.config.network_defaults import (
    DEFAULT_GOOGLE_MODEL,
    GOOGLE_API_BASE,
    GOOGLE_TIMEOUT,
)
from core.utils import safe_error

from .base import BaseLLMBackend

logger = logging.getLogger(__name__)


class GoogleAPIBackend(BaseLLMBackend):
    """Google Gemini API 後端"""

    GEMINI_BASE = GOOGLE_API_BASE

    def __init__(
        self, api_key: str, model: str = DEFAULT_GOOGLE_MODEL, timeout: float = GOOGLE_TIMEOUT
    ):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def check_health(self) -> bool:
        """Check health: the API key works AND the configured model exists.

        The key check alone was not enough: a *stale* model name (every
        "gemini-pro" / "gemini-1.5-*" name returns 404 on the API version
        this project speaks) passed the health check and then failed on
        every single generation, with the reason buried in a log line. The
        model is now verified against the models endpoint, and the warning
        names the model plus the available alternatives.
        """
        if not self.api_key:
            return False
        try:
            session = self._get_session()
            async with session.get(
                f"{self.GEMINI_BASE}/models",
                params={"key": self.api_key},
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status != 200:
                    return False
                try:
                    payload = await resp.json()
                except Exception:
                    payload = {}
        except Exception as e:
            logger.warning(f"Google health check failed: {e}", exc_info=True)
            return False

        available = self._model_names(payload)
        if available and self.model not in available:
            alternatives = ", ".join(sorted(available)[:8])
            logger.warning(
                "Google Gemini model %r is not available for this API key "
                "(404 on every request). Available models include: %s",
                self.model,
                alternatives,
            )
            return False
        return True

    @staticmethod
    def _model_names(payload: Any) -> set:
        """The model ids the endpoint offers (empty when unknown)."""
        names = set()
        entries = payload.get("models") if isinstance(payload, dict) else None
        for entry in entries or []:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            if isinstance(name, str):
                names.add(name.split("/")[-1])
        return names

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate (streaming when a stream_callback is given)."""
        stream_callback = kwargs.pop("stream_callback", None)
        if stream_callback is not None:
            return await self.generate_stream(prompt, stream_callback, **kwargs)
        start_time = time.time()
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        contents = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else msg["role"]
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": kwargs.get("max_tokens", 512),
                "temperature": kwargs.get("temperature", 0.7),
            },
        }
        try:
            session = self._get_session()
            async with session.post(
                f"{self.GEMINI_BASE}/models/{self.model}:generateContent",
                params={"key": self.api_key},
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    candidate = data.get("candidates", [{}])[0]
                    text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
                    usage = data.get("usageMetadata", {})
                    tokens = usage.get("totalTokenCount", 0)
                    return LLMResponse(
                        text=text,
                        backend="google",
                        model=self.model,
                        tokens_used=tokens,
                        response_time_ms=(time.time() - start_time) * 1000,
                        confidence=0.95,
                    )
                else:
                    err_text = await resp.text()
                    return LLMResponse(
                        text="",
                        backend="google",
                        model=self.model,
                        error=f"HTTP {resp.status}: {err_text[:200]}",
                    )
        except Exception as e:
            logger.error(f"Google Gemini API error: {e}", exc_info=True)
            return LLMResponse(text="", backend="google", model=self.model, error=safe_error(e))

    async def generate_stream(self, prompt: str, stream_callback, **kwargs) -> LLMResponse:
        """Streaming generate: Gemini's streamGenerateContent (alt=sse)."""
        start_time = time.time()
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        contents = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else msg["role"]
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": kwargs.get("max_tokens", 512),
                "temperature": kwargs.get("temperature", 0.7),
            },
        }
        try:
            session = self._get_session()
            async with session.post(
                f"{self.GEMINI_BASE}/models/{self.model}:streamGenerateContent",
                params={"key": self.api_key, "alt": "sse"},
                json=payload,
                timeout=aiohttp.ClientTimeout(total=600, sock_read=30),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return LLMResponse(
                        text="",
                        backend="google",
                        model=self.model,
                        error=f"HTTP {resp.status}: {text[:200]}",
                    )
                chunks = await self._stream_and_collect(
                    resp, stream_callback, ["candidates", 0, "content", "parts"]
                )
            return LLMResponse(
                text="".join(chunks),
                backend="google",
                model=self.model,
                response_time_ms=(time.time() - start_time) * 1000,
                confidence=0.95,
            )
        except Exception as e:
            logger.error(f"Google Gemini streaming error: {e}", exc_info=True)
            return LLMResponse(text="", backend="google", model=self.model, error=safe_error(e))
