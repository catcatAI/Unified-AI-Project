# -*- coding: utf-8 -*-
"""
Tests for MSBA Pipeline.
"""

import asyncio

import pytest
from ai.msba.pipeline import MSBAPipeline


class TestMSBAPipeline:
    def test_creation(self):
        pipeline = MSBAPipeline()
        assert len(pipeline.blocks) == 0
        assert pipeline.llm_service is None

    def test_creation_with_blocks(self):
        from ai.msba.block_factory import create_default_blocks

        blocks = create_default_blocks()
        pipeline = MSBAPipeline(blocks=blocks)
        assert len(pipeline.blocks) == 8

    def test_process_basic(self):
        from ai.msba.block_factory import create_default_blocks

        blocks = create_default_blocks()
        pipeline = MSBAPipeline(blocks=blocks)
        result = asyncio.run(pipeline.process("energy level"))
        assert result != ""
        assert isinstance(result, str)

    def test_process_lightweight(self):
        from ai.msba.block_factory import create_default_blocks

        blocks = create_default_blocks()
        pipeline = MSBAPipeline(blocks=blocks)
        # "energy" is short -> lightweight=True via _is_lightweight
        result = asyncio.run(pipeline.process("energy"))
        assert isinstance(result, str)

    def test_is_lightweight(self):
        pipeline = MSBAPipeline()
        assert pipeline._is_lightweight("hi")
        assert pipeline._is_lightweight("早安")
        assert not pipeline._is_lightweight("this is a longer question about something complex")

    def test_compute_max_blocks_lightweight(self):
        pipeline = MSBAPipeline()
        from ai.msba.types import SeedResult

        seed = SeedResult()
        assert pipeline._compute_max_blocks(seed, 100, True) == 2

    def test_compute_max_blocks_high_confidence(self):
        pipeline = MSBAPipeline()
        from ai.msba.types import SeedResult

        seed = SeedResult(answer="42", confidence=0.99)
        assert pipeline._compute_max_blocks(seed, 50, False) == 3

    def test_deterministic_seed_math(self):
        pipeline = MSBAPipeline()
        seed = pipeline._deterministic_seed("1+1", None)
        # Should try math evaluation
        assert seed is not None

    def test_deterministic_seed_none(self):
        pipeline = MSBAPipeline()
        seed = pipeline._deterministic_seed("hello world", None)
        assert not seed.has_seed

    def test_post_process(self):
        from ai.msba.block_factory import create_default_blocks
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
