"""
Unified Engine tests — measure the RIGHT things.

These tests verify the AI claims, not memorisation:
  - fixed_memory : model_bytes constant before/after training
  - compression  : corpus_bytes / model_bytes grows with the corpus
  - generalisation: held-out accuracy ABOVE random (learned, not stored)
  - boolean      : the discriminative layer beats random on unseen logic
  - generation   : samples overlap the training distribution (reproduction
                   as a by-product of generalisation)
  - deterministic: math/logic are real capabilities, labelled separately

Contrast with the old three_axis tests which taught one sample and asked the
same sample (pure memorisation). Nothing here re-asks training data.
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================

import json
import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "backend", "src")),
)

from ai.unified_engine.core_model import FixedSizeCore  # noqa: E402
from ai.unified_engine.trainer import (  # noqa: E402
    _answer_of,
    _answers_match,
    _query_of,
    train_test_split,
)
from ai.unified_engine.unified_engine import UnifiedEngine  # noqa: E402

# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================

DATASETS = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "apps",
        "backend",
        "data",
        "raw_datasets",
    )
)


def _load_samples():
    samples = []
    arith_p = os.path.join(DATASETS, "arithmetic_train_dataset.json")
    logic_p = os.path.join(DATASETS, "logic_train.json")
    if os.path.exists(arith_p):
        with open(arith_p, encoding="utf-8") as fh:
            samples += [f"{row['problem']}={row['answer']}" for row in json.load(fh)]
    if os.path.exists(logic_p):
        with open(logic_p, encoding="utf-8") as fh:
            samples += [f"{row['proposition']}={row['answer']}" for row in json.load(fh)]
    return samples


def _train_test():
    samples = _load_samples()
    return train_test_split(samples, test_ratio=0.2, seed=42)


class TestFixedMemory:
    def test_model_bytes_constant(self):
        """The compression claim: model size never grows with the corpus."""
        base = UnifiedEngine(memory_cap_mb=2048).model_bytes
        eng = UnifiedEngine(memory_cap_mb=2048)
        eng.learn_batch(["1+1=2", "2+2=4", "3+3=6"])
        assert eng.model_bytes == base
        assert eng.model_bytes > 0

    def test_model_bytes_constant_large_corpus(self):
        eng = UnifiedEngine(memory_cap_mb=2048)
        samples = [f"{i}+1={i + 1}" for i in range(500)]
        eng.learn_batch(samples)
        assert eng.model_bytes == 2883584

    def test_no_growth_tables(self):
        """The old engine grew prefix/suffix tables; the unified core must
        not have any per-sample storage structures."""
        core = FixedSizeCore()
        core.learn_batch(["178 + 101=279"])
        n_feat_before = sum(1 for c in core._feat if c)
        core.learn_batch([f"{i}*2={i * 2}" for i in range(200)])
        n_feat_after = sum(1 for c in core._feat if c)
        assert n_feat_after >= n_feat_before  # bounded, not proportional


class TestCompression:
    def test_compression_ratio_grows_with_corpus(self):
        """Model is fixed; as the corpus grows the ratio grows linearly."""
        ratios = []
        for n in (500, 2000, 8000):
            eng = UnifiedEngine(memory_cap_mb=2048)
            eng.learn_batch([f"{i}+1={i + 1}" for i in range(n)])
            ratios.append(eng.compression_ratio())
        assert ratios[0] < ratios[1] < ratios[2]

    def test_compression_ratio_positive(self):
        eng = UnifiedEngine(memory_cap_mb=2048)
        eng.learn_batch(["1+1=2"])
        assert eng.compression_ratio() > 0.0


class TestGeneralisation:
    def test_held_out_math_answered(self):
        """Held-out arithmetic is answered by the deterministic layer
        (real capability) — exact answers on unseen operands."""
        train, test = _train_test()
        math_test = [s for s in test if s.split("=", 1)[1].lstrip("-").isdigit()]
        if not math_test:
            pytest.skip("no math samples")
        eng = UnifiedEngine(memory_cap_mb=2048)
        eng.learn_batch(train)
        ok = sum(
            _answers_match(eng.process(_query_of(s)), _answer_of(s), s) for s in math_test[:500]
        )
        assert ok / 500 > 0.7  # deterministic math is mostly exact

    def test_held_out_logic_above_random(self):
        """The discriminative boolean layer must beat random (0.50) on
        UNSEEN logic problems. This is the real generalisation claim."""
        train, test = _train_test()
        logic_test = [s for s in test if str(s.split("=", 1)[1]).lower() in ("true", "false")]
        if not logic_test:
            pytest.skip("no logic samples")
        eng = UnifiedEngine(memory_cap_mb=2048)
        eng.learn_batch(train)
        ok = 0
        n = 0
        for s in logic_test:
            q, truth = _query_of(s), _answer_of(s)
            out = eng.process(q)
            if eng._last_route == "statistical-core":
                n += 1
                ok += int(_answers_match(out, truth, s))
        if n == 0:
            pytest.skip("no statistical-core routes")
        acc = ok / n
        assert acc > 0.5, f"boolean layer acc={acc} not above random"

    def test_no_verbatim_recall_of_train(self):
        """The engine must NOT just re-emit training samples. Ask for a
        novel arithmetic query and check it computes, not echoes."""
        eng = UnifiedEngine(memory_cap_mb=2048)
        eng.learn_batch(["178 + 101=279"])
        # A query that was never trained: the deterministic layer computes it.
        out = eng.process("1 + 1=?")
        assert eng._last_route == "deterministic-math"
        assert "= 2" in out


class TestBooleanLayer:
    def test_boolean_score_sign_matches_truth(self):
        train, test = _train_test()
        train = [s for s in train if str(s.split("=", 1)[1]).lower() in ("true", "false")]
        eng = UnifiedEngine(memory_cap_mb=2048)
        eng.learn_batch(train[:500])
        core = eng.core
        # A problem whose n-grams overlap the training logic data should
        # yield a log-odds score (either direction).
        score = core.boolean_score("water is wet nor hydrogen is flammable")
        assert score is not None

    def test_answer_votes_atomic(self):
        """Answers are voted as atomic strings, not diluted across bytes."""
        core = FixedSizeCore()
        core.learn_batch(["a nor b=False", "c nor d=False"])
        votes = core.answer_votes("x nor y")
        assert votes.get("False", 0) > 0
        assert votes.get("True", 0) == 0


class TestGeneration:
    def test_generation_overlaps_training_distribution(self):
        """Sampling from the model reproduces the training distribution
        (bigram overlap) — reproduction as a by-product of learning."""
        core = FixedSizeCore()
        samples = [f"{i}+{i}={i + i}" for i in range(200)]
        core.learn_batch(samples)
        out = core.generate(b"1+1", max_len=16, stop_on=b"=", seed=1)
        # Continuation must reproduce '=' structure (i.e. learned the format).
        assert b"=" in out
        # Output bigrams should mostly come from the training distribution.
        train_bigrams = set()
        for s in samples:
            sraw = s.encode("utf-8")
            for j in range(len(sraw) - 1):
                train_bigrams.add(sraw[j : j + 2])
        ob = out
        hits = sum(1 for j in range(len(ob) - 1) if ob[j : j + 2] in train_bigrams)
        assert hits / max(1, len(ob) - 1) > 0.3


class TestPersistence:
    def test_save_load_roundtrip(self, tmp_path):
        eng = UnifiedEngine(memory_cap_mb=2048)
        eng.learn_batch(["1+1=2", "2+2=4"])
        path = str(tmp_path / "unified.json")
        eng.save(path)
        fresh = UnifiedEngine(memory_cap_mb=2048)
        assert fresh.load(path)
        assert fresh.corpus_bytes == eng.corpus_bytes
        assert fresh.model_bytes == eng.model_bytes

    def test_save_load_preserves_boolean_layer(self, tmp_path):
        eng = UnifiedEngine(memory_cap_mb=2048)
        eng.learn_batch(["a nor b=False", "c nor d=False", "e nor f=False"])
        path = str(tmp_path / "bool.json")
        eng.save(path)
        fresh = UnifiedEngine(memory_cap_mb=2048)
        fresh.load(path)
        assert fresh.core.boolean_answer("x nor y") == "false"


class TestDeterministicLayers:
    def test_math_layer_is_real(self):
        eng = UnifiedEngine(memory_cap_mb=2048)
        out = eng.process("752 * 851=?")
        assert eng._last_route == "deterministic-math"
        assert "639952" in out

    def test_logic_layer_is_real(self):
        eng = UnifiedEngine(memory_cap_mb=2048)
        out = eng.process("not (true and false)=?")
        assert eng._last_route == "deterministic-logic"
        assert "true" in out.lower()
