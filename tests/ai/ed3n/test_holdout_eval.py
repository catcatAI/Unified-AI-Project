"""
A5 holdout-evaluation regression tests.

Guards the contract that (1) ED3NTrainer.evaluate_holdout is pure inference
(no dictionary growth, no weight updates) and (2) the training pipeline's
holdout helpers are deterministic and never fabricate an accuracy constant.
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [γ] [A] [L2]
# =============================================================================

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apps", "backend", "src")
)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from ai.ed3n.ed3n_engine import ED3NEngine
from ai.ed3n.ed3n_trainer import ED3NTrainer
from ai.ed3n.training_types import TrainingExample

import scripts.train_pipeline as tp


def _example(input_keys, output_keys, confidence=0.8):
    return TrainingExample(
        input_text=" ".join(input_keys),
        expected_output=" ".join(output_keys),
        input_keys=list(input_keys),
        output_keys=list(output_keys),
        relation_pairs=[],
        confidence=confidence,
        metadata={},
    )


class TestEvaluateHoldout:
    """ED3NTrainer.evaluate_holdout — pure-inference holdout scoring."""

    def _engine(self):
        e = ED3NEngine()
        e.load_presets()
        e._external_dicts_loaded = True
        return e

    def test_evaluate_holdout_does_not_grow_dictionary(self):
        """Holdout scoring must never call _grow_missing_keys (A5 contract)."""
        engine = self._engine()
        trainer = ED3NTrainer(engine)
        before = len(engine.dictionary.entries)
        # Unknown keys in input/output — encode would miss, training would grow.
        examples = [_example(["zzz_unseen_a"], ["zzz_unseen_b"])]
        trainer.evaluate_holdout(examples)
        assert (
            len(engine.dictionary.entries) == before
        ), "evaluate_holdout grew the dictionary — it must be pure inference"

    def test_evaluate_holdout_does_not_adjust_weights(self):
        """No Hebbian updates during holdout scoring."""
        engine = self._engine()
        trainer = ED3NTrainer(engine)
        key = next(iter(engine.dictionary.entries))
        group = engine.network.groups.get("mapping")
        snapshot = {k: dict(n.connections) for k, n in (group.neurons.items() if group else [])}
        trainer.evaluate_holdout([_example([key], [key])])
        now = {k: dict(n.connections) for k, n in (group.neurons.items() if group else [])}
        assert now == snapshot

    def test_accuracy_one_when_output_keys_are_input_keys(self):
        """Self-mapping examples score 1.0 (input keys self-activate at 1.0)."""
        engine = self._engine()
        trainer = ED3NTrainer(engine)
        key = next(iter(engine.dictionary.entries))
        metrics = trainer.evaluate_holdout([_example([key], [key])])
        assert metrics.accuracy == 1.0
        assert metrics.phase == "holdout"
        assert metrics.samples == 1

    def test_accuracy_zero_when_disjoint_unconnected(self):
        """Unknown (never-activated) keys score 0.0 — no neuron exists to fire."""
        engine = self._engine()
        trainer = ED3NTrainer(engine)
        metrics = trainer.evaluate_holdout([_example(["zzz_no_such_a"], ["zzz_no_such_b"])])
        assert metrics.accuracy == 0.0

    def test_empty_examples_return_zero_metrics(self):
        engine = self._engine()
        trainer = ED3NTrainer(engine)
        metrics = trainer.evaluate_holdout([])
        assert metrics.accuracy == 0.0
        assert metrics.samples == 0
        assert metrics.phase == "holdout"


class TestHoldoutSplit:
    """train_pipeline._holdout_split — deterministic index-based split."""

    def test_split_is_deterministic(self):
        items = [{"i": i} for i in range(25)]
        t1, h1 = tp._holdout_split(items, stride=10, cap=500)
        t2, h2 = tp._holdout_split(items, stride=10, cap=500)
        assert t1 == t2
        assert h1 == h2

    def test_every_stride_item_is_held_out(self):
        items = list(range(25))
        train, holdout = tp._holdout_split(items, stride=10, cap=500)
        assert holdout == [0, 10, 20]
        assert len(train) == 22
        # train + holdout reconstitute the input, order preserved
        assert sorted(train + holdout) == items

    def test_cap_limits_holdout(self):
        items = list(range(25))
        _, holdout = tp._holdout_split(items, stride=10, cap=2)
        assert holdout == [0, 10]

    def test_empty_input(self):
        train, holdout = tp._holdout_split([], stride=10, cap=500)
        assert train == []
        assert holdout == []


class _FakeGardenEngine:
    """process() stub mapping input -> canned response for eval testing."""

    def __init__(self, mapping):
        self._mapping = mapping

    def process(self, text, context=None):
        return self._mapping.get(text, "")


class TestEvalGardenHoldout:
    """train_pipeline._eval_garden_holdout — measured, contains-match scoring."""

    def test_perfect_match_scores_one(self):
        engine = _FakeGardenEngine({"a": "alpha", "b": "beta"})
        samples = [{"input": "a", "output": "alpha"}, {"input": "b", "output": "beta"}]
        assert tp._eval_garden_holdout(engine, samples) == 1.0

    def test_no_match_scores_zero(self):
        engine = _FakeGardenEngine({"a": "wrong"})
        samples = [{"input": "a", "output": "alpha"}]
        assert tp._eval_garden_holdout(engine, samples) == 0.0

    def test_partial_match_scores_half(self):
        engine = _FakeGardenEngine({"a": "the alpha value", "b": "nope"})
        samples = [
            {"input": "a", "output": "alpha"},
            {"input": "b", "output": "beta"},
        ]
        assert tp._eval_garden_holdout(engine, samples) == 0.5

    def test_contains_match_is_case_insensitive(self):
        engine = _FakeGardenEngine({"q": "The Answer Is PARIS"})
        samples = [{"input": "q", "output": "paris"}]
        assert tp._eval_garden_holdout(engine, samples) == 1.0

    def test_empty_holdout_returns_zero_not_constant(self):
        """Empty slice must return 0.0 (measured) — never a fabricated 0.7."""
        assert tp._eval_garden_holdout(_FakeGardenEngine({}), []) == 0.0

    def test_process_exception_counts_as_miss(self):
        class _Boom:
            def process(self, text, context=None):
                raise RuntimeError("engine exploded")

        samples = [{"input": "a", "output": "alpha"}]
        assert tp._eval_garden_holdout(_Boom(), samples) == 0.0

    def test_empty_output_skipped_from_denominator(self):
        engine = _FakeGardenEngine({"a": "alpha"})
        samples = [{"input": "a", "output": "alpha"}, {"input": "b", "output": ""}]
        assert tp._eval_garden_holdout(engine, samples) == 1.0
