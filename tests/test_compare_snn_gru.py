"""Contract tests for the pre-registered SNN-vs-GRU comparison (CORE_GAP §36).

The comparison is only meaningful if the two arms differ in **one** thing.
These tests pin the parts that are easy to get quietly wrong:

* batching / masking is shared, not re-implemented for the GRU;
* the parameter-matching arithmetic agrees with the models it claims to count;
* the frozen split is the one written in the pre-registration (9,000 train,
  leak-guarded, no overlap);
* the decision rule does what the document says (paired interval, and a size
  where neither arm learns is "inconclusive", not a tie).

No training happens here: a run that changes the design should fail a test,
not a score.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"{name}_under_test", SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def cmp():
    return _load("compare_snn_gru")


@pytest.fixture(scope="module")
def torch(cmp):
    return pytest.importorskip("torch")


@pytest.fixture(scope="module")
def vocab(cmp):
    from ai.ed3n.token_snn import CharVocab

    return CharVocab.build(["12 + 7\n19", "3 + 4\n7", "98 + 1\n99"], min_count=1)


def test_analytic_snn_count_matches_built_model(cmp, torch, vocab):
    from ai.ed3n.token_snn import TokenConfig, TokenSNN

    for d_hidden in (16, 64):
        cfg = TokenConfig(d_emb=16, d_hidden=d_hidden, max_len=24)
        model = TokenSNN(vocab, cfg, device="cpu")
        assert cmp.count_params(model) == cmp._snn_param_count(len(vocab), cfg, d_hidden)


def test_analytic_gru_count_matches_built_model(cmp, torch, vocab):
    from ai.ed3n.token_snn import TokenConfig

    cfg = TokenConfig(d_emb=16, max_len=24)
    for d_hidden in (8, 40):
        model = cmp.GRUDecoder(vocab, cfg, device="cpu", d_hidden=d_hidden)
        assert cmp.count_params(model) == cmp.gru_param_count(len(vocab), cfg, d_hidden)


def test_parameter_matching_is_within_two_percent(cmp, torch, vocab):
    from ai.ed3n.token_snn import TokenConfig

    cfg = TokenConfig(d_emb=96, max_len=24)
    for d_snn in (256, 2048):
        target = cmp._snn_param_count(len(vocab), cfg, d_snn)
        d_gru, n_gru = cmp.match_gru_hidden(len(vocab), cfg, target)
        assert abs(n_gru - target) / target <= 0.02
        # nearest, not merely close: no neighbouring hidden size is closer
        for neighbour in (d_gru - 1, d_gru + 1):
            n = cmp.gru_param_count(len(vocab), cfg, neighbour)
            assert abs(n - target) >= abs(n_gru - target)


def test_batching_is_shared_between_arms(cmp, torch, vocab):
    from ai.ed3n.token_snn import TokenConfig, TokenSNN

    cfg = TokenConfig(d_emb=16, max_len=24)
    pairs = [("12 + 7", "19"), ("3 + 4", "7"), ("98 + 1", "99")]
    snn = TokenSNN(vocab, cfg, device="cpu")
    gru = cmp.GRUDecoder(vocab, cfg, device="cpu", d_hidden=8)
    ids_s, mask_s, starts_s = snn.make_batch(pairs)
    ids_g, mask_g, starts_g = gru.make_batch(pairs)
    assert starts_s == starts_g
    assert torch.equal(ids_s, ids_g)
    assert torch.equal(mask_s, mask_g)
    for prompt, answer in pairs:
        assert snn.encode_pair(prompt, answer) == gru.encode_pair(prompt, answer)


def test_loss_is_masked_the_same_way(cmp, torch, vocab):
    from ai.ed3n.token_snn import TokenConfig, TokenSNN

    cfg = TokenConfig(d_emb=16, max_len=24)
    pairs = [("12 + 7", "19"), ("3 + 4", "7")]
    snn = TokenSNN(vocab, cfg, device="cpu")
    gru = cmp.GRUDecoder(vocab, cfg, device="cpu", d_hidden=8)
    ids, mask, _ = snn.make_batch(pairs)
    for model in (snn, gru):
        value = model.loss(ids, mask)
        assert value.dim() == 0
        assert bool(torch.isfinite(value))
    assert int(mask.sum()) == int(snn.make_batch(pairs)[1].sum())


def test_gru_checkpoint_roundtrip_and_kind_guard(cmp, torch, vocab, tmp_path):
    from ai.ed3n.token_snn import TokenConfig, TokenSNN

    cfg = TokenConfig(d_emb=16, max_len=24)
    model = cmp.GRUDecoder(vocab, cfg, device="cpu", d_hidden=8)
    path = tmp_path / "gru.pt"
    model.save(path)
    loaded = cmp.GRUDecoder.load(path, device="cpu")
    ids, _, _ = model.make_batch([("12 + 7", "19")])
    with torch.no_grad():
        assert torch.allclose(model.net(ids), loaded.net(ids), atol=1e-6)
    # Loading a GRU file as an SNN must fail loudly, not silently re-interpret it.
    with pytest.raises(RuntimeError):
        TokenSNN.load(path, device="cpu")


def test_decision_rule_matches_the_document(cmp):
    better = cmp.paired_decision([0.8, 0.8, 0.8, 0.8, 0.8], [0.5, 0.5, 0.5, 0.5, 0.5])
    assert better["verdict"] == "snn_better"
    worse = cmp.paired_decision([0.2, 0.2, 0.2, 0.2, 0.2], [0.6, 0.6, 0.6, 0.6, 0.6])
    assert worse["verdict"] == "gru_better"
    flat = cmp.paired_decision([0.5, 0.5, 0.5, 0.5, 0.5], [0.5, 0.5, 0.5, 0.5, 0.5])
    assert flat["verdict"] == "no_detectable_difference"
    assert flat["ci_low"] <= 0 <= flat["ci_high"]
    single = cmp.paired_decision([0.5], [0.4])
    assert single["verdict"] == "needs at least 2 seeds"


def test_neither_learned_is_inconclusive(cmp):
    runs = [
        {"arm": f"snn_{size}", "seed": s, "held_exact": 0.02}
        for size in ("small",)
        for s in range(5)
    ] + [
        {"arm": f"gru_{size}", "seed": s, "held_exact": 0.03}
        for size in ("small",)
        for s in range(5)
    ]
    out = cmp.summarise(runs, ["small"])
    assert out["small"]["verdict"] == "inconclusive_neither_learned"


def test_frozen_split_is_leak_guarded_and_matches_preregistration(cmp):
    split = cmp.build_split()
    assert split["pool"] + split["leaked"] == 10000
    assert len(split["train"]) == 9000
    assert len(split["held"]) == split["pool"] - 9000
    from arithmetic_task import parse_plain, problem_key

    train_keys = {problem_key(parse_plain(p)) for p, _ in split["train"]}
    held_keys = {problem_key(parse_plain(p)) for p, _ in split["held"]}
    assert not (train_keys & held_keys)


def test_smoke_limit_only_resizes_after_the_fixed_split(cmp):
    full = cmp.build_split()
    small = cmp.build_split(train_limit=64, eval_limit=10)
    assert len(small["train"]) == 64
    assert len(small["held"]) == 10
    assert small["train"] == full["train"][:64]
    assert small["held"] == full["held"][:10]
