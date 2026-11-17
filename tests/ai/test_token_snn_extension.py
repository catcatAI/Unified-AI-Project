# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""Extending a run must cost only the new epochs, not change the answer.

``token_snn.train_on(start_epoch=..., opt_state=..., opt_state_out=...)`` exists
so a finished arm can be lengthened without retraining what was already paid
for. That is only worth having if the extended run is the same run, so the test
compares weights directly: two epochs in one call versus one epoch plus one
epoch resumed from the saved optimizer state.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))


@pytest.fixture()
def setup():
    from ai.ed3n.token_snn import CharVocab, TokenConfig, TokenSNN

    vocab = CharVocab.build(["1+1=2", "2+2=4", "3+3=6", "4+4=8", "5+5=10", "6+6=12"], min_count=1)
    config = TokenConfig(d_emb=8, d_hidden=8, max_len=16, layers=1)
    pairs = [("1+1?", "2"), ("2+2?", "4"), ("3+3?", "6"), ("4+4?", "8")]
    return TokenSNN, vocab, config, pairs


def _run(cls, vocab, config, pairs, epochs, **kwargs):
    model = cls(vocab, config, device="cpu")
    model.train_on(pairs, epochs=epochs, batch_size=2, lr=1e-3, seed=0, guard=False, **kwargs)
    return model


def test_one_run_and_a_resumed_run_are_bitwise_equal(setup):
    import torch

    TokenSNN, vocab, config, pairs = setup
    torch.manual_seed(0)
    whole = _run(TokenSNN, vocab, config, pairs, 2)

    torch.manual_seed(0)
    carry: dict = {}
    part = _run(TokenSNN, vocab, config, pairs, 1, opt_state_out=carry)
    part.train_on(
        pairs,
        epochs=1,
        batch_size=2,
        lr=1e-3,
        seed=0,
        guard=False,
        start_epoch=1,
        opt_state=carry,
    )

    assert carry, "the optimizer state was not captured"
    left, right = whole.net.state_dict(), part.net.state_dict()
    assert set(left) == set(right)
    for key in left:
        assert torch.equal(left[key], right[key]), key


def test_the_optimizer_state_survives_a_save_and_load(setup, tmp_path):
    import torch

    TokenSNN, vocab, config, pairs = setup
    torch.manual_seed(0)
    whole = _run(TokenSNN, vocab, config, pairs, 2)

    torch.manual_seed(0)
    carry: dict = {}
    part = _run(TokenSNN, vocab, config, pairs, 1, opt_state_out=carry)
    path = tmp_path / "opt.pt"
    torch.save(carry, path)
    loaded = torch.load(path, weights_only=True)

    part.train_on(
        pairs,
        epochs=1,
        batch_size=2,
        lr=1e-3,
        seed=0,
        guard=False,
        start_epoch=1,
        opt_state=loaded,
    )
    left, right = whole.net.state_dict(), part.net.state_dict()
    for key in left:
        assert torch.equal(left[key], right[key]), key


def test_start_epoch_continues_the_batch_order(setup):
    TokenSNN, vocab, config, pairs = setup
    calls = []

    model = TokenSNN(vocab, config, device="cpu")
    model.train_on(
        pairs,
        epochs=1,
        batch_size=2,
        lr=1e-3,
        seed=0,
        guard=False,
        start_epoch=7,
        on_epoch=lambda row: calls.append(int(row["epoch"])),
    )
    assert calls == [7]
