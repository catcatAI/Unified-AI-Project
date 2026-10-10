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
        """Generate (non-streaming, or streaming when stream_callback is given)."""
        stream_callback = kwargs.pop("stream_callback", None)
        if stream_callback is not None:
            return await self.generate_stream(prompt, stream_callback, **kwargs)
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

    async def generate_stream(self, prompt: str, stream_callback, **kwargs) -> LLMResponse:
        """Streaming generate: POST stream:true, invoke callback per delta.

        Callback may be sync or async. Returns the full LLMResponse at end
        (same shape as generate) so callers keep one code path. Per-chunk
        stall timeout 30s; the caller's total timeout still bounds us.
        """
        import inspect as _inspect
        import json as _json

        start_time = time.time()
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        payload = {
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 512),
            "temperature": kwargs.get("temperature", 0.7),
            "stream": True,
        }

        async def _emit(piece: str) -> None:
            if not piece:
                return
            try:
                out = stream_callback(piece)
                if _inspect.isawaitable(out):
                    await out
            except Exception as exc:
                logger.debug("stream_callback failed: %s", exc)

        # Defensive caps (audit 2026-10-10): total wall so a wedged server
        # can't hold our worker forever; chunk cap so a runaway stream can't
        # grow memory without bound (max_tokens normally bounds this anyway).
        chunks: list = []
        truncated = False
        try:
            session = self._get_session()
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=600, sock_read=30),
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    return LLMResponse(
                        text="",
                        backend="llama.cpp",
                        model=self.model or "unknown",
                        error=f"HTTP {response.status}: {text[:200]}",
                    )
                async for raw in response.content:
                    try:
                        line = raw.decode("utf-8", errors="replace").strip()
                    except Exception:
                        continue
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = _json.loads(data)
                        delta = (obj.get("choices") or [{}])[0].get("delta", {})
                        piece = delta.get("content") or ""
                    except Exception:
                        continue
                    if piece:
                        if len(chunks) < 4096:
                            chunks.append(piece)
                        else:
                            truncated = True
                        await _emit(piece)
            text = "".join(chunks)
            if truncated:
                text += "…[truncated]"
            return LLMResponse(
                text=text,
                backend="llama.cpp",
                model=self.model or "unknown",
                tokens_used=0,
                response_time_ms=(time.time() - start_time) * 1000,
                confidence=0.9,
            )
        except Exception as e:
            logger.error(f"Error in {__name__} stream: {e}", exc_info=True)
            return LLMResponse(
                text="".join(chunks),
                backend="llama.cpp",
                model=self.model or "unknown",
                error=safe_error(e),
            )
