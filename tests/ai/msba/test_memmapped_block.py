# -*- coding: utf-8 -*-
"""
Tests for MSBA MemMappedBlock.
"""

import os
import tempfile

import numpy as np
import pytest
from ai.msba.memmapped_block import MemMappedBlock
from ai.msba.types import HitSource


class TestMemMappedBlock:
    def test_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.mmap")
            # Create a small mmap file
            data = np.zeros(1024, dtype=np.float32)
            data.tofile(path)

            block = MemMappedBlock(
                block_id="test",
                block_name="Test",
                data_path=path,
                hit_sources=[
                    HitSource("e", "energy"),
                    HitSource("c", "comfort"),
                ],
            )
            assert block.block_id == "test"
            assert len(block.hit_sources) == 2

    def test_get_hit_activations_keyword(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.mmap")
            data = np.zeros(1024, dtype=np.float32)
            data.tofile(path)

            block = MemMappedBlock(
                block_id="test",
                block_name="Test",
                data_path=path,
                hit_sources=[
                    HitSource("e", "energy"),
                    HitSource("c", "comfort"),
                ],
            )
            activations = block.get_hit_activations("energy level")
            assert activations["e"] == 1.0
            assert activations["c"] == 0.0

    def test_lru_eviction(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.mmap")
            # Create larger mmap
            data = np.random.randn(10000).astype(np.float32)
            data.tofile(path)

            block = MemMappedBlock(
                block_id="test",
                block_name="Test",
                data_path=path,
                max_memory=1024,  # 1KB limit
                chunk_size=256,
            )

            # Load multiple chunks
            block._load_chunk(0)
            block._load_chunk(1)
            block._load_chunk(2)

            stats = block.get_cache_stats()
            assert stats["cached_chunks"] <= 4  # LRU limit

    def test_cache_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.mmap")
            data = np.zeros(1024, dtype=np.float32)
            data.tofile(path)

            block = MemMappedBlock(
                block_id="test",
                block_name="Test",
                data_path=path,
            )
            stats = block.get_cache_stats()
            assert stats["block_id"] == "test"
            assert stats["cached_chunks"] == 0

    def test_clear_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.mmap")
            data = np.zeros(1024, dtype=np.float32)
            data.tofile(path)

            block = MemMappedBlock(
                block_id="test",
                block_name="Test",
                data_path=path,
            )
            block._load_chunk(0)
            block.clear_cache()
            stats = block.get_cache_stats()
            assert stats["cached_chunks"] == 0

    def test_missing_file(self):
        block = MemMappedBlock(
            block_id="test",
            block_name="Test",
            data_path="/nonexistent/path.mmap",
            hit_sources=[
                HitSource("e", "energy"),
                HitSource("c", "comfort"),
            ],
        )
        # Should not crash
        activations = block.get_hit_activations("energy")
        assert "e" in activations
        assert activations["e"] == 1.0
