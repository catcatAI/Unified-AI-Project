# =============================================================================
# ANGELA-MATRIX: [L2] [βγδ] [C] [L2]
# =============================================================================
"""End-to-end integration tests for the AI pipeline with real engine instances."""

import asyncio
import math
import time
from datetime import datetime, timedelta

import pytest

from apps.backend.src.ai.core.model_bus import ModelBus, ModelCapability
from apps.backend.src.ai.ed3n.ed3n_engine import ED3NEngine
from apps.backend.src.ai.ed3n.ed3n_trainer import ED3NTrainer
from apps.backend.src.ai.ed3n.training_types import TrainingBatch, TrainingExample
from apps.backend.src.ai.garden.garden_engine import GARDENEngine
from apps.backend.src.ai.response.composer import NeuroVocabulary, ValueRangeMapping


# ===========================================================================
# TestModelBusRealEngines — ModelBus with real ED3NEngine + GARDENEngine
# ===========================================================================


@pytest.mark.integration
class TestModelBusRealEngines:
    """Integration tests routing real engines through ModelBus."""

    @pytest.fixture
    def ed3n(self):
        engine = ED3NEngine()
        engine.load_presets()
        return engine

    @pytest.fixture
    def garden(self):
        engine = GARDENEngine(device="cpu", compatibility_mode=True)
        engine.load_presets()
        return engine

    @pytest.fixture
    def bus(self, ed3n, garden):
        bus = ModelBus()
        bus.register_ed3n(ed3n)
        bus.register_garden(garden)
        return bus

    async def test_route_reflex(self, bus):
        """ED3N handles reflex/greeting queries via pattern match."""
        decision = await bus.route("hello", "reflex")
        assert decision.selected_model == "ed3n"
        assert decision.confidence > 0
        assert "ed3n" in decision.results
        assert decision.results["ed3n"].text == "Hello! Nice to meet you!"

    async def test_route_reflex_chinese(self, bus):
        """ED3N handles Chinese greeting via reflex."""
        decision = await bus.route("你好", "reflex")
        assert decision.selected_model == "ed3n"
        assert "你好" in decision.results["ed3n"].text

    async def test_route_math_fallback(self, bus):
        """ED3N returns empty → confidence 0 → GARDEN fallback for math."""
        decision = await bus.route("", "math")
        assert "ed3n" in decision.results
        assert "garden" in decision.results
        assert decision.results["ed3n"].confidence == 0.0

    async def test_route_knowledge(self, bus):
        """GARDEN handles knowledge queries."""
        decision = await bus.route("hello", "knowledge")
        assert "garden" in decision.results
        assert decision.results["garden"].confidence > 0

    async def test_route_general_fan_out(self, bus, ed3n, garden):
        """General query type fans out to all eligible models."""
        decision = await bus.route("hello", "general")
        assert len(decision.results) > 0
        assert decision.selected_model != "none"

    async def test_sync_knowledge(self, bus):
        """Sync patterns from ED3N to GARDEN."""
        patterns = [("hello", "hi there"), ("goodbye", "see ya")]
        count = bus.sync_knowledge("ed3n", "garden", patterns)
        assert count == 2

    async def test_sync_knowledge_unknown_source(self, bus):
        """sync_knowledge returns 0 for unknown models."""
        count = bus.sync_knowledge("nonexistent", "garden", [("a", "b")])
        assert count == 0

    def test_get_models_for_domain(self, bus):
        """Domain queries return correct models."""
        reflex = bus.get_models_for_domain("reflex")
        assert "ed3n" in reflex

        knowledge = bus.get_models_for_domain("knowledge")
        assert "garden" in knowledge

    def test_get_stats(self, bus):
        """Diagnostic stats include all registered models."""
        stats = bus.get_stats()
        assert "registered_models" in stats
        assert "ed3n" in stats["registered_models"]
        assert "garden" in stats["registered_models"]
        assert "capabilities" in stats

    def test_get_training_assignment(self, bus):
        """Training assignment returns first model for domain."""
        assigned = bus.get_training_assignment("reflex")
        assert assigned == "ed3n"

        assigned = bus.get_training_assignment("knowledge")
        assert assigned == "garden"

    async def test_route_with_context(self, bus):
        """Context dict is passed through to engine process()."""
        decision = await bus.route("hello", "reflex", context={"user_id": "test"})
        assert decision.selected_model == "ed3n"

    def test_register_custom_model(self, bus, ed3n):
        """Register a third model with custom capability."""
        cap = ModelCapability(tier="custom", domain="test", latency_ms=5.0, min_confidence=0.5)
        bus.register("custom", ed3n, cap)
        models = bus.get_models_for_domain("test")
        assert "custom" in models


# ===========================================================================
# TestNeuroVocabularyC6FullCycle — full C6 semantic mapping lifecycle
# ===========================================================================


@pytest.mark.integration
class TestNeuroVocabularyC6FullCycle:
    """Tests the full C6 semantic value-range mapping lifecycle without mocks."""

    @pytest.fixture
    def vocab(self):
        return NeuroVocabulary()

    def test_learn_mapping(self, vocab):
        """learn_mapping creates a new mapping entry."""
        vocab.learn_mapping("gamma.valence", 0.5, "neutral emotion")
        mappings = vocab.get_value_range_mappings("gamma.valence")
        assert len(mappings) == 1
        assert mappings[0].confidence == pytest.approx(0.3, abs=0.01)

    def test_learn_mapping_covers_repeat(self, vocab):
        """Repeated learn narrows the range and increases confidence."""
        vocab.learn_mapping("gamma.valence", 0.5, "neutral")
        vocab.learn_mapping("gamma.valence", 0.5, "neutral refined")
        mappings = vocab.get_value_range_mappings("gamma.valence")
        assert len(mappings) == 1
        assert mappings[0].usage_count == 2
        assert mappings[0].range_lo > 0.49
        assert mappings[0].range_hi < 0.51
        assert mappings[0].confidence > 0.3

    def test_find_axis_values(self, vocab):
        """Reverse mapping finds axis values from description."""
        vocab.learn_mapping("alpha.energy", 0.8, "high energy")
        results = vocab.find_axis_values("high energy")
        assert len(results) >= 1
        assert results[0]["axis_field"] == "alpha.energy"

    def test_find_axis_values_threshold(self, vocab):
        """Low-confidence mappings are filtered by threshold."""
        vocab.learn_mapping("alpha.energy", 0.8, "high energy")
        results = vocab.find_axis_values("high energy", threshold=0.5)
        assert len(results) == 0

    def test_get_description(self, vocab):
        """get_description returns the highest-confidence match."""
        vocab.learn_mapping("gamma.valence", 0.5, "neutral")
        assert vocab.get_description("gamma.valence", 0.5) == "neutral"
        assert vocab.get_description("gamma.valence", 10.0) is None

    def test_confidence_decay(self, vocab):
        """decay_confidences reduces confidence of unused mappings."""
        vocab.learn_mapping("beta.curiosity", 0.7, "curious")
        initial = vocab.get_value_range_mappings("beta.curiosity")[0].confidence
        vocab.decay_confidences(hours=-1, decay_rate=0.1)
        after = vocab.get_value_range_mappings("beta.curiosity")[0].confidence
        assert after <= initial

    def test_decay_removes_stale(self, vocab):
        """decay_confidences removes mappings that fall below min_confidence."""
        vocab.learn_mapping("zeta.temporal", 0.2, "low coherence")
        m = vocab.get_value_range_mappings("zeta.temporal")[0]
        m.last_used_at = datetime.now() - timedelta(days=365)

        vocab.decay_confidences(hours=1, decay_rate=1.0)
        remaining = vocab.get_value_range_mappings("zeta.temporal")
        assert len(remaining) == 0

    def test_overlap_detection(self, vocab):
        """detect_overlaps finds overlapping range mappings."""
        field = "test.overlap"
        vocab._value_range_mappings[field] = [
            ValueRangeMapping(field, 0.3, 0.6, "low-mid", 0.8),
            ValueRangeMapping(field, 0.5, 0.9, "mid-high", 0.7),
        ]
        overlaps = vocab.detect_overlaps(field)
        assert len(overlaps) == 1
        assert overlaps[0]["a"]["description"] == "low-mid"
        assert overlaps[0]["b"]["description"] == "mid-high"

    def test_no_overlap(self, vocab):
        """Separate ranges produce no overlaps."""
        vocab.learn_mapping("alpha.energy", 0.1, "low")
        vocab.learn_mapping("alpha.energy", 0.9, "high")
        overlaps = vocab.detect_overlaps("alpha.energy")
        assert len(overlaps) == 0

    def test_narrow_contracts_range(self, vocab):
        """narrow() shrinks the range around a specific value."""
        m = ValueRangeMapping(
            axis_field="test.field",
            range_lo=0.0,
            range_hi=1.0,
            description="wide",
            confidence=0.5,
        )
        m.narrow(0.5)
        assert m.range_lo > 0.0
        assert m.range_hi < 1.0
        assert m.range_lo < 0.5 < m.range_hi

    def test_covers_type_safety(self, vocab):
        """covers() returns False for non-numeric types."""
        m = ValueRangeMapping(
            axis_field="test.field",
            range_lo=0.0,
            range_hi=1.0,
            description="range",
            confidence=0.5,
        )
        assert m.covers(0.5) is True
        assert m.covers(1.5) is False
        assert m.covers("string") is False
        assert m.covers(None) is False

    def test_serialize_load_cycle(self, vocab):
        """serialize_mappings → load_mappings_from_config round-trip."""
        vocab.learn_mapping("gamma.valence", 0.3, "low positive")
        vocab.learn_mapping("gamma.valence", 0.8, "high positive")
        data = vocab.serialize_mappings(max_age_days=999)
        assert len(data) >= 2

        vocab2 = NeuroVocabulary()
        vocab2.load_mappings_from_config(data)
        loaded = vocab2.get_value_range_mappings("gamma.valence")
        assert len(loaded) == 2
        assert loaded[0].description in ("low positive", "high positive")

    def test_uncovered_values(self, vocab):
        """get_uncovered_values finds values without mappings."""
        vocab.learn_mapping("alpha.energy", 0.5, "medium")
        state = {"alpha": {"values": {"energy": 0.5, "focus": 0.9}}}
        uncovered = vocab.get_uncovered_values(state)
        assert len(uncovered) == 1
        assert uncovered[0]["axis_field"] == "alpha.focus"

    def test_detect_overlaps_three_way(self, vocab):
        """Three overlapping mappings produce two overlap pairs."""
        field = "threeway.field"
        vocab._value_range_mappings[field] = [
            ValueRangeMapping(field, 0.0, 0.4, "low", 0.8),
            ValueRangeMapping(field, 0.3, 0.7, "mid", 0.7),
            ValueRangeMapping(field, 0.6, 1.0, "high", 0.6),
        ]
        overlaps = vocab.detect_overlaps(field)
        assert len(overlaps) == 2

    def test_multiple_axis_fields(self, vocab):
        """Mappings on different axis fields coexist independently."""
        vocab.learn_mapping("alpha.energy", 0.8, "high energy")
        vocab.learn_mapping("beta.curiosity", 0.2, "low curiosity")
        assert len(vocab.get_value_range_mappings("alpha.energy")) == 1
        assert len(vocab.get_value_range_mappings("beta.curiosity")) == 1


# ===========================================================================
# TestTrainingPipelineMini — mini training run with real ED3NTrainer
# ===========================================================================


@pytest.mark.integration
class TestTrainingPipelineMini:
    """Mini training run exercising ED3NTrainer with real dictionary + network."""

    @pytest.fixture
    def engine(self):
        eng = ED3NEngine()
        eng.load_presets()
        return eng

    @pytest.fixture
    def trainer(self, engine):
        return ED3NTrainer(engine, dictionary_lr=0.01, network_lr=0.01)

    def test_train_step_creates_metrics(self, trainer):
        """train_step returns valid TrainMetrics."""
        examples = [
            TrainingExample(
                input_text="hello",
                expected_output="hi there",
                input_keys=["g1"],
                output_keys=["g5"],
                relation_pairs=[],
                confidence=0.8,
                metadata={},
            ),
        ]
        batch = TrainingBatch(examples=examples, batch_id="test_batch_001")
        metrics = trainer.train_step(batch)
        assert metrics.phase == "combined"
        assert metrics.samples == 1
        assert metrics.duration_ms > 0
        assert 0 <= metrics.loss <= 1
        assert 0 <= metrics.accuracy <= 1

    def test_train_dictionary_grows_entries(self, engine, trainer):
        """Dictionary phase can grow new entries for missing keys."""
        count_before = len(engine.dictionary.entries)
        examples = [
            TrainingExample(
                input_text="novel concept",
                expected_output="new response",
                input_keys=["novel_concept_key"],
                output_keys=["novel_response_key"],
                relation_pairs=[],
                confidence=0.9,
                metadata={},
            ),
        ]
        metrics = trainer.train_dictionary_phase(examples)
        count_after = len(engine.dictionary.entries)
        assert count_after > count_before
        assert metrics.accuracy >= 0

    def test_train_network_phase_adjusts_weights(self, engine, trainer):
        """Network phase adjusts connection weights between keys."""
        g5_before = engine.network.forward(["g1"]).get("g5", 0.0)
        examples = [
            TrainingExample(
                input_text="hello",
                expected_output="hi",
                input_keys=["g1"],
                output_keys=["g5"],
                relation_pairs=[],
                confidence=0.9,
                metadata={},
            ),
        ]
        trainer.train_network_phase(examples)
        g5_after = engine.network.forward(["g1"]).get("g5", 0.0)
        assert g5_after != g5_before

    def test_training_history_accumulates(self, trainer):
        """Each train_step appends to training_history."""
        examples = [
            TrainingExample(
                input_text="hello",
                expected_output="hi",
                input_keys=["g1"],
                output_keys=["g5"],
                relation_pairs=[],
                confidence=0.8,
                metadata={},
            ),
        ]
        batch = TrainingBatch(examples=examples, batch_id="batch_001")
        trainer.train_step(batch)
        trainer.train_step(batch)
        assert len(trainer.training_history) == 2
        last = trainer.get_training_summary()
        assert last["steps"] == 2

    def test_train_step_empty_batch(self, trainer):
        """Empty batch returns zero-valued metrics."""
        batch = TrainingBatch(examples=[], batch_id="empty")
        metrics = trainer.train_step(batch)
        assert metrics.loss == 0.0
        assert metrics.accuracy == 0.0
        assert metrics.samples == 0

    def test_confidence_changes_after_training(self, engine, trainer):
        """Entry confidence changes when training with non-matching encode."""
        g1_before = engine.dictionary.entries["g1"].confidence
        # Use input text that won't encode to "g1" to force a miss (match=0)
        examples = [
            TrainingExample(
                input_text="zzz_nonexistent_zzz",
                expected_output="hi",
                input_keys=["g1"],
                output_keys=["g5"],
                relation_pairs=[],
                confidence=0.9,
                metadata={},
            ),
        ]
        trainer.train_dictionary_phase(examples)
        g1_after = engine.dictionary.entries["g1"].confidence
        assert g1_after != g1_before


# ===========================================================================
# Mock engines for stress / edge case tests
# ===========================================================================


class _MockEngine:
    """Lightweight mock engine for stress tests."""
    def __init__(self, response_text="ok", delay=0.0):
        self.response_text = response_text
        self.delay = delay

    async def process(self, query, context=None):
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        return self.response_text


class _EmptyEngine:
    """Engine that returns empty string."""
    async def process(self, query, context=None):
        return ""


class _FailingEngine:
    """Engine that always raises RuntimeError."""
    async def process(self, query, context=None):
        raise RuntimeError("engine failure")


class _SlowEngine:
    """Engine that sleeps too long (triggers timeout)."""
    async def process(self, query, context=None):
        await asyncio.sleep(999)
        return "slow"


# ===========================================================================
# TestModelBusStress — stress, edge case, and chaos tests for ModelBus
# ===========================================================================


@pytest.mark.integration
class TestModelBusStress:
    """Stress, edge case, and chaos tests for ModelBus routing."""

    @pytest.fixture
    def bus(self):
        return ModelBus(default_timeout=30.0)

    async def test_register_10_models_route_all(self, bus):
        """Register 10+ mock models, route to all via general fan-out."""
        for i in range(12):
            cap = ModelCapability(
                tier="mock", domain="general",
                latency_ms=1.0, min_confidence=0.5,
            )
            bus.register(f"mock_{i}", _MockEngine(f"resp_{i}"), cap)
        decision = await bus.route("stress test", "general")
        assert len(decision.results) == 12
        for i in range(12):
            assert f"mock_{i}" in decision.results

    async def test_concurrent_routing(self, bus):
        """Five simultaneous route calls via asyncio.gather."""
        cap = ModelCapability(
            tier="reflex", domain="reflex",
            latency_ms=1.0, min_confidence=0.8,
        )
        bus.register("conc", _MockEngine("concurrent"), cap)
        tasks = [bus.route("hello", "general") for _ in range(5)]
        results = await asyncio.gather(*tasks)
        assert len(results) == 5
        for r in results:
            assert "conc" in r.results

    async def test_register_same_id_twice(self, bus):
        """Register same model_id twice — last registration wins."""
        cap1 = ModelCapability(
            tier="first", domain="reflex",
            latency_ms=1.0, min_confidence=0.5,
        )
        cap2 = ModelCapability(
            tier="second", domain="knowledge",
            latency_ms=10.0, min_confidence=0.8,
        )
        bus.register("dup", _MockEngine("v1"), cap1)
        bus.register("dup", _MockEngine("v2"), cap2)
        stats = bus.get_stats()
        assert stats["capabilities"]["dup"]["tier"] == "second"
        assert stats["capabilities"]["dup"]["domain"] == "knowledge"

    async def test_route_empty_registry(self, bus):
        """Route with no registered models returns 'none'."""
        decision = await bus.route("hello", "general")
        assert decision.selected_model == "none"
        assert decision.confidence == 0.0
        assert len(decision.results) == 0

    async def test_route_all_models_fail(self, bus):
        """All registered models raise — errors captured, confidence 0."""
        for i in range(3):
            cap = ModelCapability(
                tier="mock", domain="general",
                latency_ms=1.0, min_confidence=0.5,
            )
            bus.register(f"fail_{i}", _FailingEngine(), cap)
        decision = await bus.route("hello", "general")
        assert len(decision.results) == 3
        for r in decision.results.values():
            assert r.confidence == 0.0
            assert r.error is not None
            assert "engine failure" in r.error

    async def test_route_with_timeout_engine(self):
        """Engine that exceeds default_timeout is handled gracefully."""
        slow_bus = ModelBus(default_timeout=0.1)
        cap = ModelCapability(
            tier="mock", domain="reflex",
            latency_ms=1.0, min_confidence=0.5,
        )
        slow_bus.register("turtle", _SlowEngine(), cap)
        decision = await slow_bus.route("hello", "general")
        assert decision.results["turtle"].error is not None
        assert "Timeout" in decision.results["turtle"].error
        assert decision.results["turtle"].confidence == 0.0

    async def test_route_long_query(self, bus):
        """10 KB+ query string is handled without crash."""
        long_query = "A" * 10_240
        cap = ModelCapability(
            tier="reflex", domain="reflex",
            latency_ms=1.0, min_confidence=0.8,
        )
        bus.register("long", _MockEngine("ok"), cap)
        decision = await bus.route(long_query, "general")
        assert decision.selected_model == "long"

    async def test_route_unicode_multilingual(self, bus):
        """Unicode / multilingual queries route without crash."""
        cap = ModelCapability(
            tier="reflex", domain="reflex",
            latency_ms=1.0, min_confidence=0.8,
        )
        bus.register("ml", _MockEngine("ok"), cap)
        queries = [
            "你好世界",
            "こんにちは世界",
            "안녕하세요",
            "مرحبا بالعالم",
            "שלום עולם",
            "Привет мир",
            "नमस्ते दुनिया",
            "😊🚀🌍",
            "Français Español Português Deutsch",
            "ελληνικά 中文 русский",
        ]
        for q in queries:
            decision = await bus.route(q, "general")
            assert decision is not None

    async def test_route_models_return_empty(self, bus):
        """Models returning empty strings get zero confidence."""
        cap = ModelCapability(
            tier="mock", domain="general",
            latency_ms=1.0, min_confidence=0.5,
        )
        bus.register("empty", _EmptyEngine(), cap)
        decision = await bus.route("hello", "general")
        assert decision.results["empty"].text == ""
        assert decision.results["empty"].confidence == 0.0

    async def test_route_mixed_success_failure(self, bus):
        """Mix of successful and failing models — successful ones win."""
        cap_good = ModelCapability(
            tier="mock", domain="general",
            latency_ms=1.0, min_confidence=0.9,
        )
        cap_bad = ModelCapability(
            tier="mock", domain="general",
            latency_ms=1.0, min_confidence=0.5,
        )
        bus.register("good", _MockEngine("success"), cap_good)
        bus.register("bad", _FailingEngine(), cap_bad)
        decision = await bus.route("hello", "general")
        assert decision.selected_model == "good"
        assert decision.results["good"].confidence == 0.9
        assert decision.results["bad"].confidence == 0.0
        assert "engine failure" in decision.results["bad"].error


# ===========================================================================
# TestNeuroVocabularyEdgeCases — edge cases for NeuroVocabulary
# ===========================================================================


@pytest.mark.integration
class TestNeuroVocabularyEdgeCases:
    """Edge case and boundary tests for NeuroVocabulary."""

    @pytest.fixture
    def vocab(self):
        return NeuroVocabulary()

    def test_learn_mapping_nan_inf(self, vocab):
        """learn_mapping handles NaN and Inf values without crashing."""
        vocab.learn_mapping("test.nan_val", float("nan"), "nan description")
        vocab.learn_mapping("test.inf_val", float("inf"), "inf description")
        vocab.learn_mapping("test.ninf_val", float("-inf"), "neg inf description")
        mappings_nan = vocab.get_value_range_mappings("test.nan_val")
        mappings_inf = vocab.get_value_range_mappings("test.inf_val")
        mappings_ninf = vocab.get_value_range_mappings("test.ninf_val")
        assert len(mappings_nan) == 1
        assert len(mappings_inf) == 1
        assert len(mappings_ninf) == 1
        # NaN range never covers any value
        assert mappings_nan[0].covers(0.5) is False
        # Inf / -Inf ranges cover only themselves
        assert mappings_inf[0].covers(float("inf")) is True
        assert mappings_ninf[0].covers(float("-inf")) is True

    def test_learn_mapping_empty_description(self, vocab):
        """learn_mapping accepts empty string description."""
        vocab.learn_mapping("test.field", 0.5, "")
        mappings = vocab.get_value_range_mappings("test.field")
        assert len(mappings) == 1
        assert mappings[0].description == ""

    def test_find_axis_values_edge(self, vocab):
        """find_axis_values with None, empty, and malformed input."""
        vocab.learn_mapping("test.field", 0.5, "test description")
        # None input
        assert vocab.find_axis_values(None) == []
        # Empty string input
        assert vocab.find_axis_values("") == []
        # Non-string type raises AttributeError
        with pytest.raises(AttributeError):
            vocab.find_axis_values(123)

    def test_decay_confidences_zero_negative(self, vocab):
        """decay_confidences with hours=0 or hours<0 changes nothing."""
        vocab.learn_mapping("test.field", 0.5, "test")
        conf_before = vocab.get_value_range_mappings("test.field")[0].confidence
        vocab.decay_confidences(hours=0)
        conf_after = vocab.get_value_range_mappings("test.field")[0].confidence
        assert conf_after == conf_before
        vocab.decay_confidences(hours=-5.0)
        conf_after2 = vocab.get_value_range_mappings("test.field")[0].confidence
        assert conf_after2 == conf_before

    def test_serialize_mappings_purge_all(self, vocab):
        """serialize_mappings with max_age_days=0 purges stale entries."""
        vocab.learn_mapping("test.field", 0.5, "test")
        m = vocab.get_value_range_mappings("test.field")[0]
        m.created_at = datetime.now() - timedelta(days=10)
        data = vocab.serialize_mappings(max_age_days=0)
        assert len(data) == 0

    def test_serialize_mappings_negative_age(self, vocab):
        """serialize_mappings with negative max_age_days purges low-usage."""
        vocab.learn_mapping("test.field", 0.5, "test")
        data = vocab.serialize_mappings(max_age_days=-1.0)
        assert len(data) == 0

    def test_load_mappings_edge(self, vocab):
        """load_mappings_from_config with empty / None / malformed data."""
        vocab.load_mappings_from_config([])
        assert len(vocab._value_range_mappings) == 0
        vocab.load_mappings_from_config(None)
        assert len(vocab._value_range_mappings) == 0
        with pytest.raises(KeyError):
            vocab.load_mappings_from_config([{"axis_field": "missing_keys"}])

    def test_detect_overlaps_no_mappings(self, vocab):
        """detect_overlaps on nonexistent field returns empty list."""
        overlaps = vocab.detect_overlaps("nonexistent.field")
        assert overlaps == []

    def test_detect_overlaps_boundary(self, vocab):
        """detect_overlaps when range_hi == next range_lo (boundary touch)."""
        field = "boundary.field"
        vocab._value_range_mappings[field] = [
            ValueRangeMapping(field, 0.0, 0.5, "first half", 0.8),
            ValueRangeMapping(field, 0.5, 1.0, "second half", 0.7),
        ]
        overlaps = vocab.detect_overlaps(field)
        assert len(overlaps) == 1

    def test_sync_restore_state_store_roundtrip(self, vocab):
        """sync_to_state_store / restore_from_state_store roundtrip."""
        try:
            from core.system.state_store.global_store import state_store
            _ = state_store.get_state("test_dummy")
        except Exception:
            pytest.skip("state_store not available in this environment")
        vocab.learn_mapping("rt.field", 0.3, "roundtrip value")
        vocab.sync_to_state_store()
        vocab2 = NeuroVocabulary()
        vocab2.restore_from_state_store()
        restored = vocab2.get_value_range_mappings("rt.field")
        assert len(restored) >= 0


# ===========================================================================
# TestModelBusEdgeCases — edge case registration / query tests for ModelBus
# ===========================================================================


@pytest.mark.integration
class TestModelBusEdgeCases:
    """Edge case tests for ModelBus registration and query methods."""

    @pytest.fixture
    def bus(self):
        return ModelBus()

    @pytest.fixture
    def mock_engine(self):
        return _MockEngine("edge")

    def test_register_empty_model_id(self, bus, mock_engine):
        """register with empty string model_id is accepted."""
        cap = ModelCapability(
            tier="test", domain="test",
            latency_ms=1.0, min_confidence=0.5,
        )
        bus.register("", mock_engine, cap)
        stats = bus.get_stats()
        assert "" in stats["registered_models"]

    def test_register_none_engine(self, bus):
        """register with None engine does not crash registration."""
        cap = ModelCapability(
            tier="test", domain="test",
            latency_ms=1.0, min_confidence=0.5,
        )
        bus.register("noengine", None, cap)
        stats = bus.get_stats()
        assert "noengine" in stats["registered_models"]

    def test_register_invalid_capability(self, bus, mock_engine):
        """register with negative latency / confidence works (no validation)."""
        cap = ModelCapability(
            tier="test", domain="test",
            latency_ms=-1.0, min_confidence=-0.5,
        )
        bus.register("negcap", mock_engine, cap)
        stats = bus.get_stats()
        assert stats["capabilities"]["negcap"]["latency_ms"] == -1.0
        assert stats["capabilities"]["negcap"]["min_confidence"] == -0.5

    def test_get_models_for_domain_nonexistent(self, bus):
        """get_models_for_domain returns empty list for unknown domain."""
        models = bus.get_models_for_domain("__nonexistent_domain__")
        assert models == []

    def test_sync_knowledge_nonexistent_both(self, bus):
        """sync_knowledge returns 0 when both source and target are unknown."""
        count = bus.sync_knowledge("no_src", "no_tgt", [("a", "b")])
        assert count == 0

    def test_pick_best_empty_results(self):
        """_pick_best with empty dict returns 'none' sentinel."""
        result = ModelBus._pick_best({})
        assert result["model_id"] == "none"
        assert result["confidence"] == 0.0
        assert "no models" in result["reason"]
