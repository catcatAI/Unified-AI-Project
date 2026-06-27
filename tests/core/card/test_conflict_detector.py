"""E6 — ConflictDetector unit tests"""

from datetime import datetime

from core.card.card_types import Card, SourceFile, Token
from core.card.parser.conflict_detector import ConflictDetector


class TestConflictDetector:

    def test_no_conflicts_for_clean_card(self):
        detector = ConflictDetector()
        card = Card(card_id="CC-01", name="Test")
        conflicts = detector.detect(card)
        assert len(conflicts) == 0

    def test_unsupported_source_format(self):
        detector = ConflictDetector()
        card = Card(
            card_id="CC-01", name="Test",
            source_files=[SourceFile(path="bad.pdf", doc_id="1", last_write_time=datetime.now())],
        )
        conflicts = detector.detect(card)
        assert any(c.dimension == "format" for c in conflicts)

    def test_numerical_out_of_range_high(self):
        detector = ConflictDetector()
        card = Card(
            card_id="CC-01", name="Test",
            tokens=[Token(category="trait", name="Power", strength=999.0)],
        )
        conflicts = detector.detect(card)
        assert any(c.dimension == "numerical" for c in conflicts)

    def test_numerical_negative(self):
        detector = ConflictDetector()
        card = Card(
            card_id="CC-01", name="Test",
            tokens=[Token(category="trait", name="Power", strength=-5.0)],
        )
        conflicts = detector.detect(card)
        assert any(c.dimension == "numerical" for c in conflicts)

    def test_numerical_in_range_ok(self):
        detector = ConflictDetector()
        card = Card(
            card_id="CC-01", name="Test",
            tokens=[Token(category="trait", name="Power", strength=5.0)],
        )
        conflicts = detector.detect(card)
        assert not any(c.dimension == "numerical" for c in conflicts)

    def test_detect_between_different_core_traits(self):
        detector = ConflictDetector()
        a = Card(card_id="CC-01", qualified_id="CC-01@W01", world_line="W01", name="A", core_trait="勇敢")
        b = Card(card_id="CC-01", qualified_id="CC-01@W02", world_line="W02", name="B", core_trait="謹慎")
        cross = detector.detect_between([a, b])
        assert len(cross) > 0

    def test_detect_between_same_trait_no_conflict(self):
        detector = ConflictDetector()
        a = Card(card_id="CC-01", qualified_id="CC-01@W01", world_line="W01", name="A", core_trait="勇敢")
        b = Card(card_id="CC-01", qualified_id="CC-01@W02", world_line="W02", name="B", core_trait="勇敢")
        cross = detector.detect_between([a, b])
        matches = [c for _, _, c in cross if c.dimension == "tone"]
        assert not any("勇敢" in c.description for c in matches)

    def test_empty_card_list_no_cross_conflicts(self):
        detector = ConflictDetector()
        cross = detector.detect_between([])
        assert len(cross) == 0

    def test_gdoc_source_no_conflict(self):
        detector = ConflictDetector()
        card = Card(
            card_id="CC-01", name="Test",
            source_files=[SourceFile(path="card.gdoc", doc_id="1", last_write_time=datetime.now())],
        )
        conflicts = detector.detect(card)
        assert not any(c.dimension == "format" for c in conflicts)

    def test_txt_source_no_conflict(self):
        detector = ConflictDetector()
        card = Card(
            card_id="CC-01", name="Test",
            source_files=[SourceFile(path="card.txt", doc_id="", last_write_time=datetime.now())],
        )
        conflicts = detector.detect(card)
        assert not any(c.dimension == "format" for c in conflicts)

    def test_mixed_format_and_numerical_conflicts(self):
        detector = ConflictDetector()
        card = Card(
            card_id="CC-01", name="Test",
            source_files=[SourceFile(path="bad.xlsx", doc_id="1", last_write_time=datetime.now())],
            tokens=[Token(category="trait", name="X", strength=99.0)],
        )
        conflicts = detector.detect(card)
        dims = {c.dimension for c in conflicts}
        assert "format" in dims
        assert "numerical" in dims
