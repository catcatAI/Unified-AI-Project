# -*- coding: utf-8 -*-
"""
Tests for MSBA BlockFactory.
"""

import pytest
from ai.msba.block_factory import (
    create_default_blocks,
    create_linguistic_block,
)


class TestBlockFactory:
    def test_create_default_blocks(self):
        blocks = create_default_blocks()
        assert len(blocks) == 8
        assert "temporal" in blocks
        assert "biological" in blocks
        assert "emotional" in blocks
        assert "cognitive" in blocks
        assert "social" in blocks
        assert "mathematical" in blocks
        assert "knowledge" in blocks
        assert "causal" in blocks

    def test_blocks_have_ids(self):
        blocks = create_default_blocks()
        for bid, block in blocks.items():
            assert block.block_id == bid
            assert block.block_name != ""

    def test_blocks_have_hit_sources(self):
        blocks = create_default_blocks()
        for bid, block in blocks.items():
            assert len(block.hit_sources) > 0

    def test_create_linguistic_block(self):
        block = create_linguistic_block()
        assert block.block_id == "linguistic"
        assert len(block.hit_sources) == 5
