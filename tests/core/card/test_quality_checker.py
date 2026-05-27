"""E6 — ImportQualityChecker unit tests"""

from core.card.card_types import Card, Token, Conflict, ConflictType, IntentFlag
from core.card.quality.import_quality_checker import ImportQualityChecker, QualityScore


class TestQualityScore:

    def test_perfect_score_passes(self):
        score = QualityScore(1.0, 1.0, 1.0)
        assert score.passed
        assert score.total == 1.0

    def test_low_score_fails(self):
        score = QualityScore(0.0, 0.0, 0.0)
        assert not score.passed

    def test_borderline_pass(self):
        score = QualityScore(0.8, 0.8, 0.6)
        total = 0.3 * 0.8 + 0.4 * 0.8 + 0.3 * 0.6
        assert abs(score.total - total) < 0.001

    def test_weights_match_plan(self):
        score = QualityScore(0.5, 0.5, 0.5)
        assert score.total == 0.5


class TestImportQualityChecker:

    def test_perfect_card(self):
        checker = ImportQualityChecker()
        card = Card(
            card_id="CC-01", name="Test", world_line="W01",
            core_trait="勇敢",
            tokens=[Token(category="trait", name="勇氣", strength=0.9)],
        )
        score = checker.check("Test 勇敢 勇氣", card)
        assert score.passed

    def test_empty_card_low_score(self):
        checker = ImportQualityChecker()
        card = Card()
        score = checker.check("original text", card)
        assert not score.passed

    def test_conflict_score_perfect_when_no_conflicts(self):
        checker = ImportQualityChecker()
        card = Card(card_id="CC-01", name="Test")
        score = checker.check("Test", card)
        assert score.conflict == 1.0

    def test_conflict_score_partial(self):
        checker = ImportQualityChecker()
        card = Card(card_id="CC-01", name="Test")
        card.conflicts.append(Conflict(type=ConflictType.HARD_ERROR, resolution="fixed"))
        card.conflicts.append(Conflict(type=ConflictType.HARD_ERROR))
        score = checker.check("Test", card)
        assert score.conflict == 0.5

    def test_conflict_score_with_kept(self):
        checker = ImportQualityChecker()
        card = Card(card_id="CC-01", name="Test")
        card.conflicts.append(Conflict(
            type=ConflictType.INTENTIONAL, suppressed=True,
            user_intent=IntentFlag.CONFIRMED_KEEP,
        ))
        card.conflicts.append(Conflict(type=ConflictType.HARD_ERROR, resolution="fixed"))
        score = checker.check("Test", card)
        assert score.conflict == 1.0

    def test_semantic_score_entity_retention(self):
        checker = ImportQualityChecker()
        card = Card(card_id="CC-01", name="林明", core_trait="務實行動派")
        score = checker.check("林明 是 務實行動派", card)
        assert score.semantic > 0.0

    def test_empty_original_returns_high_if_card_has_data(self):
        checker = ImportQualityChecker()
        card = Card(card_id="CC-01", name="Test")
        score = checker.check("", card)
        assert score.semantic == 1.0

    def test_structural_score_counts_fields(self):
        checker = ImportQualityChecker()
        card = Card(card_id="CC-01", name="Test", world_line="W01", core_trait="X")
        score = checker.check("", card)
        assert score.structural > 0.5
