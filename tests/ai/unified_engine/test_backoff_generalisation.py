# ANGELA-MATRIX: [L3] [β] [B] [L2]
"""
The byte model's backoff must GENERALISE, not memorise.

The n-gram tables are hash buckets, so an unseen context still lands in an
occupied cell. The old "first non-empty cell wins" rule answered such a
context with a confidently wrong distribution: on a held-out split of the
project's own documentation it scored 9.42 bits/byte — worse than the 8.0
of a uniform guess, i.e. the model was memorising the training stream and
generalising worse than chance.

These tests pin the interpolated backoff that fixed it.
"""

import math
import os
import tempfile

from ai.unified_engine.core_model import VOCAB, FixedSizeCore
from ai.unified_engine.trainer import heldout_bpc, train_exact_bytes

# 8 bits/byte = a uniform guess over the 256-byte vocabulary.
UNIFORM_BPC = math.log2(VOCAB)


def _corpus() -> bytes:
    """A text corpus with structure (not noise) to train on."""
    parts = []
    for i in range(400):
        parts.append(
            f"section {i}: the quick brown fox jumps over the lazy dog; "
            f"value = {i * 3} and label = alpha{i % 7}.\n"
        )
    return "".join(parts).encode("utf-8")


def test_unseen_context_scores_better_than_a_uniform_guess():
    """The hold-out split must be predicted BETTER than chance.

    This is the property the old rule violated (9.42 bits/byte).
    """
    raw = _corpus()
    cut = int(len(raw) * 0.75)
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as fh:
        fh.write(raw)
        path = fh.name
    try:
        core = FixedSizeCore()
        train_exact_bytes(core, path, cut)
        train_score = heldout_bpc(core, path, 0, n=20000)
        holdout_score = heldout_bpc(core, path, cut, n=20000)
    finally:
        os.unlink(path)

    assert holdout_score < UNIFORM_BPC, (
        f"hold-out bpc {holdout_score:.3f} is not better than the uniform "
        f"guess {UNIFORM_BPC:.3f} — the backoff is memorising, not generalising"
    )
    # And the hold-out must not be dramatically worse than the train region:
    # a model that only memorises shows a huge gap.
    assert holdout_score < train_score * 4, (
        f"hold-out bpc {holdout_score:.3f} vs train bpc {train_score:.3f} — "
        "the model does not generalise across the split"
    )


def test_a_narrow_context_stays_peaked():
    """Interpolation must not flatten a context the model knows well."""
    core = FixedSizeCore()
    core.learn_bytes(b"ab ab ab ab ab ab ab")
    dist = core.gram_dist(b"ab ")
    assert dist[ord("a")] > 0.5


def test_every_byte_keeps_a_probability():
    """The uniform floor keeps impossible bytes away from zero."""
    core = FixedSizeCore()
    core.learn_bytes(b"ab ab ab ab ab ab ab")
    dist = core.gram_dist(b"ab ")
    assert min(dist) > 0.0
    assert abs(sum(dist) - 1.0) < 1e-6
