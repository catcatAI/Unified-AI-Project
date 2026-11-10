# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""On-disk distillation targets, and the loss that consumes them.

A KD target costs a 1.5B-parameter teacher forward pass per row, so it is built
once and reused. The cache is deliberately dumb — numpy arrays plus pointers —
because the interesting decisions all live in :mod:`ai.ed3n.kd_teacher` (where a
teacher decision exists) and :mod:`ai.ed3n.kd_targets` (which atom a teacher
probability belongs to). This module only has to be *exact* about three things:

1. **Ids are vocabulary-bound.** ``atom_id`` means nothing without the atom list
   it was built from, so the cache carries a fingerprint of the student's
   vocabulary and refuses to load against a different one. A silent mismatch
   trains the model to emit the wrong word, and the loss curve looks normal.
2. **Positions are hidden-state positions.** A row stores ``start + k - 1``
   where ``k`` is the answer-atom index — the index of the hidden vector whose
   next-token prediction *is* atom ``k``. Teacher token indices never appear.
3. **Targets stay unnormalised.** ``probs`` sum to the mapped mass, which is
   below 1 when the teacher's top-k lost mass in the projection. Renormalising
   would silently promote a position whose target is mostly missing.

The loss is ``-sum_a q_a log p_a`` with ``p`` the model's real softmax over the
whole vocabulary. A softmax over the target atoms alone would let the model
reduce the term by inflating every target atom while ignoring the rest of the
vocabulary — a loss that falls without the model predicting anything.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

FORMAT_VERSION = 2


def vocab_fingerprint(itos: Sequence[str]) -> str:
    """Stable fingerprint of an atom list (``\\x00``-separated, so ids matter)."""
    digest = hashlib.sha256()
    for atom in itos:
        digest.update(atom.encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()


@dataclass
class KdRow:
    """One training row's targets, sliced out of the flat cache arrays."""

    ids: np.ndarray
    start: int
    positions: np.ndarray
    atom_ptr: np.ndarray
    atom_ids: np.ndarray
    probs: np.ndarray

    def __len__(self) -> int:
        return int(len(self.positions))


class KdCache:
    """Flat, vocabulary-bound storage for per-row distillation targets."""

    def __init__(
        self,
        n_rows: int,
        ids: np.ndarray,
        ids_ptr: np.ndarray,
        starts: np.ndarray,
        pos: np.ndarray,
        pos_ptr: np.ndarray,
        atom_ids: np.ndarray,
        atom_ptr: np.ndarray,
        probs: np.ndarray,
        meta: Dict[str, Any],
    ) -> None:
        self.n_rows = int(n_rows)
        self._ids = ids
        self._ids_ptr = ids_ptr
        self._starts = starts
        self._pos = pos
        self._pos_ptr = pos_ptr
        self._atom_ids = atom_ids
        self._atom_ptr = atom_ptr
        self._probs = probs
        self.meta = dict(meta)

    # -- construction -------------------------------------------------------
    @classmethod
    def build(
        cls,
        rows: Iterable[Tuple[Sequence[int], int, Sequence[Tuple[int, Any]]]],
        vocab_itos: Sequence[str],
        meta: Optional[Dict[str, Any]] = None,
    ) -> "KdCache":
        """``rows`` yields ``(student_ids, answer_start, [(position, KdTargets)])``.

        ``KdTargets.probs`` is renormalised to 1 over the atoms the projection
        retained; the cache stores it **multiplied by** ``mapped_mass`` so the
        summed target mass is the fraction of the teacher's distribution that
        survived. Renormalising here would give a position whose target is
        mostly missing the same pull as a clean one.
        """
        ids_parts: List[np.ndarray] = []
        ids_ptr: List[int] = [0]
        starts: List[int] = []
        pos_parts: List[np.ndarray] = []
        pos_ptr: List[int] = [0]
        atom_ids_parts: List[np.ndarray] = []
        probs_parts: List[np.ndarray] = []
        atom_ptr: List[int] = [0]
        n_rows = 0
        for student_ids, start, targets in rows:
            ids_parts.append(np.asarray(student_ids, dtype=np.int32))
            ids_ptr.append(ids_ptr[-1] + len(student_ids))
            starts.append(int(start))
            n_pos_before = pos_ptr[-1]
            for position, target in targets:
                pos_parts.append(np.asarray([int(position)], dtype=np.int32))
                atom_ids_parts.append(np.asarray(target.atom_ids, dtype=np.int32))
                q = np.asarray(target.probs, dtype=np.float64) * float(target.mapped_mass)
                probs_parts.append(q.astype(np.float16))
                atom_ptr.append(atom_ptr[-1] + len(target.atom_ids))
            pos_ptr.append(n_pos_before + len(targets))
            n_rows += 1

        def _cat(parts: List[np.ndarray], dtype: Any) -> np.ndarray:
            if not parts:
                return np.empty((0,), dtype=dtype)
            return np.concatenate(parts).astype(dtype, copy=False)

        payload = dict(meta or {})
        payload.update(
            {
                "format": FORMAT_VERSION,
                "rows": n_rows,
                "atoms": len(vocab_itos),
                "vocab_sha256": vocab_fingerprint(vocab_itos),
            }
        )
        return cls(
            n_rows=n_rows,
            ids=_cat(ids_parts, np.int32),
            ids_ptr=np.asarray(ids_ptr, dtype=np.int64),
            starts=np.asarray(starts, dtype=np.int32),
            pos=_cat(pos_parts, np.int32),
            pos_ptr=np.asarray(pos_ptr, dtype=np.int64),
            atom_ids=_cat(atom_ids_parts, np.int32),
            atom_ptr=np.asarray(atom_ptr, dtype=np.int64),
            probs=_cat(probs_parts, np.float16),
            meta=payload,
        )

    # -- persistence --------------------------------------------------------
    def save(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            ids=self._ids,
            ids_ptr=self._ids_ptr,
            starts=self._starts,
            pos=self._pos,
            pos_ptr=self._pos_ptr,
            atom_ids=self._atom_ids,
            atom_ptr=self._atom_ptr,
            probs=self._probs,
            meta=np.asarray(json.dumps(self.meta)),
        )
        return path

    @classmethod
    def load(cls, path: Path) -> "KdCache":
        path = Path(path)
        with np.load(path, allow_pickle=False) as data:
            meta = json.loads(str(data["meta"]))
            if int(meta.get("format", 0)) != FORMAT_VERSION:
                raise ValueError(
                    f"{path}: cache format {meta.get('format')} != {FORMAT_VERSION}; rebuild it"
                )
            cache = cls(
                n_rows=int(meta["rows"]),
                ids=data["ids"],
                ids_ptr=data["ids_ptr"],
                starts=data["starts"],
                pos=data["pos"],
                pos_ptr=data["pos_ptr"],
                atom_ids=data["atom_ids"],
                atom_ptr=data["atom_ptr"],
                probs=data["probs"],
                meta=meta,
            )
            cache.validate()
            return cache

    def validate(self) -> None:
        """Reject a structurally inconsistent cache before it trains anything.

        ``atom_ptr`` is indexed by *position*, not by row: a row holds a
        variable number of distilled positions and each position a variable
        number of atoms, so it is the one pointer array whose length is not
        ``rows + 1``.
        """
        n = self.n_rows
        n_pos = int(self._pos_ptr[-1]) if len(self._pos_ptr) else 0
        checks = (
            ("ids_ptr", self._ids_ptr, n + 1, len(self._ids)),
            ("pos_ptr", self._pos_ptr, n + 1, len(self._pos)),
            ("atom_ptr", self._atom_ptr, n_pos + 1, len(self._atom_ids)),
        )
        for name, ptr, expected, total in checks:
            if len(ptr) != expected:
                raise ValueError(f"{name}: expected {expected} entries, got {len(ptr)}")
            if int(ptr[-1]) != total:
                raise ValueError(f"{name}: ends at {int(ptr[-1])}, data has {total}")
            if int(ptr[0]) != 0:
                raise ValueError(f"{name}: starts at {int(ptr[0])}, not 0")
        if len(self._probs) != len(self._atom_ids):
            raise ValueError("probs and atom_ids have different lengths")
        if len(self._starts) != n:
            raise ValueError(f"starts: expected {n} entries, got {len(self._starts)}")

    # -- binding ------------------------------------------------------------
    def matches_vocab(self, itos: Sequence[str]) -> bool:
        return int(self.meta.get("atoms", -1)) == len(itos) and self.meta.get(
            "vocab_sha256"
        ) == vocab_fingerprint(itos)

    def require_vocab(self, itos: Sequence[str], source: str = "cache") -> None:
        if self.matches_vocab(itos):
            return
        raise ValueError(
            f"{source}: distillation targets were built for a different vocabulary "
            f"({self.meta.get('atoms')} atoms, {str(self.meta.get('vocab_sha256'))[:12]}) "
            f"than this model ({len(itos)} atoms, {vocab_fingerprint(itos)[:12]}). "
            "Atom ids would mean different words; rebuild the cache."
        )

    def row(self, index: int) -> Optional[KdRow]:
        if index < 0 or index >= self.n_rows:
            return None
        i0, i1 = int(self._ids_ptr[index]), int(self._ids_ptr[index + 1])
        p0, p1 = int(self._pos_ptr[index]), int(self._pos_ptr[index + 1])
        a0, a1 = int(self._atom_ptr[p0]), int(self._atom_ptr[p1])
        return KdRow(
            ids=self._ids[i0:i1],
            start=int(self._starts[index]),
            positions=self._pos[p0:p1],
            atom_ptr=self._atom_ptr[p0 : p1 + 1] - a0,
            atom_ids=self._atom_ids[a0:a1],
            probs=self._probs[a0:a1].astype(np.float32),
        )

    # -- measurement --------------------------------------------------------
    def stats(self, sample: int = 2000) -> Dict[str, float]:
        """Coverage / mass numbers, for the run report (not for grading)."""
        n = min(self.n_rows, max(1, sample))
        positions = 0
        atoms = 0
        mass = 0.0
        for index in range(n):
            row = self.row(index)
            if row is None:
                continue
            positions += len(row)
            atoms += len(row.atom_ids)
            # per position, not per row: the mean of a mean would weight a
            # 1-target row like a 40-target one
            for j in range(len(row.positions)):
                lo, hi = int(row.atom_ptr[j]), int(row.atom_ptr[j + 1])
                mass += float(row.probs[lo:hi].sum())
        return {
            # named ``sampled_rows`` so it cannot be mistaken for ``KdCache.n_rows``
            # (the trainer report puts both side by side)
            "sampled_rows": float(n),
            "positions_per_row": positions / n,
            "atoms_per_position": atoms / max(1, positions),
            "mapped_mass": mass / max(1, positions),
        }

    # -- the loss -----------------------------------------------------------
    def batch_loss(self, net: Any, hidden: Any, rows: Sequence[int]) -> Optional[Any]:
        """``-sum_a q_a log p_a`` at this batch's distilled positions.

        ``hidden`` is the student's ``encode(ids)[:, :-1, :]`` — the same tensor
        the hard-label loss uses, so distillation adds a head pass over a few
        hundred vectors and nothing else.
        """
        import torch

        b_idx: List[int] = []
        p_idx: List[int] = []
        atom_slices: List[np.ndarray] = []
        q_slices: List[np.ndarray] = []
        for batch_index, row_index in enumerate(rows):
            row = self.row(int(row_index))
            if row is None or len(row) == 0:
                continue
            for j, position in enumerate(row.positions):
                if position < 0 or int(position) >= hidden.shape[1]:
                    continue  # answer cut by max_len
                lo, hi = int(row.atom_ptr[j]), int(row.atom_ptr[j + 1])
                if hi <= lo:
                    continue
                b_idx.append(batch_index)
                p_idx.append(int(position))
                atom_slices.append(row.atom_ids[lo:hi])
                q_slices.append(row.probs[lo:hi])
        if not b_idx:
            return None

        device = hidden.device
        sel = hidden[
            torch.as_tensor(b_idx, dtype=torch.long, device=device),
            torch.as_tensor(p_idx, dtype=torch.long, device=device),
        ]
        logits = net.head(sel.float())
        lse = torch.logsumexp(logits, dim=-1, keepdim=True)

        counts = np.asarray([len(a) for a in atom_slices], dtype=np.int64)
        owner = np.repeat(np.arange(len(atom_slices), dtype=np.int64), counts)
        flat_ids = np.concatenate(atom_slices).astype(np.int64, copy=False)
        flat_q = np.concatenate(q_slices).astype(np.float32, copy=False)
        owner_t = torch.as_tensor(owner, dtype=torch.long, device=device)
        picked = logits[owner_t, torch.as_tensor(flat_ids, dtype=torch.long, device=device)]
        terms = -(
            torch.as_tensor(flat_q, dtype=torch.float32, device=device) * (picked - lse[owner_t, 0])
        )
        per_position = torch.zeros(len(atom_slices), dtype=terms.dtype, device=device)
        per_position = per_position.index_add(0, owner_t, terms)
        return per_position.mean()

    # -- integrity ----------------------------------------------------------
    def verify_rows(
        self, pairs: Sequence[Tuple[str, str]], model: Any, sample: int = 32
    ) -> List[str]:
        """Re-encode a sample of rows and compare against the stored ids.

        Catches corpus drift, a different ``max_len``, or an off-by-one in the
        builder — all of which would otherwise show up only as a slightly worse
        loss. Returns a list of problems (empty means the sample agreed).
        """
        problems: List[str] = []
        n = min(len(pairs), self.n_rows)
        if n == 0:
            return ["no rows to verify"]
        step = max(1, n // max(1, sample))
        checked = 0
        for index in range(0, n, step):
            row = self.row(index)
            if row is None:
                continue
            ids, start, _cut = model._encode(pairs[index][0], pairs[index][1])
            checked += 1
            if list(row.ids) != list(ids):
                problems.append(f"row {index}: {len(row.ids)} cached ids != {len(ids)} re-encoded")
                continue
            if row.start != int(start):
                problems.append(f"row {index}: cached start {row.start} != {start}")
            if len(problems) >= 3:
                break
        if checked == 0:
            problems.append("verified no rows")
        return problems


__all__ = ["FORMAT_VERSION", "KdCache", "KdRow", "vocab_fingerprint"]
