"""The token-level SNN decoder: representation and objective that actually learn."""

from __future__ import annotations

import json

import pytest

pytest.importorskip("torch")

from ai.ed3n.token_snn import BOS, EOS, UNK, CharVocab, TokenConfig, TokenSNN  # noqa: E402


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


def test_tf_accuracy_is_a_sane_diagnostic(vocab):
    """Teacher-forced accuracy must count only answer tokens and lie in [0, 1]."""
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=24))
    stat = model.tf_accuracy([("abc", "def"), ("bcd", "efg")])
    assert 0.0 <= stat["tf_acc"] <= 1.0
    assert stat["tokens"] > 0
    # untrained model: roughly chance; must not be reported as skill
    assert stat["tokens"] == sum(len(a) + 1 for _, a in [("abc", "def"), ("bcd", "efg")])
