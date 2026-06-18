"""
Tests for the ED3N InputEnricher module.

Covers:
  - Empty / edge-case inputs
  - Text variant generation (NFKC, romaji)
  - Key scoring with dictionary
  - Key scoring without dictionary (uniform fallback)
  - Ambiguity computation
  - Coherence computation
  - Combined confidence
  - Integration with DictionaryLayer
"""

from ai.ed3n.dictionary_layer import DictionaryEntry, DictionaryLayer
from ai.ed3n.input_enricher import EnrichedInput, InputEnricher


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_dict() -> DictionaryLayer:
    """Build a minimal DictionaryLayer with preset entries."""
    d = DictionaryLayer()
    d.entries = {
        "g1": DictionaryEntry(
            key="g1",
            surface_forms={"zh": "你好", "en": "hello"},
            confidence=1.0,
        ),
        "g2": DictionaryEntry(
            key="g2",
            surface_forms={"zh": "哈囉", "en": "hi"},
            confidence=0.9,
        ),
        "w1": DictionaryEntry(
            key="w1",
            surface_forms={"zh": "天氣", "en": "weather"},
            confidence=0.8,
        ),
        "w2": DictionaryEntry(
            key="w2",
            surface_forms={"zh": "下雨", "en": "rain"},
            relations={"synonym": ["w1", "w3"]},
            confidence=0.7,
        ),
        "w3": DictionaryEntry(
            key="w3",
            surface_forms={"zh": "晴天", "en": "sunny"},
            confidence=0.6,
        ),
    }
    # Add relations between g1 and g2
    d.entries["g1"].relations = {"synonym": ["g2"]}
    d.entries["g2"].relations = {"synonym": ["g1"]}
    return d


# ---------------------------------------------------------------------------
# EnrichedInput
# ---------------------------------------------------------------------------


class TestEnrichedInput:
    def test_default_construction(self):
        ei = EnrichedInput()
        assert ei.raw_text == ""
        assert ei.confidence == 0.0
        assert ei.ambiguity == 0.0
        assert ei.coherence == 1.0

    def test_custom_construction(self):
        ei = EnrichedInput(
            raw_text="hello",
            normalized_text="hello",
            text_variants=["hello"],
            matched_keys=["g1"],
            key_scores={"g1": 1.0},
            ambiguity=0.0,
            coherence=1.0,
            confidence=0.95,
        )
        assert ei.raw_text == "hello"
        assert ei.key_scores["g1"] == 1.0
        assert ei.confidence == 0.95


# ---------------------------------------------------------------------------
# InputEnricher — text variants
# ---------------------------------------------------------------------------


class TestTextVariants:
    enricher = InputEnricher()

    def test_empty_text(self):
        result = self.enricher.enrich("", [], None)
        assert result.normalized_text == ""
        assert result.text_variants == []

    def test_ascii_no_change(self):
        result = self.enricher.enrich("hello", ["g1"], None)
        assert result.normalized_text == "hello"
        assert "hello" in result.text_variants

    def test_fullwidth_normalization(self):
        result = self.enricher.enrich("ｎｉｈａｏ", [], None)
        assert result.normalized_text == "nihao"

    def test_japanese_romaji_generated(self):
        result = self.enricher.enrich("こんにちは", [], None)
        assert "konnichiha" in result.text_variants
        # NFKC normalization doesn't change hiragana, so normalized == raw
        assert result.normalized_text == "こんにちは"
        # normalized form is always first variant
        assert result.text_variants[0] == "こんにちは"

    def test_variant_deduplication(self):
        result = self.enricher.enrich("hello", [], None)
        assert len(result.text_variants) == 1
        assert result.text_variants == ["hello"]

    def test_variants_includes_normalized_first(self):
        result = self.enricher.enrich("HELLO", [], None)
        assert result.text_variants[0] == "HELLO"  # NFKC doesn't change ASCII


# ---------------------------------------------------------------------------
# InputEnricher — key scoring
# ---------------------------------------------------------------------------


class TestKeyScoring:
    enricher = InputEnricher()

    def test_no_keys(self):
        result = self.enricher.enrich("hello", [], None)
        assert result.key_scores == {}

    def test_no_dictionary_uniform_scores(self):
        result = self.enricher.enrich("hello", ["g1", "g2"], None)
        assert result.key_scores["g1"] == 0.5
        assert result.key_scores["g2"] == 0.5

    def test_with_dictionary_exact_match(self):
        d = _make_dict()
        result = self.enricher.enrich("你好", ["g1"], d)
        # g1 surface "你好" matches exactly
        assert result.key_scores["g1"] > 0.9  # near 1.0 after normalization

    def test_with_dictionary_no_match(self):
        d = _make_dict()
        result = self.enricher.enrich("zzzzz", ["g1"], d)
        # Single key always gets 1.0 after normalization, but confidence is low
        assert result.key_scores["g1"] == 1.0
        assert result.confidence < 0.15  # raw base is 0.1

    def test_multiple_keys_normalization(self):
        d = _make_dict()
        result = self.enricher.enrich("hello", ["g1", "g2"], d)
        assert len(result.key_scores) == 2
        # g1 has surface "hello" exact match, so should score higher than g2
        assert result.key_scores["g1"] > result.key_scores["g2"]

    def test_scores_sum_to_one(self):
        d = _make_dict()
        result = self.enricher.enrich("hello", ["g1", "w1", "w2"], d)
        total = sum(result.key_scores.values())
        assert abs(total - 1.0) < 1e-6


# ---------------------------------------------------------------------------
# InputEnricher — ambiguity
# ---------------------------------------------------------------------------


class TestAmbiguity:
    enricher = InputEnricher()

    def test_single_key_no_ambiguity(self):
        result = self.enricher.enrich("hello", ["g1"], None)
        assert result.ambiguity == 0.0

    def test_no_keys_no_ambiguity(self):
        result = self.enricher.enrich("hello", [], None)
        assert result.ambiguity == 0.0

    def test_equal_scores_high_ambiguity(self):
        result = self.enricher.enrich("hello", ["g1", "g2"], None)
        # Uniform scores → top2_ratio = 1.0, len=2, ambiguity = min(1, 1*2*0.25) = 0.5
        assert result.ambiguity == 0.5

    def test_biased_scores_low_ambiguity(self):
        d = _make_dict()
        result = self.enricher.enrich("hello", ["g1", "w1"], d)
        # g1 matches "hello" well, w1 doesn't → scores are biased
        assert result.ambiguity < 0.5


# ---------------------------------------------------------------------------
# InputEnricher — coherence
# ---------------------------------------------------------------------------


class TestCoherence:
    enricher = InputEnricher()

    def test_single_key_max_coherence(self):
        result = self.enricher.enrich("hello", ["g1"], None)
        assert result.coherence == 1.0

    def test_no_keys_max_coherence(self):
        result = self.enricher.enrich("hello", [], None)
        assert result.coherence == 1.0

    def test_no_dictionary_max_coherence(self):
        result = self.enricher.enrich("hello", ["g1", "g2"], None)
        assert result.coherence == 1.0

    def test_connected_keys_high_coherence(self):
        d = _make_dict()
        # g1 and g2 are connected via synonym relation
        result = self.enricher.enrich("hello", ["g1", "g2"], d)
        # g1→g2 and g2→g1 = 2 connections out of pairs*2 = 2*1 = 2 → 2/2 = 1.0
        assert result.coherence == 1.0

    def test_unconnected_keys_low_coherence(self):
        d = _make_dict()
        # g1 and w2 have no direct relation
        result = self.enricher.enrich("hello", ["g1", "w2"], d)
        # 0 connections / 2 pairs = 0
        assert result.coherence == 0.0

    def test_partially_connected(self):
        d = _make_dict()
        # w2 → w1 (synonym), g1 and g2 (synonym). Mixed group: g1, w1, w2
        # g1-w1: no relation, g1-w2: no, w1-w2: w2→w1 yes (1 connection)
        # pairs = 3*2/2 = 3, max = 6, connections = 1 (w2→w1)
        result = self.enricher.enrich("hello", ["g1", "w1", "w2"], d)
        assert 0 < result.coherence < 1.0


# ---------------------------------------------------------------------------
# InputEnricher — combined confidence
# ---------------------------------------------------------------------------


class TestConfidence:
    enricher = InputEnricher()

    def test_no_keys_zero_confidence(self):
        result = self.enricher.enrich("hello", [], None)
        assert result.confidence == 0.0

    def test_single_exact_match_high_confidence(self):
        d = _make_dict()
        result = self.enricher.enrich("你好", ["g1"], d)
        # g1 confidence=1.0, exact match → key_score ≈ 1.0
        # ambiguity=0 (single key), coherence=1.0
        # confidence ≈ 1.0 * (1 - 0) * 1.0 ≈ 1.0
        assert result.confidence > 0.9

    def test_low_quality_match_low_confidence(self):
        d = _make_dict()
        result = self.enricher.enrich("zzzzz", ["g1"], d)
        # g1 doesn't match → base score 0.1, confidence ≈ 0.1 * 1 * 1 = 0.1
        assert result.confidence < 0.2

    def test_multiple_keys_penalized_by_ambiguity(self):
        d = _make_dict()
        # Equal-match keys get ambiguity penalty
        result = self.enricher.enrich("hello", ["g1", "g2"], d)
        # g1 exact match "hello" → raw 1.0, g2 no match → raw 0.9*0.1=0.09
        # raw_avg = (1.0 + 0.09) / 2 ≈ 0.545
        # ambiguity = (0.09/1.0) * 2 * 0.25 ≈ 0.045
        # confidence = 0.545 * (1 - 0.5*0.045) ≈ 0.533
        raw_avg = (1.0 + 0.09) / 2
        assert result.confidence < raw_avg  # ambiguity penalty applies
