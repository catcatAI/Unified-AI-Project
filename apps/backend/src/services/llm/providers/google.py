# ANGELA-MATRIX: L3 [γ] [B] [L0]
"""Google Gemini API LLM backend"""

import logging
import time

import aiohttp

from core.interfaces.protocols import LLMResponse
from core.system.config.network_defaults import (
    GOOGLE_API_BASE,
    DEFAULT_GOOGLE_MODEL,
    GOOGLE_TIMEOUT,
)
from .base import BaseLLMBackend

logger = logging.getLogger(__name__)


class GoogleAPIBackend(BaseLLMBackend):
    """Google Gemini API 後端"""

    GEMINI_BASE = GOOGLE_API_BASE

    def __init__(self, api_key: str, model: str = DEFAULT_GOOGLE_MODEL):
        self.api_key = api_key
        self.model = model
        self.timeout = GOOGLE_TIMEOUT

    async def check_health(self) -> bool:
        if not self.api_key:
            return False
        return True

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
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
            async with aiohttp.ClientSession() as session:
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
                            text=text, backend="google", model=self.model,
                            tokens_used=tokens, response_time_ms=(time.time() - start_time) * 1000,
                            confidence=0.95,
                        )
                    else:
                        err_text = await resp.text()
                        return LLMResponse(
                            text="", backend="google", model=self.model,
                            error=f"HTTP {resp.status}: {err_text[:200]}",
                        )
        except Exception as e:
            logger.error(f"Google Gemini API error: {e}", exc_info=True)
            return LLMResponse(text="", backend="google", model=self.model, error=str(e))
