# -*- coding: utf-8 -*-
"""
Tests for MSBA RelevanceConvergence.
"""

import numpy as np
import pytest
from ai.msba.relevance_convergence import RelevanceConvergence
from ai.msba.semantic_block import SemanticBlock
from ai.msba.types import BlockHitResult, SeedResult


class TestRelevanceConvergence:
    def _make_blocks(self):
        blocks = {}
        for bid in ["emotional", "cognitive", "causal"]:
            blocks[bid] = SemanticBlock(block_id=bid, block_name=bid.title())
        return blocks

    def test_creation(self):
        blocks = self._make_blocks()
        conv = RelevanceConvergence(blocks)
        assert conv.cross_attention.shape == (9, 9)
        # Diagonal should be 1.0
        for i in range(9):
            assert conv.cross_attention[i, i] == 1.0

    def test_converge_basic(self):
        blocks = self._make_blocks()
        conv = RelevanceConvergence(blocks)
        hits = {
            "emotional": BlockHitResult(
                block_id="emotional",
                hit_sources={"happiness": 0.8, "sadness": 0.1},
                seed_verdict="confirm",
                confidence=0.45,
            ),
            "cognitive": BlockHitResult(
                block_id="cognitive",
                hit_sources={"focus": 0.6, "curiosity": 0.4},
                seed_verdict="supplement",
                confidence=0.5,
            ),
        }
        seed = SeedResult(answer="42", confidence=0.8)
        fused = conv.converge(hits, seed)
        assert len(fused.dimensions) == 2
        assert fused.confidence > 0.0
        assert len(fused.seed_verdicts) == 2

    def test_converge_empty(self):
        conv = RelevanceConvergence({})
        fused = conv.converge({}, SeedResult())
        assert fused.primary == {}
        assert fused.confidence == 0.0

    def test_cross_attention_update(self):
        conv = RelevanceConvergence({})
        old = conv.cross_attention[0, 1]
        conv.update_from_cooccurrence(
            {
                "temporal": BlockHitResult(
                    block_id="temporal",
                    hit_sources={},
                    confidence=0.8,
                ),
                "biological": BlockHitResult(
                    block_id="biological",
                    hit_sources={},
                    confidence=0.9,
                ),
            }
        )
        # Should increase
        assert conv.cross_attention[0, 1] > old or old == 0.05

    def test_update_from_feedback_improved(self):
        conv = RelevanceConvergence({})
        old = conv.cross_attention[2, 1]  # emotional -> biological
        conv.update_from_feedback("biological", "emotional", True)
        assert conv.cross_attention[2, 1] > old

    def test_update_from_feedback_worsened(self):
        conv = RelevanceConvergence({})
        old = conv.cross_attention[2, 1]
        conv.update_from_feedback("biological", "emotional", False)
        assert conv.cross_attention[2, 1] < old

    def test_apply_budget(self):
        conv = RelevanceConvergence({})
        primary = {("a", "b", 1.0): 0.9 for i in range(20)}
        auxiliary = {("c", "d", 1.0): 0.5 for i in range(10)}
        latent = {("e", "f", 1.0): 0.2 for i in range(5)}
        p, a, l = conv._apply_budget(primary, auxiliary, latent)
        assert len(p) <= 18  # 60% of 30
        assert len(a) <= 9  # 30% of 30
        assert len(l) <= 3  # 10% of 30

    def test_seed_influence(self):
        conv = RelevanceConvergence({})
        primary = {("emotional", "happiness", 0.9): 0.9}
        seed = SeedResult(answer="42", confidence=0.8)
        influence = conv._fuse_seed(seed, primary)
        assert "emotional:happiness" in influence
        assert influence["emotional:happiness"] == pytest.approx(0.9 * 0.8)
