"""Contract tests for the architecture-comparison harness (CORE_GAP §十八).

Claims pinned here — each is a property the comparison depends on, not a
restatement of the script:

1. the baseline is sized to the SNN's *parameter count* (within 10%), so a
   0 from it cannot be dismissed as "too small";
2. its greedy decode stops at eos/pad/bos and never exceeds ``max_new``
   tokens (the same budget the instrument hands the SNN);
3. the teacher-forced split reports both buckets and non-empty token counts,
   because "tail_tf high, gate 0" is the evidence used to locate the
   bottleneck;
4. the batch/loss plumbing is the SNN's own (``make_batch_weighted``), so the
   comparison does not secretly measure a second data format.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "compare_al_baselines.py"


def _load(path: Path):
    spec = importlib.util.spec_from_file_location("compare_al_baselines_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def compare():
    return _load(SCRIPT)


@pytest.fixture(scope="module")
def tiny(compare):
    from ai.ed3n.token_snn import TokenConfig, TokenVocab

    texts = ["v=0.26 a=0.17 | 653 + 12", "<al_out> v=0.28 a=0.26"]
    vocab = TokenVocab.build(texts, min_count=1, max_vocab=64)
    cfg = TokenConfig(d_emb=32, d_hidden=64, max_len=48)
    lm = compare.BaselineLM(vocab, cfg, device="cpu", d_model=32, ff=64, layers=1)
    return compare, lm


def test_baseline_matches_snn_capacity(compare):
    """The comparison knobs must produce ~1.24M params on the real config."""
    from ai.ed3n.token_snn import TokenConfig, TokenSNN, TokenVocab

    vocab = TokenVocab.build(["v=0.26 a=0.17"], min_count=1, max_vocab=80)
    cfg = TokenConfig(d_emb=96, d_hidden=1024, max_len=384)
    snn = TokenSNN(vocab, cfg, device="cpu")
    snn_params = sum(p.numel() for p in snn.net.parameters())
    net = compare._transformer(torch, vocab.pad_id, cfg, 256, 512, 2)(len(vocab))
    params = sum(p.numel() for p in net.parameters())
    assert abs(params - snn_params) / snn_params < 0.10, (params, snn_params)


def test_generate_respects_budget_and_stops(tiny):
    _, lm = tiny
    out = lm.generate("v=0.26 a=0.17 | 653 + 12", max_new=6)
    assert isinstance(out, str)
    # six ids at most; decode drops specials, so compare on ids
    ids = lm.vocab.encode(out)
    assert len(ids) <= 6


def test_split_tf_accuracy_covers_both_buckets(tiny):
    _, lm = tiny
    pairs = [
        ("v=0.26 a=0.17 | 653 + 12", "665\n<al_out> v=0.28 a=0.26"),
        ("v=0.10 a=0.40 | 12 + 7", "19\n<al_out> v=0.11 a=0.38"),
    ]
    split = lm.split_tf_accuracy(pairs)
    assert set(split) == {"response_tf", "tail_tf", "response_tokens", "tail_tokens"}
    assert split["response_tokens"] > 0
    assert split["tail_tokens"] > 0
    assert 0.0 <= split["response_tf"] <= 1.0
    assert 0.0 <= split["tail_tf"] <= 1.0


def test_batches_come_from_the_snn_encoder(tiny):
    """One data format only: the baseline reuses the SNN's batch builder."""
    _, lm = tiny
    from ai.ed3n.token_snn import TokenSNN

    assert isinstance(lm.encoder, TokenSNN)
    assert lm.encoder.vocab is lm.vocab
