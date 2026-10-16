# =============================================================================
# ANGELA-MATRIX: L6 [η] [A] L2+
# =============================================================================
"""StreamingPipeline — sequential multi-level streaming orchestrator.

Runs Section→Paragraph→Sentence→Token level-by-level.
Each level: fast pass → emit → slow pass → emit.
Output buffer fills in progressively: keywords → grammar → exact sentences.
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional, Tuple

from .producers import (
    BaseLevelProducer,
    ParagraphProducer,
    SectionProducer,
    SentenceProducer,
    TokenProducer,
)
from .token_stream import StreamToken, TokenStream, TokenType

logger = logging.getLogger(__name__)


class StreamingPipeline:
    """Sequential multi-level streaming pipeline."""

    def __init__(self, garden=None, ed3n=None, fallback_fn=None):
        self.producers: List[Tuple[str, BaseLevelProducer]] = [
            ("section", SectionProducer(garden=garden, ed3n=ed3n)),
            ("paragraph", ParagraphProducer(garden=garden, ed3n=ed3n)),
            ("sentence", SentenceProducer(garden=garden, ed3n=ed3n)),
            ("token", TokenProducer(garden=garden, ed3n=ed3n)),
        ]
        self.fallback_fn = fallback_fn

    def set_fallback(self, fn):
        """Set fallback function called when all levels produce empty output."""
        self.fallback_fn = fn

    async def _run_level_pass(
        self,
        level_name: str,
        producer,
        query: str,
        buffer: str,
        stream: TokenStream,
        pass_type: str,
    ) -> Tuple[str, object]:
        """Run one pass (fast/slow) on a level. Returns (new_buffer, output)."""
        t0 = time.time()
        try:
            if pass_type == "fast":
                out = producer.fast_pass(query, buffer)
            else:
                out = producer.slow_pass(query, buffer, None)
        except Exception as e:
            logger.warning("%s %s_pass failed: %s", level_name, pass_type, e)
            out = None

        if out:
            buffer = self._merge(buffer, out)
            confidence = 0.55 if pass_type == "fast" else 0.85
            await self._emit(stream, out, level_name, pass_type, confidence, time.time() - t0)
        return buffer, out

    async def _run_level(
        self, level_name: str, producer, query: str, buffer: str, stream: TokenStream
    ) -> Optional[str]:
        """Run fast+slow passes for one level. Returns updated buffer, None to break."""
        if not producer.garden and not producer.ed3n:
            return buffer

        buffer, fast_out = await self._run_level_pass(
            level_name, producer, query, buffer, stream, "fast"
        )
        buffer, _slow_out = await self._run_level_pass(
            level_name, producer, query, buffer, stream, "slow"
        )

        # If section level produced nothing, skip remaining (no learned knowledge)
        if level_name == "section" and not buffer and not fast_out:
            return None  # signal break
        return buffer

    async def _run_fallback(self, query: str, stream: TokenStream) -> None:
        """Trigger LLM fallback when buffer is empty."""
        if self.fallback_fn:
            try:
                fallback_text = await self.fallback_fn(query)
                if fallback_text:
                    await self._emit(stream, fallback_text, "fallback", "llm", 0.5, 0.0)
            except Exception as e:
                logger.warning("Fallback failed: %s", e)

    async def stream(self, query: str, stream: TokenStream, timeout: float = 5.0) -> None:
        """Run streaming pipeline, emitting tokens to stream."""
        buffer = ""

        for level_name, producer in self.producers:
            result = await self._run_level(level_name, producer, query, buffer, stream)
            if result is None:
                break
            buffer = result

        # Final: if buffer is still empty, trigger fallback
        if not buffer:
            await self._run_fallback(query, stream)

        # Signal done
        await stream.put(StreamToken.create_control("DONE"))

    async def _emit(
        self,
        stream: TokenStream,
        text: str,
        level: str,
        pass_type: str,
        confidence: float,
        latency: float,
    ) -> None:
        token = StreamToken(
            content=text,
            type=TokenType.SYNTHESIZED,
            source=f"{level}_{pass_type}",
            confidence=confidence,
            metadata={"level": level, "pass": pass_type, "latency_ms": round(latency * 1000, 1)},
        )
        await stream.put(token)

    def _merge(self, buffer: str, new_text: str) -> str:
        """Fill-in partial replace merge."""
        if not buffer:
            return new_text
        if not new_text:
            return buffer

        buffer_lower = buffer.lower()
        new_lower = new_text.lower()
        buf_words = set(buffer_lower.split())
        new_words = set(new_lower.split())

        overlap = buf_words & new_words
        new_only = new_words - buf_words

        if not overlap:
            # No overlap: append
            return f"{buffer}. {new_text}"

        if new_lower in buffer_lower:
            # New text is fully contained in buffer → no change
            return buffer

        if buffer_lower in new_lower:
            # Buffer is fully contained in new → replace entirely
            return new_text

        # Partial overlap: fill in new words
        if new_only:
            return f"{buffer} {new_text}"
        return buffer
