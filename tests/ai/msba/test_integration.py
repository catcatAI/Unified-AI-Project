# -*- coding: utf-8 -*-
"""
Integration tests for MSBA full pipeline.
"""

import asyncio

import pytest
from ai.msba import (
    BlockHistoryPersistence,
    LinguisticBlock,
    MemMappedBlock,
    MSBAPipeline,
    create_default_blocks,
    create_linguistic_block,
)


class TestMSBAIntegration:
    """End-to-end integration tests for MSBA pipeline."""

    def test_full_pipeline_creation(self):
        """Test full pipeline with all components."""
        blocks = create_default_blocks()
        linguistic = create_linguistic_block()
        blocks["linguistic"] = linguistic

        pipeline = MSBAPipeline(blocks=blocks)
        assert len(pipeline.blocks) == 9

    def test_pipeline_with_all_blocks(self):
        """Test pipeline with linguistic block included."""
        blocks = create_default_blocks()
        blocks["linguistic"] = LinguisticBlock()

        pipeline = MSBAPipeline(blocks=blocks)
        result = asyncio.run(pipeline.process("What is the time?"))
        assert isinstance(result, str)
        assert len(result) > 0

    def test_pipeline_deterministic_seed(self):
        """Test that deterministic seed is generated."""
        blocks = create_default_blocks()
        pipeline = MSBAPipeline(blocks=blocks)

        seed = pipeline._deterministic_seed("1+1", None)
        assert seed is not None
        # Math evaluation should return something
        assert seed.source in ("math", "knowledge", "none")

    def test_pipeline_lightweight_detection(self):
        """Test lightweight input detection."""
        blocks = create_default_blocks()
        pipeline = MSBAPipeline(blocks=blocks)

        assert pipeline._is_lightweight("hi")
        assert pipeline._is_lightweight("早安")
        assert not pipeline._is_lightweight("What is the meaning of life?")

    def test_pipeline_max_blocks_computation(self):
        """Test max blocks computation logic."""
        from ai.msba.types import SeedResult

        blocks = create_default_blocks()
        pipeline = MSBAPipeline(blocks=blocks)

        # Lightweight
        seed = SeedResult()
        assert pipeline._compute_max_blocks(seed, 100, True) == 2

        # High confidence
        seed = SeedResult(answer="42", confidence=0.99)
        assert pipeline._compute_max_blocks(seed, 100, False) == 3

        # Medium confidence
        seed = SeedResult(answer="42", confidence=0.8)
        assert pipeline._compute_max_blocks(seed, 100, False) == 5

        # Low confidence
        seed = SeedResult()
        assert pipeline._compute_max_blocks(seed, 100, False) == 7

    def test_pipeline_post_process(self):
        """Test post-processing without errors."""
        from ai.msba.types import FusedRepresentation, SeedResult

        blocks = create_default_blocks()
        pipeline = MSBAPipeline(blocks=blocks)

        fused = FusedRepresentation(
            primary={("emotional", "happiness", 0.9): 0.9},
            dimensions=["emotional"],
            seed_verdicts={"emotional": "confirm"},
        )

        # Should not raise
        pipeline._post_process("result", fused, SeedResult(), None)

    def test_linguistic_block_integration(self):
        """Test linguistic block in pipeline."""
        blocks = create_default_blocks()
        blocks["linguistic"] = LinguisticBlock()

        pipeline = MSBAPipeline(blocks=blocks)
        result = asyncio.run(pipeline.process("I will go to the store"))
        assert isinstance(result, str)

    def test_block_history_persistence(self):
        """Test block history persistence integration."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            persist = BlockHistoryPersistence(tmpdir)
            blocks = create_default_blocks()
            pipeline = MSBAPipeline(blocks=blocks)

            # Process some inputs
            asyncio.run(pipeline.process("energy level"))

            # Save history
            persist.save(pipeline.block_selector.block_history)

            # Load and verify
            loaded = persist.load()
            assert len(loaded) > 0
