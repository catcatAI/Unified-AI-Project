"""
ANGELA-MATRIX: [L3-L4] [γδ] [B] [L2]
Tests for StreamingPipeline — merge algorithm + producer scaffolding.
"""

from ai.streaming.pipeline import StreamingPipeline
from ai.streaming.producers import (
    SectionProducer, ParagraphProducer, SentenceProducer, TokenProducer,
)


class TestMerge:
    def setup_method(self):
        self.p = StreamingPipeline()

    def test_empty_buffer(self):
        assert self.p._merge("", "new") == "new"

    def test_empty_new(self):
        assert self.p._merge("old", "") == "old"

    def test_no_overlap_append(self):
        assert self.p._merge("hello", "world") == "hello. world"

    def test_new_fully_contained(self):
        assert self.p._merge("paris capital france", "paris") == "paris capital france"

    def test_buffer_fully_contained(self):
        assert self.p._merge("paris", "paris capital france") == "paris capital france"

    def test_partial_overlap(self):
        merged = self.p._merge("paris capital", "capital france")
        assert "france" in merged.lower()
        # Both paris and france should survive
        words = merged.lower().split()
        assert "paris" in words
        assert "france" in words


class TestProducers:
    def test_all_producers_have_methods(self):
        for cls in [SectionProducer, ParagraphProducer, SentenceProducer, TokenProducer]:
            inst = cls()
            assert hasattr(inst, "fast_pass")
            assert hasattr(inst, "slow_pass")

    def test_all_return_none_without_engine(self):
        for cls in [SectionProducer, ParagraphProducer, SentenceProducer, TokenProducer]:
            inst = cls()
            assert inst.fast_pass("test", "") is None
            assert inst.slow_pass("test", "", None) is None

    def test_garden_encode_none_without_garden(self):
        prod = TokenProducer()
        assert prod._garden_encode_snn("test") is None

    def test_ed3n_process_none_without_ed3n(self):
        prod = TokenProducer()
        assert prod._ed3n_process("test") is None


class TestPipeline:
    def test_init_without_engines(self):
        p = StreamingPipeline()
        assert len(p.producers) == 4

    def test_set_fallback(self):
        p = StreamingPipeline()
        p.set_fallback(lambda q: "fallback")
        assert p.fallback_fn is not None
        assert p.fallback_fn("q") == "fallback"
