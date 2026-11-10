"""Contract tests for the shared distillation teacher wrapper.

The readiness probe and the trainer must agree on two things that are easy to
drift apart:

1. *Which* student atom a teacher probability belongs to — that rule lives in
   :mod:`ai.ed3n.kd_targets` and is not re-implemented here.
2. *Where* the teacher makes a decision at all. When a teacher token straddles an
   atom boundary there is no teacher distribution for that atom, and reading the
   neighbouring row of the score buffer pairs the atom with a distribution
   emitted for a different character position. Measured on the real teacher,
   doing that turned a 0.84 gold agreement into 0.32 and a 1.65-nat teacher into
   an 11.9-nat one — a wrong number that still looks like a number.

The tests use a fake tokeniser and a hand-written score buffer, so they run
without the 1.5B GGUF or ``llama_cpp`` installed.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from ai.ed3n.kd_targets import AtomPrefixIndex
from ai.ed3n.kd_teacher import AtomAlignment, KdTeacher

# Fake teacher vocabulary. ``""`` is BOS: real llama.cpp detokenises BOS to an
# empty string, and the alignment depends on that being true.
VOCAB = ["", "Q", "\n", "a", "b ", "cd"]
STOI = {text: i for i, text in enumerate(VOCAB)}


class _FakeLlama:
    """The slice of the llama.cpp API that :class:`KdTeacher` calls.

    Tokenisation is greedy-longest-match over the fake vocabulary. That is not
    how BPE works, but it produces the property under test — tokens whose
    boundaries do not coincide with atom boundaries — deterministically.
    """

    def __init__(self, rows=None) -> None:
        self.rows = rows or {}
        self._scores = None
        self.evaluations = 0

    def n_vocab(self) -> int:
        return len(VOCAB)

    def detokenize(self, ids) -> bytes:
        return "".join(VOCAB[int(i)] for i in ids).encode("utf-8")

    def tokenize(self, data: bytes, add_bos: bool = True):
        text = data.decode("utf-8")
        ids = [0] if add_bos else []
        i = 0
        while i < len(text):
            for end in range(len(text), i, -1):
                fragment = text[i:end]
                if fragment in STOI:
                    ids.append(STOI[fragment])
                    i = end
                    break
            else:  # pragma: no cover - only on a broken fake vocabulary
                raise ValueError(f"fake teacher cannot tokenize {text[i:]!r}")
        return ids

    def reset(self) -> None:
        return None

    def eval(self, ids) -> None:
        self.evaluations += 1
        scores = np.zeros((64, len(VOCAB)), dtype=np.float32)
        for row, logits in self.rows.items():
            for token_id, value in logits.items():
                scores[row, token_id] = value
        self._scores = scores

    @property
    def scores(self):
        return self._scores


def _teacher(rows=None) -> KdTeacher:
    return KdTeacher(llm=_FakeLlama(rows), n_ctx=64)


# "Q\nab cd":  Q=0 \n=1 a=2 b=3 ' '=4 c=5 d=6
# teacher tokens: "Q"(0,1) "\n"(1,2) "a"(2,3) "b "(3,5) "cd"(5,7)
# answer atoms:   "ab"(2,4)  " c"(4,6)  "d"(6,7)
# Only the first atom starts where a teacher token starts.
PROMPT = "Q"
ANSWER = "ab cd"


def test_alignment_reports_shared_boundaries_only() -> None:
    rows, scores, spans = _teacher().align(PROMPT, ANSWER)
    assert scores is not None
    # "ab" starts where the teacher's "a" starts -> a teacher decision exists.
    # " c" starts *inside* the teacher's "b ", and "d" inside "cd", so there is
    # no teacher distribution for those boundaries.
    assert [(r.text, r.token_index) for r in rows] == [
        ("ab", 3),
        (" c", None),
        ("d", None),
    ]
    assert spans[-1][1] == len(PROMPT) + 1 + len(ANSWER)


def test_alignment_carries_character_offsets() -> None:
    rows, _scores, _spans = _teacher().align(PROMPT, ANSWER)
    offset = len(PROMPT) + 1
    assert [(r.start, r.end) for r in rows] == [
        (offset, offset + 2),
        (offset + 2, offset + 4),
        (offset + 4, offset + 5),
    ]
    # Contiguous and exactly the answer: no caller has to recompute the seam.
    assert "".join(r.text for r in rows) == ANSWER


def test_alignment_of_a_row_that_does_not_fit_is_skipped() -> None:
    teacher = KdTeacher(llm=_FakeLlama(), n_ctx=4)  # "Q\nab cd" needs 6 tokens
    rows, scores, spans = teacher.align(PROMPT, ANSWER)
    assert (rows, scores, spans) == ([], None, None)
    assert teacher._llm.evaluations == 0, "an oversized row must not be evaluated"


def test_alignment_indexes_atoms_from_the_answer_not_the_row() -> None:
    rows, _scores, _spans = _teacher().align(PROMPT, ANSWER)
    # ``atom_index`` is what the trainer adds ``answer_start - 1`` to; it must be
    # answer-relative, or every distilled position shifts by the prompt length.
    assert [r.atom_index for r in rows] == list(range(len(rows)))


def test_token_logprobs_match_a_manual_log_softmax() -> None:
    teacher = _teacher()
    ids = teacher.tokenize("Q\nab cd")
    teacher.evaluate(ids)
    lp = teacher.token_logprobs(ids)
    assert len(lp) == len(ids) - 1, "the first token is a prediction target, not a source"
    assert all(value == pytest.approx(-math.log(len(VOCAB))) for value in lp)


def test_token_logprobs_track_a_peaked_distribution() -> None:
    # Row 2 predicts the 4th token ("a", id 3); make it dominant.
    teacher = _teacher(rows={2: {3: 30.0}})
    ids = teacher.tokenize("Q\nab cd")
    teacher.evaluate(ids)
    lp = teacher.token_logprobs(ids)
    assert lp[2] == pytest.approx(0.0, abs=1e-3)
    assert lp[0] == pytest.approx(-math.log(len(VOCAB)), rel=1e-2)


def test_atom_logprob_charges_every_covering_token() -> None:
    teacher = _teacher()
    _rows, _scores, spans = teacher.align(PROMPT, ANSWER)
    lp = teacher.token_logprobs(teacher.tokenize(PROMPT + "\n" + ANSWER))
    uniform = -math.log(len(VOCAB))
    # "ab" (2,4) is covered by the tokens (2,3) and (3,5): two predictions.
    assert teacher.atom_logprob(lp, spans, 2, 4) == pytest.approx(2 * uniform)
    # " c" (4,6) is covered by (3,5) and (5,7). A straddling token is charged in
    # full: splitting its probability by character would invent mass the teacher
    # never assigned.
    assert teacher.atom_logprob(lp, spans, 4, 6) == pytest.approx(2 * uniform)
    # "d" (6,7) is covered by (5,7) alone.
    assert teacher.atom_logprob(lp, spans, 6, 7) == pytest.approx(uniform)


def test_atom_logprob_is_none_when_no_prediction_covers_the_atom() -> None:
    teacher = _teacher()
    _rows, _scores, spans = teacher.align(PROMPT, ANSWER)
    lp = teacher.token_logprobs(teacher.tokenize(PROMPT + "\n" + ANSWER))
    assert teacher.atom_logprob(lp, spans, 0, 0) is None


def test_targets_only_come_from_aligned_atoms() -> None:
    teacher = _teacher(rows={2: {3: 30.0}})
    rows, scores, _spans = teacher.align(PROMPT, ANSWER)
    atoms = AtomPrefixIndex([(10, "ab"), (11, " c"), (12, "d")])
    targets = teacher.targets(rows, scores, atoms, top_k=64)
    assert [atom_index for atom_index, _tgt in targets] == [0]


def test_targets_fall_back_to_the_shortest_extension() -> None:
    # The teacher's dominant token "a" is shorter than every atom; it can only
    # commit the student to the smallest atom that starts with it, which is
    # "ab". That is a coarse mapping and must be counted as one.
    teacher = _teacher(rows={2: {3: 30.0}})
    rows, scores, _spans = teacher.align(PROMPT, ANSWER)
    atoms = AtomPrefixIndex([(10, "ab"), (11, " c"), (12, "d")])
    ((atom_index, target),) = teacher.targets(rows, scores, atoms, top_k=64)
    assert atom_index == 0
    assert target.coarse == 1
    assert int(target.atom_ids[0]) == 10
    assert 0.0 < target.mapped_mass <= 1.0


def test_agreement_is_only_reported_for_aligned_atoms() -> None:
    teacher = _teacher(rows={2: {3: 30.0}})
    rows, scores, _spans = teacher.align(PROMPT, ANSWER)
    aligned = [r for r in rows if r.token_index is not None]
    values = teacher.agreement(aligned, scores)
    assert len(values) == 1
    # "a" agrees with "ab" (the atom is an extension of the token), so a
    # dominant "a" must be read as support for the gold atom.
    assert values[0] > 0.5


def test_agreement_reads_the_row_before_the_aligned_token() -> None:
    """Guards the off-by-one that produced the 11.9-nat teacher CE."""
    teacher = _teacher(rows={3: {3: 30.0}})  # row 3 predicts token 4, not 3
    rows, scores, _spans = teacher.align(PROMPT, ANSWER)
    aligned = [r for r in rows if r.token_index is not None]
    assert teacher.agreement(aligned, scores)[0] < 0.5


def test_close_drops_the_model_handle() -> None:
    teacher = _teacher()
    teacher.close()
    assert teacher._llm is None


def test_alignment_dataclass_defaults_are_contiguous_zeroes() -> None:
    span = AtomAlignment(atom_index=0, token_index=None, text="x")
    assert (span.start, span.end) == (0, 0)
