# -*- coding: utf-8 -*-
"""
Tests for MSBA types module.
"""

import time

import pytest
from ai.msba.types import (
    BlockHistory,
    BlockHitResult,
    BlockSelection,
    FusedRepresentation,
    HitSource,
    SeedResult,
)


class TestSeedResult:
    def test_default_seed(self):
        seed = SeedResult()
        assert seed.answer == ""
        assert seed.confidence == 0.0
        assert seed.source == "none"
        assert not seed.has_seed

    def test_has_seed_with_answer(self):
        seed = SeedResult(answer="42", confidence=0.9, source="math")
        assert seed.has_seed

    def test_has_seed_zero_confidence(self):
        seed = SeedResult(answer="42", confidence=0.0)
        assert not seed.has_seed

    def test_has_seed_empty_answer(self):
        seed = SeedResult(answer="", confidence=0.9)
        assert not seed.has_seed

    def test_timestamp_auto(self):
        before = time.time()
        seed = SeedResult()
        after = time.time()
        assert before <= seed.timestamp <= after


class TestHitSource:
    def test_creation(self):
        hs = HitSource(
            source_id="energy",
            source_name="energy_level",
            threshold=0.2,
        )
        assert hs.source_id == "energy"
        assert hs.threshold == 0.2
        assert hs.activation == 0.0
        assert hs.connections == {}


class TestBlockSelection:
    def test_default(self):
        sel = BlockSelection()
        assert sel.scores == {}
        assert sel.selected == []
        assert sel.seed_confidence == 0.0

    def test_with_data(self):
        sel = BlockSelection(
            scores={"a": 0.9, "b": 0.3},
            selected=["a"],
            seed_confidence=0.8,
        )
        assert sel.scores["a"] == 0.9
        assert sel.selected == ["a"]


class TestBlockHitResult:
    def test_default(self):
        r = BlockHitResult()
        assert r.block_id == ""
        assert r.hit_sources == {}
        assert r.seed_verdict == "neutral"
        assert r.confidence == 0.0

    def test_with_data(self):
        r = BlockHitResult(
            block_id="emotional",
            hit_sources={"happiness": 0.8, "sadness": 0.1},
            seed_verdict="confirm",
            confidence=0.45,
        )
        assert r.block_id == "emotional"
        assert r.seed_verdict == "confirm"


class TestFusedRepresentation:
    def test_default(self):
        f = FusedRepresentation()
        assert f.primary == {}
        assert f.auxiliary == {}
        assert f.latent == {}
        assert f.confidence == 0.0

    def test_all_entries(self):
        f = FusedRepresentation(
            primary={("a", "b", 1.0): 0.9},
            auxiliary={("c", "d", 2.0): 0.5},
            latent={("e", "f", 3.0): 0.2},
        )
        all_e = f.all_entries
        assert len(all_e) == 3
        assert ("a", "b", 1.0) in all_e


class TestBlockHistory:
    def test_record(self):
        h = BlockHistory()
        h.record("confirm")
        h.record("question")
        h.record("confirm")
        assert h.total == 3
        assert h.confirm_count == 2
        assert h.question_count == 1

    def test_to_dict(self):
        h = BlockHistory()
        h.record("confirm")
        d = h.to_dict()
        assert d["total"] == 1
        assert d["confirm"] == 1
