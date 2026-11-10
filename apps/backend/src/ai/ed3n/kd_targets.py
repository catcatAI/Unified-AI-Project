# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""Map a teacher LM's next-token distribution onto the student's word atoms.

Why this file exists
--------------------
Knowledge distillation needs ``q`` — a probability distribution over the
*student's* next token — not just a teacher-written string. The teacher here is
a BPE model (Qwen, 151k tokens); the student is :class:`~ai.ed3n.token_snn.TokenVocab`,
which splits "the cat" into ``["the", " c", "at"]``. The two segmentations do not
coincide, so ``q`` has to be *derived*, and the derivation has to be measurable
rather than assumed.

The rule this module implements (and the only one it implements):

    for each teacher token ``t`` above the cut, the atom that receives its
    probability is the **longest student atom that is a prefix of ``t``'s
    text**; if no atom is a prefix (the token is shorter than every atom that
    starts with it, e.g. the BPE fragment ``"cc"`` for the atom
    ``"cceleration"``), the **shortest atom that starts with ``t``** receives
    it; otherwise the mass is dropped and counted.

Why "longest prefix" and not "text equality": a teacher token ``" cat"`` is one
BPE unit but the student needs two atoms (``" c"``, ``"at"``). Assigning
``" cat"`` to ``" c"`` is correct *at that boundary* — the student's next atom
really is ``" c"`` — and the ``"at"`` target comes from the teacher's
distribution at the *following* boundary, which is measured on the gold string.
Equality-only matching was measured at 24.9% retained mass; prefix matching is
what makes the remaining mass usable.

What this module deliberately does not do
-----------------------------------------
It does not re-rank, renormalise toward the gold label, or invent mass: the
returned ``mapped_mass`` is the fraction of the teacher's top-k probability that
actually landed on an atom, and ``dropped`` is the rest. A caller that wants to
know whether distillation is viable reads those two numbers; it does not get to
assume they are 1.0.

It also does not depend on llama.cpp, torch or numpy beyond ``numpy``: the
teacher's logits and its vocabulary's token texts are inputs, so the mapping can
be unit-tested against a fake vocabulary with no model on disk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np


@dataclass
class KdTargets:
    """A distillation target over student atom ids.

    ``atom_ids``/``probs`` are aligned and ``probs`` sums to 1 (empty when no
    teacher token mapped — callers must check ``mapped_mass`` rather than
    assume a usable target).
    """

    atom_ids: np.ndarray
    probs: np.ndarray
    mapped_mass: float
    topk_mass: float
    coarse: int
    dropped: int
    top_k: int
    stats: Dict[str, float] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return bool(len(self.atom_ids)) and float(self.probs.sum()) > 0.0

    def as_dict(self) -> Dict[str, object]:
        return {
            "n_atoms": int(len(self.atom_ids)),
            "mapped_mass": round(self.mapped_mass, 4),
            "topk_mass": round(self.topk_mass, 4),
            "coarse": int(self.coarse),
            "dropped": int(self.dropped),
            "top_k": int(self.top_k),
            **{k: round(v, 4) for k, v in self.stats.items()},
        }


class AtomPrefixIndex:
    """Prefix lookups over the student's atom texts.

    Two indices, both built once:

    - ``_exact``: atom text → id, so ``longest_prefix`` is at most
      ``max_atom_len`` dict lookups (not a trie walk; atoms are short).
    - ``_by_prefix``: every prefix of every atom → the shortest atom id that
      starts with it. Used only when the teacher token is shorter than any
      atom, i.e. when the token cannot decide *which* atom it belongs to.
    """

    def __init__(self, atoms: Iterable[Tuple[int, str]]) -> None:
        self._exact: Dict[str, int] = {}
        longest = 0
        for atom_id, text in atoms:
            if not text:
                continue
            self._exact[text] = int(atom_id)
            longest = max(longest, len(text))
        self.max_atom_len = longest
        self._by_prefix: Dict[str, int] = {}
        # Shortest wins: a token that is a prefix of several atoms is the
        # weakest evidence, so it should commit the student to the smallest
        # unit rather than guess a long word.
        for text in sorted(self._exact, key=len):
            for end in range(1, len(text) + 1):
                self._by_prefix.setdefault(text[:end], self._exact[text])

    def __len__(self) -> int:
        return len(self._exact)

    def longest_prefix(self, text: str) -> Optional[int]:
        """Atom id whose text is the longest prefix of ``text`` (or None)."""
        if not text:
            return None
        upper = min(len(text), self.max_atom_len)
        for end in range(upper, 0, -1):
            hit = self._exact.get(text[:end])
            if hit is not None:
                return hit
        return None

    def shortest_extension(self, text: str) -> Optional[int]:
        """Shortest atom id that starts with ``text`` (or None)."""
        if not text:
            return None
        return self._by_prefix.get(text)


def softmax_topk(logits: np.ndarray, top_k: int) -> Tuple[np.ndarray, np.ndarray, float]:
    """(ids, probabilities over the full vocab for those ids, top-k mass).

    ``probabilities`` are ``softmax`` over the whole vocabulary, restricted to
    the selected ids — not a softmax over the top-k alone. That distinction is
    what makes ``topk_mass`` meaningful: it is the teacher's real confidence,
    not an artefact of truncation.
    """
    logits = np.asarray(logits, dtype=np.float64).reshape(-1)
    if logits.size == 0:
        return np.empty((0,), dtype=np.int64), np.empty((0,), dtype=np.float64), 0.0
    k = int(min(max(1, top_k), logits.size))
    peak = float(np.max(logits))
    exp = np.exp(logits - peak)
    total = float(exp.sum())
    if not np.isfinite(total) or total <= 0.0:
        return np.empty((0,), dtype=np.int64), np.empty((0,), dtype=np.float64), 0.0
    if k < logits.size:
        ids = np.argpartition(-logits, k - 1)[:k]
        ids = ids[np.argsort(-logits[ids])]
    else:
        ids = np.argsort(-logits)
    probs = exp[ids] / total
    return ids.astype(np.int64), probs.astype(np.float64), float(probs.sum())


def targets_from_logits(
    logits: np.ndarray,
    token_texts: Sequence[str],
    atoms: AtomPrefixIndex,
    top_k: int = 64,
    temperature: float = 1.0,
) -> KdTargets:
    """Project one teacher distribution onto the student's atom vocabulary.

    ``temperature`` softens (``>1``) or sharpens (``<1``) the teacher *before*
    the projection, which is the standard KD knob and is applied to the logits
    so the top-k cut is made on the distribution that is actually used.
    """
    logits = np.asarray(logits, dtype=np.float64).reshape(-1)
    if temperature and temperature != 1.0:
        logits = logits / float(temperature)
    ids, probs, topk_mass = softmax_topk(logits, top_k)
    assigned: Dict[int, float] = {}
    coarse = 0
    dropped_mass = 0.0
    for tid, p in zip(ids, probs):
        text = token_texts[int(tid)] if 0 <= int(tid) < len(token_texts) else ""
        atom_id = atoms.longest_prefix(text)
        if atom_id is None:
            atom_id = atoms.shortest_extension(text)
            if atom_id is not None:
                coarse += 1
        if atom_id is None:
            dropped_mass += float(p)
            continue
        assigned[atom_id] = assigned.get(atom_id, 0.0) + float(p)

    if not assigned:
        return KdTargets(
            atom_ids=np.empty((0,), dtype=np.int64),
            probs=np.empty((0,), dtype=np.float64),
            mapped_mass=0.0,
            topk_mass=topk_mass,
            coarse=coarse,
            dropped=len(ids),
            top_k=int(top_k),
        )
    atom_ids = np.array(sorted(assigned), dtype=np.int64)
    mass = np.array([assigned[int(a)] for a in atom_ids], dtype=np.float64)
    mapped = float(mass.sum())
    stats = {
        "mean_atoms": float(len(atom_ids)),
        "max_atom_prob": float(mass.max() / mapped),
        "coarse_share": float(coarse / max(1, len(ids))),
    }
    dropped = sum(
        1
        for tid in ids
        if atoms.longest_prefix(_text_of(token_texts, tid)) is None
        and atoms.shortest_extension(_text_of(token_texts, tid)) is None
    )
    return KdTargets(
        atom_ids=atom_ids,
        probs=mass / mapped,
        mapped_mass=mapped,
        topk_mass=topk_mass,
        coarse=coarse,
        dropped=int(dropped),
        top_k=int(top_k),
        stats=stats,
    )


def _text_of(token_texts: Sequence[str], tid: int) -> str:
    return token_texts[int(tid)] if 0 <= int(tid) < len(token_texts) else ""


def agrees_with_atom(token_text: str, atom_text: str) -> bool:
    """True when the token and the atom agree on every character they share.

    "Agree" means one is a prefix of the other — ``" cat"``/``" c"`` agree on
    ``" c"`` (the atom is a prefix of the token), ``"cc"``/``"cceleration"``
    agree on ``"cc"`` (the token is a prefix of the atom). A token that merely
    shares a *later* substring does not count, which is why this is not
    ``in``: ``"at"`` and ``" cat"`` share "at" but disagree at the first
    character.
    """
    if not token_text or not atom_text:
        return False
    common = min(len(token_text), len(atom_text))
    return token_text[:common] == atom_text[:common]


def gold_atom_prefix_mass(
    logits: np.ndarray,
    token_texts: Sequence[str],
    atom_text: str,
    top_k: int = 64,
) -> float:
    """Teacher probability on tokens that agree with the gold atom.

    This is the teacher's support for the gold continuation at this boundary: a
    token that agrees with the atom keeps the atom reachable. It says whether a
    soft target that pulls the student toward the teacher also pulls it toward
    the corpus answer, or away from it.
    """
    ids, probs, _ = softmax_topk(logits, top_k)
    return float(
        sum(
            float(p)
            for tid, p in zip(ids, probs)
            if agrees_with_atom(_text_of(token_texts, tid), atom_text)
        )
    )


__all__ = [
    "AtomPrefixIndex",
    "KdTargets",
    "agrees_with_atom",
    "gold_atom_prefix_mass",
    "softmax_topk",
    "targets_from_logits",
]
