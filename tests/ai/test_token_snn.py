"""The token-level SNN decoder: representation and objective that actually learn."""

from __future__ import annotations

import json

import pytest

pytest.importorskip("torch")

from ai.ed3n.token_snn import (  # noqa: E402
    AL_OUT_MARK,
    BOS,
    EOS,
    UNK,
    CharVocab,
    TokenConfig,
    TokenSNN,
    TokenVocab,
    tokenize,
)


@pytest.fixture(scope="module")
def vocab() -> CharVocab:
    return CharVocab.build(["abc def", "bcd efg"], min_count=1)


def test_vocab_roundtrip(vocab):
    ids = vocab.encode("abc")
    assert vocab.decode(ids) == "abc"
    assert vocab.decode([vocab.bos_id, *ids, vocab.eos_id]) == "abc"
    assert vocab.decode([vocab.eos_id, *ids]) == ""


def test_unknown_character_does_not_crash(vocab):
    ids = vocab.encode("aZ")
    assert ids[1] == vocab.stoi[UNK]


def test_encode_pair_marks_where_the_answer_starts(vocab):
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=32))
    ids, start = model.encode_pair("abc", "def")
    assert ids[0] == vocab.bos_id
    assert vocab.decode(ids[1:start]).startswith("abc")
    assert vocab.decode(ids[start:]) == "def"


def test_batch_mask_covers_answer_and_eos(vocab):
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=32))
    ids, mask, starts = model.make_batch([("abc", "de")])
    assert ids.shape == mask.shape
    assert mask.sum().item() == len(ids[0]) - starts[0]
    assert ids[0, -1] == vocab.eos_id


def test_copy_task_is_learnable():
    """If the architecture cannot copy, the rest of the measurements are noise."""
    words = ["alpha", "bravo", "cobalt", "delta", "ember"]
    pairs = [(w, w) for w in words] * 20
    word_vocab = CharVocab.build([p + "\n" + a for p, a in pairs], min_count=1)
    model = TokenSNN(word_vocab, TokenConfig(d_emb=32, d_hidden=64, max_len=24))
    model.train_on(pairs, epochs=60, batch_size=8, lr=5e-3)
    hits = sum(model.generate(w, 8).strip() == w for w in words)
    assert hits >= 4, f"only {hits}/5 copied"


def test_on_epoch_callback_runs_once_per_epoch(vocab):
    seen = []
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=16))
    model.train_on([("abc", "de")], epochs=3, batch_size=1, on_epoch=seen.append)
    assert [row["epoch"] for row in seen] == [0, 1, 2]
    assert all("loss" in row for row in seen)


def test_save_load_roundtrip(tmp_path, vocab):
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=16, max_len=24))
    model.train_on([("abc", "def")], epochs=1, batch_size=1)
    path = tmp_path / "m.pt"
    model.save(path)
    restored = TokenSNN.load(path)
    assert restored.generate("abc", 5) == model.generate("abc", 5)
    assert restored.vocab.itos == model.vocab.itos


def test_checkpoint_carries_the_config(tmp_path, vocab):
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=16, max_len=24))
    model.save(tmp_path / "m.pt")
    restored = TokenSNN.load(tmp_path / "m.pt")
    assert restored.config.d_hidden == 16
    assert json.loads(json.dumps(restored.config.to_dict()))


def test_generation_stops_at_eos(vocab):
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=16))
    assert EOS in vocab.itos and BOS in vocab.itos
    out = model.generate("abc", max_new=4)
    assert len(out) <= 4


def test_configured_beta_is_the_effective_leak():
    """A configured 0.9 must leak 0.9, not sigmoid(0.9)=0.711.

    The parameter used to be stored raw and pushed through sigmoid() at
    use, silently shortening every memory horizon (0.9 kept 35% of the
    state after 10 steps; the effective 0.711 kept 3%).
    """
    import torch

    for beta in (0.9, 0.711, 0.5):
        model = TokenSNN(vocab_for_beta(), TokenConfig(d_emb=8, d_hidden=8, beta=beta))
        effective = float(torch.sigmoid(model.net.beta))
        assert effective == pytest.approx(beta, abs=1e-4)


def vocab_for_beta() -> CharVocab:
    return CharVocab.build(["abc"], min_count=1)


def test_membrane_readout_and_depth_roundtrip(tmp_path, vocab):
    """SLAYER-style readout and stacked layers must train and reload."""
    cfg = TokenConfig(d_emb=8, d_hidden=16, max_len=24, readout="membrane", layers=2)
    model = TokenSNN(vocab, cfg)
    model.train_on([("abc", "def")], epochs=1, batch_size=1)
    ids, mask, _ = model.make_batch([("abc", "def")])
    assert model.net(ids).shape == (1, ids.shape[1], len(vocab))
    path = tmp_path / "m.pt"
    model.save(path)
    restored = TokenSNN.load(path)
    assert restored.config.readout == "membrane"
    assert restored.config.layers == 2
    assert restored.generate("abc", 5) == model.generate("abc", 5)


def test_timesteps_keep_output_shape_and_roundtrip(tmp_path, vocab):
    """K timesteps per token must not change the (batch, steps, vocab) shape."""
    cfg = TokenConfig(d_emb=8, d_hidden=16, max_len=24, readout="membrane", timesteps=4)
    model = TokenSNN(vocab, cfg)
    ids, mask, _ = model.make_batch([("abc", "de")])
    assert model.net(ids).shape == (1, ids.shape[1], len(vocab))
    model.train_on([("abc", "de")], epochs=1, batch_size=1)
    path = tmp_path / "k4.pt"
    model.save(path)
    restored = TokenSNN.load(path)
    assert restored.config.timesteps == 4
    assert restored.generate("abc", 4) == model.generate("abc", 4)


def test_unknown_readout_is_rejected(vocab):
    with pytest.raises(ValueError, match="readout"):
        TokenSNN(vocab, TokenConfig(readout="graded"))


def test_tokenize_roundtrips_and_splits_numbers():
    """Join(tokenize(s)) == s; a word absorbs its leading space; digits split."""
    text = "What is 214.0 + 7% of 3?"
    atoms = tokenize(text)
    assert "".join(atoms) == text
    assert "1" in atoms and "4" in atoms  # digits, so unseen values compose
    assert " i" in atoms  # leading-space atom (GPT-2 style)
    assert "What" in atoms


def test_tokenize_never_drops_a_character():
    r"""The catch-all must be a separate alternative.

    It used to be concatenated onto ``\s+`` (``\s+.`` with no fallback), so a
    trailing whitespace run and chars like ``_`` matched nothing and vanished:
    join(tokenize("abc ")) != "abc ".
    """
    for text in ("abc ", "a_b", "answer: 42  \n", "  leading", "café"):
        assert "".join(tokenize(text)) == text, text
    assert tokenize("a_b") == ["a", "_", "b"]


def test_token_vocab_roundtrip_and_unk():
    vocab = TokenVocab.build(["the cat sat", "the dog sat"], min_count=1)
    ids = vocab.encode("the cat")
    assert vocab.decode(ids) == "the cat"
    # an unseen word becomes <unk> instead of crashing
    assert vocab.stoi[UNK] in vocab.encode("the zebra")
    assert vocab.pad_id >= 0 and vocab.eos_id >= 0 and vocab.bos_id >= 0


def test_token_vocab_shortens_long_questions():
    """The whole point of the token kind: long prose collapses >2x.

    74-char questions land at ~16-25 atoms, back inside the band the
    learnability diagnosis measured as trainable (<=18 steps)."""
    q = "What is the force on a 5 kg mass with acceleration 2 m/s2?"
    token_ids = TokenVocab.build([q], min_count=1).encode(q)
    char_ids = CharVocab.build([q], min_count=1).encode(q)
    assert len(token_ids) * 2 < len(char_ids)


def test_token_vocab_save_load_dispatches(tmp_path):
    """load() must rebuild the token kind, not fall back to characters."""
    vocab = TokenVocab.build(["alpha beta gamma"], min_count=1)
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=16))
    path = tmp_path / "t.pt"
    model.save(path)
    restored = TokenSNN.load(path)
    assert isinstance(restored.vocab, TokenVocab)
    assert restored.generate("alpha", 4) == model.generate("alpha", 4)


def test_numeric_atoms_make_a_contract_value_one_id():
    """CORE_GAP §十八: the graded block's numbers must be single atoms.

    Counts, not vibes: `v=0.26` is 5 ids with the historical atomisation
    (v, =, 0, ., 2, 6 -> with the leading-space word: 4) and must be 3 here
    (v, =, 0.26). That is the difference between digit-carrying arithmetic and
    a 201-way choice over the contract's own grid.
    """
    plain = tokenize("v=0.26")
    atoms = tokenize("v=0.26", numeric_atoms=True)
    assert atoms[-1] == "0.26"
    assert len(atoms) < len(plain)
    assert "".join(atoms) == "v=0.26"


def test_numeric_atoms_keep_the_alphabet_closed_and_roundtripping():
    """The value alphabet is seeded, bounded, and cannot be truncated."""
    # a gold value that never appeared in the training text is still emittable
    vocab = TokenVocab.build(["v=0.26 a=0.17"], min_count=1, max_vocab=4096, numeric_atoms=True)
    for value in ("-1.00", "0.00", "0.99", "1.00", "2.00"):
        assert value in vocab.stoi, value
    assert "0.26" in vocab.stoi
    assert vocab.decode(vocab.encode("v=0.26")) == "v=0.26"
    # a budget smaller than the alphabet drops *words*, never value atoms
    tiny = TokenVocab.build(["v=0.26"], min_count=1, max_vocab=4, numeric_atoms=True)
    assert len(tiny) >= 202
    assert "0.26" in tiny.stoi and "0.00" in tiny.stoi
    # the closed alphabet does not leak into other numbers
    assert tokenize("0.268", numeric_atoms=True) == list("0.268")
    assert tokenize("12.50", numeric_atoms=True) == list("12.50")
    assert tokenize("7.1944", numeric_atoms=True) == list("7.1944")


def test_numeric_atoms_can_target_the_three_decimal_grid():
    """A 3-dp corpus needs its own grid, or the flag silently does nothing.

    Round-7's 3-dp corpus writes ``0.261``; the 2-dp candidate pattern needs
    exactly two decimals and no third digit, so it never matched and every
    value was still emitted digit by digit (measured block accuracy 0.721 with
    ``--numeric-atoms`` against 0.723 without).
    """
    atoms = tokenize("v=0.261", numeric_atoms=True, value_decimals=3)
    assert atoms[-1] == "0.261"
    assert "".join(atoms) == "v=0.261"
    assert tokenize("0.261", numeric_atoms=True) == list("0.261")
    vocab = TokenVocab.build(["v=0.261"], min_count=1, numeric_atoms=True, value_decimals=3)
    for value in ("-1.000", "0.000", "0.261", "1.000"):
        assert value in vocab.stoi, value
    assert vocab.decode(vocab.encode("v=0.261")) == "v=0.261"
    with pytest.raises(ValueError):
        tokenize("0.261", numeric_atoms=True, value_decimals=4)


def test_value_decimals_survive_save_load(tmp_path):
    """The grid is part of the representation: a checkpoint must keep it."""
    vocab = TokenVocab.build(["v=0.261"], min_count=1, numeric_atoms=True, value_decimals=3)
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=24))
    path = tmp_path / "d3.pt"
    model.save(path)
    restored = TokenSNN.load(path)
    assert restored.vocab.value_decimals == 3
    assert restored.vocab.encode("0.261") == vocab.encode("0.261")
    assert TokenVocab.build(["x"], min_count=1).value_decimals == 2


def test_numeric_atom_mode_survives_save_load(tmp_path):
    """A checkpoint must remember the representation it was trained under."""
    vocab = TokenVocab.build(["v=0.26 a=0.17"], min_count=1, numeric_atoms=True)
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=24))
    path = tmp_path / "na.pt"
    model.save(path)
    restored = TokenSNN.load(path)
    assert restored.vocab.numeric_atoms is True
    assert restored.vocab.encode("v=0.26") == vocab.encode("v=0.26")
    assert TokenVocab.build(["x"], min_count=1).numeric_atoms is False


def test_membrane_readout_is_normalized():
    """LayerNorm on the membrane path: logits must not saturate with length.

    Without it the membrane accumulates (leak 0.9 -> ~10x steady-state gain)
    and the initial loss explodes with sequence length (18 chars: 19; 74: 174).
    """
    import torch

    vocab = TokenVocab.build(["abcdefgh" * 8], min_count=1)
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=16, max_len=96))
    ids = torch.tensor([vocab.encode("abcdefgh" * 8)], device=model.device)
    with torch.no_grad():
        long_logits = model.net(ids)
        short_ids = torch.tensor([vocab.encode("abcd")], device=model.device)
        short_logits = model.net(short_ids)
    assert torch.isfinite(long_logits).all()
    assert float(long_logits.abs().max()) < 40.0
    assert float(short_logits.abs().max()) < 40.0


def test_tf_accuracy_is_a_sane_diagnostic(vocab):
    """Teacher-forced accuracy must count only answer tokens and lie in [0, 1]."""
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=24))
    stat = model.tf_accuracy([("abc", "def"), ("bcd", "efg")])
    assert 0.0 <= stat["tf_acc"] <= 1.0
    assert stat["tokens"] > 0
    # untrained model: roughly chance; must not be reported as skill
    assert stat["tokens"] == sum(len(a) + 1 for _, a in [("abc", "def"), ("bcd", "efg")])


def _al_vocab():
    return CharVocab.build([f"abc def {AL_OUT_MARK} v=0.1"], min_count=1)


def test_response_end_splits_response_from_state_block():
    """_encode must locate the <al_out> marker, and be a no-op without it."""
    answer = f"def {AL_OUT_MARK} v=0.1"
    model = TokenSNN(_al_vocab(), TokenConfig(d_emb=8, d_hidden=8, max_len=64))
    ids, start, cut = model._encode("abc", answer)
    assert start < cut < len(ids)
    assert model.vocab.decode(ids[cut:]).startswith(AL_OUT_MARK)

    ids2, start2, cut2 = model._encode("abc", "def")
    # no marker: the whole answer is response, so the split falls on the eos
    assert cut2 == len(ids2) - 1
    assert start2 < cut2


def test_tail_weight_only_downweights_the_state_block(vocab):
    answer = f"def {AL_OUT_MARK} v=0.1"
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=64))
    _, start, cut = model._encode("abc", answer)
    _, _, _, weights = model.make_batch_weighted([("abc", answer)], tail_weight=0.25)
    assert float(weights[0, start]) == 1.0
    assert float(weights[0, cut - 1]) == 1.0
    assert float(weights[0, cut]) == 0.25

    # marker-free answer: nothing gets down-weighted (the eos ends the response)
    _, _, _, plain = model.make_batch_weighted([("abc", "def")], tail_weight=0.25)
    assert float(plain.min()) == 1.0


def test_weighted_loss_keeps_the_unweighted_scale(vocab):
    """A tail weight must not silently rescale the learning rate."""
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=64))
    answer = f"def {AL_OUT_MARK} v=0.1"
    ids, mask, _ = model.make_batch([("abc", answer)])
    _, _, _, weights = model.make_batch_weighted([("abc", answer)], tail_weight=1.0)
    plain = model.loss(ids, mask)
    weighted = model.loss(ids, mask, weights)
    assert float(plain) == pytest.approx(float(weighted), rel=1e-5)


def test_split_tf_separates_response_from_state_block():
    model = TokenSNN(_al_vocab(), TokenConfig(d_emb=8, d_hidden=8, max_len=64))
    split = model.split_tf_accuracy([("abc", f"def {AL_OUT_MARK} v=0.1")])
    assert split["response_tokens"] > 0 and split["tail_tokens"] > 0
    assert 0.0 <= split["response_tf"] <= 1.0
    assert 0.0 <= split["tail_tf"] <= 1.0

    plain = model.split_tf_accuracy([("abc", "def")])
    assert plain["tail_tokens"] == 0
    # without a state block the split must equal the aggregate diagnostic
    assert plain["response_tf"] == model.tf_accuracy([("abc", "def")])["tf_acc"]


def test_train_on_accepts_a_tail_weight(vocab):
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=64))
    answer = f"def {AL_OUT_MARK} v=0.1"
    history = model.train_on([("abc", answer)], epochs=2, batch_size=1, tail_weight=0.25)
    assert len(history) == 2
    assert all(row["loss"] == row["loss"] for row in history)  # finite


# -- scheduled sampling (round-3 objective knob) ---------------------------


def test_ss_off_returns_the_gold_inputs(vocab):
    """p=0 must be the identity — the default path cannot drift."""
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=32))
    ids, mask, _ = model.make_batch([("abc", "def")])
    assert model._ss_inputs(ids, mask, 0.0) is ids


def test_ss_touches_only_the_answer_region(vocab):
    """Corruption may never reach the prompt: every sample starts from the
    real question, so only mask-True (answer) positions may differ."""
    import torch

    torch.manual_seed(0)
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=32))
    ids, mask, _ = model.make_batch([("abc", "defgh")])
    ss = model._ss_inputs(ids, mask, 1.0)
    changed = ss != ids
    assert torch.equal(ss[~mask], ids[~mask]), "prompt positions were corrupted"
    assert not bool((changed & ~mask).any()), "a change landed outside the answer region"
    assert bool(changed.any()), "p=1.0 must replace something in the answer region"
    assert int(ss.max()) < len(vocab) and int(ss.min()) >= 0, "replacement must be a vocab id"


def test_loss_scores_gold_targets_against_corrupted_inputs(vocab):
    """Scheduled sampling trains on self-generated context but is still graded
    on the gold sequence — targets=ids must keep the loss finite and usable."""
    import torch

    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=32))
    ids, mask, _ = model.make_batch([("abc", "defgh")])
    ss = model._ss_inputs(ids, mask, 1.0)
    loss = model.loss(ss, mask, targets=ids)
    assert float(loss) == float(loss)  # finite, not NaN
    loss.backward()
    assert all(p.grad is None or torch.isfinite(p.grad).all() for p in model.net.parameters())


def test_train_on_runs_with_scheduled_sampling(vocab):
    """The round-3 objective knob must train end-to-end; ss_final=0 must give
    exactly the plain teacher-forced history (regression pin for the default)."""
    pairs = [("abc", "def"), ("bcd", "efg")] * 3
    import torch

    torch.manual_seed(7)  # identical initial weights across the three models
    plain = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=32))
    torch.manual_seed(7)
    off = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=32))
    torch.manual_seed(7)
    ramped = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=32))
    base = plain.train_on(pairs, epochs=3, batch_size=2, seed=0)
    explicit_off = off.train_on(pairs, epochs=3, batch_size=2, seed=0, ss_final=0.0)
    assert base == explicit_off, "ss_final=0 must not change the training path"

    history = ramped.train_on(pairs, epochs=3, batch_size=2, seed=0, ss_final=1.0)
    assert len(history) == 3
    assert all(row["loss"] == row["loss"] for row in history)  # finite


def test_stacked_layers_carry_the_embedding_forward(vocab):
    """Depth needs a path for token identity that does not go through spikes.

    Measured 2026-11-04: three stacked LIF layers at d_emb 256 / d_hidden 4096
    flattened to the unconditional distribution (loss 3.89 against a 4.10-nat
    marginal entropy) at both lr 3e-3 and 3e-4, and removing the DC offset of
    the inter-layer drive did not move it. Adding a per-layer skip from the
    embedding dropped the same config to 2.96 within four epochs.
    """
    import torch

    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=16, layers=3, max_len=32))
    ids = torch.tensor([[1, 2, 3, 4]]).to(model.device)
    logits = model.net(ids)
    assert tuple(logits.shape) == (1, 4, len(vocab))
    assert torch.isfinite(logits).all()
    # one skip per layer above the first, and the first is the no-op slot
    skips = list(model.net.w_skip)
    assert len(skips) == 3
    assert type(skips[0]).__name__ == "Identity"
    assert sum(p.numel() for p in model.net.w_skip.parameters()) == 2 * (8 * 16 + 16)


def test_single_layer_checkpoints_have_no_skip_weights(vocab):
    """Rounds 1-9 trained with layers=1 must keep loading byte-for-byte."""
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=16, layers=1, max_len=16))
    keys = list(model.net.state_dict())
    assert not any("w_skip" in k for k in keys)


def _tiny_pairs():
    return [("abc", "def"), ("bcd", "efg")] * 3


def test_guard_rolls_back_and_lowers_the_rate(vocab):
    """The stability rule: a runaway epoch restores weights instead of keeping them.

    Round-10 lost nineteen good epochs to a twentieth (loss 1.04 -> 7.02 at
    unchanged lr). The rule under test is that no epoch may sit more than
    ``diverge_factor`` times the best one: it rolls back, halves the rate and
    carries on, so the run degrades into oscillation rather than ruin.
    """
    import math

    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=16))
    history = model.train_on(_tiny_pairs(), epochs=6, batch_size=2, lr=200.0, diverge_factor=1.2)
    rows = [row for row in history if "loss" in row and "lr" in row]
    assert any(row["rolled_back"] for row in rows), "the rule was never exercised"
    assert all(math.isfinite(row["loss"]) for row in rows)
    # the rate only ever goes down, and it moves when a rollback happens
    rates = [row["lr"] for row in rows]
    assert rates == sorted(rates, reverse=True)
    assert rates[-1] < rates[0]
    # weights after the run are finite everywhere (a rollback restored them)
    assert all(bool(model.torch.isfinite(p).all()) for p in model.net.parameters())


def test_guard_is_off_by_request(vocab):
    """`--no-guard` must be a real opt-out, not a silently ignored flag."""
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=16))
    history = model.train_on(
        _tiny_pairs(), epochs=3, batch_size=2, lr=200.0, diverge_factor=1.2, guard=False
    )
    assert not any(row.get("rolled_back") for row in history)


def test_lr_at_and_should_stop_are_honoured(vocab):
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=16))
    seen = []
    history = model.train_on(
        _tiny_pairs(),
        epochs=6,
        batch_size=2,
        lr=1e-2,
        lr_at=lambda epoch: 1e-2 / (epoch + 1),
        should_stop=lambda: len(seen) >= 2,
        on_epoch=seen.append,
    )
    assert [round(row["lr"], 6) for row in history[:3]] == [0.01, 0.005, 0.003333]
    assert history[-1].get("stopped") is True
    assert len(history) == 3, "must stop at the epoch after the second callback"


def test_dynamics_reports_a_silenced_stack(vocab):
    """The feature that tells 'alive' from 'firing without gradient'."""
    import torch

    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=16, layers=2, max_len=16))
    alive = model.dynamics(_tiny_pairs(), n=2)
    assert alive["verdict"] in {"alive", "firing-without-gradient"}
    assert [row["layer"] for row in alive["per_layer"]] == [0, 1]
    with torch.no_grad():
        model.net.threshold.fill_(1000.0)
    silenced = model.dynamics(_tiny_pairs(), n=2)
    assert silenced["verdict"] == "dead-or-saturated"
    assert all(row["spike_rate"] == 0.0 for row in silenced["per_layer"])


def test_theta_max_bounds_the_learned_threshold(vocab):
    """An unbounded threshold is a free way to stop learning (CORE_GAP §三十).

    Round-9 drove theta from 0.5 to 6.75 and silenced 97% of its spikes while the
    loss curve stayed healthy, because the surrogate gradient is
    ``sigmoid(5 * (mem - theta))``: far above the membrane distribution nothing
    reaches the threshold and nothing reaches the gradient either. The bound is a
    projection after each step, so it must hold for a deliberately abusive rate.
    """
    bound = 0.8
    # the bound is a projection, not a starting condition, so both models are
    # started out of band at the same 5.0 and given one step
    bounded = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=16, theta_max=bound))
    free = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=16, theta_max=0.0))
    for model in (bounded, free):
        with model.torch.no_grad():
            model.net.threshold.fill_(5.0)
        model.train_on(_tiny_pairs(), epochs=1, batch_size=2, lr=1e-4)
    assert float(bounded.net.threshold) <= bound + 1e-6
    assert float(free.net.threshold) > bound, "0 must not clamp"
    assert TokenConfig().theta_max == 2.0, "the bound is on by default"
    assert TokenConfig(theta_max=0.0).to_dict()["theta_max"] == 0.0


def test_theta_max_zero_is_the_historical_behaviour(vocab):
    """0 must mean 'no bound', not 'clamp at zero' — 0 is how it is turned off."""
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=16, theta_max=0.0))
    model.train_on(_tiny_pairs(), epochs=2, batch_size=2, lr=5e-2)
    assert float(model.net.threshold) != 0.0
