# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""Contract tests for widening a trained token-SNN without losing its function.

The point of the widening is arithmetic, so the tests pin the arithmetic: the
child's logits equal the parent's up to float32 summation order, the hidden
axis is the only axis that grows, and the copy-symmetry breaker stays bounded.
No checkpoint from ``data/`` is loaded; the models here are tiny and built in
the test process.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPAND = REPO_ROOT / "scripts" / "expand_token_snn.py"
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))


def _load():
    spec = importlib.util.spec_from_file_location("expand_token_snn_under_test", EXPAND)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["expand_token_snn_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def expand():
    return _load()


@pytest.fixture()
def tiny(expand):
    from ai.ed3n.token_snn import CharVocab, TokenConfig, TokenSNN

    vocab = CharVocab.build(["hello world", "abc abc", "the quick brown fox"], min_count=1)
    config = TokenConfig(d_emb=8, d_hidden=8, max_len=16, layers=1)
    model = TokenSNN(vocab, config, device="cpu")
    model.net.eval()
    return model


def logits(model, ids):
    import torch

    with torch.no_grad():
        return model.net(ids)


def test_probe_ids_are_deterministic(expand):
    a = expand.probe_ids(31, seed=7, batch=2, seq=5)
    b = expand.probe_ids(31, seed=7, batch=2, seq=5)
    c = expand.probe_ids(31, seed=8, batch=2, seq=5)
    assert (a == b).all()
    assert not (a == c).all()


@pytest.mark.parametrize("factor", [2, 3])
def test_widening_preserves_the_parent_function(expand, tiny, factor):
    ids = expand.probe_ids(len(tiny.vocab), seed=3, batch=2, seq=6)
    child = expand.expand_model(tiny, factor=factor)
    measured = expand.preservation(tiny, child, ids)
    assert measured["shapes_equal"]
    assert measured["relative"] <= expand.TOLERANCE_EXACT, measured
    assert (logits(child, ids) - logits(tiny, ids)).abs().max() < 1e-4


def test_only_the_hidden_axis_grows(expand, tiny):
    child = expand.expand_model(tiny, factor=4)
    parent_state = tiny.net.state_dict()
    child_state = child.net.state_dict()
    assert child.config.d_hidden == tiny.config.d_hidden * 4
    assert child.config.d_emb == tiny.config.d_emb
    assert child.config.layers == tiny.config.layers
    assert (child_state["embed.weight"] == parent_state["embed.weight"]).all()
    assert child_state["w_in.0.weight"].shape == (
        tiny.config.d_hidden * 4,
        tiny.config.d_emb,
    )
    assert child_state["w_rec.0.weight"].shape == (
        tiny.config.d_hidden * 4,
        tiny.config.d_hidden * 4,
    )
    assert child_state["head.weight"].shape[1] == tiny.config.d_hidden * 4
    assert child_state["head.weight"].shape[0] == len(tiny.vocab)


def test_noise_breaks_copies_but_stays_bounded(expand, tiny):
    ids = expand.probe_ids(len(tiny.vocab), seed=5, batch=2, seq=6)
    child = expand.expand_model(tiny, factor=2, noise=1e-3, seed=11)
    measured = expand.preservation(tiny, child, ids)
    assert measured["relative"] > 0.0
    assert measured["relative"] <= expand.TOLERANCE_NOISY, measured
    parent_state = tiny.net.state_dict()
    state = child.net.state_dict()
    hidden = tiny.config.d_hidden
    # The parent's rows are untouched; only the new copies were perturbed.
    assert (state["w_in.0.weight"][:hidden] == parent_state["w_in.0.weight"]).all()
    assert not (state["w_in.0.weight"][hidden:] == parent_state["w_in.0.weight"]).all()


def test_noise_is_reproducible(expand, tiny):
    first = expand.expand_model(tiny, factor=2, noise=1e-3, seed=11)
    second = expand.expand_model(tiny, factor=2, noise=1e-3, seed=11)
    a = first.net.state_dict()["w_in.0.weight"]
    b = second.net.state_dict()["w_in.0.weight"]
    assert (a == b).all()


def test_multilayer_widening_preserves_the_parent_function(expand, tiny):
    from ai.ed3n.token_snn import TokenConfig, TokenSNN

    config = TokenConfig(d_emb=8, d_hidden=8, max_len=16, layers=2)
    model = TokenSNN(tiny.vocab, config, device="cpu")
    model.net.eval()
    ids = expand.probe_ids(len(model.vocab), seed=13, batch=2, seq=6)
    child = expand.expand_model(model, factor=2)
    measured = expand.preservation(model, child, ids)
    assert measured["shapes_equal"]
    assert measured["relative"] <= expand.TOLERANCE_EXACT, measured
    state = child.net.state_dict()
    hidden = config.d_hidden
    assert state["w_in.1.weight"].shape == (hidden * 2, hidden * 2)
    assert state["w_skip.1.weight"].shape == (hidden * 2, config.d_emb)


def test_factor_below_two_is_refused(expand, tiny):
    with pytest.raises(ValueError):
        expand.expand_state_dict(tiny.net.state_dict(), tiny.config, len(tiny.vocab), factor=1)


def test_weights_digest_is_order_independent(expand, tiny):
    state = tiny.net.state_dict()
    reversed_order = {key: state[key] for key in reversed(list(state))}
    assert expand.weights_digest(state) == expand.weights_digest(reversed_order)


def test_cli_roundtrip_and_check(expand, tiny, tmp_path):
    parent_path = tmp_path / "parent.pt"
    child_path = tmp_path / "child.pt"
    report_path = tmp_path / "report.json"
    tiny.save(parent_path)
    report = expand.run(
        checkpoint=parent_path,
        out=child_path,
        factor=2,
        noise=0.0,
        seed=0,
        batch=2,
        seq=6,
        device="cpu",
    )
    report_path.write_text(json.dumps(report), encoding="utf-8")
    ok, message = expand.check(report_path)
    assert ok, message
    assert report["preservation"]["pass"]
    assert report["child"]["params"] > report["parent"]["params"]


def test_check_refuses_a_tampered_child(expand, tiny, tmp_path):
    parent_path = tmp_path / "parent.pt"
    child_path = tmp_path / "child.pt"
    report_path = tmp_path / "report.json"
    tiny.save(parent_path)
    report = expand.run(
        checkpoint=parent_path,
        out=child_path,
        factor=2,
        noise=0.0,
        seed=0,
        batch=2,
        seq=6,
        device="cpu",
    )
    report_path.write_text(json.dumps(report), encoding="utf-8")
    import torch

    tampered = expand.TokenSNN.load(child_path, device="cpu")
    with torch.no_grad():
        tampered.net.head.weight += 1.0
    tampered.save(child_path)
    ok, _ = expand.check(report_path)
    assert not ok
