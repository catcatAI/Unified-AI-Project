# ANGELA-MATRIX: L3 [γ] [B] [L0]
"""Ollama LLM backend"""

import json
import logging
import time

import aiohttp
from core.interfaces.protocols import LLMResponse
from core.system.config.network_defaults import DEFAULT_OLLAMA_MODEL, OLLAMA_HOST, OLLAMA_TIMEOUT
from core.utils import safe_error

from .base import BaseLLMBackend

logger = logging.getLogger(__name__)


class OllamaBackend(BaseLLMBackend):
    """Ollama 後端"""

    def __init__(
        self,
        base_url: str = OLLAMA_HOST,
        model: str = DEFAULT_OLLAMA_MODEL,
        api_key: str = "",
        timeout: float = OLLAMA_TIMEOUT,
    ):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    async def check_health(self) -> bool:
        """Check health."""
        try:
            session = self._get_session()
            async with session.get(
                f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("models", [])
                    for m in models:
                        if self.model in m.get("name", ""):
                            return True
                    if models:
                        self.model = models[0].get("name", DEFAULT_OLLAMA_MODEL)
                        return True
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")
        return False

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate."""
        start_time = time.time()
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        payload = {
            "model": self.model,
            "messages": messages,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 256),
            },
        }
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            session = self._get_session()
            async with session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers=headers or None,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                if response.status == 200:
                    text = ""
                    async for line in response.content:
                        line = line.decode("utf-8").strip()
                        if line:
                            try:
                                data = json.loads(line)
                                if data.get("message", {}).get("content"):
                                    text += data["message"]["content"]
                            except json.JSONDecodeError:
                                continue
                    return LLMResponse(
                        text=text,
                        backend="ollama",
                        model=self.model,
                        response_time_ms=(time.time() - start_time) * 1000,
                        confidence=0.9,
                    )
                else:
                    return LLMResponse(
                        text="",
                        backend="ollama",
                        model=self.model,
                        error=f"HTTP {response.status}",
                    )
        except Exception as e:
            logger.error(f"Error in {__name__}: {e}", exc_info=True)
            return LLMResponse(text="", backend="ollama", model=self.model, error=safe_error(e))
