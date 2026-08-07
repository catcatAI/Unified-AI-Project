# =============================================================================
# ANGELA-MATRIX: [L3] [γδ] [C] [L0]
# =============================================================================
"""
Tests for GARDEN GARDENEngine.
"""

import os
import random
import string
import tempfile

import pytest
from ai.garden.garden_engine import (
    GARDENEngine,
    _anchored_decode,
    _output_matches,
    _ReflexTable,
    is_deterministic_match,
)


class TestReflexTable:
    """Tests for the fast reflex pattern matcher."""

    def test_match_exact_reflex(self):
        rt = _ReflexTable()
        result = rt.match("你好")
        assert result is not None
        assert "很高兴" in result

    def test_match_substring(self):
        rt = _ReflexTable()
        result = rt.match("say 你好 there")
        assert result is not None

    def test_match_no_reflex(self):
        rt = _ReflexTable()
        assert rt.match("completely unknown text") is None

    def test_match_case_insensitive(self):
        rt = _ReflexTable()
        result = rt.match("HELLO")
        assert result is not None
        assert "Hello" in result

    def test_match_cache(self):
        rt = _ReflexTable()
        rt.match("你好")
        assert "你好" in rt._cache or "你好".lower() in rt._cache
        # Should use cache
        result = rt.match("你好")
        assert result is not None

    def test_add_pattern(self):
        rt = _ReflexTable()
        rt.add("custom_pattern", "custom_response")
        result = rt.match("custom_pattern")
        assert result == "custom_response"

    def test_presets_loaded(self):
        rt = _ReflexTable()
        assert len(rt.patterns) >= 18
        assert "你好" in rt.patterns
        assert "help" in rt.patterns


class TestAnchoredDecode:
    """Tests for output anchoring."""

    def test_decode_with_output(self, dictionary):
        result = _anchored_decode(
            network_output={"g5": 0.9, "r1": 0.7},
            input_keys={"g1": 1.0},
            dictionary=dictionary,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_decode_empty(self, dictionary):
        result = _anchored_decode({}, {}, dictionary)
        assert result == ""

    def test_decode_empty_keys(self, dictionary):
        result = _anchored_decode({"g5": 0.9}, {"g1": 1.0}, dictionary)
        assert isinstance(result, str)

    def test_decode_anchoring(self, dictionary):
        """Anchors should appear in output."""
        result = _anchored_decode(
            network_output={"g5": 0.9},
            input_keys={"g1": 1.0},
            dictionary=dictionary,
            top_k=2,
        )
        assert "你好" in result or "嗨" in result or "hi" in result


class TestGARDENEngineInit:
    """Tests for engine construction."""

    def test_init_defaults_engine(self):
        engine = GARDENEngine(compatibility_mode=True)
        assert engine.reflex is not None
        assert engine.dictionary is not None
        assert engine.snn is not None
        assert engine._presets_loaded is False
        assert engine._query_count == 0
        assert engine._learning_enabled is True
        assert engine._learn_count == 0

    def test_init_custom(self):
        engine = GARDENEngine(top_k=4, similarity_threshold=0.5, snn_timesteps=3, compatibility_mode=True)
        assert engine.dictionary.top_k == 4
        assert engine.dictionary.similarity_threshold == 0.5
        assert engine.snn.timesteps == 3


class TestGARDENEnginePresets:
    """Tests for preset loading."""

    def test_load_presets(self, engine: GARDENEngine):
        assert engine._presets_loaded is True
        assert len(engine.dictionary.entries) >= 50
        assert engine.snn.vocab_size >= 50

    def test_load_presets_wires_snn(self, engine: GARDENEngine):
        """Relations from presets should be in the SNN matrix."""
        i = engine.snn._key_to_idx.get("g1")
        j = engine.snn._key_to_idx.get("g5")
        assert i is not None
        assert j is not None
        assert engine.snn._W[i, j] >= 0.9  # synonym weight


class TestGARDENEngineProcess:
    """Tests for the main processing pipeline."""

    def test_process_reflex(self, engine: GARDENEngine):
        result = engine.process("你好")
        assert "很高兴" in result

    def test_process_reflex_english(self, engine: GARDENEngine):
        result = engine.process("hello")
        assert "Hello" in result or "Nice" in result

    def test_process_vector_greeting(self, engine: GARDENEngine):
        """Greeting that may not match reflex exactly, falls through to vector."""
        result = engine.process("good morning")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_process_unknown(self, engine: GARDENEngine):
        """Completely unknown input should return fallback message."""
        result = engine.process("zxvqwybpqxz")
        # Either empty response or fallback
        assert isinstance(result, str)

    def test_process_empty(self, engine: GARDENEngine):
        assert engine.process("") == ""

    def test_process_none(self, engine: GARDENEngine):
        assert engine.process(None) == ""

    def test_process_emotion(self, engine: GARDENEngine):
        result = engine.process("happy")
        assert isinstance(result, str)

    def test_process_math(self, engine: GARDENEngine):
        result = engine.process("five plus three")
        assert isinstance(result, str)

    def test_process_question(self, engine: GARDENEngine):
        result = engine.process("What is your name")
        assert isinstance(result, str)

    def test_process_increment_query_count(self, engine: GARDENEngine):
        before = engine._query_count
        engine.process("hello")
        assert engine._query_count == before + 1

    def test_process_idempotent(self, engine: GARDENEngine):
        r1 = engine.process("hello")
        r2 = engine.process("hello")
        # Same query should produce same result (reflex is deterministic)
        assert r1 == r2

    def test_last_confidence_after_reflex(self, engine: GARDENEngine):
        engine.process("你好")
        assert engine._last_confidence == 0.95

    def test_last_confidence_after_empty(self, engine: GARDENEngine):
        engine.process("")
        assert engine._last_confidence == 0.0

    def test_last_confidence_after_unknown(self, engine: GARDENEngine):
        engine.process("zxvqwybpqxz")
        assert engine._last_confidence == 0.0

    def test_last_confidence_after_vector(self, engine: GARDENEngine):
        engine.process("good morning")
        assert engine._last_confidence > 0.0


class TestGARDENEngineLearning:
    """Tests for online learning."""

    def test_learn_from_interaction(self, engine: GARDENEngine):
        result = engine.learn_from_interaction(
            user_text="hello world this is a new concept",
            response_text="hi there",
            confidence=0.9,
        )
        assert isinstance(result, dict)
        assert "interaction" in result
        assert "new_concepts" in result
        assert engine._learn_count > 0

    def test_learn_increases_query_count(self, engine: GARDENEngine):
        engine.learn_from_interaction("new phrase here", "response", confidence=0.9)
        assert engine._learn_count > 0

    def test_learn_hebbian_update(self, engine: GARDENEngine):
        result = engine.learn_from_interaction("happy glad", "joy delight", confidence=0.9)
        assert result["hebbian_delta"] >= 0


class TestGARDENEngineHormonal:
    """Tests for hormonal modulation."""

    def test_set_hormone(self, engine: GARDENEngine):
        engine.set_hormone("cortisol", 0.8)
        assert engine.snn.modulator.hormones["cortisol"] == 0.8

    def test_set_hormone_clamps(self, engine: GARDENEngine):
        engine.set_hormone("cortisol", 2.0)
        assert engine.snn.modulator.hormones["cortisol"] == 1.0

    def test_hormone_affects_process(self, engine: GARDENEngine):
        engine.set_hormone("cortisol", 1.0)
        engine.set_hormone("serotonin", 0.0)
        result = engine.process("hello")
        assert isinstance(result, str)


class TestGARDENEngineStats:
    """Tests for statistics reporting."""

    def test_stats(self, engine: GARDENEngine):
        s = engine.stats()
        assert s["tier"] == "GARDEN-1G (Lightweight Local)"
        assert s["presets_loaded"] is True
        assert s["reflex_patterns"] >= 18
        assert "dictionary" in s
        assert "snn" in s
        assert s["dictionary"]["entry_count"] > 0
        assert s["snn"]["vocab_size"] > 0

    def test_stats_after_queries(self, engine: GARDENEngine):
        engine.process("hello")
        engine.process("hi")
        s = engine.stats()
        assert s["query_count"] >= 2


class TestGARDENEnginePersistence:
    """Tests for save/load."""

    def test_save_load_engine(self, engine: GARDENEngine):
        engine.process("hello")
        with tempfile.TemporaryDirectory() as tmp:
            engine.save(tmp)
            engine2 = GARDENEngine(compatibility_mode=True)
            engine2.load(tmp)
        assert engine2._presets_loaded is True
        # Should have all the concept entries
        assert len(engine2.dictionary.entries) >= len(engine.dictionary.entries) // 2
        assert engine2._query_count >= engine._query_count
        assert engine2.reflex is not None
        assert engine2.snn is not None

    def test_save_load_preserves_snn_weights(self, engine: GARDENEngine):
        with tempfile.TemporaryDirectory() as tmp:
            engine.save(tmp)
            engine2 = GARDENEngine(compatibility_mode=True)
            engine2.load(tmp)
        # Check a known relation was preserved
        i = engine.snn._key_to_idx.get("g1")
        j = engine.snn._key_to_idx.get("g5")
        i2 = engine2.snn._key_to_idx.get("g1")
        j2 = engine2.snn._key_to_idx.get("g5")
        if i is not None and j is not None and i2 is not None and j2 is not None:
            assert engine.snn._W[i, j] == engine2.snn._W[i2, j2]

    def test_save_creates_files(self, engine: GARDENEngine):
        with tempfile.TemporaryDirectory() as tmp:
            engine.save(tmp)
            assert os.path.exists(os.path.join(tmp, "dictionary.json"))
            assert os.path.exists(os.path.join(tmp, "snn.pt")) or os.path.exists(os.path.join(tmp, "snn.pt.npy"))
            assert os.path.exists(os.path.join(tmp, "engine_meta.json"))

    def test_save_meta(self, engine: GARDENEngine):
        engine.process("hello")
        with tempfile.TemporaryDirectory() as tmp:
            engine.save(tmp)
            import json
            with open(os.path.join(tmp, "engine_meta.json"), "r", encoding="utf-8") as f:
                meta = json.load(f)
        assert meta["tier"] == "GARDEN-1G"
        assert meta["query_count"] >= 1


# ===========================================================================
# Phase 5: VectorDecoder tests
# ===========================================================================


class TestVectorDecoderInit:
    def test_init_defaults(self, engine: GARDENEngine):
        vd = engine.vector_decoder
        assert vd.dictionary is engine.dictionary
        assert vd.snn is engine.snn
        assert vd.max_steps == 10
        assert vd.min_score == 0.15
        assert vd.temperature == 0.3

    def test_init_custom_construction(self, engine: GARDENEngine):
        from ai.garden.vector_decoder import VectorDecoder

        vd = VectorDecoder(
            dictionary=engine.dictionary,
            snn=engine.snn,
            max_steps=5,
            min_score=0.3,
            temperature=0.5,
        )
        assert vd.max_steps == 5
        assert vd.min_score == 0.3
        assert vd.temperature == 0.5

    def test_engine_generate_method_exists(self, engine: GARDENEngine):
        assert hasattr(engine, "generate")
        assert callable(engine.generate)


class TestVectorDecoderGenerate:
    def test_generate_empty_input(self, engine: GARDENEngine):
        result = engine.generate("")
        assert result == ""

    def test_generate_none_input(self, engine: GARDENEngine):
        result = engine.generate(None)
        assert result == ""

    def test_generate_returns_string(self, engine: GARDENEngine):
        # Force first encode to build index (reflex may short-circuit)
        result = engine.generate("good morning")
        assert isinstance(result, str)

    def test_generate_unknown_input(self, engine: GARDENEngine):
        result = engine.generate("zxvqwybpqxz")
        assert isinstance(result, str)

    def test_generate_with_temperature(self, engine: GARDENEngine):
        result = engine.generate("hello", temperature=0.0)
        assert isinstance(result, str)

    def test_generate_with_custom_steps(self, engine: GARDENEngine):
        result = engine.generate("happy", max_steps=3)
        assert isinstance(result, str)


class TestVectorDecoderSampling:
    def test_sample_deterministic_at_zero_temp(self, engine: GARDENEngine):
        from ai.garden.vector_decoder import VectorDecoder

        vd = VectorDecoder(
            dictionary=engine.dictionary,
            snn=engine.snn,
            temperature=0.0,
        )
        # Deterministic: always picks the max
        result = vd._sample({"a": 0.9, "b": 0.5})
        assert result == "a"

    def test_sample_single_candidate(self, engine: GARDENEngine):
        from ai.garden.vector_decoder import VectorDecoder

        vd = VectorDecoder(
            dictionary=engine.dictionary,
            snn=engine.snn,
        )
        result = vd._sample({"only_key": 0.8})
        assert result == "only_key"

    def test_sample_empty_candidates(self, engine: GARDENEngine):
        from ai.garden.vector_decoder import VectorDecoder

        vd = VectorDecoder(
            dictionary=engine.dictionary,
            snn=engine.snn,
        )
        assert vd._sample({}) is None


class TestOutputMatches:
    """Tests for _output_matches — deterministic engine ↔ training output."""

    def test_exact_match(self):
        assert _output_matches("279", "279") is True

    def test_engine_in_expected(self):
        """Engine returns bare number, training has formatted expression."""
        assert _output_matches("279", "178 + 101 = 279") is True

    def test_expected_in_engine(self):
        """Engine returns formatted expression, training has bare number."""
        assert _output_matches("178 + 101 = 279", "279") is True

    def test_no_match(self):
        assert _output_matches("42", "hello world") is False

    def test_short_token_no_false_positive(self):
        """Single-digit numbers should not substring-match, too ambiguous."""
        assert _output_matches("7", "I have 7 cats") is False

    def test_both_empty(self):
        assert _output_matches("", "") is True

    def test_case_mismatch(self):
        assert _output_matches("Hello", "hello") is False

    def test_single_digit_no_false_positive(self):
        """Single-digit numbers guarded by length >= 2."""
        assert _output_matches("7", "I have 7 cats") is False

    def test_spaces_stripped(self):
        assert _output_matches("  279  ", "279") is True

    def test_multi_word_engine_in_expected(self):
        assert _output_matches("42", "the answer is 42") is True


class TestIsDeterministicMatch:
    """Tests for is_deterministic_match — end-to-end engine dispatch."""

    def test_math_query(self):
        assert is_deterministic_match("178 + 101", "279") is True

    def test_math_as_sentence(self):
        assert is_deterministic_match("What is 178 + 101?", "279") is True

    def test_non_math_query(self):
        assert is_deterministic_match("Hello, how are you?", "I'm fine") is False

    def test_division(self):
        assert is_deterministic_match("100 / 4", "100 / 4 = 25") is True

    def test_float_result(self):
        assert is_deterministic_match("22 / 7", "22 / 7 = 3.14") is True


def _rand_word(min_len=4, max_len=10):
    return "".join(random.choice(string.ascii_lowercase) for _ in range(random.randint(min_len, max_len)))


class TestLearnBatchRobustness:
    """GARDEN learn_batch must tolerate non-string / empty training samples."""

    def _engine(self):
        e = GARDENEngine(compatibility_mode=True)
        e.load_presets()
        return e

    def test_non_string_samples(self):
        e = self._engine()
        samples = [
            {"input": None, "output": "hello world"},
            {"input": 123, "output": "numeric input"},
            {"input": "", "output": ""},
            {"input": "x", "output": "y"},  # below min token length
            {"input": "a b c", "output": "d e f"},
        ]
        result = e.learn_batch(samples, confidence=0.7, train_associations=True)
        assert result["samples_processed"] == len(samples)

    def test_cross_batch_vocab_growth_no_crash(self):
        """Regression: stale embed cache after encoder re-fit (dim change) must
        not raise 'all input arrays must have the same shape'."""
        e = self._engine()
        b1 = [{"input": _rand_word() + " one", "output": _rand_word() + " two"} for _ in range(8)]
        e.learn_batch(b1, confidence=0.7)
        # Batch 2 adds many distinct tokens -> encoder re-fit with larger dim.
        b2 = [
            {"input": _rand_word() + " xyzqr abcde", "output": _rand_word()}
            for _ in range(30)
        ]
        r2 = e.learn_batch(b2, confidence=0.7)
        assert r2["samples_processed"] == 30
        # A query that must run TF-IDF Step 4 (unmatched token, uses cache).
        out = e.process("ponupp zzz")
        assert isinstance(out, str)

    def test_cjk_batch(self):
        e = self._engine()
        samples = [
            {"input": "中国是世界上人口最多的国家", "output": "中国拥有十四亿人口"},
            {"input": "北京是中国的首都", "output": "北京是政治文化中心"},
        ]
        result = e.learn_batch(samples, confidence=0.7, train_associations=True)
        assert result["samples_processed"] == 2
