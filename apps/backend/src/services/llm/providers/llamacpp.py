# ANGELA-MATRIX: L3 [γ] [B] [L0]
"""llama.cpp LLM backend"""

import logging
import time
from typing import Optional

import aiohttp
from core.interfaces.protocols import LLMResponse
from core.system.config.network_defaults import LLAMACPP_HOST, LLM_REQUEST_TIMEOUT
from core.utils import safe_error

from .base import BaseLLMBackend

logger = logging.getLogger(__name__)


class LlamaCppBackend(BaseLLMBackend):
    """llama.cpp 後端"""

    def __init__(
        self,
        base_url: str = LLAMACPP_HOST,
        model: Optional[str] = None,
        timeout: float = LLM_REQUEST_TIMEOUT,
        context_window: int = 4096,
    ):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        try:
            self.context_window = int(context_window)
        except (TypeError, ValueError):
            self.context_window = 4096
        if self.context_window <= 0:
            self.context_window = 4096

    async def check_health(self) -> bool:
        """Check the OpenAI-compatible model endpoint, with legacy health fallback."""
        session = self._get_session()
        for endpoint in ("/v1/models", "/health"):
            try:
                async with session.get(
                    f"{self.base_url}{endpoint}", timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status != 200:
                        continue
                    if endpoint == "/v1/models" and not self.model:
                        data = await response.json()
                        models = data.get("data", []) if isinstance(data, dict) else []
                        if models:
                            model_id = models[0].get("id") or models[0].get("model")
                            if model_id:
                                self.model = str(model_id)
                    return True
            except Exception as exc:
                logger.debug("llama.cpp health probe %s failed: %s", endpoint, exc)
        return False

    async def _fetch_model_name(self) -> Optional[str]:
        """Best-effort model name from /v1/models (llama.cpp OpenAI-compatible)."""
        try:
            session = self._get_session()
            async with session.get(
                f"{self.base_url}/v1/models", timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("data") or []
                    if models:
                        mid = models[0].get("id") or models[0].get("model")
                        return str(mid) if mid is not None else None
        except Exception as e:
            logger.warning(f"llama.cpp model fetch failed: {e}", exc_info=True)
        return None

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
                        text=text,
                        backend="llama.cpp",
                        model=self.model or "unknown",
                        tokens_used=tokens,
                        response_time_ms=(time.time() - start_time) * 1000,
                        confidence=0.9,
                    )
                else:
                    text = await response.text()
                    return LLMResponse(
                        text="",
                        backend="llama.cpp",
                        model=self.model or "unknown",
                        error=f"HTTP {response.status}: {text[:200]}",
                    )
        except Exception as e:
            logger.error(f"Error in {__name__}: {e}", exc_info=True)
            return LLMResponse(
                text="", backend="llama.cpp", model=self.model or "unknown", error=safe_error(e)
            )
