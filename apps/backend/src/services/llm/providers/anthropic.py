# ANGELA-MATRIX: L3 [γ] [B] [L0]
"""Anthropic API LLM backend (Claude series)"""

import logging
import time

import aiohttp

from core.interfaces.protocols import LLMResponse
from core.system.config.network_defaults import ANTHROPIC_API_BASE, DEFAULT_ANTHROPIC_MODEL, ANTHROPIC_TIMEOUT
from .base import BaseLLMBackend

logger = logging.getLogger(__name__)


class AnthropicAPIBackend(BaseLLMBackend):
    """Anthropic API 後端 (Claude 系列)"""

    def __init__(self, api_key: str, base_url: str = ANTHROPIC_API_BASE, model: str = DEFAULT_ANTHROPIC_MODEL, timeout: float = ANTHROPIC_TIMEOUT):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def check_health(self) -> bool:
        if not self.api_key or "your_" in self.api_key or "PLACEHOLDER" in self.api_key:
            return False
        return True

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        start_time = time.time()
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 512),
            "temperature": kwargs.get("temperature", 0.7),
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    headers={
                        "x-api-key": self.api_key,
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01",
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        text = data.get("content", [{}])[0].get("text", "")
                        tokens = data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0)
                        return LLMResponse(
                            text=text, backend="anthropic", model=self.model,
                            tokens_used=tokens, response_time_ms=(time.time() - start_time) * 1000,
                            confidence=0.95,
                        )
                    else:
                        text = await response.text()
                        return LLMResponse(
                            text="", backend="anthropic", model=self.model,
                            error=f"HTTP {response.status}: {text[:200]}",
                        )
        except Exception as e:
            logger.error(f"Anthropic API error: {e}", exc_info=True)
            return LLMResponse(text="", backend="anthropic", model=self.model, error=str(e))
