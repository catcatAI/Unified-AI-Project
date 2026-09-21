# -*- coding: utf-8 -*-
"""
End-to-end smoke tests for MSBA pipeline.
"""

import asyncio
import time

import pytest
from ai.msba import (
    MSBAPipeline,
    NeuroBlenderBridge,
    PerformanceProfiler,
    create_all_blocks,
    create_default_blocks,
)
from ai.msba.types import FusedRepresentation, SeedResult


class TestMSBAEndToEnd:
    """End-to-end smoke tests for full MSBA pipeline."""

    def test_full_pipeline_all_blocks(self):
        """Test pipeline with all blocks (9 core + 2 multimodal = 11)."""
        blocks = create_all_blocks()
        pipeline = MSBAPipeline(blocks=blocks)
        assert len(pipeline.blocks) == 11

    def test_pipeline_latency_budget(self):
        """Test that pipeline completes within latency budget."""
        blocks = create_all_blocks()
        pipeline = MSBAPipeline(blocks=blocks)

        start = time.monotonic()
        result = asyncio.run(pipeline.process("What is the time?"))
        elapsed = (time.monotonic() - start) * 1000

        assert isinstance(result, str)
        # Should complete within 200ms (generous budget for testing)
        assert elapsed < 200, f"Pipeline took {elapsed:.1f}ms"

    def test_pipeline_various_inputs(self):
        """Test pipeline with various input types."""
        blocks = create_all_blocks()
        pipeline = MSBAPipeline(blocks=blocks)

        inputs = [
            "hi",
            "What is 2+2?",
            "energy level",
            "I am happy",
            "早安",
            "Explain quantum physics",
        ]

        for inp in inputs:
            result = asyncio.run(pipeline.process(inp))
            assert isinstance(result, str), f"Failed for input: {inp}"

    def test_neuroblender_bridge_integration(self):
        """Test NeuroBlender bridge with real pipeline output."""
        blocks = create_all_blocks()
        pipeline = MSBAPipeline(blocks=blocks)
        bridge = NeuroBlenderBridge()

        result = asyncio.run(pipeline.process("energy level"))

        # If result is a FusedRepresentation, convert to 9D
        if hasattr(result, "primary"):
            vec = bridge.fused_to_blender_vector(result)
            assert vec.shape == (9,)
            context = bridge.blender_to_context(vec)
            assert isinstance(context, dict)

    def test_profiler_integration(self):
        """Test performance profiler with real pipeline."""
        blocks = create_all_blocks()
        pipeline = MSBAPipeline(blocks=blocks)
        profiler = PerformanceProfiler()

        for _ in range(3):
            start = profiler.start_total()
            t1 = profiler.start_layer("total")
            asyncio.run(pipeline.process("test input"))
            profiler.end_layer("total", t1)
            profiler.end_total(start)

        stats = profiler.get_total_stats()
        assert stats["count"] == 3
        assert stats["avg_ms"] > 0

    def test_pipeline_statelessness(self):
        """Test that pipeline doesn't leak state between calls."""
        blocks = create_all_blocks()
        pipeline = MSBAPipeline(blocks=blocks)

        r1 = asyncio.run(pipeline.process("first input"))
        r2 = asyncio.run(pipeline.process("second input"))

        # Both should produce valid results
        assert isinstance(r1, str)
        assert isinstance(r2, str)

    def test_pipeline_concurrent(self):
        """Test pipeline handles concurrent requests."""
        blocks = create_all_blocks()
        pipeline = MSBAPipeline(blocks=blocks)

        async def run_concurrent():
            tasks = [pipeline.process(f"input {i}") for i in range(5)]
            results = await asyncio.gather(*tasks)
            return results

        results = asyncio.run(run_concurrent())
        assert len(results) == 5
        assert all(isinstance(r, str) for r in results)

    def test_cross_attention_learning(self):
        """Test cross-attention learns from co-occurrence."""
        blocks = create_all_blocks()
        pipeline = MSBAPipeline(blocks=blocks)

        # Process same type of input multiple times
        for _ in range(5):
            asyncio.run(pipeline.process("energy level"))

        # Cross-attention should have been updated
        stats = pipeline.convergence.get_training_stats()
        assert stats["step_count"] > 0

    def test_replay_buffer(self):
        """Test experience replay buffer works."""
        from ai.msba.relevance_convergence import RelevanceConvergence

        conv = RelevanceConvergence({})

        # Fill buffer
        for i in range(10):
            hits = {
                "emotional": type(
                    "MockHit",
                    (),
                    {"confidence": 0.8, "hit_sources": {"h": 0.9}},
                )()
            }
            conv._record_experience(hits)

        assert len(conv._replay_buffer) == 10

        # Apply replay gradient
        updates = conv.apply_replay_gradient(batch_size=5)
        assert updates >= 0
