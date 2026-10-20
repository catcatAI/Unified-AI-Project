# ANGELA-MATRIX: L3 [γ] [B] [L0]
"""LLM backend abstract base class"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Callable, List, Optional

import aiohttp
from core.interfaces.protocols import LLMResponse

logger = logging.getLogger(__name__)


class BaseLLMBackend(ABC):
    """LLM 後端抽象基類"""

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    def _get_session(self) -> aiohttp.ClientSession:
        """Return the long-lived ClientSession (lazy-init, enables connection pooling)."""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=10, keepalive_timeout=30)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    async def close(self) -> None:
        """Close the HTTP session. Call during shutdown."""
        session = getattr(self, "_session", None)
        if session and not session.closed:
            await session.close()
            self._session = None

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """生成回應"""

    @abstractmethod
    async def check_health(self) -> bool:
        """檢查後端健康狀態"""

    # ------------------------------------------------------------------
    # Streaming helpers (shared by the HTTP providers)
    # ------------------------------------------------------------------
    @staticmethod
    async def _iter_sse_payloads(response: Any) -> AsyncIterator[str]:
        """Yield the JSON payload of every SSE ``data:`` line.

        A network chunk can carry several lines (and a line can be split
        across chunks), so the payload is buffered and split on newlines
        before it is interpreted. ``[DONE]`` terminates the stream and is not
        yielded; a malformed line is skipped (a provider must not die because
        one chunk was odd).
        """
        buffer = ""
        async for raw in response.content:
            buffer += raw.decode("utf-8", "replace")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line or line.startswith(":"):
                    continue
                if line.startswith("data:"):
                    line = line[5:].strip()
                if line == "[DONE]":
                    return
                if line:
                    yield line
        # A stream that ends without a trailing newline still has a last line.
        line = buffer.strip()
        if line.startswith("data:"):
            line = line[5:].strip()
        if line and line != "[DONE]":
            yield line

    @staticmethod
    async def _iter_ndjson_payloads(response: Any) -> AsyncIterator[str]:
        """Yield every non-empty line of an NDJSON stream (Ollama)."""
        async for raw in response.content:
            line = raw.decode("utf-8", "replace").strip()
            if line:
                yield line

    @staticmethod
    def _walk_path(data: Any, path: List[Any]) -> Any:
        """Follow *path* into a decoded payload (None when the path misses).

        A path element is either a mapping key or a list index (the OpenAI
        shape is ``choices[0].delta.content``).
        """
        node: Any = data
        for key in path:
            if isinstance(key, int):
                if not isinstance(node, list) or key >= len(node):
                    return None
                node = node[key]
                continue
            if not isinstance(node, dict):
                return None
            node = node.get(key)
            if node is None:
                return None
        return node

    @staticmethod
    def _join_text_parts(node: Any) -> str:
        """Join the text of a list-of-parts payload (Gemini's shape)."""
        if isinstance(node, str):
            return node
        if not isinstance(node, list):
            return ""
        parts = []
        for item in node:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)

    @classmethod
    def _extract_delta(cls, payload: str, path: List[Any]) -> str:
        """Pull the text delta out of a provider payload (empty when absent)."""
        try:
            data = json.loads(payload)
        except (TypeError, ValueError):
            return ""
        return cls._join_text_parts(cls._walk_path(data, path))

    async def _stream_and_collect(
        self,
        response: Any,
        stream_callback: Callable[[str], Any],
        delta_path: List[Any],
        ndjson: bool = False,
    ) -> List[str]:
        """Feed every delta to *stream_callback* and return the collected text.

        The callback may be sync or async; a failing callback is logged and
        skipped (one bad chunk must not abort the answer).
        """
        import inspect as _inspect

        chunks: List[str] = []
        iterator = (
            self._iter_ndjson_payloads(response) if ndjson else self._iter_sse_payloads(response)
        )
        async for payload in iterator:
            piece = self._extract_delta(payload, delta_path)
            if not piece:
                continue
            chunks.append(piece)
            try:
                out = stream_callback(piece)
                if _inspect.isawaitable(out):
                    await out
            except Exception as exc:
                logger.debug("stream_callback failed: %s", exc)
        return chunks
