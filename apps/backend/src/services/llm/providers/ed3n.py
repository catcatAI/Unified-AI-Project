# ANGELA-MATRIX: L3 [γ] [B] [L0]
"""ED3N LLM backend — three-layer cognitive architecture provider"""

import asyncio
import logging
import time

from core.interfaces.protocols import LLMResponse
from core.utils import safe_error

from .base import BaseLLMBackend

logger = logging.getLogger(__name__)


class ED3NBackend(BaseLLMBackend):
    """ED3N 後端 — 使用三層認知架構 (L1 Biological / L2 Cognitive / L3 Identity)"""

    def __init__(self, base_url="", model="ed3n-v1", api_key="", timeout=30.0, depth="auto"):
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.depth = depth
        self._engine = None
        self._kwargs_store = {}

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        start_time = time.time()
        depth = kwargs.pop("depth", self.depth)
        context = kwargs.get("context")
        self._kwargs_store = {
            "max_tokens": kwargs.get("max_tokens"),
            "temperature": kwargs.get("temperature"),
            "top_p": kwargs.get("top_p"),
            "stop": kwargs.get("stop"),
        }
        try:
            if self._engine is None:
                from ai.ed3n.ed3n_engine import ED3NEngine

                self._engine = ED3NEngine.get_shared()

            if depth == "reflex":
                text = self._engine.process_reflex(prompt)
            else:
                text = await asyncio.to_thread(
                    self._engine.process, prompt, context=context, depth=depth
                )
                if not text:
                    text = self._engine.process_shallow(prompt, context)

            return LLMResponse(
                text=text,
                backend="ed3n",
                model=self.model,
                tokens_used=self._kwargs_store.get("max_tokens") or 0,
                response_time_ms=(time.time() - start_time) * 1000,
                confidence=0.85,
            )
        except Exception as e:
            logger.error(f"Error in {__name__}: {e}", exc_info=True)
            return LLMResponse(text="", backend="ed3n", model=self.model, error=safe_error(e))

    async def check_health(self) -> bool:
        try:
            if self._engine is None:
                from ai.ed3n.ed3n_engine import ED3NEngine

                self._engine = ED3NEngine.get_shared()
            return self._engine is not None
        except Exception as e:
            logger.warning(f"ED3N health check failed: {e}", exc_info=True)
            return False
