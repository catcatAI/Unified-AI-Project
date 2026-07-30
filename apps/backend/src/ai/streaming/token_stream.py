"""
Token Stream Infrastructure

Core data structures for unified token streaming across all producers/consumers.
"""
from __future__ import annotations

import asyncio
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Deque, Dict, List, Optional, Union

from core.utils import safe_error


class TokenType(Enum):
    """Token type enumeration for stream classification."""
    
    # Input sources
    PREDICTED = "predicted"      # Predictive producer (speculative)
    RETRIEVED = "retrieved"      # Retrieval producer (factual)
    GENERATED = "generated"      # Generative producer (LLM)
    
    # Internal processing
    VERIFIED = "verified"        # Verified prediction (confirmed by retrieval)
    CORRECTION = "correction"    # Correction token (synthesizer correction)
    
    # Output
    SYNTHESIZED = "synthesized"  # Final synthesized output
    
    # Control
    CONTROL = "control"          # Control tokens (start/end/error)
    HEARTBEAT = "heartbeat"      # Keep-alive


@dataclass
class StreamToken:
    """Unified token structure for all stream sources."""
    
    # Identity
    seq_id: int = 0                          # Global sequence ID
    token_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    
    # Content
    content: str = ""                         # Token text content
    type: TokenType = TokenType.GENERATED    # Token type
    
    # Source tracking
    source: str = "unknown"                  # Producer source name
    producer_seq: int = 0                    # Producer-local sequence
    
    # Quality signals
    confidence: float = 0.5                  # 0.0-1.0 confidence score
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Timing
    timestamp: float = field(default_factory=time.time)
    latency_ms: float = 0.0                  # Producer latency
    
    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = TokenType(self.type)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "seq_id": self.seq_id,
            "token_id": self.token_id,
            "content": self.content,
            "type": self.type.value,
            "source": self.source,
            "producer_seq": self.producer_seq,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "latency_ms": self.latency_ms,
        }
    
    @classmethod
    def create_predicted(cls, content: str, source: str, confidence: float = 0.6, **kwargs) -> "StreamToken":
        """Create a predicted token."""
        return cls(
            content=content,
            type=TokenType.PREDICTED,
            source=source,
            confidence=confidence,
            metadata=kwargs,
        )
    
    @classmethod
    def create_retrieved(cls, content: str, source: str, confidence: float = 0.8, **kwargs) -> "StreamToken":
        """Create a retrieved token."""
        return cls(
            content=content,
            type=TokenType.RETRIEVED,
            source=source,
            confidence=confidence,
            metadata=kwargs,
        )
    
    @classmethod
    def create_generated(cls, content: str, source: str, confidence: float = 0.9, **kwargs) -> "StreamToken":
        """Create a generated token."""
        return cls(
            content=content,
            type=TokenType.GENERATED,
            source=source,
            confidence=confidence,
            metadata=kwargs,
        )
    
    @classmethod
    def create_synthesized(cls, content: str, source: str = "synthesizer", **kwargs) -> "StreamToken":
        """Create a synthesized output token."""
        return cls(
            content=content,
            type=TokenType.SYNTHESIZED,
            source=source,
            confidence=kwargs.pop("confidence", 0.95),
            metadata=kwargs,
        )
    
    @classmethod
    def create_control(cls, control_type: str, **kwargs) -> "StreamToken":
        """Create a control token."""
        return cls(
            content=f"[CONTROL:{control_type}]",
            type=TokenType.CONTROL,
            source="synthesizer",
            confidence=1.0,
            metadata={"control_type": control_type, **kwargs},
        )


class TokenTypeMismatch(Exception):
    """Raised when token type doesn't match expected."""
    pass


class TokenStream:
    """
    Async token stream with buffering and flow control.
    
    Thread-safe async queue with backpressure support.
    """
    
    def __init__(self, config: Optional["StreamConfig"] = None):
        self.config = config or StreamConfig()
        self._queue: asyncio.Queue[StreamToken] = asyncio.Queue(maxsize=self.config.buffer_size)
        self._closed = False
        self._seq_counter = 0
        self._producer_counters: Dict[str, int] = {}
        self._stats = {
            "produced": 0,
            "consumed": 0,
            "dropped": 0,
            "errors": 0,
        }
        self._closed_event = asyncio.Event()
    
    def _next_seq(self, producer: str = "default") -> int:
        """Get next sequence ID."""
        self._seq_counter += 1
        self._producer_counters[producer] = self._producer_counters.get(producer, 0) + 1
        return self._seq_counter
    
    async def put(self, token: StreamToken, timeout: Optional[float] = None) -> bool:
        """Put token into stream with backpressure."""
        if self._closed:
            raise RuntimeError("Stream is closed")
        
        # Assign sequence IDs
        token.seq_id = self._next_seq(token.source)
        token.producer_seq = self._producer_counters.get(token.source, 0)
        
        timeout = timeout or self.config.put_timeout
        try:
            await asyncio.wait_for(self._queue.put(token), timeout=timeout)
            self._stats["produced"] += 1
            return True
        except asyncio.TimeoutError:
            self._stats["dropped"] += 1
            return False
    
    async def get(self, timeout: Optional[float] = None) -> Optional[StreamToken]:
        """Get next token from stream."""
        if self._closed and self._queue.empty():
            return None
        
        timeout = timeout or self.config.get_timeout
        try:
            token = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            self._stats["consumed"] += 1
            return token
        except asyncio.TimeoutError:
            return None
    
    async def __aiter__(self) -> AsyncGenerator[StreamToken, None]:
        """Async iterator over tokens."""
        while True:
            token = await self.get()
            if token is None:
                break
            yield token
    
    def put_nowait(self, token: StreamToken) -> bool:
        """Non-blocking put."""
        if self._closed:
            return False
        token.seq_id = self._next_seq(token.source)
        token.producer_seq = self._producer_counters.get(token.source, 0)
        try:
            self._queue.put_nowait(token)
            self._stats["produced"] += 1
            return True
        except asyncio.QueueFull:
            self._stats["dropped"] += 1
            return False
    
    def get_nowait(self) -> Optional[StreamToken]:
        """Non-blocking get."""
        try:
            token = self._queue.get_nowait()
            self._stats["consumed"] += 1
            return token
        except asyncio.QueueEmpty:
            return None
    
    def close(self):
        """Close the stream."""
        self._closed = True
        self._closed_event.set()
    
    @property
    def closed(self) -> bool:
        return self._closed
    
    @property
    def empty(self) -> bool:
        return self._queue.empty()
    
    @property
    def qsize(self) -> int:
        return self._queue.qsize()
    
    def stats(self) -> Dict[str, int]:
        return dict(self._stats)
    
    async def wait_closed(self):
        """Wait for stream to close."""
        await self._closed_event.wait()


@dataclass
class StreamConfig:
    """Stream configuration."""
    
    buffer_size: int = 1000              # Max queue size
    enable_stats: bool = True            # Enable statistics
    max_token_size: int = 8192           # Max token content size
    
    # Timeout configuration (private storage with property accessors)
    _put_timeout_val: float = 5.0        # Put timeout (seconds)
    _get_timeout_val: float = 30.0       # Get timeout (seconds)
    
    @property
    def put_timeout(self) -> float:
        return self._put_timeout_val
    
    @put_timeout.setter
    def put_timeout(self, value: float):
        self._put_timeout_val = max(0.1, value)
    
    @property
    def get_timeout(self) -> float:
        return self._get_timeout_val
    
    @get_timeout.setter
    def get_timeout(self, value: float):
        self._get_timeout_val = max(0.1, value)


# UUID import at module level
import uuid