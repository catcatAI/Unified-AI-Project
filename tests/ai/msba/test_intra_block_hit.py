# -*- coding: utf-8 -*-
"""
Tests for MSBA IntraBlockHitEngine.
"""

import asyncio

import pytest
from ai.msba.intra_block_hit import IntraBlockHitEngine
from ai.msba.semantic_block import SemanticBlock
from ai.msba.types import SeedResult


class TestIntraBlockHitEngine:
    def _make_blocks(self):
        blocks = {}
        for bid in ["emotional", "cognitive", "temporal"]:
            blocks[bid] = SemanticBlock(block_id=bid, block_name=bid.title())
        return blocks

    def test_creation(self):
        blocks = self._make_blocks()
        engine = IntraBlockHitEngine(blocks)
        assert len(engine.blocks) == 3

    def test_hit_all_basic(self):
        blocks = self._make_blocks()
        engine = IntraBlockHitEngine(blocks)
        seed = SeedResult(answer="42", confidence=0.8)
        result = asyncio.run(engine.hit_all("energy level", seed, ["emotional", "cognitive"]))
        assert "emotional" in result
        assert "cognitive" in result
        assert result["emotional"].block_id == "emotional"
        assert result["emotional"].confidence >= 0.0

    def test_hit_all_partial(self):
        blocks = self._make_blocks()
        engine = IntraBlockHitEngine(blocks)
        seed = SeedResult(answer="42", confidence=0.8)
        result = asyncio.run(
            engine.hit_all(
                "test",
                seed,
                ["emotional", "nonexistent"],
            )
        )
        assert "emotional" in result
        assert "nonexistent" not in result

    def test_hit_all_empty(self):
        engine = IntraBlockHitEngine({})
        result = asyncio.run(engine.hit_all("test", SeedResult(), []))
        assert result == {}

    def test_seed_verification_confirm(self):
        engine = IntraBlockHitEngine({})
        # Very high overlap => confirm (avg product > 0.7)
        input_hits = {"a": 0.9, "b": 0.9}
        seed_hits = {"a": 0.9, "b": 0.9}
        verdict = engine._verify_seed(input_hits, seed_hits)
        # avg = (0.81 + 0.81) / 2 = 0.81 > 0.7
        assert verdict == "confirm"

    def test_seed_verification_question(self):
        engine = IntraBlockHitEngine({})
        # Low overlap => question (avg product < 0.3)
        input_hits = {"a": 0.1, "b": 0.1}
        seed_hits = {"a": 0.9, "b": 0.8}
        verdict = engine._verify_seed(input_hits, seed_hits)
        # avg = (0.09 + 0.08) / 2 = 0.085 < 0.3
        assert verdict == "question"

    def test_seed_verification_supplement(self):
        engine = IntraBlockHitEngine({})
        # Medium overlap => supplement (0.3 <= avg <= 0.7)
        input_hits = {"a": 0.6, "b": 0.4}
        seed_hits = {"a": 0.7, "b": 0.5}
        verdict = engine._verify_seed(input_hits, seed_hits)
        # avg = (0.42 + 0.20) / 2 = 0.31 in [0.3, 0.7]
        assert verdict == "supplement"

    def test_seed_verification_neutral(self):
        engine = IntraBlockHitEngine({})
        verdict = engine._verify_seed({}, {})
        assert verdict == "neutral"

    def test_seed_verification_neutral_no_seed(self):
        engine = IntraBlockHitEngine({})
        verdict = engine._verify_seed({"a": 0.5}, {})
        assert verdict == "neutral"

    def test_get_partial_results(self):
        blocks = self._make_blocks()
        engine = IntraBlockHitEngine(blocks)
        seed = SeedResult(answer="42", confidence=0.8)
        asyncio.run(engine.hit_all("test", seed, ["emotional"]))
        partial = engine.get_partial_results()
        assert "emotional" in partial
