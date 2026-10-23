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
