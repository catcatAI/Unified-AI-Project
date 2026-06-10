# =============================================================================
# ANGELA-MATRIX: [L2] [βγδ] [C] [L2]
# =============================================================================
"""End-to-end integration tests for the AI pipeline with real engine instances."""

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
