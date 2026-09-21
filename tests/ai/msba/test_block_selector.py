# -*- coding: utf-8 -*-
"""
Tests for MSBA BlockSelector.
"""

import pytest

from ai.msba.block_selector import BlockSelector
from ai.msba.semantic_block import SemanticBlock
from ai.msba.types import SeedResult


class TestBlockSelector:
    def _make_blocks(self):
        blocks = {}
        for bid in ["temporal", "biological", "emotional", "cognitive"]:
            blocks[bid] = SemanticBlock(block_id=bid, block_name=bid.title())
        return blocks

    def test_creation(self):
        blocks = self._make_blocks()
        sel = BlockSelector(blocks)
        assert len(sel.blocks) == 4

    def test_select_basic(self):
        blocks = self._make_blocks()
        sel = BlockSelector(blocks)
        seed = SeedResult(answer="42", confidence=0.8)
        result = sel.select("energy level", seed)
        assert len(result.selected) > 0
        assert result.seed_confidence == 0.8

    def test_select_lightweight(self):
        blocks = self._make_blocks()
        sel = BlockSelector(blocks)
        seed = SeedResult(answer="hello", confidence=0.9)
        result = sel.select("energy", seed, lightweight=True)
        assert len(result.selected) <= 3

    def test_select_empty_blocks(self):
        sel = BlockSelector({})
        result = sel.select("test", SeedResult())
        assert result.selected == []

    def test_select_by_confidence(self):
        blocks = self._make_blocks()
        sel = BlockSelector(blocks)
        # Low confidence seed -> more blocks
        result = sel.select("complex question", SeedResult())
        assert len(result.selected) >= 4

    def test_record_verdict(self):
        blocks = self._make_blocks()
        sel = BlockSelector(blocks)
        sel.record_verdict("temporal", "confirm")
        assert sel.block_history["temporal"].confirm_count == 1

    def test_record_verdict_creates_history(self):
        blocks = self._make_blocks()
        sel = BlockSelector(blocks)
        sel.record_verdict("temporal", "question")
        assert "temporal" in sel.block_history
        assert sel.block_history["temporal"].question_count == 1

    def test_compute_block_score(self):
        blocks = self._make_blocks()
        sel = BlockSelector(blocks)
        seed = SeedResult()
        score = sel._compute_block_score(
            "emotional",
            blocks["emotional"],
            "energy level",
            [0.1] * 64,
            seed,
        )
        assert 0.0 <= score <= 1.0

    def test_cosine_similarity(self):
        sel = BlockSelector({})
        a = [1.0, 0.0, 0.0]
        b = [1.0, 0.0, 0.0]
        assert sel._cosine_similarity(a, b) == pytest.approx(1.0)

    def test_cosine_similarity_none(self):
        sel = BlockSelector({})
        assert sel._cosine_similarity(None, [1.0]) == 0.0
        assert sel._cosine_similarity([1.0], None) == 0.0
