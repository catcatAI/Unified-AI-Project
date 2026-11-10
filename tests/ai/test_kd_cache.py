"""Contract tests for the distillation cache and its loss.

Three properties are load-bearing and each is pinned here:

* the cache is **bound to a vocabulary** — a mismatch must be refused, not
  silently train the wrong atoms;
* positions are **hidden-state positions** (``start + k - 1``), never teacher
  token indices;
* the loss is ``-sum_a q_a log p_a`` under the model's **full** softmax, with
  ``q`` left unnormalised. A softmax over the target atoms alone would let the
  loss fall while the model predicts nothing.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import torch
from ai.ed3n.kd_cache import FORMAT_VERSION, KdCache, vocab_fingerprint
from ai.ed3n.kd_targets import KdTargets

VOCAB = ["<pad>", "<bos>", "<eos>", "<unk>", "ab", " c", "d"]


def _target(atom_ids, probs, mapped=None) -> KdTargets:
    atom_ids = np.asarray(atom_ids, dtype=np.int64)
    probs = np.asarray(probs, dtype=np.float64)
    return KdTargets(
        atom_ids=atom_ids,
        probs=probs / probs.sum() if probs.sum() else probs,
        mapped_mass=float(probs.sum()) if mapped is None else mapped,
        topk_mass=float(probs.sum()),
        coarse=0,
        dropped=0,
        top_k=64,
    )


def _build(rows=None, vocab=VOCAB) -> KdCache:
    rows = (
        rows
        if rows is not None
        else [
            ([1, 4, 5, 6, 2], 1, [(0, _target([4], [1.0])), (1, _target([5], [1.0]))]),
            ([1, 4, 5, 6, 2], 1, []),
        ]
    )
    return KdCache.build(rows, vocab, meta={"teacher": "fake", "top_k": 64})


class _FakeModel:
    """Only the two members the cache touches."""

    def __init__(self, ids, start=1):
        self._ids = list(ids)
        self._start = int(start)

    def _encode(self, prompt, answer):
        return list(self._ids), self._start, len(self._ids)


class _BiasHead(torch.nn.Module):
    """``head(x) == bias`` for every input, so the expected loss is hand-computable."""

    def __init__(self, bias) -> None:
        super().__init__()
        self.bias = torch.nn.Parameter(torch.tensor(bias, dtype=torch.float32))

    def forward(self, x):
        return self.bias.expand(x.shape[0], -1)


def _net(bias) -> torch.nn.Module:
    module = torch.nn.Module()
    module.head = _BiasHead(bias)
    return module


# ---------------------------------------------------------------------------
# structure and persistence
# ---------------------------------------------------------------------------
def test_build_records_rows_positions_and_targets() -> None:
    cache = _build()
    assert cache.n_rows == 2
    first = cache.row(0)
    assert first is not None
    assert list(first.ids) == [1, 4, 5, 6, 2]
    assert first.start == 1
    assert list(first.positions) == [0, 1]
    assert list(first.atom_ids) == [4, 5]
    assert first.probs.tolist() == pytest.approx([1.0, 1.0])


def test_the_cache_keeps_the_teacher_coverage_as_target_mass() -> None:
    """A position that retained 60% of the teacher's mass must stay 0.6.

    ``KdTargets.probs`` is renormalised to 1; the cache scales it by
    ``mapped_mass``. Storing 1.0 would give a mostly-dropped position the same
    pull as a clean one.
    """
    cache = _build([([1, 4, 5, 6, 2], 1, [(0, _target([4, 5], [0.6, 0.4], mapped=0.6))])])
    row = cache.row(0)
    assert row is not None
    assert float(row.probs.sum()) == pytest.approx(0.6, abs=2e-3)  # float16
    assert cache.stats(sample=10)["mapped_mass"] == pytest.approx(0.6, abs=2e-3)


def test_a_row_without_targets_is_still_indexable() -> None:
    cache = _build()
    second = cache.row(1)
    assert second is not None
    assert len(second) == 0
    assert second.atom_ids.size == 0


def test_roundtrip_preserves_every_row(tmp_path) -> None:
    cache = _build()
    path = cache.save(tmp_path / "kd.npz")
    loaded = KdCache.load(path)
    assert loaded.n_rows == cache.n_rows
    assert loaded.meta["format"] == FORMAT_VERSION
    for index in range(cache.n_rows):
        before, after = cache.row(index), loaded.row(index)
        assert before is not None and after is not None
        assert list(before.ids) == list(after.ids)
        assert before.start == after.start
        assert list(before.positions) == list(after.positions)
        assert list(before.atom_ids) == list(after.atom_ids)
        assert after.probs.tolist() == pytest.approx(before.probs.tolist(), abs=1e-3)


def test_meta_records_the_vocabulary_fingerprint() -> None:
    cache = _build()
    assert cache.meta["atoms"] == len(VOCAB)
    assert cache.meta["vocab_sha256"] == vocab_fingerprint(VOCAB)
    assert cache.meta["teacher"] == "fake"


def test_out_of_range_row_is_none() -> None:
    cache = _build()
    assert cache.row(-1) is None
    assert cache.row(2) is None


# ---------------------------------------------------------------------------
# vocabulary binding
# ---------------------------------------------------------------------------
def test_matching_vocabulary_is_accepted() -> None:
    assert _build().matches_vocab(VOCAB)


def test_same_size_different_vocabulary_is_rejected() -> None:
    other = list(VOCAB)
    other[4], other[5] = other[5], other[4]
    assert len(other) == len(VOCAB)
    assert not _build().matches_vocab(other)


def test_require_vocab_names_the_problem() -> None:
    with pytest.raises(ValueError, match="different vocabulary"):
        _build().require_vocab(VOCAB[:-1])


def test_validate_rejects_a_broken_pointer() -> None:
    cache = _build()
    cache._pos_ptr[0] = 1
    with pytest.raises(ValueError, match="pos_ptr"):
        cache.validate()


def test_validate_accepts_a_position_per_atom_layout() -> None:
    """``atom_ptr`` is per *position*, so its length is not ``rows + 1``.

    A first cut of ``validate`` assumed it was per row and refused every cache
    whose rows held more than one target — which is nearly all of them.
    """
    cache = _build(
        [
            ([1, 4, 5, 2], 1, [(0, _target([4], [1.0])), (1, _target([5, 6], [0.5, 0.5]))]),
        ]
    )
    assert len(cache._atom_ptr) == 3, "two positions -> three pointers"
    cache.validate()


def test_validate_rejects_a_truncated_atom_pointer() -> None:
    cache = _build()
    cache._atom_ptr = cache._atom_ptr[:-1]
    with pytest.raises(ValueError, match="atom_ptr"):
        cache.validate()


# ---------------------------------------------------------------------------
# the loss
# ---------------------------------------------------------------------------
def _hidden(batch_size=1, steps=4, width=3) -> torch.Tensor:
    torch.manual_seed(0)
    return torch.randn(batch_size, steps, width)


def test_loss_skips_positions_past_the_row() -> None:
    cache = _build([([1, 4, 2], 1, [(9, _target([4], [1.0]))])])
    assert cache.batch_loss(_net([0.0] * len(VOCAB)), _hidden(), [0]) is None


def test_loss_of_an_empty_row_is_none() -> None:
    cache = _build([([1, 4, 2], 1, [])])
    assert cache.batch_loss(_net([0.0] * len(VOCAB)), _hidden(), [0]) is None


def test_loss_equals_the_cross_entropy_of_a_certain_target() -> None:
    bias = [0.0, 1.0, 2.0, 3.0, 0.5, -1.0, 0.25]
    cache = _build([([1, 4, 2], 1, [(0, _target([4], [1.0]))])])
    loss = cache.batch_loss(_net(bias), _hidden(), [0])
    p = [math.exp(b) for b in bias]
    expected = -math.log(p[4] / sum(p))
    assert float(loss) == pytest.approx(expected, rel=1e-6)


def test_loss_of_a_two_atom_target_is_their_mean_cross_entropy() -> None:
    bias = [0.0, 1.0, 2.0, 3.0, 0.5, -1.0, 0.25]
    cache = _build([([1, 4, 2], 1, [(0, _target([4, 5], [0.5, 0.5]))])])
    loss = float(cache.batch_loss(_net(bias), _hidden(), [0]))
    p = [math.exp(b) for b in bias]
    total = sum(p)
    expected = -(0.5 * math.log(p[4] / total) + 0.5 * math.log(p[5] / total))
    assert loss == pytest.approx(expected, rel=1e-6)


def test_loss_scales_with_the_teacher_coverage() -> None:
    """A position whose target kept half the teacher's mass pulls half as hard.

    Without the ``mapped_mass`` factor the loss would be the same for a target
    that retained 50% of the teacher's distribution and one that retained 100%.
    """
    bias = [0.0, 1.0, 2.0, 3.0, 0.5, -1.0, 0.25]
    full = _build([([1, 4, 2], 1, [(0, _target([4, 5], [0.5, 0.5], mapped=1.0))])])
    half = _build([([1, 4, 2], 1, [(0, _target([4, 5], [0.5, 0.5], mapped=0.5))])])
    net = _net(bias)
    a = float(full.batch_loss(net, _hidden(), [0]))
    b = float(half.batch_loss(net, _hidden(), [0]))
    assert b == pytest.approx(0.5 * a, rel=1e-3)


def test_loss_uses_the_full_softmax_not_the_target_subset() -> None:
    """A high-probability *non-target* atom must lower the target's probability."""
    cache = _build([([1, 4, 2], 1, [(0, _target([4], [1.0]))])])
    peaked_elsewhere = [10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    loss = float(cache.batch_loss(_net(peaked_elsewhere), _hidden(), [0]))
    p = [math.exp(b) for b in peaked_elsewhere]
    assert loss == pytest.approx(-math.log(p[4] / sum(p)), rel=1e-6)
    # If the subset were renormalised this would be 0.0 regardless of the rest.
    assert loss > 9.0


def test_loss_mixes_rows_in_one_batch() -> None:
    cache = _build(
        [
            ([1, 4, 2], 1, [(0, _target([4], [1.0]))]),
            ([1, 5, 2], 1, [(1, _target([5], [1.0]))]),
        ]
    )
    hidden = _hidden(batch_size=2, steps=4)
    bias = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
    loss = cache.batch_loss(_net(bias), hidden, [0, 1])
    total = 4 * 1.0 + 3 * math.e
    expected = -math.log(math.e / total)
    assert float(loss) == pytest.approx(expected, rel=1e-6)


def test_loss_trains_the_head() -> None:
    cache = _build([([1, 4, 2], 1, [(0, _target([4, 5], [0.5, 0.5]))])])
    net = torch.nn.Module()
    net.head = torch.nn.Linear(3, len(VOCAB))
    loss = cache.batch_loss(net, _hidden(), [0])
    assert loss.requires_grad
    loss.backward()
    assert net.head.weight.grad is not None
    assert float(net.head.weight.grad.abs().sum()) > 0.0


def test_stats_report_coverage_per_position() -> None:
    stats = _build().stats(sample=10)
    assert stats["sampled_rows"] == 2
    assert stats["positions_per_row"] == pytest.approx(1.0)
    assert stats["atoms_per_position"] == pytest.approx(1.0)
    assert stats["mapped_mass"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# integrity
# ---------------------------------------------------------------------------
def test_verify_rows_accepts_a_matching_model() -> None:
    cache = _build()
    pairs = [("q", "ab"), ("q", "ab")]
    assert cache.verify_rows(pairs, _FakeModel([1, 4, 5, 6, 2], start=1)) == []


def test_verify_rows_reports_a_changed_encoding() -> None:
    cache = _build()
    problems = cache.verify_rows([("q", "ab"), ("q", "ab")], _FakeModel([1, 4, 5], start=1))
    assert problems and "ids" in problems[0]


def test_verify_rows_reports_a_moved_answer_start() -> None:
    cache = _build()
    problems = cache.verify_rows([("q", "ab"), ("q", "ab")], _FakeModel([1, 4, 5, 6, 2], start=2))
    assert problems and "start" in problems[0]


def test_cache_rows_line_up_with_the_real_model_that_will_train() -> None:
    """The join that matters: cache row *i* must be pairs row *i*.

    ``build_kd_cache.py`` builds over ``fits(read_pairs(...))`` and the trainer
    trains on exactly that filtered list; this pins the arithmetic in
    ``encode_ids`` (which both use) rather than a hand-written expectation.
    """
    from ai.ed3n.token_snn import TokenConfig, TokenSNN, TokenVocab, encode_ids

    pairs = [("2+3", "5"), ("capital of France", "Paris")]
    vocab = TokenVocab.build([p + "\n" + a for p, a in pairs], min_count=1, max_vocab=1000)
    cfg = TokenConfig(d_emb=8, d_hidden=16, max_len=32)
    model = TokenSNN(vocab, cfg, device="cpu")
    rows = []
    for prompt, answer in pairs:
        ids, start, _cut = encode_ids(vocab, prompt, answer, cfg.max_len)
        rows.append((ids, start, []))
    cache = KdCache.build(rows, vocab.itos)
    assert cache.n_rows == len(pairs)
    assert cache.verify_rows(pairs, model) == []
    # An off-by-one in the row order is exactly what verify_rows exists to catch.
    assert cache.verify_rows(list(reversed(pairs)), model) != []
