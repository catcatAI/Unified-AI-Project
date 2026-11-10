# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""A llama.cpp teacher, wrapped once so probe and trainer cannot disagree.

The tokenisers do not match (Qwen BPE at 151k tokens vs the student's word
atoms), so every distillation target has to answer two questions at once:

1. *Which* student atom does a teacher probability belong to? That rule lives in
   :mod:`ai.ed3n.kd_targets` and is not repeated here.
2. *Where* does the teacher make a decision at all? A teacher token that starts
   before an atom and ends inside it means there is no teacher decision at that
   boundary, and reading the neighbouring row of `llama_cpp`'s score buffer
   would silently pair the atom with a distribution emitted for a different
   character position. Measured: doing that turned a 0.84 agreement into 0.32
   and a 1.65-nat teacher into an 11.9-nat one.

``align()`` is the only place that decides (2), so the readiness probe and the
training data builder measure the same thing.

This module imports ``llama_cpp`` lazily: importing it without the optional
dependency must not fail (the token-SNN and its tests do not need a teacher).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .kd_targets import AtomPrefixIndex, KdTargets, targets_from_logits
from .token_snn import tokenize


@dataclass
class AtomAlignment:
    """One answer atom and the teacher boundary it may be distilled from.

    ``token_index`` is ``None`` when no teacher token *starts* at this atom's
    first character — the atom keeps its hard label at that position.

    ``start``/``end`` are character offsets into the teacher's decoded text,
    carried on the object so no caller has to recompute the prompt offset: that
    offset was the source of two measurement bugs (a misaligned agreement of
    0.32 and an 11.9-nat atom CE).
    """

    atom_index: int
    token_index: Optional[int]
    text: str
    start: int = 0
    end: int = 0


class KdTeacher:
    """Teacher probabilities at answer-atom boundaries.

    Every method that evaluates the model leaves ``llama_cpp``'s score buffer in
    a state that the *next* ``eval`` overwrites, so callers must consume the
    returned array before the next call. ``align()`` returns it deliberately:
    one teacher forward pass can then feed a cross-entropy measurement, an
    agreement measurement and target construction without paying for the pass
    three times.
    """

    def __init__(
        self,
        model_path: str = "",
        n_ctx: int = 512,
        n_threads: int = 6,
        llm: Any = None,
    ) -> None:
        """``llm`` injects an object with the llama.cpp call interface.

        That is how the arithmetic below is tested without a 1.5B GGUF on disk:
        a fake that returns fixed token spans exercises exactly the code the
        real teacher runs. Passing ``llm`` also avoids importing ``llama_cpp``
        at all, which keeps this module importable on a machine that has the
        student but not the teacher.
        """
        self.model_path = str(model_path)
        self.n_ctx = int(n_ctx)
        if llm is None:
            from llama_cpp import Llama

            llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=int(n_threads),
                logits_all=True,
                verbose=False,
            )
        self._llm = llm
        self._texts: Optional[List[str]] = None

    # -- vocabulary ---------------------------------------------------------
    @property
    def token_texts(self) -> List[str]:
        """Decoded text of every teacher token (the projection needs it)."""
        if self._texts is None:
            n = int(self._llm.n_vocab())
            texts = [""] * n
            for tid in range(n):
                try:
                    texts[tid] = self._llm.detokenize([tid]).decode("utf-8", "replace")
                except Exception:  # noqa: BLE001 — a broken fragment maps to nothing
                    texts[tid] = ""
            self._texts = texts
        return self._texts

    def tokenize(self, text: str) -> List[int]:
        return list(self._llm.tokenize(text.encode("utf-8"), add_bos=True))

    # -- one row ------------------------------------------------------------
    def spans(self, ids: Sequence[int]) -> List[Tuple[int, int]]:
        """Character span of each token, from the teacher's own decode."""
        out: List[Tuple[int, int]] = []
        pos = 0
        for tid in ids:
            text = self.token_texts[int(tid)]
            out.append((pos, pos + len(text)))
            pos += len(text)
        return out

    def evaluate(self, ids: Sequence[int]) -> None:
        self._llm.reset()
        self._llm.eval(list(ids))

    @property
    def scores(self) -> Any:
        """``(n_ctx, n_vocab)`` logits from the last ``evaluate``.

        Only the first ``len(ids)`` rows are filled; other rows are zeros. Use
        ``scores[i - 1]`` to get the distribution that predicts ``ids[i]``.
        """
        return self._llm.scores

    def token_logprobs(self, ids: Sequence[int]) -> List[float]:
        """Log-probability of each token given its prefix (index 0 unused)."""
        scores = self.scores
        out: List[float] = []
        for pos in range(1, len(ids)):
            row = np.asarray(scores[pos - 1], dtype=np.float32)
            peak = float(row.max())
            lse = peak + math.log(float(np.exp(row - peak).sum()))
            out.append(float(row[int(ids[pos])]) - lse)
        return out

    def align(
        self, prompt: str, answer: str
    ) -> Tuple[List[AtomAlignment], Any, Optional[List[Tuple[int, int]]]]:
        """Evaluate ``prompt + "\\n" + answer`` and align answer atoms to tokens.

        Returns ``(alignments, scores, spans)``. ``scores`` is ``None`` when the
        row does not fit ``n_ctx`` (the caller skips it rather than measuring a
        truncated answer).
        """
        ids = self.tokenize(prompt + "\n" + answer)
        if len(ids) < 2 or len(ids) > self.n_ctx - 2:
            return [], None, None
        spans = self.spans(ids)
        starts = {s0: i for i, (s0, _s1) in enumerate(spans)}
        self.evaluate(ids)
        offset = len(prompt) + 1
        out: List[AtomAlignment] = []
        pos = offset
        for k, atom in enumerate(tokenize(answer)):
            start = pos
            pos += len(atom)
            if pos > spans[-1][1]:
                break
            token_index = starts.get(start)
            out.append(
                AtomAlignment(
                    atom_index=k,
                    token_index=(
                        token_index if token_index is not None and token_index >= 1 else None
                    ),
                    text=atom,
                    start=start,
                    end=start + len(atom),
                )
            )
        return out, self.scores, spans

    def atom_logprob(
        self,
        token_lp: Sequence[float],
        spans: Sequence[Tuple[int, int]],
        astart: int,
        aend: int,
    ) -> Optional[float]:
        """Teacher log-probability of the characters ``[astart, aend)``.

        A token that straddles a boundary is charged in full to the atom it
        overlaps: splitting a token's probability by characters would invent
        mass the teacher never assigned. ``None`` means no prediction exists
        (the atom starts at the very first token).
        """
        total = 0.0
        found = False
        for i, (s0, s1) in enumerate(spans):
            if i == 0:
                continue  # token 0 has no prediction
            if s1 <= astart:
                continue
            if s0 >= aend:
                break
            total += float(token_lp[i - 1])
            found = True
        return total if found else None

    def targets(
        self,
        alignments: Sequence[AtomAlignment],
        scores: Any,
        atoms: AtomPrefixIndex,
        top_k: int = 64,
        temperature: float = 1.0,
    ) -> List[Tuple[int, KdTargets]]:
        """Project the teacher's distribution at each aligned atom boundary."""
        out: List[Tuple[int, KdTargets]] = []
        for row in alignments:
            if row.token_index is None:
                continue
            target = targets_from_logits(
                scores[row.token_index - 1],
                self.token_texts,
                atoms,
                top_k=top_k,
                temperature=temperature,
            )
            if target.ok:
                out.append((row.atom_index, target))
        return out

    def agreement(
        self, alignments: Sequence[AtomAlignment], scores: Any, top_k: int = 64
    ) -> List[float]:
        """Mass on tokens that agree with each gold atom (aligned positions)."""
        from .kd_targets import gold_atom_prefix_mass

        return [
            gold_atom_prefix_mass(scores[row.token_index - 1], self.token_texts, row.text, top_k)
            for row in alignments
            if row.token_index is not None
        ]

    def close(self) -> None:
        self._llm = None  # type: ignore[assignment]


__all__ = ["AtomAlignment", "KdTeacher"]
