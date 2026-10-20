# ANGELA-MATRIX: L3 [γ] [B] [L0]
"""OpenAI API LLM backend (GPT-4, GPT-3.5, etc.)"""

import logging
import time

import aiohttp
from core.interfaces.protocols import LLMResponse
from core.system.config.network_defaults import (
    DEFAULT_OPENAI_MODEL,
    OPENAI_API_BASE,
    OPENAI_TIMEOUT,
)
from core.utils import safe_error

from .base import BaseLLMBackend

logger = logging.getLogger(__name__)


class OpenAIAPIBackend(BaseLLMBackend):
    """OpenAI API 後端 (GPT-4, GPT-3.5 等)"""

    def __init__(
        self,
        api_key: str,
        base_url: str = OPENAI_API_BASE,
        model: str = DEFAULT_OPENAI_MODEL,
        timeout: float = OPENAI_TIMEOUT,
    ):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def check_health(self) -> bool:
        """Check health."""
        if not self.api_key or "your_" in self.api_key or "PLACEHOLDER" in self.api_key:
            return False
        try:
            session = self._get_session()
            async with session.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}", exc_info=True)
        return False

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate (streaming when a stream_callback is given)."""
        stream_callback = kwargs.pop("stream_callback", None)
        if stream_callback is not None:
            return await self.generate_stream(prompt, stream_callback, **kwargs)
        start_time = time.time()
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 512),
            "temperature": kwargs.get("temperature", 0.7),
        }
        try:
            session = self._get_session()
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    text = data["choices"][0]["message"]["content"]
                    tokens = data.get("usage", {}).get("total_tokens", 0)
                    return LLMResponse(
                        text=text,
                        backend="openai",
                        model=self.model,
                        tokens_used=tokens,
                        response_time_ms=(time.time() - start_time) * 1000,
                        confidence=0.95,
                    )
                else:
                    text = await response.text()
                    return LLMResponse(
                        text="",
                        backend="openai",
                        model=self.model,
                        error=f"HTTP {response.status}: {text[:200]}",
                    )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            return LLMResponse(text="", backend="openai", model=self.model, error=safe_error(e))

    async def generate_stream(self, prompt: str, stream_callback, **kwargs) -> LLMResponse:
        """Streaming generate: POST stream:true, invoke the callback per delta.

        The SSE chat endpoint (POST /api/v1/chat/stream) delivers tokens as
        the model produces them; without this the cloud providers answered in
        one piece and the desktop app could not show a progressive reply.
        """
        start_time = time.time()
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 512),
            "temperature": kwargs.get("temperature", 0.7),
            "stream": True,
        }
        try:
            session = self._get_session()
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=600, sock_read=30),
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    return LLMResponse(
                        text="",
                        backend="openai",
                        model=self.model,
                        error=f"HTTP {response.status}: {text[:200]}",
                    )
                chunks = await self._stream_and_collect(
                    response, stream_callback, ["choices", 0, "delta", "content"]
                )
            return LLMResponse(
                text="".join(chunks),
                backend="openai",
                model=self.model,
                tokens_used=0,
                response_time_ms=(time.time() - start_time) * 1000,
                confidence=0.95,
            )
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}", exc_info=True)
            return LLMResponse(text="", backend="openai", model=self.model, error=safe_error(e))
