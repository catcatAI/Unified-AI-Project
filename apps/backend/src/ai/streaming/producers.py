# =============================================================================
# ANGELA-MATRIX: L6 [η] [A] L2+
# =============================================================================
"""Stream Producers

Multi-level token producers for hierarchical document streaming.
Section→Paragraph→Sentence→Token, each with fast+slow pass.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ai.garden.garden_engine import GARDENEngine
    from ai.ed3n.ed3n_engine import ED3NEngine


@dataclass
class ProducerConfig:
    """Base producer configuration."""
    enabled: bool = True
    max_tokens: int = 512
    chunk_size: int = 32
    min_chunk_size: int = 8
    timeout: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseLevelProducer(ABC):
    def __init__(self, garden=None, ed3n=None):
        self.garden = garden
        self.ed3n = ed3n

    @abstractmethod
    def fast_pass(self, query: str, buffer: str) -> Optional[str]:
        """Fast: encode→SNN→decode. Returns output text or None."""
        pass

    @abstractmethod
    def slow_pass(self, query: str, buffer: str, fast_output: Optional[str]) -> Optional[str]:
        """Slow: enrich→cycle→refine. Returns refined text or None."""
        pass

    def _garden_encode_snn(self, text: str) -> Optional[str]:
        if self.garden is None:
            return None
        keys = self.garden.dictionary.encode(text)
        if not keys:
            return None
        network_out = self.garden.snn.forward(keys)
        from ai.garden.garden_engine import _anchored_decode
        return _anchored_decode(network_out, keys, self.garden.dictionary, original_text=text)

    def _ed3n_process(self, text: str, depth: str = "shallow") -> Optional[str]:
        if self.ed3n is None:
            return None
        try:
            return self.ed3n.process(text, depth=depth)
        except Exception:
            logger.debug("ED3N process failed", exc_info=True)
            return None


class SectionProducer(BaseLevelProducer):
    """Section-level: broad topic association."""

    def fast_pass(self, query: str, buffer: str) -> Optional[str]:
        if self.garden is None:
            return None
        keys = self.garden.dictionary.encode(query)
        if not keys:
            return None
        network_out = self.garden.snn.forward(keys)
        from ai.garden.garden_engine import _anchored_decode
        return _anchored_decode(network_out, keys, self.garden.dictionary, original_text=query)

    def slow_pass(self, query: str, buffer: str, fast_output: Optional[str]) -> Optional[str]:
        if self.garden is None:
            return None
        enriched = self._garden_encode_snn(query)
        if enriched and enriched != fast_output:
            return enriched
        return None


class ParagraphProducer(BaseLevelProducer):
    """Paragraph-level: finer context within sections."""

    def fast_pass(self, query: str, buffer: str) -> Optional[str]:
        result = self._garden_encode_snn(query)
        return result

    def slow_pass(self, query: str, buffer: str, fast_output: Optional[str]) -> Optional[str]:
        enriched = self._garden_encode_snn(query)
        if enriched and enriched != fast_output:
            return enriched
        return None


class SentenceProducer(BaseLevelProducer):
    """Sentence-level: exact sentence recall via GARDEN + ED3N."""

    def fast_pass(self, query: str, buffer: str) -> Optional[str]:
        garden_out = self._garden_encode_snn(query)
        ed3n_out = self._ed3n_process(query, depth="shallow")
        if garden_out and ed3n_out:
            return ed3n_out if len(ed3n_out) >= len(garden_out) else garden_out
        return garden_out or ed3n_out

    def slow_pass(self, query: str, buffer: str, fast_output: Optional[str]) -> Optional[str]:
        garden_out = self._garden_encode_snn(query)
        ed3n_out = self._ed3n_process(query, depth="deep") if self.ed3n else None
        if garden_out and ed3n_out:
            winner = ed3n_out if len(ed3n_out) >= len(garden_out) else garden_out
            return winner if winner != fast_output else None
        result = garden_out or ed3n_out
        return result if result and result != fast_output else None


class TokenProducer(BaseLevelProducer):
    """Token-level: word association confirmation."""

    def fast_pass(self, query: str, buffer: str) -> Optional[str]:
        return self._garden_encode_snn(query)

    def slow_pass(self, query: str, buffer: str, fast_output: Optional[str]) -> Optional[str]:
        return None  # Token slow adds confidence, no visible text change
