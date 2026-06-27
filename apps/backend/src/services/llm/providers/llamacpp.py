# ANGELA-MATRIX: L3 [γ] [B] [L0]
"""llama.cpp LLM backend"""

import logging
import time

import aiohttp
from core.interfaces.protocols import LLMResponse
from core.system.config.network_defaults import LLAMACPP_HOST, LLM_REQUEST_TIMEOUT

from .base import BaseLLMBackend

logger = logging.getLogger(__name__)


class LlamaCppBackend(BaseLLMBackend):
    """llama.cpp 後端"""

    def __init__(self, base_url: str = LLAMACPP_HOST, model: str = None, timeout: float = LLM_REQUEST_TIMEOUT):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def check_health(self) -> bool:
        """Check health."""
        try:
            session = self._get_session()
            async with session.get(
                f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.model = data.get("model_name", self.model)
                    return True
        except Exception as e:
            logger.debug(f"llama.cpp health check failed: {e}")
        return False

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate."""
        start_time = time.time()
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        payload = {
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 512),
            "temperature": kwargs.get("temperature", 0.7),
            "stream": False,
        }
        try:
            session = self._get_session()
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    text = data["choices"][0]["message"]["content"]
                    tokens = data.get("usage", {}).get("total_tokens", 0)
                    return LLMResponse(
                        text=text, backend="llama.cpp", model=self.model or "unknown",
                        tokens_used=tokens, response_time_ms=(time.time() - start_time) * 1000,
                        confidence=0.9,
                    )
                else:
                    text = await response.text()
                    return LLMResponse(
                        text="", backend="llama.cpp", model=self.model,
                        error=f"HTTP {response.status}: {text[:200]}",
                    )
        except Exception as e:
            logger.error(f"Error in {__name__}: {e}", exc_info=True)
            return LLMResponse(text="", backend="llama.cpp", model=self.model, error=str(e))
