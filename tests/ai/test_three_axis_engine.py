"""
Tests for the Three-Axis engine (UTF-8 x position x content).

Covers the honest behaviour verified against real project datasets: exact
full-context recall drives dialogue generation; short-window prefix recall is
only a single-step fallback; generation stops at the end of a memorised answer
instead of hallucinating trailing characters from ambiguous contexts.

See docs/03-technical-architecture/THREE_AXIS_SYSTEM.md.
"""

# =============================================================================
# ANGELA-MATRIX: [L2-L3] [βγδ] [C] [L2]
# =============================================================================

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "backend", "src")),
)

from ai.three_axis.anchor_learner import AnchorLearner  # noqa: E402
from ai.three_axis.three_axis_engine import ThreeAxisEngine  # noqa: E402

# =============================================================================
# ANGELA-MATRIX: [L2-L3] [βγδ] [C] [L2]
# =============================================================================


@pytest.fixture()
def engine() -> ThreeAxisEngine:
    return ThreeAxisEngine(memory_cap_mb=2048)


class TestTraining:
    def test_learn_batch_stats(self, engine):
        stats = engine.learn_batch(["178 + 101=279", "293 - 192=101", "917 * 814=746438"])
        assert stats["samples"] == 3
        assert stats["corpus_bytes"] > 0
        assert stats["positions"] > 0
        assert stats["transitions"] > 0
        assert stats["exact_completions"] > 0
        assert stats["memory_ratio"] <= 1.0
        assert stats["memory_bytes"] > 0

    def test_memory_cap_respected(self, engine):
        engine.learn_batch([f"{i}+{i}={i * 2}" for i in range(500)])
        assert engine.memory_usage_ratio() <= 1.0

    def test_freeze_prevents_training(self, engine):
        engine.freeze()
        engine.learn("2 + 2=4")
        assert engine.corpus_bytes == 0


class TestExactCompletionDialogue:
    def test_process_ends_with_question_mark(self, engine):
        engine.learn_batch(["178 + 101=279"])
        out = engine.process("178 + 101=?")
        assert out == "178 + 101=279"

    def test_generate_stops_at_end_of_answer(self, engine):
        engine.learn_batch(["178 + 101=279"])
        out = engine.generate("178 + 101=")
        assert out == "178 + 101=279"

    def test_multiple_training_samples(self, engine):
        engine.learn_batch(["178 + 101=279", "293 - 192=101", "917 * 814=746438"])
        assert engine.process("178 + 101=?") == "178 + 101=279"
        assert engine.process("293 - 192=?") == "293 - 192=101"
        assert engine.process("917 * 814=?") == "917 * 814=746438"

    def test_ambiguous_short_window_does_not_corrupt_answer(self, engine):
        # "92=101" is a shared truncated context: 293 - 192=101 vs 827 + 192=1019.
        # The full-context exact path must win over the ambiguous short window.
        engine.learn_batch(["293 - 192=101", "827 + 192=1019"])
        assert engine.process("293 - 192=?") == "293 - 192=101"

    def test_no_trailing_garbage(self, engine):
        engine.learn_batch(["917 * 814=746438"])
        out = engine.generate("917 * 814=")
        assert out == "917 * 814=746438"
        assert not out.endswith("=")


class TestInlineUnknown:
    def test_resolve_middle_unknown(self, engine):
        engine.learn_batch(["ab=c", "de=f"])
        out = engine.process("ab=?")
        assert out.startswith("ab=")


class TestPersistence:
    def test_save_load_roundtrip(self, engine, tmp_path):
        engine.learn_batch(["178 + 101=279", "293 - 192=101"])
        path = os.path.join(tmp_path, "checkpoint.json")
        engine.save(path)
        loaded = ThreeAxisEngine(memory_cap_mb=2048)
        assert loaded.load(path)
        assert loaded.process("178 + 101=?") == "178 + 101=279"
        assert loaded.process("293 - 192=?") == "293 - 192=101"

    def test_load_missing_returns_false(self, engine, tmp_path):
        assert engine.load(os.path.join(tmp_path, "nope.json")) is False


class TestPrecedence:
    def test_exact_beats_position_majority(self, engine):
        engine.learn_batch(["999 + 111=1110", "999 + 222=222", "999 + 333=333"])
        assert engine.process("999 + 111=?") == "999 + 111=1110"

    def test_unknown_prompt(self, engine):
        assert engine.process("") == ""
        assert engine.process("no unknown here") == "no unknown here"


class TestUtf8ByteSemantics:
    def test_cjk_char_occupies_three_positions(self, engine):
        # A CJK char is 3 UTF-8 bytes: 中 = [228, 184, 173]. The position axis
        # must therefore count bytes, not Unicode code points.
        engine.learn("中=中")
        # '中' occupies positions 0..2; '=' at position 3; '中' at 4..6.
        assert 228 in engine._position_content[0]
        assert 184 in engine._position_content[1]
        assert 173 in engine._position_content[2]
        # ord('中') = 20013 must NOT appear anywhere (that was the old bug).
        assert 20013 not in {v for cells in engine._position_content.values() for v in cells}

    def test_learn_stats_count_bytes(self, engine):
        engine.learn("中")  # 3 bytes, not 1 char
        assert engine.corpus_bytes == 3

    def test_cjk_query_roundtrip(self, engine):
        engine.learn_batch(["太陽是熱的=true", "天空是藍的=true"])
        assert engine.process("太陽是熱的=?") == "太陽是熱的=true"
        assert engine.process("天空是藍的=?") == "天空是藍的=true"

    def test_cjk_alignment_via_anchor(self, engine):
        # Anchor split happens at the ASCII '=' byte; the CJK regions on both
        # sides must decode cleanly (byte index != char index).
        learner = AnchorLearner()
        learner.learn(["太陽是熱的=true"])
        problem, delimiter, answer = learner.align("太陽是熱的=true")
        assert delimiter == "="
        assert problem == "太陽是熱的"
        assert answer == "true"


class TestRealDatasetTraining:
    def test_trains_on_real_arithmetic_within_cap(self):
        root = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "apps", "backend", "data", "raw_datasets"
            )
        )
        path = os.path.join(root, "arithmetic_train_dataset.json")
        if not os.path.exists(path):
            pytest.skip("real arithmetic dataset not present")
        import json

        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        samples = [f"{x['problem']}={x['answer']}" for x in data[:2000]]
        engine = ThreeAxisEngine(memory_cap_mb=2048)
        stats = engine.learn_batch(samples)
        assert stats["memory_ratio"] <= 1.0
        # A sample that appears verbatim in the training slice must be recalled.
        probe_problem = data[0]["problem"]
        probe_answer = data[0]["answer"]
        out = engine.process(f"{probe_problem}=?")
        assert out == f"{probe_problem}={probe_answer}"


class TestAnchorLearner:
    def test_converges_to_answer_delimiter(self):
        learner = AnchorLearner()
        samples = ["178 + 101=279", "293 - 192=101", "917 * 814=746438", "5 * 5=25"]
        learner.learn(samples)
        assert ord("=") in learner.anchors
        assert learner.converged

    def test_anchor_values_are_utf8_bytes(self):
        # Anchors are UTF-8 byte values (0..255), not Unicode code points:
        # ord("中") = 20013 > 255, so a CJK char can never be an anchor byte.
        assert all(0 <= a <= 255 for a in AnchorLearner.DEFAULT_ANCHORS)
        assert max(AnchorLearner.DEFAULT_ANCHORS) <= 127  # all ASCII single bytes

    def test_align_splits_problem_answer(self):
        learner = AnchorLearner()
        learner.learn(["178 + 101=279", "293 - 192=101"])
        problem, delimiter, answer = learner.align("178 + 101=279")
        assert delimiter == "="
        assert answer == "279"

    def test_normalize_collapses_whitespace(self):
        assert AnchorLearner.normalize("178  +  101") == "178+101"


class TestSlidingAlignment:
    def test_whitespace_variant_aligns(self, engine):
        engine.learn_batch(["178 + 101=279"])
        assert engine.process("178+101=?") == "178+101=279"
        assert engine.process("178  +  101=?") == "178  +  101=279"

    def test_leading_word_aligns(self, engine):
        engine.learn_batch(["178 + 101=279"])
        assert engine.process("what is 178 + 101=?") == "what is 178 + 101=279"

    def test_suffix_unambiguous_lookup(self, engine):
        engine.learn_batch(["178 + 101=279", "827 + 101=928"])
        # Suffix "101" is ambiguous: both problems end with "+101" but map to
        # different answers -> suffix lookup must refuse to fire.
        assert engine._lookup_anchor("101") is None
        # Full key (or a longer unambiguous suffix) still resolves.
        assert engine._lookup_anchor("178 + 101") == "279"
        assert engine._lookup_anchor("827 + 101") == "928"

    def test_anchor_route_reported(self, engine):
        engine.learn_batch(["178 + 101=279"])
        out = engine.process("178+101=?")
        assert engine.last_confidence == pytest.approx(0.95)
        assert engine._last_route == "anchor-aligned"
        assert out == "178+101=279"
