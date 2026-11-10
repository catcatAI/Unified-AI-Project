"""Contract tests for mapping a teacher's next-token distribution onto atoms.

The mapping is the part of distillation that can silently destroy the signal:
if it drops most of the teacher's probability mass, the "soft target" is really
a hard label with extra noise, and the run measures the mapper rather than the
student. These tests pin the two directions (atom is a prefix of the token, and
the token is a prefix of the atom), the accounting, and the fact that unmapped
mass is *reported* rather than hidden.
"""

from __future__ import annotations

import numpy as np
import pytest
from ai.ed3n.kd_targets import (
    AtomPrefixIndex,
    agrees_with_atom,
    gold_atom_prefix_mass,
    softmax_topk,
    targets_from_logits,
)

# A miniature student vocabulary in the real atomisation's shape: a space is
# glued to the following character, so a word after the first is two atoms.
ATOMS = {0: "the", 1: " c", 2: "at", 3: " s", 4: "at2", 5: "cceleration", 6: " ", 7: "a"}


def _index() -> AtomPrefixIndex:
    return AtomPrefixIndex(ATOMS.items())


def test_longest_prefix_prefers_the_longest_matching_atom() -> None:
    index = _index()
    # " cat" -> " c" (the atom is a prefix); "at" is NOT a prefix of " cat".
    assert index.longest_prefix(" cat") == 1
    assert index.longest_prefix("at") == 2
    assert index.longest_prefix("the") == 0
    # No atom is a prefix of an unrelated token.
    assert index.longest_prefix("zzz") is None


def test_shortest_extension_handles_tokens_shorter_than_every_atom() -> None:
    index = _index()
    # "cc" is a BPE fragment of "cceleration": no atom is a prefix of "cc",
    # but the token is a prefix of an atom.
    assert index.longest_prefix("cc") is None
    assert index.shortest_extension("cc") == 5
    assert index.shortest_extension("zzz") is None


def test_token_is_mapped_to_the_atom_it_starts() -> None:
    texts = [" cat", "at", "the", "<|end|>"]
    logits = np.array([4.0, 1.0, 0.5, -20.0])
    out = targets_from_logits(logits, texts, _index(), top_k=4)
    # " cat" -> " c"; "at" -> "at"; "the" -> "the"; the special token is dropped.
    assert out.ok
    by_atom = dict(zip(out.atom_ids.tolist(), out.probs.tolist()))
    assert set(by_atom) == {0, 1, 2}
    assert by_atom[1] > by_atom[2] > by_atom[0]
    assert out.dropped == 1
    assert 0.0 < out.mapped_mass <= 1.0
    assert pytest.approx(1.0) == float(out.probs.sum())


def test_mapped_mass_is_reported_not_assumed() -> None:
    # 80% of the mass sits on a token that maps to no atom.
    texts = ["the", "<|end|>"]
    # logit gap chosen so p(<|end|>) ~ 0.8
    logits = np.array([0.0, np.log(4.0)])
    out = targets_from_logits(logits, texts, _index(), top_k=2)
    assert out.mapped_mass == pytest.approx(0.2, abs=1e-6)
    assert out.dropped == 1
    # The surviving probability is renormalised, so the target itself is usable
    # — the caller is warned by mapped_mass, not by a sum far from 1.
    assert out.probs.sum() == pytest.approx(1.0)


def test_empty_mapping_is_an_empty_target_not_a_zero_vector() -> None:
    texts = ["<|end|>", "\n\n"]
    out = targets_from_logits(np.array([1.0, 0.0]), texts, _index(), top_k=2)
    assert not out.ok
    assert out.mapped_mass == 0.0
    assert out.atom_ids.size == 0


def test_softmax_topk_reports_real_confidence() -> None:
    logits = np.array([0.0, 0.0, 0.0, 0.0])
    ids, probs, mass = softmax_topk(logits, 2)
    assert len(ids) == 2
    assert probs.sum() == pytest.approx(0.5, abs=1e-9)  # top-2 of a uniform 4-way
    assert mass == pytest.approx(0.5, abs=1e-9)


def test_temperature_is_applied_to_the_logits_before_the_cut() -> None:
    # Temperature changes the teacher's confidence. With top_k == |vocab| all the
    # mass is mapped either way, so the visible effect is the concentration of
    # the renormalised target (max_atom_prob), not mapped_mass.
    texts = ["the", " c", "at"]
    logits = np.array([5.0, 0.0, 0.0])
    sharp = targets_from_logits(logits, texts, _index(), top_k=3, temperature=0.5)
    soft = targets_from_logits(logits, texts, _index(), top_k=3, temperature=2.0)
    assert sharp.stats["max_atom_prob"] > soft.stats["max_atom_prob"]
    assert sharp.stats["max_atom_prob"] > 0.99 and soft.stats["max_atom_prob"] < 0.90


@pytest.mark.parametrize(
    ("token", "atom", "expected"),
    [
        (" cat", " c", True),
        ("cc", "cceleration", True),
        ("at", " cat", False),
        ("", " c", False),
        (" c", " c", True),
    ],
)
def test_agreement_is_prefix_agreement(token: str, atom: str, expected: bool) -> None:
    assert agrees_with_atom(token, atom) is expected


def test_gold_prefix_mass_ignores_tokens_that_disagree_at_the_start() -> None:
    texts = [" cat", "at", "the"]
    logits = np.array([2.0, 2.0, 0.0])
    # " cat" agrees with the atom " c"; "at" does not begin the same way.
    mass = gold_atom_prefix_mass(logits, texts, " c", top_k=3)
    expected = float(np.exp(2.0) / (np.exp(2.0) + np.exp(2.0) + np.exp(0.0)))
    assert mass == pytest.approx(expected, rel=1e-6)
