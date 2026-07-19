"""
Stream Synthesizer Core

Core synthesis logic for incremental multi-source token synthesis.
"""
from __future__ import annotations

import asyncio
import re
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional

from .token_stream import StreamToken, TokenType, StreamToken, TokenType


@dataclass
class SynthesizerConfig:
    """Configuration for stream synthesis."""
    max_buffer_size: int = 1024
    correction_threshold: float = 0.7
    min_verified_confidence: float = 0.7
    max_pending_predicted: int = 128
    max_verified_context: int = 256
    correction_threshold: float = 0.6
    max_corrections: int = 16
    flush_interval: float = 0.01
    enable_corrections: bool = True


class StreamSynthesizer:
    """
    Incremental multi-source token synthesizer.
    
    Consumes token streams from predictive, retrieval, and generative producers,
    synthesizes them incrementally, and outputs verified tokens.
    """
    
    def __init__(
        self,
        output_stream: "TokenStream",
        config: Optional["SynthesizerConfig"] = None,
    ):
        self.output_stream = output_stream
        self.config = config or SynthesizerConfig()
        
        # Input buffers
        self.pending_predicted: deque = deque()
        self.verified_context: List[StreamToken] = []
        self.generated_buffer: List[StreamToken] = []
        self.pending_corrections: Dict[int, StreamToken] = {}
        
        # State
        self._running = False
        self._stats = {
            "output_tokens": 0,
            "corrections": 0,
            "verified_predictions": 0,
            "corrections_made": 0,
        }
    
    @property
    def stats(self) -> Dict[str, int]:
        return dict(self._stats)
    
    def feed_token(self, token: StreamToken) -> None:
        """Feed a token from any producer."""
        if token.type == TokenType.PREDICTED:
            self._on_predicted(token)
        elif token.type == TokenType.RETRIEVED:
            self._on_retrieved(token)
        elif token.type == TokenType.GENERATED:
            self._on_generated(token)
    
    def _on_predicted(self, token: StreamToken) -> None:
        """Handle predicted token."""
        if len(self.pending_predicted) >= self.config.max_pending_predicted:
            # Remove oldest
            self.pending_predicted.popleft()
        self.pending_predicted.append(token)
    
    def _on_retrieved(self, token: StreamToken) -> None:
        """Handle retrieved token - verify predictions."""
        # Find best matching prediction
        best_match = self._find_best_match(token, self.pending_predicted)
        if best_match:
            best_match.metadata["verified"] = True
            best_match.metadata["retrieved_ref"] = token.seq_id
            best_match.confidence = max(best_match.confidence, token.confidence)
            self._stats["verified_predictions"] += 1
        
        # Add to verified context
        if len(self.verified_context) >= self.config.max_verified_context:
            self.verified_context.pop(0)
        self.verified_context.append(token)
    
    def _on_generated(self, token: StreamToken) -> None:
        """Handle generated token."""
        if len(self.generated_buffer) >= 256:
            self.generated_buffer.pop(0)
        self.generated_buffer.append(token)
    
    def _find_best_match(self, target: StreamToken, candidates: List[StreamToken]) -> Optional[StreamToken]:
        """Find best matching predicted token for retrieved content."""
        if not candidates:
            return None
        
        # Simple keyword overlap scoring
        target_words = set(target.content.lower().split())
        best_score = 0.0
        best_token = None
        
        for candidate in candidates:
            candidate_words = set(candidate.content.lower().split())
            if not candidate_words or not target_words:
                continue
            overlap = len(target_words & candidate_words)
            score = overlap / max(len(target_words), len(candidate_words))
            if score > best_score and score > 0.3:
                best_score = score
                best_token = candidate
        
        return best_token
    
    async def flush_verified(self) -> int:
        """Flush verified predictions to output."""
        flushed = 0
        while self.pending_predicted and self.pending_predicted[0].metadata.get("verified"):
            token = self.pending_predicted.popleft()
            await self._emit_synthesized(token)
            self._stats["verified_predictions"] += 1
            flushed += 1
        return flushed
    
    async def flush_retrieved(self) -> int:
        """Flush retrieved content."""
        flushed = 0
        while self.verified_context:
            token = self.verified_context.pop(0)
            await self._emit_synthesized(token)
            flushed += 1
        return flushed
    
    async def flush_generated(self) -> int:
        """Flush generated content with corrections."""
        flushed = 0
        while self.generated_buffer:
            token = self.generated_buffer.pop(0)
            
            # Check for corrections
            if token.seq_id in self.pending_corrections:
                correction = self.pending_corrections.pop(token.seq_id)
                await self._emit_synthesized(correction)
                self._stats["corrections_made"] += 1
                continue
            
            await self._emit_synthesized(token)
            flushed += 1
        return flushed
    
    async def _emit_synthesized(self, token: StreamToken) -> None:
        """Emit final synthesized token."""
        from .token_stream import StreamToken, TokenType
        
        synced = StreamToken(
            content=token.content,
            type=TokenType.SYNTHESIZED,
            source=f"synthesized:{token.source}",
            confidence=token.confidence,
            metadata={
                **token.metadata,
                "original_source": token.source,
                "verified": token.metadata.get("verified", False),
            },
        )
        await self.output_stream.put(synced)
        self._stats["output_tokens"] += 1
    
    async def process_cycle(self) -> int:
        """Process one synthesis cycle."""
        flushed = 0
        flushed += await self.flush_verified()
        flushed += await self.flush_retrieved()
        flushed += await self.flush_generated()
        return flushed
    
    async def run(self) -> None:
        """Run synthesis loop."""
        while True:
            flushed = await self.process_cycle()
            if flushed == 0:
                await asyncio.sleep(0.01)
    
    def get_stats(self) -> Dict[str, int]:
        return dict(self._stats)


class StreamSynthesizer(StreamSynthesizer):
    """Alias for compatibility."""
    pass