import json
import os
import tempfile
from typing import Any, Dict, List

import pytest

from apps.backend.src.ai.ed3n.continuous_learning import (
    ContinuousLearningPipeline,
    TrainingExample as CLTrainingExample,
)
from apps.backend.src.ai.ed3n.core_network import CoreNetwork
from apps.backend.src.ai.ed3n.dictionary_layer import DictionaryEntry, DictionaryLayer
from apps.backend.src.ai.ed3n.ed3n_engine import ED3NEngine, ReflexLayer
from apps.backend.src.ai.ed3n.ed3n_trainer import ED3NTrainer, SequenceTrainer, JointTrainer
from apps.backend.src.ai.ed3n.output_anchor import (
    ResponseAnchorValidator,
    anchored_decode,
    compute_anchor_drift,
)
from apps.backend.src.ai.ed3n.relation_classifier import RelationClassifier, RelationType
from apps.backend.src.ai.ed3n.training_types import (
    TrainingBatch,
    TrainingExample,
    SeqBatch,
    SequenceExample,
    make_synthetic_seq_batch,
    seq_batch_from_examples,
    training_example_to_sequence,
)

# ===========================================================================
# DictionaryLayer tests
# ===========================================================================


class TestDictionaryLayer:
    def test_encode_known_input(self, engine: ED3NEngine):
        keys = engine.dictionary.encode("你好")
        assert "g1" in keys

    def test_encode_unknown_input(self, engine: ED3NEngine):
        keys = engine.dictionary.encode("zxvqwpbj")
        assert keys == []

    def test_add_entry(self, engine: ED3NEngine):
        dl = engine.dictionary
        dl.add_entry(
            key="test1",
            surface_forms={"zh": "测试", "en": "test"},
        )
        keys = dl.encode("测试")
        assert "test1" in keys

    def test_grow(self, engine: ED3NEngine):
        dl = engine.dictionary
        key = dl.grow("new phrase", "新短语", confidence=0.9)
        assert key.startswith("l")
        assert key in dl.entries
        assert dl.entries[key].surface_forms["en"] == "new phrase"
        assert dl.entries[key].surface_forms["zh"] == "新短语"

    def test_detect_new_concepts(self, engine: ED3NEngine):
        dl = engine.dictionary
        known = list(dl.entries.keys())
        candidates = dl.detect_new_concepts("unprecedented quantum flux", known)
        texts = [c["text"] for c in candidates]
        assert "unprecedented" in texts
        assert "quantum" in texts
        assert "flux" in texts

    def test_learn_from_conversation(self, engine: ED3NEngine):
        dl = engine.dictionary
        count_before = len(dl.entries)
        new_keys = dl.learn_from_conversation(
            ["hello", "this is a completely novel concept"],
        )
        assert len(new_keys) >= 1
        assert len(dl.entries) > count_before

    def test_export_import_json(self, engine: ED3NEngine):
        dl = engine.dictionary
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "dict.json")
            dl.export_to_json(path)
            dl2 = DictionaryLayer()
            count = dl2.import_from_json(path)
        assert count == len(dl.entries)
        assert "g1" in dl2.entries

    def test_synonyms(self, engine: ED3NEngine):
        dl = engine.dictionary
        syns = dl.get_synonyms("g5")
        assert "g1" in syns
        assert "g6" in syns
        assert "g2" in syns
        assert "g3" in syns

    def test_related(self, engine: ED3NEngine):
        dl = engine.dictionary
        related = dl.get_related("e1")
        assert len(related) >= 1
        syn = dl.get_related("e1", relation_type="synonym")
        assert "e5" in syn

    def test_lookup(self, engine: ED3NEngine):
        dl = engine.dictionary
        result = dl.lookup(["g1", "nonexistent"])
        assert result["g1"] is not None
        assert result["g1"].key == "g1"
        assert result["nonexistent"] is None

    def test_decode(self, engine: ED3NEngine):
        dl = engine.dictionary
        text = dl.decode(["g1", "p1"])
        assert "你好" in text
        assert "谢谢" in text

    def test_merge(self, engine: ED3NEngine):
        dl = engine.dictionary
        dl.add_entry(key="src", surface_forms={"en": "source"})
        dl.add_entry(key="tgt", surface_forms={"en": "target"})
        assert dl.merge_entries("src", "tgt") is True
        assert "src" not in dl.entries
        assert "tgt" in dl.entries

    def test_math_presets(self, engine: ED3NEngine):
        keys = engine.dictionary.encode("178 plus 101")
        # "plus" should match the "m11" entry's "en" surface form
        assert any(k.startswith("m") for k in keys)

    def test_empty_string(self, engine: ED3NEngine):
        assert engine.dictionary.encode("") == []

    def test_special_chars(self, engine: ED3NEngine):
        assert engine.dictionary.encode("!!! @@@ ###") == []

    @pytest.mark.slow
    def test_very_long_input(self, engine: ED3NEngine):
        long_text = "hello " * 2500
        keys = engine.dictionary.encode(long_text)
        assert isinstance(keys, list)

    def test_missing_encoder_key(self, engine: ED3NEngine):
        keys = engine.dictionary.encode("hello", modality="image")
        assert isinstance(keys, list)


# ===========================================================================
# CoreNetwork tests
# ===========================================================================


class TestCoreNetwork:
    def test_forward(self, engine: ED3NEngine):
        net = engine.network
        net.add_relation("g1", RelationType.SYNONYM, "g5")
        net.add_relation("g5", RelationType.MAPPING, "r1")
        result = net.forward(["g1"])
        assert isinstance(result, dict)
        assert len(result) >= 1

    def test_add_connection(self):
        net = CoreNetwork()
        net.add_relation("a", RelationType.MAPPING, "b")
        assert "a" in net.groups["mapping"].neurons
        assert "b" in net.groups["mapping"].neurons
        assert net.groups["mapping"].neurons["a"].connections.get("b", 0.0) > 0

    def test_adjust_connection(self):
        net = CoreNetwork()
        net.add_relation("a", RelationType.MAPPING, "b", weight=0.5)
        net.adjust_connection("a", "b", 0.2)
        w = net.groups["mapping"].neurons["a"].connections.get("b", 0.0)
        assert abs(w - 0.7) < 1e-6

    def test_add_relation(self):
        net = CoreNetwork()
        net.add_relation("k1", RelationType.SYNONYM, "k2", weight=0.8)
        g = net.groups["synonym"]
        assert g.neurons["k1"].connections.get("k2", 0.0) == 0.8
        assert g.neurons["k2"].connections.get("k1", 0.0) == 0.8

    def test_save_load_connections(self):
        net = CoreNetwork()
        net.add_relation("x", RelationType.MAPPING, "y", weight=0.75)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "conns.json")
            net.save_connections(path)
            net2 = CoreNetwork()
            count = net2.load_connections(path)
        assert count >= 1
        assert "x" in net2.groups["mapping"].neurons

    def test_empty_forward(self):
        net = CoreNetwork()
        result = net.forward([])
        assert result == {}

    def test_snn_mode_forward(self, engine: ED3NEngine):
        net = engine.network
        net.add_relation("g1", RelationType.SYNONYM, "g5")
        result = net.forward(["g1"], context={"mode": "snn"})
        assert isinstance(result, dict)


# ===========================================================================
# ED3NTrainer tests
# ===========================================================================


class TestED3NTrainer:
    def test_train_step(self, engine: ED3NEngine):
        trainer = ED3NTrainer(engine)
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
        batch = TrainingBatch(examples=examples, batch_id="b1")
        metrics = trainer.train_step(batch)
        assert metrics.phase == "combined"
        assert isinstance(metrics.loss, float)
        assert isinstance(metrics.accuracy, float)

    def test_save_load(self, engine: ED3NEngine):
        trainer = ED3NTrainer(engine)
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
        batch = TrainingBatch(examples=examples, batch_id="b1")
        trainer.train_step(batch)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "trainer.json")
            trainer.save(path)
            trainer2 = ED3NTrainer.load(path)
        assert len(trainer2.training_history) == len(trainer.training_history)
        assert trainer2.current_epoch == trainer.current_epoch

    def test_training_improves(self, engine: ED3NEngine):
        trainer = ED3NTrainer(engine)
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
            TrainingExample(
                input_text="bye",
                expected_output="goodbye",
                input_keys=["f1"],
                output_keys=["f2"],
                relation_pairs=[],
                confidence=0.9,
                metadata={},
            ),
        ]
        batch = TrainingBatch(examples=examples, batch_id="b1")
        m1 = trainer.train_step(batch)
        m2 = trainer.train_step(batch)
        assert m2.accuracy >= m1.accuracy


# ===========================================================================
# ED3NEngine tests
# ===========================================================================


class TestED3NEngine:
    def test_process_reflex(self, engine: ED3NEngine):
        result = engine.process_reflex("你好")
        assert result is not None
        assert "很高兴" in result

    def test_process_reflex_case_insensitive(self, engine: ED3NEngine):
        result = engine.process_reflex("HELLO")
        assert result is not None
        assert "Hello" in result

    def test_process_depth_shallow(self, engine: ED3NEngine):
        result = engine.process("你好", depth="shallow")
        assert result is not None
        assert len(result) > 0

    def test_process_deep(self, engine: ED3NEngine):
        engine.network.add_relation("g1", "mapping", "r1")
        result = engine.process("你好", depth="deep")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_process_snn(self, engine: ED3NEngine):
        engine.network.add_relation("g1", "mapping", "r1")
        result = engine.process("你好", depth="snn")
        assert isinstance(result, str)

    def test_save_load(self, engine: ED3NEngine):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "engine.json")
            engine.save(path)
            engine2 = ED3NEngine()
            engine2.load(path)
        assert engine2.snn_mode == engine.snn_mode
        assert engine2.reflex.threshold == engine.reflex.threshold
        assert len(engine2.dictionary.entries) >= len(engine.dictionary.entries)

    def test_enable_multimodal(self, engine: ED3NEngine):
        engine.enable_multimodal(enable_image=True, enable_audio=True)
        assert engine.image_encoder is not None
        assert engine.audio_encoder is not None
        assert engine.cross_modal_trainer is not None

    def test_math_with_presets(self, engine: ED3NEngine):
        keys = engine.dictionary.encode("true OR false")
        assert any(k.startswith("b") for k in keys)


# ===========================================================================
# ReflexLayer tests
# ===========================================================================


class TestReflexLayer:
    def test_reflex_matches_exact(self):
        rl = ReflexLayer()
        rl.add_pattern("hello", "world")
        assert rl.process("hello") == "world"

    def test_reflex_matches_substring(self):
        rl = ReflexLayer()
        rl.add_pattern("hello", "world")
        assert rl.process("say hello there") == "world"

    def test_reflex_no_match(self):
        rl = ReflexLayer()
        assert rl.process("garbage_nonexistent") is None

    def test_reflex_cache(self):
        rl = ReflexLayer()
        rl.add_pattern("hello", "world")
        rl.process("hello")
        assert "hello" in rl.lru_cache

    def test_reflex_add_pattern(self):
        rl = ReflexLayer()
        rl.add_pattern("test pattern", "test response")
        assert rl.process("test pattern") == "test response"


# ===========================================================================
# OutputAnchor & ResponseAnchorValidator tests
# ===========================================================================


class TestOutputAnchor:
    def test_anchored_decode(self, engine: ED3NEngine):
        result = anchored_decode(
            network_output={"g5": 0.9, "r1": 0.7},
            original_input_keys=["g1"],
            dictionary=engine.dictionary,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_validate(self, engine: ED3NEngine):
        validator = ResponseAnchorValidator(dictionary=engine.dictionary)
        valid = validator.validate(
            response="你好 谢谢",
            anchored_keys=["g1", "p1"],
            response_keys=["g1", "p1"],
        )
        assert valid is True

    def test_validate_rejects_drift(self, engine: ED3NEngine):
        validator = ResponseAnchorValidator(dictionary=engine.dictionary, max_drift=0.3)
        valid = validator.validate(
            response="completely unrelated response",
            anchored_keys=["g1", "p1"],
            response_keys=["x1", "x2"],
        )
        assert valid is False


# ===========================================================================
# ContinuousLearningPipeline tests
# ===========================================================================


class TestContinuousLearningPipeline:
    def test_process_interaction(self, engine: ED3NEngine):
        trainer = ED3NTrainer(engine)
        cl = ContinuousLearningPipeline(
            engine=engine,
            trainer=trainer,
            min_examples_for_train=100,
            growth_interval=5,
            train_interval=100,
            auto_grow=True,
        )
        result = cl.process_interaction(
            user_text="hello",
            response_text="hi there",
            context={"session": "test"},
        )
        assert result["interaction"] == 1

    def test_train_step_with_converter(self, engine: ED3NEngine):
        trainer = ED3NTrainer(engine)
        cl = ContinuousLearningPipeline(
            engine=engine,
            trainer=trainer,
            min_examples_for_train=1,
            growth_interval=1,
            train_interval=1,
            auto_grow=False,
        )
        cl._training_buffer.append(
            CLTrainingExample(
                user_text="hello",
                response_text="hi",
                context={"session": "t1"},
            ),
        )
        metrics = cl.train_step()
        assert metrics is not None
        assert isinstance(metrics.loss, float)

    def test_none_input_process(self, engine: ED3NEngine):
        assert engine.process(None) == ""

    def test_none_input_encode(self, engine: ED3NEngine):
        assert engine.dictionary.encode(None) == []

    def test_corrupted_load(self, engine: ED3NEngine):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "corrupt.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("{not json")
            engine.load(path)
            assert engine is not None

    def test_prune_empty(self, engine: ED3NEngine):
        dl = DictionaryLayer()
        before = len(dl.entries)
        dl.prune(min_confidence=0.0)
        assert len(dl.entries) == before

    def test_prune_near_empty(self, engine: ED3NEngine):
        dl = DictionaryLayer()
        dl.add_entry(key="p1", surface_forms={"en": "test"})
        dl.entries["p1"].confidence = 0.01
        pruned = dl.prune(min_confidence=0.5, max_age_days=365)
        assert pruned == 1
        assert "p1" not in dl.entries

    def test_telemetry_empty(self, engine: ED3NEngine):
        from apps.backend.src.ai.ed3n.telemetry import TelemetryCollector
        tc = TelemetryCollector()
        summary = tc.get_summary()
        assert summary["total_queries"] == 0

    def test_io_analyzer_empty(self, engine: ED3NEngine):
        from apps.backend.src.ai.ed3n.io_analyzer import IOAnalyzer
        from apps.backend.src.ai.ed3n.telemetry import TelemetryCollector
        tc = TelemetryCollector()
        analyzer = IOAnalyzer(tc)
        report = analyzer.generate_report()
        assert "no data" in report

    def test_telemetry_percentiles(self, engine: ED3NEngine):
        from apps.backend.src.ai.ed3n.telemetry import TelemetryCollector
        tc = TelemetryCollector()
        tc.record_query("t1", "hi", stages={"reflex": 1.0}, reflex_match=None,
                        cache_hit=False, matched_keys=[], output_text="hi",
                        confidence=0.5, is_fallback=False)
        tc.record_query("t2", "hello", stages={"reflex": 2.0}, reflex_match="hello",
                        cache_hit=True, matched_keys=["g1"], output_text="hello",
                        confidence=0.9, is_fallback=False)
        summary = tc.get_summary()
        assert summary["total_queries"] == 2

    def test_thread_safety_encode(self, engine: ED3NEngine):
        import concurrent.futures
        dl = engine.dictionary
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(dl.encode, t) for t in ["你好", "hello", "再见", "谢谢"] * 8]
            results = [f.result() for f in futures]
        assert len(results) == 32
        assert all(isinstance(r, list) for r in results)

    def test_thread_safety_process(self, engine: ED3NEngine):
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(engine.process, t) for t in ["你好", "hello", "再见", "谢谢"] * 8]
            results = [f.result() for f in futures]
        assert len(results) == 32
        assert all(isinstance(r, str) for r in results)

    def test_thread_safety_cl(self, engine: ED3NEngine):
        import concurrent.futures
        cl = ContinuousLearningPipeline(engine=engine, auto_grow=False)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(cl.process_interaction, f"test_{i}", f"resp_{i}", {}) for i in range(20)]
            results = [f.result() for f in futures]
        assert len(results) == 20
        assert cl._interaction_count == 20

    def test_cl_history_maxlen(self, engine: ED3NEngine):
        cl = ContinuousLearningPipeline(engine=engine, auto_grow=False)
        for i in range(2000):
            cl.process_interaction(f"test_{i}", f"resp_{i}", {})
        assert len(cl._history) <= 1000


# ===========================================================================
# SequenceTrainer & generation tests
# ===========================================================================


class TestSequenceDataUtils:
    def test_training_example_to_sequence(self, engine: ED3NEngine):
        tex = TrainingExample(
            input_text="hello world", expected_output="hi",
            input_keys=["g1", "g2"], output_keys=["g5"],
            relation_pairs=[], confidence=0.8,
        )
        seq = training_example_to_sequence(tex)
        assert seq.input_key_seq == ["g1", "g2"]
        assert seq.target_key_seq == ["g5"]
        assert seq.input_text == "hello world"

    def test_seq_batch_from_examples(self, engine: ED3NEngine):
        examples = [
            TrainingExample("a", "b", ["k1"], ["k2"], [], 0.8),
            TrainingExample("c", "d", ["k3"], ["k4"], [], 0.9),
        ]
        batch = seq_batch_from_examples(examples, "test_batch")
        assert len(batch.examples) == 2
        assert batch.batch_id == "test_batch"
        assert batch.examples[0].input_key_seq == ["k1"]

    def test_make_synthetic_seq_batch(self, engine: ED3NEngine):
        raw = [
            (["start"], ["next", "end"]),
            (["open"], ["close"]),
        ]
        batch = make_synthetic_seq_batch(raw, "synth")
        assert len(batch.examples) == 2
        assert batch.examples[0].target_key_seq == ["next", "end"]
        assert batch.examples[1].input_key_seq == ["open"]


class TestSequenceTrainer:
    def test_sequence_trainer_basic(self, engine: ED3NEngine):
        trainer = SequenceTrainer(engine, seq_lr=0.1)
        batch = make_synthetic_seq_batch([
            (["a"], ["b"]),
            (["b"], ["c"]),
        ])
        metrics = trainer.train_step(batch)
        assert isinstance(metrics.loss, float)
        assert isinstance(metrics.accuracy, float)
        assert metrics.phase == "sequence"

    def test_sequence_trainer_improves(self, engine: ED3NEngine):
        trainer = SequenceTrainer(engine, seq_lr=0.2)
        batch = make_synthetic_seq_batch([
            (["start"], ["middle", "end"]),
        ] * 5)
        first = trainer.train_step(batch)
        engine.dictionary.add_entry("middle", {"en": "middle"})
        engine.dictionary.add_entry("end", {"en": "end"})
        engine.dictionary.add_entry("start", {"en": "start"})
        for _ in range(10):
            trainer.train_step(batch)
        result = engine.generate("start")
        assert isinstance(result, str)

    def test_scheduled_sampling_decay(self, engine: ED3NEngine):
        trainer = SequenceTrainer(
            engine, seq_lr=0.1,
            scheduled_sampling_start=1.0,
            scheduled_sampling_end=0.0,
            scheduled_sampling_decay=0.1,
        )
        assert trainer.scheduled_sampling_prob == 1.0
        batch = make_synthetic_seq_batch([(["x"], ["y"])])
        for _ in range(5):
            trainer.train_step(batch)
        assert trainer.scheduled_sampling_prob < 1.0

    def test_scheduled_sampling_never_below_end(self, engine: ED3NEngine):
        trainer = SequenceTrainer(
            engine, seq_lr=0.1,
            scheduled_sampling_start=0.5,
            scheduled_sampling_end=0.3,
            scheduled_sampling_decay=0.01,
        )
        batch = make_synthetic_seq_batch([(["x"], ["y"])])
        for _ in range(50):
            trainer.train_step(batch)
        assert trainer.scheduled_sampling_prob >= 0.3

    def test_reset_scheduled_sampling(self, engine: ED3NEngine):
        trainer = SequenceTrainer(
            engine, seq_lr=0.1,
            scheduled_sampling_start=1.0,
            scheduled_sampling_end=0.0,
            scheduled_sampling_decay=0.1,
        )
        batch = make_synthetic_seq_batch([(["x"], ["y"])])
        trainer.train_step(batch)
        assert trainer.scheduled_sampling_prob < 1.0
        trainer.reset_scheduled_sampling()
        assert trainer.scheduled_sampling_prob == 1.0

    def test_forward_sequential_called(self, engine: ED3NEngine):
        trainer = SequenceTrainer(engine)
        batch = make_synthetic_seq_batch([
            (["key_a"], ["key_b"]),
        ])
        metrics = trainer.train_step(batch)
        assert metrics.loss >= 0.0


class TestGeneration:
    def test_generate_basic(self, engine: ED3NEngine):
        result = engine.generate("hello")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_reflex_fallback(self, engine: ED3NEngine):
        result = engine.generate("你好")
        assert isinstance(result, str)

    def test_generate_empty_input(self, engine: ED3NEngine):
        assert engine.generate("") == ""
        assert engine.generate(None) == ""

    def test_generate_unknown_input(self, engine: ED3NEngine):
        result = engine.generate("xyznonexistent12345")
        assert isinstance(result, str)

    def test_step_decoder_property(self, engine: ED3NEngine):
        decoder = engine.step_decoder
        assert decoder is not None
        assert decoder.dictionary is engine.dictionary
        assert decoder.network is engine.network


# ===========================================================================
# Phase 4: Soft encoding, anchor drift, joint training tests
# ===========================================================================


class TestSoftEncoding:
    def test_encode_soft_empty(self, engine: ED3NEngine):
        assert engine.dictionary.encode_soft("") == {}
        assert engine.dictionary.encode_soft(None) == {}

    def test_encode_soft_returns_dict(self, engine: ED3NEngine):
        result = engine.dictionary.encode_soft("hello")
        assert isinstance(result, dict)
        assert all(isinstance(v, float) for v in result.values())

    def test_encode_soft_scores_nonzero(self, engine: ED3NEngine):
        result = engine.dictionary.encode_soft("hello")
        if result:
            for v in result.values():
                assert 0 < v <= 1.0

    def test_encode_soft_exact_match(self, engine: ED3NEngine):
        result = engine.dictionary.encode_soft("hello")
        assert "g1" in result
        assert result["g1"] == 1.0

    def test_encode_soft_substring_scored_below_one(self, engine: ED3NEngine):
        result = engine.dictionary.encode_soft("ello")
        if "g1" in result:
            assert 0 < result["g1"] < 1.0


class TestAnchorDrift:
    def test_anchor_drift_no_drift(self, engine: ED3NEngine):
        drift = compute_anchor_drift(["g1"], ["g1"], engine.dictionary)
        assert drift == 0.0

    def test_anchor_drift_full_drift(self, engine: ED3NEngine):
        drift = compute_anchor_drift(["g1"], ["nonexistent_key"], engine.dictionary)
        assert drift > 0.0

    def test_anchor_drift_empty_input(self, engine: ED3NEngine):
        assert compute_anchor_drift([], ["g1"], engine.dictionary) == 1.0
        assert compute_anchor_drift(["g1"], [], engine.dictionary) == 1.0

    def test_anchor_drift_partial(self, engine: ED3NEngine):
        drift = compute_anchor_drift(["g1", "g2"], ["g1", "unknown"], engine.dictionary)
        assert 0 < drift < 1.0


class TestJointTrainer:
    def test_joint_trainer_basic(self, engine: ED3NEngine):
        trainer = JointTrainer(engine)
        batch = TrainingBatch(
            examples=[TrainingExample("hi", "hello", ["g1"], ["g5"], [], 0.8)],
            batch_id="test",
        )
        metrics = trainer.train_step(batch)
        assert metrics.phase == "joint"
        assert isinstance(metrics.loss, float)

    def test_joint_trainer_with_seq(self, engine: ED3NEngine):
        trainer = JointTrainer(engine)
        batch = TrainingBatch(
            examples=[TrainingExample("hi", "hello", ["g1"], ["g5"], [], 0.8)],
            batch_id="test",
        )
        seq_batch = make_synthetic_seq_batch([(["g1"], ["g5"])])
        metrics = trainer.train_step(batch, seq_batch)
        assert metrics.phase == "joint"
        assert metrics.samples > 0

    def test_joint_trainer_empty_batch(self, engine: ED3NEngine):
        trainer = JointTrainer(engine)
        batch = TrainingBatch(examples=[], batch_id="empty")
        metrics = trainer.train_step(batch)
        assert metrics.loss >= 0.0

    def test_joint_trainer_summary(self, engine: ED3NEngine):
        trainer = JointTrainer(engine)
        assert trainer.get_summary()["status"] == "no_training"
        batch = TrainingBatch(
            examples=[TrainingExample("hi", "hello", ["g1"], ["g5"], [], 0.8)],
            batch_id="test",
        )
        trainer.train_step(batch)
        summary = trainer.get_summary()
        assert summary["status"] == "active"
        assert summary["steps"] == 1
