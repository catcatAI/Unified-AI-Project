# -*- coding: utf-8 -*-
"""
Tests for MSBA ColdStartManager.
"""

import pytest

from ai.msba.block_coordinator import BlockCoordinator
from ai.msba.cold_start import ColdStartManager
from ai.msba.semantic_block import SemanticBlock


class MockEngine:
    def __init__(self, warmed=False):
        self.W = None
        if warmed:
            import numpy as np

            self.W = np.ones((5, 5)) * 0.1

    def forward(self, projection):
        return {k: v * 0.8 for k, v in projection.items()}


class TestColdStartManager:
    def _make_blocks(self, warmed=False):
        engine = MockEngine(warmed=warmed)
        blocks = {}
        for bid in ["emotional", "cognitive"]:
            block = SemanticBlock(block_id=bid, block_name=bid.title())
            block.coordinator = BlockCoordinator(engine, bid)
            blocks[bid] = block
        return blocks

    def test_is_warmed(self):
        blocks = self._make_blocks(warmed=True)
        mgr = ColdStartManager(blocks)
        assert mgr.is_warmed("emotional")

    def test_is_not_warmed(self):
        blocks = self._make_blocks(warmed=False)
        mgr = ColdStartManager(blocks)
        assert not mgr.is_warmed("emotional")

    def test_is_warmed_nonexistent(self):
        mgr = ColdStartManager({})
        assert not mgr.is_warmed("nonexistent")

    def test_fallback_compute_warmed(self):
        blocks = self._make_blocks(warmed=True)
        mgr = ColdStartManager(blocks)
        result = mgr.fallback_compute("emotional", {"a": 1.0})
        assert "a" in result
        # Should use engine forward
        assert result["a"] == pytest.approx(0.8)

    def test_fallback_compute_not_warmed(self):
        blocks = self._make_blocks(warmed=False)
        mgr = ColdStartManager(blocks)
        result = mgr.fallback_compute("emotional", {"a": 1.0})
        # When not warmed and no fallback, pass-through
        assert result == {"a": 1.0}

    def test_fallback_compute_with_core_network(self):
        class MockCore:
            def forward(self, x):
                return {k: v * 0.5 for k, v in x.items()}

        blocks = self._make_blocks(warmed=False)
        mgr = ColdStartManager(blocks, core_network=MockCore())
        result = mgr.fallback_compute("emotional", {"a": 1.0})
        assert result["a"] == pytest.approx(0.5)

    def test_get_warmup_status(self):
        blocks = self._make_blocks(warmed=True)
        mgr = ColdStartManager(blocks)
        status = mgr.get_warmup_status()
        assert "emotional" in status
        assert status["emotional"]
