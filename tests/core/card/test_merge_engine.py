"""E6 — MergeEngine unit tests"""

from datetime import datetime

from core.card.card_types import Card, Token, SourceFile
try:
    from core.card.parser.merge_engine import MergeEngine
except ImportError:
    import pytest; pytest.skip("MergeEngine is a stub", allow_module_level=True)


class TestMergeEngine:

    def test_merge_new_card(self):
        engine = MergeEngine()
        card = Card(
            card_id="CC-01", world_line="W01",
            qualified_id="CC-01@W01", name="Test",
        )
        result = engine.merge(None, card)
        assert result.qualified_id == "CC-01@W01"

    def test_merge_name_newer_wins(self):
        engine = MergeEngine()
        old = Card(
            card_id="CC-01", qualified_id="CC-01@W01", name="Old",
            source_files=[
                SourceFile(path="a.gdoc", doc_id="1",
                           last_write_time=datetime(2020, 1, 1))
            ],
        )
        new = Card(
            card_id="CC-01", qualified_id="CC-01@W01", name="New",
            source_files=[
                SourceFile(path="b.gdoc", doc_id="2",
                           last_write_time=datetime(2025, 1, 1))
            ],
        )
        result = engine.merge(old, new)
        assert result.name == "New"

    def test_merge_combines_tokens(self):
        engine = MergeEngine()
        a = Card(
            card_id="CC-01", qualified_id="CC-01@W01", name="A",
            tokens=[Token(category="trait", name="勇氣", strength=0.8)],
        )
        b = Card(
            card_id="CC-01", qualified_id="CC-01@W01", name="B",
            tokens=[Token(category="trait", name="智慧", strength=0.7)],
        )
        result = engine.merge(a, b)
        assert len(result.tokens) == 2

    def test_merge_deduplicates_tokens(self):
        engine = MergeEngine()
        a = Card(
            card_id="CC-01", qualified_id="CC-01@W01", name="A",
            tokens=[Token(category="trait", name="勇氣", strength=0.8)],
        )
        b = Card(
            card_id="CC-01", qualified_id="CC-01@W01", name="B",
            tokens=[Token(category="trait", name="勇氣", strength=0.9)],
        )
        result = engine.merge(a, b)
        assert len(result.tokens) == 1

    def test_merge_combines_source_files(self):
        engine = MergeEngine()
        a = Card(
            card_id="CC-01", qualified_id="CC-01@W01", name="A",
            source_files=[
                SourceFile(path="a.gdoc", doc_id="1",
                           last_write_time=datetime(2020, 1, 1))
            ],
        )
        b = Card(
            card_id="CC-01", qualified_id="CC-01@W01", name="B",
            source_files=[
                SourceFile(path="b.gdoc", doc_id="2",
                           last_write_time=datetime(2021, 1, 1))
            ],
        )
        result = engine.merge(a, b)
        assert len(result.source_files) == 2

    def test_merge_deduplicates_source_files(self):
        engine = MergeEngine()
        sf = SourceFile(path="a.gdoc", doc_id="1",
                        last_write_time=datetime(2020, 1, 1))
        a = Card(
            card_id="CC-01", qualified_id="CC-01@W01",
            name="A", source_files=[sf],
        )
        b = Card(
            card_id="CC-01", qualified_id="CC-01@W01",
            name="B", source_files=[sf],
        )
        result = engine.merge(a, b)
        assert len(result.source_files) == 1

    def test_merge_meta_data_merged(self):
        engine = MergeEngine()
        a = Card(
            card_id="CC-01", qualified_id="CC-01@W01",
            name="A", meta_data={"color": "red"},
        )
        b = Card(
            card_id="CC-01", qualified_id="CC-01@W01",
            name="B", meta_data={"size": "big"},
        )
        result = engine.merge(a, b)
        assert result.meta_data == {"color": "red", "size": "big"}

    def test_merge_alternate_selves(self):
        engine = MergeEngine()
        a = Card(
            card_id="CC-01", qualified_id="CC-01@W01",
            name="A", alternate_selves=["CC-01@W02"],
        )
        b = Card(
            card_id="CC-01", qualified_id="CC-01@W01",
            name="B", alternate_selves=["CC-01@W03"],
        )
        result = engine.merge(a, b)
        assert "CC-01@W02" in result.alternate_selves
        assert "CC-01@W03" in result.alternate_selves

    def test_merge_qualified_id_mismatch_uses_incoming(self):
        engine = MergeEngine()
        a = Card(card_id="CC-01", qualified_id="CC-01@W01", name="A")
        b = Card(card_id="CC-02", qualified_id="CC-02@W02", name="B")
        result = engine.merge(a, b)
        assert result.qualified_id == "CC-02@W02"

    def test_empty_incoming_keeps_existing(self):
        engine = MergeEngine()
        existing = Card(
            card_id="CC-01", qualified_id="CC-01@W01",
            name="Existing",
        )
        incoming = Card(card_id="CC-01", qualified_id="CC-01@W01")
        result = engine.merge(existing, incoming)
        assert result.name == "Existing"
