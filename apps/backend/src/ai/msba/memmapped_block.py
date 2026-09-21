# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
MemMappedBlock — memory-mapped semantic block for 1TB/1GB storage.

Each block stores its weights on disk (numpy memmap),
with only active chunks loaded into memory via LRU cache.
"""

import logging
import os
from collections import OrderedDict
from typing import Any, Dict, List, Optional

import numpy as np

from .types import HitSource

logger = logging.getLogger(__name__)

# Default chunk size: 128MB
DEFAULT_CHUNK_SIZE = 128 * 1024 * 1024

# Default max memory: 1GB
DEFAULT_MAX_MEMORY = 1024 * 1024 * 1024


class MemMappedBlock:
    """
    Memory-mapped semantic block.

    Stores weights on disk via numpy memmap,
    loads only active chunks into memory via LRU cache.
    """

    def __init__(
        self,
        block_id: str,
        block_name: str,
        data_path: str,
        hit_sources: Optional[List[HitSource]] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        max_memory: int = DEFAULT_MAX_MEMORY,
    ):
        """
        Args:
            block_id: Unique block identifier.
            block_name: Human-readable name.
            data_path: Path to .mmap file on disk.
            hit_sources: List of hit sources for this block.
            chunk_size: Size of each chunk in bytes.
            max_memory: Maximum memory for LRU cache in bytes.
        """
        self.block_id = block_id
        self.block_name = block_name
        self.data_path = data_path
        self.hit_sources = hit_sources or []
        self.chunk_size = chunk_size
        self.max_memory = max_memory

        # LRU cache: chunk_idx -> numpy array
        self._lru_cache: OrderedDict[int, np.ndarray] = OrderedDict()
        self._current_memory = 0

        # Memory-mapped file (lazy loaded); ndarray fallback when data file missing
        self._mmap: Optional[np.ndarray] = None
        self._total_chunks = 0

    def _ensure_mmap(self) -> None:
        """Lazy-load memory-mapped file."""
        if self._mmap is not None:
            return

        if not os.path.exists(self.data_path):
            logger.warning(
                "MemMappedBlock[%s]: data file not found: %s",
                self.block_id,
                self.data_path,
            )
            # Create empty mmap for testing
            self._mmap = np.zeros((1024,), dtype=np.float32)
            self._total_chunks = 1
            return

        try:
            self._mmap = np.memmap(
                self.data_path,
                dtype="float32",
                mode="r",
            )
            self._total_chunks = max(
                1,
                len(self._mmap) // self.chunk_size + 1,
            )
            logger.info(
                "MemMappedBlock[%s]: loaded %s (%d chunks)",
                self.block_id,
                self.data_path,
                self._total_chunks,
            )
        except Exception as e:
            logger.error(
                "MemMappedBlock[%s]: failed to load %s: %s",
                self.block_id,
                self.data_path,
                e,
            )
            self._mmap = np.zeros((1024,), dtype=np.float32)
            self._total_chunks = 1

    def get_hit_activations(
        self,
        input_text: str,
        seed_answer: str = "",
    ) -> Dict[str, float]:
        """
        Compute hit source activations for this block.

        Uses keyword matching for basic activation,
        with optional memmap lookup for deeper processing.
        """
        # Keyword-based activation (Phase 1)
        result: Dict[str, float] = {}
        text_lower = input_text.lower()

        # If no hit sources, return empty
        if not self.hit_sources:
            return result

        for hs in self.hit_sources:
            if hs.source_name.lower() in text_lower:
                result[hs.source_id] = 1.0
            else:
                result[hs.source_id] = 0.0

        # If we have memmap data, enhance with chunk lookup
        if self._mmap is not None and result:
            chunk_idx = self._compute_chunk_idx(input_text)
            chunk_data = self._load_chunk(chunk_idx)
            if chunk_data is not None:
                # Use chunk data to modulate activations
                for hs in self.hit_sources:
                    if hs.source_id in result:
                        # Simple modulation: boost if chunk has signal
                        modulation = float(np.mean(np.abs(chunk_data)))
                        result[hs.source_id] *= 1.0 + modulation * 0.1

        return result

    def _compute_chunk_idx(self, input_text: str) -> int:
        """Compute which chunk to load based on input text."""
        # Simple hash-based chunk selection
        text_hash = hash(input_text) & 0xFFFFFFFF
        return text_hash % max(1, self._total_chunks)

    def _load_chunk(self, chunk_idx: int) -> Optional[np.ndarray]:
        """
        Load a chunk from disk into LRU cache.

        Evicts oldest chunks if memory limit exceeded.
        """
        self._ensure_mmap()
        mmap = self._mmap
        if mmap is None:
            return None

        # Check cache first
        if chunk_idx in self._lru_cache:
            # Move to end (most recently used)
            self._lru_cache.move_to_end(chunk_idx)
            return self._lru_cache[chunk_idx]

        # Evict if needed
        self._evict_if_needed()

        # Load from disk
        start = chunk_idx * self.chunk_size
        end = min(start + self.chunk_size, len(mmap))

        if start >= len(mmap):
            return None

        chunk = np.asarray(mmap[start:end], dtype=np.float32).copy()
        chunk_bytes = chunk.nbytes

        # Check if we can fit this chunk
        while self._current_memory + chunk_bytes > self.max_memory and self._lru_cache:
            self._evict_one()

        # Add to cache
        self._lru_cache[chunk_idx] = chunk
        self._current_memory += chunk_bytes

        return chunk

    def _evict_if_needed(self) -> None:
        """Evict oldest chunks until we have room."""
        while self._current_memory > self.max_memory * 0.9 and self._lru_cache:
            self._evict_one()

    def _evict_one(self) -> None:
        """Evict the least recently used chunk."""
        if not self._lru_cache:
            return

        # Pop oldest item (first in OrderedDict)
        idx, chunk = self._lru_cache.popitem(last=False)
        self._current_memory -= chunk.nbytes
        logger.debug(
            "MemMappedBlock[%s]: evicted chunk %d (%d bytes)",
            self.block_id,
            idx,
            chunk.nbytes,
        )

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "block_id": self.block_id,
            "cached_chunks": len(self._lru_cache),
            "total_chunks": self._total_chunks,
            "current_memory_bytes": self._current_memory,
            "max_memory_bytes": self.max_memory,
            "memory_usage_pct": (
                self._current_memory / self.max_memory * 100 if self.max_memory > 0 else 0
            ),
        }

    def clear_cache(self) -> None:
        """Clear the LRU cache."""
        self._lru_cache.clear()
        self._current_memory = 0
