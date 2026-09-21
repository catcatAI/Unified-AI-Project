# -*- coding: utf-8 -*-
"""
Tests for MSBA SemanticBlock.
"""

import numpy as np
import pytest
from ai.msba.semantic_block import SemanticBlock
from ai.msba.types import HitSource


class TestSemanticBlock:
    def test_creation(self):
        block = SemanticBlock(
            block_id="test",
            block_name="Test Block",
            capacity=5,
        )
        assert block.block_id == "test"
        assert block.capacity == 5
        assert len(block.hit_sources) == 0

    def test_hit_sources_via_constructor(self):
        sources = [
            HitSource("e", "energy"),
            HitSource("c", "comfort"),
        ]
        block = SemanticBlock(
            block_id="test",
            block_name="Test Block",
            hit_sources=sources,
        )
        assert len(block.hit_sources) == 2

    def test_get_hit_activations_basic(self):
        block = SemanticBlock(
            block_id="test",
            block_name="Test",
            hit_sources=[
                HitSource("e", "energy"),
                HitSource("c", "comfort"),
            ],
        )
        act = block.get_hit_activations("energy level")
        assert "e" in act
        assert "c" in act
        assert act["e"] == 1.0  # keyword match
        assert act["c"] == 0.0

    def test_get_hit_activations_with_reference(self):
        block = SemanticBlock(
            block_id="test",
            block_name="Test",
            hit_sources=[
                HitSource("e", "energy"),
            ],
        )
        act = block.get_hit_activations("energy", seed_answer="energy")
        assert "e" in act
        assert act["e"] == 1.0

    def test_get_hit_activations_no_coordinator(self):
        block = SemanticBlock(
            block_id="test",
            block_name="Test",
            hit_sources=[
                HitSource("e", "energy"),
            ],
        )
        act = block.get_hit_activations("hello")
        assert act == {"e": 0.0}

    def test_split(self):
        block = SemanticBlock(
            block_id="parent",
            block_name="Parent",
            capacity=4,
            hit_sources=[
                HitSource("a", "alpha"),
                HitSource("b", "beta"),
                HitSource("c", "gamma"),
                HitSource("d", "delta"),
            ],
        )
        result = block.split(threshold=0.5)
        # Returns list of child blocks
        assert len(result) == 2
        child1, child2 = result
        assert child1.parent_block == "parent"
        assert child2.parent_block == "parent"
        assert child1.block_id == "parent_a"
        assert child2.block_id == "parent_b"

    def test_split_too_few_sources(self):
        block = SemanticBlock(
            block_id="test",
            block_name="Test",
            hit_sources=[HitSource("a", "alpha")],
        )
        result = block.split()
        # Returns list containing self
        assert len(result) == 1
        assert result[0].block_id == "test"

    def test_merge(self):
        block1 = SemanticBlock(
            block_id="b1",
            block_name="B1",
            hit_sources=[HitSource("a", "alpha")],
        )
        block2 = SemanticBlock(
            block_id="b2",
            block_name="B2",
            hit_sources=[HitSource("a", "alpha")],  # Same source
        )
        merged = block1.merge(block2)
        # Same hit_sources => overlap = 1.0, should merge
        assert merged.block_id == "b1_merged"
        assert len(merged.hit_sources) == 2

    def test_merge_low_overlap(self):
        block1 = SemanticBlock(
            block_id="b1",
            block_name="B1",
            hit_sources=[HitSource("a", "alpha")],
        )
        block2 = SemanticBlock(
            block_id="b2",
            block_name="B2",
            hit_sources=[HitSource("b", "beta")],
        )
        merged = block1.merge(block2)
        # Different sources => overlap = 0.0, no merge
        assert merged.block_id == "b1"

    def test_project_input(self):
        block = SemanticBlock(block_id="test", block_name="Test")
        proj = block._project_input("energy level")
        assert isinstance(proj, dict)

    def test_compute_overlap(self):
        block1 = SemanticBlock(
            block_id="b1",
            block_name="B1",
            hit_sources=[
                HitSource("a", "alpha"),
                HitSource("b", "beta"),
            ],
        )
        block2 = SemanticBlock(
            block_id="b2",
            block_name="B2",
            hit_sources=[
                HitSource("a", "alpha"),
                HitSource("c", "gamma"),
            ],
        )
        overlap = block1._compute_overlap(block2)
        # Intersection = {a}, Union = {a,b,c} => 1/3
        assert overlap == pytest.approx(1.0 / 3.0)

    def test_compute_overlap_empty(self):
        block1 = SemanticBlock(block_id="b1", block_name="B1")
        block2 = SemanticBlock(block_id="b2", block_name="B2")
        overlap = block1._compute_overlap(block2)
        assert overlap == 0.0
