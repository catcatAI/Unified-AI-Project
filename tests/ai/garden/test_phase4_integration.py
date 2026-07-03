# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [C] [L0]
# =============================================================================
"""
Phase 4 Integration Tests — GARDEN Integration (ChromaDB, KG, Multi-step, Emotion, Learning).
"""

import pytest
from ai.garden.dictionary import VectorDictionary, _ChromaEncoder, _TfidfEncoder
from ai.garden.garden_engine import GARDENEngine
from ai.garden.kg_import import KGImporter

# ---------------------------------------------------------------------------
# Phase 4.1: ChromaDB Encoder
# ---------------------------------------------------------------------------

class TestChromaEncoder:
    """Tests for _ChromaEncoder semantic encoding."""

    def test_chroma_encoder_init(self):
        enc = _ChromaEncoder()
        assert enc._collection is not None

    def test_chroma_encoder_encode(self):
        enc = _ChromaEncoder()
        texts = ["hello", "world", "test"]
        result = enc.encode(texts)
        assert result.shape[0] == 3
        assert result.shape[1] > 0

    def test_chroma_encoder_fit_noop(self):
        enc = _ChromaEncoder()
        enc.fit(["test"])  # Should not raise
        # fit() is a no-op for ChromaDB; collection should still work
        result = enc.encode(["after fit"])
        assert result.shape[0] == 1

    def test_chroma_encoder_dedup(self):
        enc = _ChromaEncoder()
        enc.encode(["hello", "hello"])
        # Should only add "hello" once
        assert enc._collection.count() == 1

    def test_chroma_encoder_query_embedding(self):
        enc = _ChromaEncoder()
        enc.encode(["hello world"])
        emb = enc.query_embedding("hello")
        assert emb is not None
        assert len(emb) > 0

    def test_chroma_encoder_empty(self):
        enc = _ChromaEncoder()
        result = enc.encode([])
        assert result.shape[0] == 0


class TestChromaEncoderFallback:
    """Tests for ChromaDB in the fallback chain."""

    def test_fallback_chain_includes_chroma(self):
        d = VectorDictionary(compatibility_mode=False)
        encoder_name = type(d._encoder).__name__
        # Should be Chroma, ST, or TF-IDF (never CharBag as first choice)
        assert any(name in encoder_name for name in ("Chroma", "STEncoder", "Tfidf"))

    def test_compatibility_mode_uses_tfidf(self):
        d = VectorDictionary(compatibility_mode=True)
        assert isinstance(d._encoder, _TfidfEncoder)


# ---------------------------------------------------------------------------
# Phase 4.2: KG Import Integration
# ---------------------------------------------------------------------------

class TestKGImportIntegration:
    """Tests for KGImporter wiring to GARDENEngine."""

    def test_bulk_load_100_entities(self):
        engine = GARDENEngine(compatibility_mode=True)
        engine.load_presets()
        kg = KGImporter()
        kg.generate_synthetic(num_entities=100)
        result = kg.bulk_load(engine)
        assert result["dictionary_entries"] >= 100
        assert result["snn_relations"] > 0

    def test_engine_process_with_kg(self):
        engine = GARDENEngine(compatibility_mode=True)
        engine.load_presets()
        kg = KGImporter()
        kg.generate_synthetic(num_entities=200)
        kg.bulk_load(engine)
        response = engine.process("hello")
        assert isinstance(response, str)
        assert len(response) > 0

    def test_engine_stats_with_kg(self):
        engine = GARDENEngine(compatibility_mode=True)
        engine.load_presets()
        kg = KGImporter()
        kg.generate_synthetic(num_entities=100)
        kg.bulk_load(engine)
        stats = engine.stats()
        assert stats["dictionary"]["entry_count"] >= 100


# ---------------------------------------------------------------------------
# Phase 4.3: Multi-step Reasoning
# ---------------------------------------------------------------------------

class TestMultiStepReasoning:
    """Tests for multi-step query decomposition."""

    def test_single_step_not_multi(self):
        engine = GARDENEngine(compatibility_mode=True)
        engine.load_presets()
        assert engine._is_multi_step("hello") is False

    def test_chinese_multi_step(self):
        engine = GARDENEngine(compatibility_mode=True)
        engine.load_presets()
        assert engine._is_multi_step("搜尋天氣然後整理成報告") is True

    def test_english_multi_step(self):
        engine = GARDENEngine(compatibility_mode=True)
        engine.load_presets()
        assert engine._is_multi_step("search weather and then summarize") is True

    def test_multi_step_process(self):
        engine = GARDENEngine(compatibility_mode=True)
        engine.load_presets()
        result = engine.process("hello and then goodbye")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_multi_step_markers(self):
        engine = GARDENEngine(compatibility_mode=True)
        markers = engine._MULTI_STEP_MARKERS
        assert "然后" in markers
        assert "and then" in markers
        assert "接著" in markers


# ---------------------------------------------------------------------------
# Phase 4.4: Emotion Detection + Hormonal Modulation
# ---------------------------------------------------------------------------

class TestEmotionDetection:
    """Tests for emotion detection and hormonal modulation."""

    def test_detect_happy(self):
        engine = GARDENEngine(compatibility_mode=True)
        assert engine._detect_emotion("我好开心") == "happy"

    def test_detect_sad(self):
        engine = GARDENEngine(compatibility_mode=True)
        assert engine._detect_emotion("我好难过") == "sad"

    def test_detect_angry(self):
        engine = GARDENEngine(compatibility_mode=True)
        assert engine._detect_emotion("我好生气") == "angry"

    def test_detect_anxious(self):
        engine = GARDENEngine(compatibility_mode=True)
        assert engine._detect_emotion("我好担心") == "anxious"

    def test_detect_neutral(self):
        engine = GARDENEngine(compatibility_mode=True)
        assert engine._detect_emotion("今天天气不错") == "neutral"

    def test_hormone_adjustment(self):
        engine = GARDENEngine(compatibility_mode=True)
        # Record initial state
        initial_stats = engine.stats()
        engine._adjust_hormones("happy")
        # Verify engine is still functional after adjustment
        post_stats = engine.stats()
        assert post_stats is not None

    def test_emotion_affects_process(self):
        engine = GARDENEngine(compatibility_mode=True)
        engine.load_presets()
        # Should not crash with emotional input
        result = engine.process("我好开心")
        assert isinstance(result, str)

    def test_emotion_keywords_coverage(self):
        engine = GARDENEngine(compatibility_mode=True)
        assert len(engine._EMOTION_KEYWORDS) >= 4
        assert "happy" in engine._EMOTION_KEYWORDS
        assert "sad" in engine._EMOTION_KEYWORDS

    def test_hormone_adjustments_coverage(self):
        engine = GARDENEngine(compatibility_mode=True)
        assert len(engine._HORMONE_ADJUSTMENTS) >= 4
        assert "happy" in engine._HORMONE_ADJUSTMENTS
        assert "neutral" in engine._HORMONE_ADJUSTMENTS


# ---------------------------------------------------------------------------
# Phase 4.5: GARDEN Continuous Learning
# ---------------------------------------------------------------------------

class TestGARDENContinuousLearning:
    """Tests for GARDEN learn_from_interaction."""

    def test_learn_from_interaction(self):
        engine = GARDENEngine(compatibility_mode=True)
        engine.load_presets()
        result = engine.learn_from_interaction("hello", "hi there")
        assert "interaction" in result
        assert "hebbian_delta" in result

    def test_learn_grows_dictionary(self):
        engine = GARDENEngine(compatibility_mode=True)
        engine.load_presets()
        count_before = len(engine.dictionary.entries)
        engine.learn_from_interaction("completely novel phrase xyz", "response")
        # Dictionary may grow if tokens are novel enough
        assert len(engine.dictionary.entries) >= count_before

    def test_learn_count_increments(self):
        engine = GARDENEngine(compatibility_mode=True)
        engine.load_presets()
        assert engine._learn_count == 0
        engine.learn_from_interaction("test", "response")
        assert engine._learn_count == 1

    def test_multiple_interactions(self):
        engine = GARDENEngine(compatibility_mode=True)
        engine.load_presets()
        for i in range(5):
            engine.learn_from_interaction(f"input {i}", f"output {i}")
        assert engine._learn_count == 5


# ---------------------------------------------------------------------------
# Phase 4.6: End-to-End Quality
# ---------------------------------------------------------------------------

class TestGARDENQuality:
    """Tests for GARDEN response quality."""

    def test_reflex_quality(self):
        engine = GARDENEngine(compatibility_mode=True)
        engine.load_presets()
        result = engine.process("你好")
        assert "你好" in result or "hi" in result.lower() or "hello" in result.lower()

    def test_greeting_response(self):
        engine = GARDENEngine(compatibility_mode=True)
        engine.load_presets()
        result = engine.process("hello")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empty_input(self):
        engine = GARDENEngine(compatibility_mode=True)
        assert engine.process("") == ""
        assert engine.process(None) == ""

    def test_stats_after_interactions(self):
        engine = GARDENEngine(compatibility_mode=True)
        engine.load_presets()
        engine.process("hello")
        engine.learn_from_interaction("hello", "hi")
        stats = engine.stats()
        assert stats["query_count"] >= 1
        assert stats["learn_count"] >= 1
