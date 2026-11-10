# -*- coding: utf-8 -*-
"""train_token_snn.py 的評分契約：訓練結果不得被計分方式誤判成 0。

重點不是「模型很弱」，而是「模型答對時要被算對」。答案尾端的
``<al_out>`` 是量測區塊（六個數值），把它算進 exact 會讓一個答對題目的
模型仍然被記成 0。
"""

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = REPO_ROOT / "scripts" / "train_token_snn.py"

pytest.importorskip("torch")

from ai.ed3n.token_snn import AL_OUT_MARK, CharVocab, TokenConfig, TokenSNN  # noqa: E402


def load_tool():
    sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
    spec = importlib.util.spec_from_file_location("train_token_snn", TOOL_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


tool = load_tool()


class TestResponseOnly:
    def test_state_block_is_not_part_of_the_answer(self):
        answer = f"18{AL_OUT_MARK} v=0.2 a=0.3"
        assert tool._response_only(answer) == "18"

    def test_answer_without_a_block_is_unchanged(self):
        assert tool._response_only("  carbon dioxide  ") == "carbon dioxide"

    def test_block_only_answer_has_no_response(self):
        assert tool._response_only(f"{AL_OUT_MARK} v=0.2") == ""


class TestExactMatch:
    """A model that answers correctly but scrambles the state block must count."""

    @pytest.fixture(scope="class")
    def model(self):
        vocab = CharVocab.build(["18", "9", "42", " 1", "6"], min_count=1)
        m = TokenSNN(vocab, TokenConfig(d_emb=16, d_hidden=16, max_len=32), device="cpu")
        # Force the model to always answer "18" (whatever the prompt).
        m.generate = lambda prompt, max_new=8, temperature=0.0: "18"  # type: ignore[method-assign]
        return m

    def test_correct_response_with_a_wrong_block_counts(self, model):
        pairs = [("what is 9 + 9", f"18{AL_OUT_MARK} v=0.9 a=0.9")]
        stats = tool.exact_match(model, pairs, sample=10)
        assert stats["exact"] == 1.0
        assert stats["exact_full"] == 0.0

    def test_wrong_response_is_still_wrong(self, model):
        pairs = [("what is 9 + 9", f"19{AL_OUT_MARK} v=0.9")]
        stats = tool.exact_match(model, pairs, sample=10)
        assert stats["exact"] == 0.0

    def test_full_match_is_reported_separately(self):
        vocab = CharVocab.build(["18", "9"], min_count=1)
        m = TokenSNN(vocab, TokenConfig(d_emb=16, d_hidden=16, max_len=32), device="cpu")
        m.generate = lambda prompt, max_new=8, temperature=0.0: "18"  # type: ignore[method-assign]
        stats = tool.exact_match(m, [("q", "18")], sample=10)
        assert stats["exact"] == 1.0
        assert stats["exact_full"] == 1.0

    def test_a_non_positive_sample_never_reports_a_fake_zero(self, model):
        """``sample=0`` must not mean "measured nothing, reported 0.0".

        The old expression sampled an empty list and returned exact=0.0, which
        is indistinguishable from a model that answered everything wrong.
        """
        stats = tool.exact_match(model, [("q", "18")], sample=0)
        assert stats["n"] == 1
        assert stats["exact"] == 1.0


class TestKdCacheWiring:
    """A distillation cache is bound to a vocabulary *and* to a row order.

    Both bindings fail silently if unchecked — the run still trains, the loss
    still falls, and the targets belong to other prompts. These are source
    contracts because the alternative is launching a 1.5B teacher in a unit
    test; the arithmetic itself is pinned in ``tests/ai/test_kd_cache.py``.
    """

    def test_the_trainer_accepts_a_cache_and_a_weight(self):
        source = TOOL_PATH.read_text(encoding="utf-8")
        assert '"--kd-cache"' in source
        assert '"--kd-weight"' in source

    def test_a_mismatched_cache_is_refused_before_training(self):
        source = TOOL_PATH.read_text(encoding="utf-8")
        assert "cache.require_vocab(" in source
        assert "cache.n_rows != len(train_fit)" in source
        assert "cache.verify_rows(train_fit, model)" in source

    def test_the_soft_target_reaches_the_epoch_loop(self):
        source = TOOL_PATH.read_text(encoding="utf-8")
        assert "kd=kd" in source

    def test_the_teacher_coverage_is_reported(self):
        """``q`` is scaled by the mapped mass, so the report must say what that was."""
        source = TOOL_PATH.read_text(encoding="utf-8")
        assert '"teacher_mapped_mass": cache.meta.get("teacher_mapped_mass")' in source


class TestSeeding:
    """A paired comparison needs the *initialisation* fixed, not just the order.

    ``train_on`` already reseeds for batch order, but it runs after the
    parameters exist; ``torch.initial_seed()`` differs in every process, so
    without a seed before construction two arms differ by an initialisation
    larger than the effect being measured.
    """

    def test_seed_is_accepted_and_recorded(self):
        source = TOOL_PATH.read_text(encoding="utf-8")
        assert '"--seed"' in source
        assert '"seed": int(args.seed)' in source

    def test_the_model_is_seeded_before_it_is_built(self):
        source = TOOL_PATH.read_text(encoding="utf-8")
        seed_at = source.index("torch.manual_seed(int(args.seed))")
        build_at = source.index("model = TokenSNN(vocab, cfg, device=device)")
        assert seed_at < build_at, "seeding after construction cannot fix the init"

    def test_the_same_seed_reaches_the_batch_order(self):
        source = TOOL_PATH.read_text(encoding="utf-8")
        assert "seed=int(args.seed)," in source
