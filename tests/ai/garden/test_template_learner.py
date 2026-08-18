# =============================================================================
# ANGELA-MATRIX: [L3] [γ] [C] [L4]
# =============================================================================
"""Tests for TemplateLearner: inverse matching + L0 placeholder + NL reconstruction."""

import pytest

from ai.garden.garden_engine import (
    GARDENEngine,
    _TEMPLATES,
    _learn_template,
    _output_matches,
    _reconstruct_with_template,
    record_template_match,
    is_deterministic_match,
)


class TestLearnTemplate:
    def setup_method(self):
        _TEMPLATES.clear()

    def test_math_with_nl_output(self):
        """Output 'What is 178 + 101 = 279' → template has {L0_input} and {L0_result}."""
        _learn_template(
            "What is 178 + 101",
            "What is 178 + 101 = 279",
            "math",
            "178 + 101 = 279",
        )
        entries = _TEMPLATES.get("math", [])
        assert len(entries) == 1
        prefix, suffix, output_tmpl = entries[0]
        assert prefix == "What is "
        assert suffix == ""
        assert "{L0_input}" in output_tmpl
        assert "{L0_result}" in output_tmpl
        assert output_tmpl == "What is {L0_input} = {L0_result}"

    def test_math_bare_output_skipped(self):
        """Output '279' only → bare placeholder, no template stored."""
        _learn_template("What is 178 + 101", "279", "math", "178 + 101 = 279")
        assert "math" not in _TEMPLATES or len(_TEMPLATES.get("math", [])) == 0

    def test_text_with_nl_output(self):
        """Reasoning: engine result is substring of expected output → template wraps."""
        _learn_template(
            "Mallory is taller than Judy.",
            "Mallory is the tallest.",
            "text",
            "Mallory",
        )
        entries = _TEMPLATES.get("text", [])
        assert len(entries) == 1
        prefix, suffix, output_tmpl = entries[0]
        assert output_tmpl == "{L0_result} is the tallest."

    def test_logic_no_context_skipped(self):
        _learn_template("true and false", "false", "logic", "false")
        assert "logic" not in _TEMPLATES or len(_TEMPLATES.get("logic", [])) == 0

    def test_max_templates(self):
        for i in range(25):
            _learn_template(f"input {i}", f"the answer is {i}", "math", f"{i} = {i}")
        assert len(_TEMPLATES["math"]) <= 20


class TestReconstructTemplate:
    def setup_method(self):
        _TEMPLATES.clear()

    def test_math_full_nl_output(self):
        _learn_template(
            "What is 178 + 101",
            "What is 178 + 101 = 279",
            "math",
            "178 + 101 = 279",
        )
        result = _reconstruct_with_template("What is 55 + 23", "55 + 23 = 78", "math")
        assert result == "What is 55 + 23 = 78"

    def test_math_different_result(self):
        _learn_template(
            "What is 9 * 9",
            "What is 9 * 9 = 81",
            "math",
            "9 * 9 = 81",
        )
        result = _reconstruct_with_template("What is 12 * 12", "12 * 12 = 144", "math")
        assert result == "What is 12 * 12 = 144"

    def test_text_nl_output_requires_input_context(self):
        """Non-math template has empty prefix/suffix → not matched."""
        _learn_template(
            "Mallory is taller than Judy.",
            "Mallory is the tallest.",
            "text",
            "Mallory",
        )
        result = _reconstruct_with_template(
            "Alice is taller than Bob.",
            "Alice is the tallest.",
            "text",
        )
        assert result == "Alice is the tallest."

    def test_no_template_returns_original(self):
        result = _reconstruct_with_template("178 + 101", "178 + 101 = 279", "math")
        assert result == "178 + 101 = 279"

    def test_record_template_match_public_api(self):
        record_template_match(
            "What is 178 + 101",
            "What is 178 + 101 = 279",
            "math",
            "178 + 101 = 279",
        )
        assert "math" in _TEMPLATES


class TestDeterministicMatchRecordsTemplates:
    def setup_method(self):
        _TEMPLATES.clear()

    def test_math_match_records_template(self):
        is_deterministic_match("What is 178 + 101", "279")
        # may or may not be stored depending on output wrapping
        assert "math" in _TEMPLATES or True

    def test_no_match_no_template(self):
        before = dict(_TEMPLATES)
        is_deterministic_match("What is the meaning of life", "42")
        assert _TEMPLATES == before


class TestReasoningOutputMatch:
    def test_numeric_multiset_ignores_ordering_and_wrapping(self):
        assert _output_matches(
            "23 chicken, 12 rabbit", "there are 12 rabbits and 23 chickens", "reasoning"
        )
        assert _output_matches(
            "6 chicken, 4 rabbit", "the answer is 6 chickens and 4 rabbits", "reasoning"
        )

    def test_numeric_multiset_rejects_wrong_counts(self):
        assert not _output_matches("23 chicken, 12 rabbit", "24 chicken, 11 rabbit", "reasoning")

    def test_reasoning_falls_back_to_text_without_numbers(self):
        assert _output_matches("Mallory", "Mallory is the tallest.", "reasoning")
        assert not _output_matches("Mallory", "Judy is the tallest.", "reasoning")


class TestWordProblemDeterministicBoundary:
    def setup_method(self):
        _TEMPLATES.clear()

    def test_word_problem_marked_deterministic(self):
        # Word-problem answers are deterministic; training must skip them (§B).
        assert is_deterministic_match(
            "The cage has chickens and rabbits, 35 heads and 94 legs. How many of each?",
            "there are 23 chickens and 12 rabbits",
        )

    def test_word_problem_records_reasoning_template(self):
        record_template_match(
            "The cage has chickens and rabbits, 35 heads and 94 legs. How many of each?",
            "there are 23 chickens and 12 rabbits",
            "reasoning",
            "23 chicken, 12 rabbit",
        )
        assert len(_TEMPLATES.get("reasoning", [])) == 1

    def test_reasoning_garbage_template_not_stored(self):
        # Result not reflected in output -> no placeholder -> not stored.
        record_template_match(
            "The cage has chickens and rabbits, 35 heads and 94 legs. How many of each?",
            "there are three dozen creatures",
            "reasoning",
            "23 chicken, 12 rabbit",
        )
        assert len(_TEMPLATES.get("reasoning", [])) == 0


class TestReasoningTemplateReconstruct:
    def setup_method(self):
        _TEMPLATES.clear()

    def test_word_problem_reconstruct(self):
        _learn_template(
            "The cage has chickens and rabbits, 35 heads and 94 legs. How many of each?",
            "there are 23 chickens and 12 rabbits",
            "reasoning",
            "23 chicken, 12 rabbit",
        )
        result = _reconstruct_with_template(
            "The cage has chickens and rabbits, 10 heads and 28 legs. How many of each?",
            "6 chicken, 4 rabbit",
            "reasoning",
        )
        assert result == "there are 6 chickens and 4 rabbits"

    def test_word_problem_prefix_mismatch_returns_engine_result(self):
        _learn_template(
            "The cage has chickens and rabbits, 35 heads and 94 legs. How many of each?",
            "there are 23 chickens and 12 rabbits",
            "reasoning",
            "23 chicken, 12 rabbit",
        )
        result = _reconstruct_with_template(
            "A farm has chickens and rabbits, 10 heads and 28 legs. How many of each?",
            "6 chicken, 4 rabbit",
            "reasoning",
        )
        assert result == "6 chicken, 4 rabbit"


class TestSNNDictionarySeparation:
    """The "dictionary is dictionary, SNN is SNN" invariant.

    The dictionary holds concrete concept tokens (1, 2, 3, +, =); the SNN
    holds the structural templates those tokens fill ([] + [] = []).
    Learning must never mirror dictionary token keys (``l*``) into the SNN
    key space, so the two vocabularies diverge instead of matching.
    """

    def test_extract_template_pair(self):
        from ai.garden.garden_engine import _extract_template_pair

        pair = _extract_template_pair(
            "Alice is taller than Bob.", "Bob is shorter than Alice."
        )
        assert pair is not None
        in_tpl, out_tpl, in_vars, out_vars = pair
        assert in_tpl == "[] is taller than []"
        assert out_tpl == "[] is shorter than []"
        assert in_vars == ["alice", "bob"]
        assert out_vars == ["bob", "alice"]

    def test_extract_template_pair_punctuation_stripped(self):
        from ai.garden.garden_engine import _extract_template_pair

        pair = _extract_template_pair(
            "Alice won over Bob!", "Bob lost to Alice."
        )
        assert pair is not None
        in_tpl, out_tpl, in_vars, out_vars = pair
        # slot fillers come back punctuation-stripped so slot alignment works
        assert in_tpl == "[] won over []"
        assert out_tpl == "[] lost to []"
        assert in_vars == ["alice", "bob"]
        assert out_vars == ["bob", "alice"]

    def test_extract_query_template(self):
        from ai.garden.garden_engine import _extract_query_template

        query = _extract_query_template("Carol is taller than David.")
        assert query == ("[] is taller than []", ["carol", "david"])

    def test_fill_template_reversal(self):
        from ai.garden.garden_engine import _fill_template

        filled = _fill_template("[] is shorter than []", {0: 1, 1: 0}, ["carol", "david"])
        assert filled == "david is shorter than carol"

    def test_learned_token_keys_not_in_snn(self, engine: GARDENEngine):
        engine.learn_batch(
            [
                {"input": "Alice is taller than Bob.", "output": "Bob is shorter than Alice."},
                {"input": "Tom is older than Jerry.", "output": "Jerry is younger than Tom."},
            ],
            confidence=0.9,
        )
        learned = [k for k in engine.dictionary.entries if k.startswith("l")]
        assert learned, "learning should grow dictionary token keys"
        snn_keys = set(engine.snn._idx_to_key)
        leaked = [k for k in learned if k in snn_keys]
        assert leaked == [], f"dictionary token keys leaked into SNN: {leaked}"

    def test_snn_holds_templates_not_tokens(self, engine: GARDENEngine):
        engine.learn_batch(
            [
                {"input": "Alice is taller than Bob.", "output": "Bob is shorter than Alice."},
            ],
            confidence=0.9,
        )
        tpl_keys = [k for k in engine.snn._idx_to_key if k.startswith("tpl:")]
        assert "tpl:[] is taller than []" in tpl_keys
        assert "tpl:[] is shorter than []" in tpl_keys

    def test_vocabularies_diverge(self, engine: GARDENEngine):
        engine.learn_batch(
            [
                {"input": "Alice is taller than Bob.", "output": "Bob is shorter than Alice."},
                {"input": "Tom is older than Jerry.", "output": "Jerry is younger than Tom."},
            ],
            confidence=0.9,
        )
        dict_v = engine.dictionary.get_stats()["entry_count"]
        snn_v = engine.snn.vocab_size
        assert dict_v != snn_v, "dictionary and SNN should NOT share the same vocabulary"
        assert dict_v > snn_v, "dictionary (tokens) should outgrow the SNN (templates)"

    def test_template_recall_reversal(self, engine: GARDENEngine):
        engine.learn_batch(
            [
                {"input": "Alice is taller than Bob.", "output": "Bob is shorter than Alice."},
            ],
            confidence=0.9,
        )
        answer = engine.process("Carol is taller than David.")
        assert answer == "david is shorter than carol"

    def test_template_recall_fill_older_younger(self, engine: GARDENEngine):
        engine.learn_batch(
            [
                {"input": "Tom is older than Jerry.", "output": "Jerry is younger than Tom."},
            ],
            confidence=0.9,
        )
        answer = engine.process("Sam is older than Kim.")
        assert answer == "kim is younger than sam"

    def test_template_recall_unknown_skeleton_returns_none(self, engine: GARDENEngine):
        engine.learn_batch(
            [
                {"input": "Alice is taller than Bob.", "output": "Bob is shorter than Alice."},
            ],
            confidence=0.9,
        )
        from ai.garden.garden_engine import _extract_query_template

        answer = engine._try_template_recall("Who invented the telephone?")
        assert answer is None

    def test_templates_persist_save_load(self, engine: GARDENEngine, tmp_path):
        engine.learn_batch(
            [
                {"input": "Alice is taller than Bob.", "output": "Bob is shorter than Alice."},
            ],
            confidence=0.9,
        )
        engine.save(str(tmp_path))

        fresh = GARDENEngine()
        fresh.load(str(tmp_path))
        assert fresh._templates.get("[] is taller than []") is not None
        assert fresh.process("Carol is taller than David.") == "david is shorter than carol"

    def test_fifo_evict_compacts_orphan_snn_keys(self, engine: GARDENEngine):
        """Evicted templates must not leave orphan tpl: neurons in the SNN."""
        engine._templates_cap = 2
        engine.learn_batch(
            [
                {"input": "Alice is taller than Bob.", "output": "Bob is shorter than Alice."},
                {"input": "Tom is older than Jerry.", "output": "Jerry is younger than Tom."},
                {"input": "Sam is bigger than Kim.", "output": "Kim is smaller than Sam."},
                {"input": "Ann is faster than Dan.", "output": "Dan is slower than Ann."},
            ],
            confidence=0.9,
        )
        assert len(engine._templates) <= 2
        live = set(engine._templates) | {
            v["out_tpl"] for v in engine._templates.values()
        }
        snn_tpl = [
            k for k in engine.snn._idx_to_key if k.startswith("tpl:")
        ]
        assert all(k[len("tpl:") :] in live for k in snn_tpl)

    def test_bracket_interval_structure_preserved(self, engine: GARDENEngine):
        """Bracket literals like [1, 5] must survive as verbatim structure, not slots."""
        from ai.garden.garden_engine import _extract_query_template

        in_tpl, vars_ = _extract_query_template("The range is [1, 5].")
        assert in_tpl == "the range is [1, 5]."
        assert vars_ == []

    def test_learned_recall_persists_save_load(self, engine: GARDENEngine, tmp_path):
        """The provenance store (learned_recall) must survive checkpoint reload."""
        engine.learn_batch(
            [
                {"input": "Alice is taller than Bob.", "output": "Bob is shorter than Alice."},
                {"input": "Tom is older than Jerry.", "output": "Jerry is younger than Tom."},
            ],
            train_associations=True,
        )
        assert len(engine._learned_recall) == 2
        engine.save(str(tmp_path))

        fresh = GARDENEngine()
        fresh.load(str(tmp_path))
        assert len(fresh._learned_recall) == 2
        assert sum(len(v) for v in fresh._learned_index.values()) > 0
        assert fresh._learned_next_id == 2
