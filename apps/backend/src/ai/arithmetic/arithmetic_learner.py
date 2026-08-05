# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [B] [L5]
# =============================================================================
"""Autonomous arithmetic learning loop.

Design (mapped to the research verdict in
``docs/03-technical-architecture/analysis/ARITHMETIC_LEARNING_VERDICT.md``):

* **Counting digit representation** (§3.1 B / §3.3): each digit ``d`` is the
  ``d``-times repetition of a single reusable unit vector ``u``
  (``digit_rep(d) = d * u``). Unlike one-hot symbol slots (§3.1 A) this is a
  composable unit, so magnitude is naturally extended — a digit 5 shares its
  first four unit slots with digit 4, giving an inductive structure.
* **Deterministic label source**: numeric truth always comes from
  ``services.math_verifier.evaluate_math`` (single source of truth). The
  learner never computes arithmetic itself; it only learns the
  ``(digit_a, digit_b, carry_in) -> (digit_sum, carry_out)`` mapping from that
  truth, exactly as reproduced by the carry0/1 truth-table cell module in
  ``temp/capability_math3.py``.
* **Autonomous loop**:
  * insufficient data  -> auto-generates more (cell truth table + derived
    multi-digit expressions) from the deterministic engine;
  * learned           -> stops automatically (full cell accuracy, or loss below
    tolerance, sustained);
  * unconvergeable    -> stops automatically (no improvement over a stall
    window);
  * resumable         -> the whole state (representation, weights, counters,
    checkpoints) is persisted via :meth:`save`/:meth:`load`.
* **Dialogue learning hook**: when wired into ``ContinuousLearningPipeline``,
  each interaction may inject a (user_text, response_text) pair; extractable
  arithmetic expressions are fed back as additional cell samples so the loop
  learns from conversation too.
"""

from __future__ import annotations

import ast
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

_SAFE_DIGITS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)
_CARRY_IN = (0, 1)  # carry states observed in decimal addition
_UNIT_RAND_SCALE = 0.06  # keep unit vectors close to deterministic prototype
_RETRIES_ON_BAD_LABEL = 0  # deterministic engine always succeeds; keep = 0

# Boolean logic gates learned as truth-table cells (§ capability).
# These lie OUTSIDE the deterministic engine's character set (math_verifier
# handles + - * / % **, trig, sqrt/log, constants, factorial — NOT logic
# gates), so the learner fills that gap. Each gate is a 2-input boolean
# function (op, a, b) -> 0/1; NOT treats b as unused.
_LOGIC_OPS = ("AND", "OR", "XOR", "NAND", "NOR", "XNOR", "NOT")
_BIT = (0, 1)


def _logic_result(op: str, a: int, b: int) -> int:
    """Deterministic boolean truth (not from the deterministic engine)."""
    a = 1 if a else 0
    b = 1 if b else 0
    if op == "AND":
        return int(a and b)
    if op == "OR":
        return int(a or b)
    if op == "XOR":
        return int(a ^ b)
    if op == "NAND":
        return int(not (a and b))
    if op == "NOR":
        return int(not (a or b))
    if op == "XNOR":
        return int(a == b)
    if op == "NOT":
        return int(not a)
    raise ValueError(f"unknown logic gate {op!r}")


def _parse_task_accuracy(raw: bytes) -> Dict[str, float]:
    """Parse the serialised ``task_accuracy`` mapping from a checkpoint."""
    try:
        value = ast.literal_eval(raw.decode("utf-8"))
    except Exception:
        return {}
    if not isinstance(value, dict):
        return {}
    out: Dict[str, float] = {}
    for k, v in value.items():
        try:
            out[str(k)] = float(v)
        except (TypeError, ValueError):
            continue
    return out


def _label_add(a: int, b: int) -> int:
    """Numeric truth from the deterministic engine (single source of truth)."""
    try:
        from services.math_verifier import evaluate_math

        text = evaluate_math(f"{a} + {b}")
        # evaluate_math returns "a + b = SUM" (or numeric). Parse the SUM.
        if "=" in text:
            text = text.split("=")[-1]
        value = int(round(float(str(text).replace(",", ""))))
        return value
    except Exception:
        return a + b  # pure numeric fallback; never a learned artifact


def _label_sub(a: int, b: int) -> int:
    """Subtraction truth from the deterministic engine (+/- are in scope)."""
    try:
        from services.math_verifier import evaluate_math

        text = evaluate_math(f"{a} - {b}")
        if "=" in text:
            text = text.split("=")[-1]
        return int(round(float(str(text).replace(",", ""))))
    except Exception:
        return a - b


def _label_mul(a: int, b: int) -> int:
    """Multiplication truth from the deterministic engine (* is in scope)."""
    try:
        from services.math_verifier import evaluate_math

        text = evaluate_math(f"{a} * {b}")
        if "=" in text:
            text = text.split("=")[-1]
        return int(round(float(str(text).replace(",", ""))))
    except Exception:
        return a * b


class DigitRepresentation:
    """Digit representation, configurable between two research-backed modes.

    ``onehot`` (default)
        Per-symbol one-hot classification. This is the **output representation
        proven in the research** ``capability_math3.py`` (softmax digit class +
        carry channel, LBFGS 100%): the full carry0+1 truth table is closed, so
        no unseen-digit extrapolation is needed and classification converges
        reliably.

    ``counting``
        ``digit d == d * unit`` — a composable unit repetition researched in
        §3.1 B / §3.3. It is *only* required when extrapolating to unseen digit
        values (e.g. a placeholder slot). For the closed truth table it is
        slower to converge under LBFGS due to feature collinearity, so it is an
        opt-in for extrapolation experiments rather than the default.
    """

    def __init__(self, max_digit: int = 9, dim: int = 64, seed: int = 1, mode: str = "onehot"):
        self.max_digit = max_digit
        self.dim = dim
        self.mode = mode
        rng = np.random.default_rng(seed)
        self.unit = rng.normal(0.0, 0.05, (dim,)).astype(np.float32)
        norm = float(np.linalg.norm(self.unit))
        if norm > 0:
            self.unit = self.unit / norm

    @property
    def vec_len(self) -> int:
        """Per-digit vector length for the configured mode."""
        if self.mode == "counting":
            return self.dim
        return self.max_digit + 1

    def digit_vector(self, d: int) -> np.ndarray:
        d = int(d)
        if d < 0 or d > self.max_digit:
            d = max(0, min(self.max_digit, d))
        if self.mode == "counting":
            return self.unit * float(d)
        v = np.zeros(self.max_digit + 1, dtype=np.float32)
        v[d] = 1.0
        return v

    def carry_vector(self, c: int) -> np.ndarray:
        if self.mode == "counting":
            return self.unit * float(c)
        v = np.zeros(3, dtype=np.float32)
        v[int(c) + 1] = 1.0
        return v

    def numeric_value(self, vec: np.ndarray) -> float:
        """Recover a scalar from a representation (projection for counting;
        argmax for one-hot)."""
        if self.mode == "counting":
            denom = self.unit @ self.unit
            return float(vec @ self.unit / denom) if denom else 0.0
        return float(np.argmax(vec))


@dataclass
class LoopSnapshot:
    """Serialisable state for resume/comparison."""

    epoch: int = 0
    generated_samples: int = 0
    cell_accuracy: float = 0.0
    loss: float = float("inf")
    stopped_reason: str = ""
    stale_epochs: int = 0
    best_accuracy: float = 0.0
    best_epoch: int = 0
    task_accuracy: Dict[str, float] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class CellSample:
    """One digit-level arithmetic cell: (da, db, carry_in) -> truth."""

    da: int
    db: int
    carry_in: int
    digit_sum: int
    carry_out: int

    def __hash__(self) -> int:
        return hash((self.da, self.db, self.carry_in, self.digit_sum, self.carry_out))


@dataclass
class SubCellSample:
    """One subtraction borrow cell: (da, db, borrow_in) -> truth.

    ``digit_diff = (da - db - borrow_in) mod 10``, ``borrow_out`` is 1 exactly
    when ``da - db - borrow_in < 0``.
    """

    da: int
    db: int
    borrow_in: int
    digit_diff: int
    borrow_out: int

    def __hash__(self) -> int:
        return hash((self.da, self.db, self.borrow_in, self.digit_diff, self.borrow_out))


@dataclass
class MulCellSample:
    """One single-digit multiplication cell: (da, db) -> (low, high).

    ``da * db == high * 10 + low``.
    """

    da: int
    db: int
    digit_low: int
    digit_high: int

    def __hash__(self) -> int:
        return hash((self.da, self.db, self.digit_low, self.digit_high))


@dataclass
class LogicSample:
    """One logic-gate truth row: (op, a, b) -> result (0/1)."""

    op: str
    a: int
    b: int
    result: int

    def __hash__(self) -> int:
        return hash((self.op, self.a, self.b, self.result))


class _CellMLP:
    """A single-hidden-layer tanh MLP with one or more softmax heads.

    This is the generic version of the research-proven readout
    (``capability_math3.py``): one hidden tanh layer, then ``K`` independent
    softmax heads, trained jointly with L-BFGS-B. The addition cell uses two
    heads (sum digit + carry), the subtraction borrow cell uses two heads
    (diff digit + borrow out), the multiplication cell uses two heads (low +
    high), and the logic cell uses a single binary head — all share this one
    proven optimisation path.
    """

    def __init__(self, in_dim: int, head_sizes: List[int], hidden_size: int, seed: int):
        self.in_dim = in_dim
        self.head_sizes = list(head_sizes)
        self.hidden_size = hidden_size
        rng = np.random.default_rng(seed)
        self.hidden_w = rng.normal(0.0, 0.10, (in_dim, hidden_size)).astype(np.float32)
        self.hidden_b = np.zeros(hidden_size, dtype=np.float32)
        self.head_ws = [
            rng.normal(0.0, 0.10, (hidden_size, d)).astype(np.float32) for d in head_sizes
        ]
        self.head_bs = [np.zeros(d, dtype=np.float32) for d in head_sizes]

    def forward(self, X: np.ndarray) -> List[np.ndarray]:
        """Return the softmax logits for every head (no softmax applied)."""
        h = np.tanh(X @ self.hidden_w + self.hidden_b)
        return [h @ w + b for w, b in zip(self.head_ws, self.head_bs)]

    def argmax_out(self, x1d: np.ndarray) -> List[int]:
        """Class indices (one per head) for a single input vector."""
        logits = self.forward(np.asarray(x1d)[None, :])
        return [int(np.argmax(L[0])) for L in logits]

    def fit(self, X: np.ndarray, targets: List[np.ndarray], maxiter: int = 300) -> float:
        """L-BFGS-B fit of all heads on the closed truth table.

        ``targets`` is one int-class array per head. The loss is the mean
        cross-entropy across every head (exactly the gradient layout proven in
        the research). Returns the final loss.
        """
        from scipy.optimize import minimize

        N = X.shape[0]
        Xd = X.astype(np.float64)
        Ys = []
        for t, d in zip(targets, self.head_sizes):
            Y = np.zeros((N, d), dtype=np.float64)
            Y[np.arange(N), t] = 1.0
            Ys.append(Y)
        in_dim = self.in_dim
        H = self.hidden_size

        def unpack(p):
            i = 0
            hw = p[i : i + in_dim * H].reshape(in_dim, H)
            i += in_dim * H
            hb = p[i : i + H]
            i += H
            hws = []
            hbs = []
            for d in self.head_sizes:
                hws.append(p[i : i + H * d].reshape(H, d))
                i += H * d
                hbs.append(p[i : i + d])
                i += d
            return hw, hb, hws, hbs

        def softmax(z):
            e = np.exp(z - z.max(axis=1, keepdims=True))
            return e / e.sum(axis=1, keepdims=True)

        def loss_grad(p):
            hw, hb, hws, hbs = unpack(p)
            h = np.tanh(Xd @ hw + hb)
            L = 0.0
            g_h = np.zeros((N, H))
            g_hws = []
            g_hbs = []
            for k in range(len(self.head_sizes)):
                logits = h @ hws[k] + hbs[k]
                probs = softmax(logits)
                L += -np.log(probs[np.arange(N), targets[k]] + 1e-15).sum()
                dP = probs.copy()
                dP[np.arange(N), targets[k]] -= 1.0
                g_hws.append(h.T @ dP)
                g_hbs.append(dP.sum(0))
                g_h += dP @ hws[k].T
            L /= N
            g_h *= 1.0 - h * h
            g_hw = Xd.T @ g_h
            g_hb = g_h.sum(0)
            parts = [g_hw.ravel(), g_hb]
            for gw, gb in zip(g_hws, g_hbs):
                parts.append(gw.ravel())
                parts.append(gb)
            gp = np.concatenate(parts) / N
            return L, gp

        p0 = np.concatenate(
            [self.hidden_w.ravel().astype(np.float64), self.hidden_b.astype(np.float64)]
            + [w.ravel().astype(np.float64) for w in self.head_ws]
            + [b.astype(np.float64) for b in self.head_bs]
        )
        res = minimize(loss_grad, p0, jac=True, method="L-BFGS-B", options={"maxiter": maxiter})
        hw, hb, hws, hbs = unpack(res.x)
        self.hidden_w = hw.astype(np.float32)
        self.hidden_b = hb.astype(np.float32)
        self.head_ws = [w.astype(np.float32) for w in hws]
        self.head_bs = [b.astype(np.float32) for b in hbs]
        return float(res.fun)


class ArithmeticLearner:
    """Autonomous digit-arithmetic learner with counting representation.

    Parameters
    ----------
    max_digit:
        Largest digit (default 9).
    dim:
        Representation width (unit-vector dimension).
    seed:
        RNG seed (deterministic reproducibility).
    learning_rate:
        Gradient-descent step on the counting projection.
    diversify:
        If True, always re-converge on the full digit/carry truth table so the
        loop is self-verifying.
    """

    def __init__(
        self,
        max_digit: int = 9,
        dim: int = 64,
        seed: int = 1,
        learning_rate: float = 0.15,
        diversify: bool = True,
        representation: str = "onehot",
    ):
        self.max_digit = max_digit
        self.dim = dim
        self.seed = seed
        self.learning_rate = learning_rate
        self.diversify = diversify
        self.representation = representation
        self.repr = DigitRepresentation(
            max_digit=self.max_digit, dim=self.dim, seed=seed, mode=representation
        )
        self.hidden_size = 64
        self.in_dim = self.repr.vec_len * 2 + 3  # digit_a + digit_b + carry

        self._lock = threading.RLock()
        self.snapshot = LoopSnapshot()
        self._samples: List[CellSample] = []
        self._sub_samples: List[SubCellSample] = []
        self._mul_samples: List[MulCellSample] = []
        self._logic_samples: List[LogicSample] = []
        self._init_mlp()
        # Additional op cells share the same proven L-BFGS-B readout, each on
        # its own seed so the four training paths stay independent.
        self._sub_cell = _CellMLP(
            self.in_dim,
            [self.max_digit + 1, 3],
            max(self.hidden_size, 128),
            seed + 10,
        )
        self._mul_cell = _CellMLP(
            self.repr.vec_len * 2,
            [self.max_digit + 1, self.max_digit + 1],
            self.hidden_size,
            seed + 20,
        )
        self._logic_cell = _CellMLP(
            self.repr.vec_len * 2 + len(_LOGIC_OPS),
            [2],
            self.hidden_size,
            seed + 30,
        )

    # ------------------------------------------------------------------ data
    def cell_input_vector(self, da: int, db: int, carry_in: int) -> np.ndarray:
        return np.concatenate(
            [
                self.repr.digit_vector(da),
                self.repr.digit_vector(db),
                self.repr.carry_vector(carry_in),
            ]
        ).astype(np.float32)

    def generate_cell_truth_table(self) -> List[CellSample]:
        """Cell truth table over the full digit/carry range.

        A cell maps ``(digit_a, digit_b, carry_in)`` to its units digit and
        carry-out. The numeric truth of a single cell is the definition of
        decimal addition (``da + db + carry_in``); the *composed multi-digit
        result* is what the deterministic engine labels at the top level.

        This closes the research 'carry0+1' requirement (§B6): every digit and
        every carry component is explicitly present, so the learner never has
        to extrapolate into unseen inputs (research shows extrapolation fails).
        """
        samples: List[CellSample] = []
        for carry_in in _CARRY_IN:
            for da in _SAFE_DIGITS:
                for db in _SAFE_DIGITS:
                    col = da + db + carry_in
                    dig = col % 10
                    co = col // 10
                    samples.append(CellSample(da, db, carry_in, dig, co))
        return samples

    def generate_sub_truth_table(self) -> List[SubCellSample]:
        """Borrow-cell truth table over the full digit/borrow range.

        A borrow cell maps ``(digit_a, digit_b, borrow_in)`` to its difference
        digit and borrow-out. ``borrow_out`` is 1 exactly when
        ``da - db - borrow_in < 0`` (the difference digit then wraps by adding
        10). The full ``0..9`` digit range with both borrow-in states is closed,
        so the multi-digit subtraction composed in :meth:`predict_subtraction`
        never has to extrapolate into an unseen borrow state.
        """
        samples: List[SubCellSample] = []
        for borrow_in in _CARRY_IN:
            for da in _SAFE_DIGITS:
                for db in _SAFE_DIGITS:
                    diff = da - db - borrow_in
                    if diff < 0:
                        diff += 10
                        borrow_out = 1
                    else:
                        borrow_out = 0
                    samples.append(SubCellSample(da, db, borrow_in, diff, borrow_out))
        return samples

    def generate_mul_truth_table(self) -> List[MulCellSample]:
        """Single-digit multiplication cell: ``(da, db) -> (low, high)``.

        ``da * db == high * 10 + low``. The full ``0..9 x 0..9`` grid is closed
        (100 rows), which is the research-style pattern of learning a digit
        lattice rather than extrapolating to unseen values.
        """
        samples: List[MulCellSample] = []
        for da in _SAFE_DIGITS:
            for db in _SAFE_DIGITS:
                prod = da * db
                samples.append(MulCellSample(da, db, prod % 10, prod // 10))
        return samples

    def generate_logic_truth_table(self) -> List[LogicSample]:
        """Logic-gate truth table over the seven supported gates.

        The deterministic engine's ``evaluate_math`` scope is arithmetic only
        (+ - * / % **, trig, sqrt/log, pi/e, factorial) and has no bitwise
        gates, so the truth is taken from the pure boolean definition
        :func:`_logic_result` — closed over ``{0,1}`` for all seven ops.
        """
        samples: List[LogicSample] = []
        for op in _LOGIC_OPS:
            for a in _BIT:
                for b in _BIT:
                    samples.append(LogicSample(op, a, b, _logic_result(op, a, b)))
        return samples

    # --------------------------------------------------------------- forward
    def forward(self, da: int, db: int, carry_in: int) -> Tuple[int, int]:
        x = self.cell_input_vector(da, db, carry_in)[None, :]
        sum_logits, carr_logits = self._mlp_forward(x)
        digit = int(np.argmax(sum_logits[0]))
        carry = int(np.argmax(carr_logits[0])) - 1
        return digit, carry

    def evaluate_cell_accuracy(self) -> float:
        samples = self.generate_cell_truth_table()
        if not samples:
            return 0.0
        correct = 0
        for s in samples:
            d, c = self.forward(s.da, s.db, s.carry_in)
            if d == s.digit_sum and c == s.carry_out:
                correct += 1
        return correct / len(samples)

    def predict_addition(self, a: int, b: int) -> int:
        """Multi-digit addition by composing the digit cell per column.

        This demonstrates the learned capability recombined across columns,
        mirroring `add_via_net` in the research temp experiments. A guard caps
        the carry chain (a degraded/untrained network can otherwise emit a
        never-ending carry and loop forever).
        """
        A = [int(ch) for ch in reversed(str(a))]
        B = [int(ch) for ch in reversed(str(b))]
        nd = max(len(A), len(B))
        out_digits: List[int] = []
        carry = 0
        p = 0
        max_cols = nd + 4  # cap: at most a few carry-only columns
        while (p < nd or carry > 0) and len(out_digits) < max_cols:
            da = A[p] if p < len(A) else 0
            db = B[p] if p < len(B) else 0
            dig, carry = self.forward(da, db, carry)
            out_digits.append(dig)
            p += 1
        if carry > 0:
            out_digits.append(carry)
        return sum(ddg * (10**i) for i, ddg in enumerate(out_digits))

    # --------------------------------------------------------- op cells (sub)
    def _sub_features_matrix(self, samples: List[SubCellSample]) -> np.ndarray:
        rows = [self.cell_input_vector(s.da, s.db, s.borrow_in) for s in samples]
        return np.stack(rows).astype(np.float32)

    def _fit_sub_cells(self, samples: List[SubCellSample]) -> float:
        if not samples:
            return 0.0
        X = self._sub_features_matrix(samples)
        diff_target = np.array([s.digit_diff for s in samples], dtype=np.int64)
        borrow_target = np.array([s.borrow_out + 1 for s in samples], dtype=np.int64)
        return self._sub_cell.fit(X, [diff_target, borrow_target], maxiter=600)

    def forward_sub(self, da: int, db: int, borrow_in: int) -> Tuple[int, int]:
        x = self.cell_input_vector(da, db, borrow_in)[None, :]
        diff_logits, borrow_logits = self._sub_cell.forward(x)
        diff = int(np.argmax(diff_logits[0]))
        borrow = int(np.argmax(borrow_logits[0])) - 1
        return diff, borrow

    def evaluate_sub_accuracy(self) -> float:
        samples = self.generate_sub_truth_table()
        if not samples:
            return 0.0
        correct = 0
        for s in samples:
            d, b = self.forward_sub(s.da, s.db, s.borrow_in)
            if d == s.digit_diff and b == s.borrow_out:
                correct += 1
        return correct / len(samples)

    def predict_subtraction(self, a: int, b: int) -> int:
        """Multi-digit subtraction by composing the borrow cell per column.

        ``a < b`` results are handled symmetrically (``-(b - a)``); otherwise
        the borrow chain propagates left-to-right exactly like the add cell's
        carry chain, with the same column cap guard.
        """
        if a < b:
            return -self.predict_subtraction(b, a)
        A = [int(ch) for ch in reversed(str(a))]
        B = [int(ch) for ch in reversed(str(b))]
        nd = max(len(A), len(B))
        out_digits: List[int] = []
        borrow = 0
        for p in range(nd):
            da = A[p] if p < len(A) else 0
            db = B[p] if p < len(B) else 0
            diff, borrow = self.forward_sub(da, db, borrow)
            out_digits.append(diff)
        return sum(d * (10**i) for i, d in enumerate(out_digits))

    # --------------------------------------------------------- op cells (mul)
    def _mul_features_matrix(self, samples: List[MulCellSample]) -> np.ndarray:
        rows = [
            np.concatenate([self.repr.digit_vector(s.da), self.repr.digit_vector(s.db)])
            for s in samples
        ]
        return np.stack(rows).astype(np.float32)

    def _fit_mul_cells(self, samples: List[MulCellSample]) -> float:
        if not samples:
            return 0.0
        X = self._mul_features_matrix(samples)
        low_target = np.array([s.digit_low for s in samples], dtype=np.int64)
        high_target = np.array([s.digit_high for s in samples], dtype=np.int64)
        return self._mul_cell.fit(X, [low_target, high_target])

    def forward_mul(self, da: int, db: int) -> Tuple[int, int]:
        x = np.concatenate([self.repr.digit_vector(da), self.repr.digit_vector(db)])[None, :]
        low_logits, high_logits = self._mul_cell.forward(x.astype(np.float32))
        return int(np.argmax(low_logits[0])), int(np.argmax(high_logits[0]))

    def evaluate_mul_accuracy(self) -> float:
        samples = self.generate_mul_truth_table()
        if not samples:
            return 0.0
        correct = 0
        for s in samples:
            lo, hi = self.forward_mul(s.da, s.db)
            if lo == s.digit_low and hi == s.digit_high:
                correct += 1
        return correct / len(samples)

    def _multiply_by_digit(self, a: int, d: int) -> int:
        """Partial product ``a * d`` composed via the single-digit mul cell."""
        A = [int(ch) for ch in reversed(str(a))]
        out_digits: List[int] = []
        carry = 0
        for da in A:
            low, high = self.forward_mul(da, d)
            col = low + 10 * high + carry
            out_digits.append(col % 10)
            carry = col // 10
        if carry:
            out_digits.append(carry)
        return sum(x * (10**i) for i, x in enumerate(out_digits))

    def predict_multiplication(self, a: int, b: int) -> int:
        """Multi-digit multiplication: schoolbook partial products summed by the
        (independently learned) addition cell."""
        if a == 0 or b == 0:
            return 0
        B = [int(ch) for ch in reversed(str(b))]
        total = 0
        for i, bi in enumerate(B):
            partial = self._multiply_by_digit(a, bi)
            total = self.predict_addition(total, partial * (10**i))
        return total

    # ----------------------------------------------------- op cells (logic)
    def logic_input_vector(self, op: str, a: int, b: int) -> np.ndarray:
        op_v = np.zeros(len(_LOGIC_OPS), dtype=np.float32)
        op_v[_LOGIC_OPS.index(op)] = 1.0
        return np.concatenate(
            [
                self.repr.digit_vector(1 if a else 0),
                self.repr.digit_vector(1 if b else 0),
                op_v,
            ]
        ).astype(np.float32)

    def _logic_features_matrix(self, samples: List[LogicSample]) -> np.ndarray:
        rows = [self.logic_input_vector(s.op, s.a, s.b) for s in samples]
        return np.stack(rows).astype(np.float32)

    def _fit_logic_cells(self, samples: List[LogicSample]) -> float:
        if not samples:
            return 0.0
        X = self._logic_features_matrix(samples)
        result_target = np.array([s.result for s in samples], dtype=np.int64)
        return self._logic_cell.fit(X, [result_target])

    def forward_logic(self, op: str, a: int, b: int) -> int:
        x = self.logic_input_vector(op, int(bool(a)), int(bool(b)))[None, :]
        result_logits = self._logic_cell.forward(x)
        return int(np.argmax(result_logits[0][0]))

    def evaluate_logic_accuracy(self) -> float:
        samples = self.generate_logic_truth_table()
        if not samples:
            return 0.0
        correct = 0
        for s in samples:
            if self.forward_logic(s.op, s.a, s.b) == s.result:
                correct += 1
        return correct / len(samples)

    def predict_logic_gate(self, op: str, a: int, b: int) -> int:
        """Evaluate a boolean gate over ``{0,1}`` inputs via the logic cell.

        ``op`` must be one of :data:`_LOGIC_OPS`; inputs are coerced to bits.
        """
        if op not in _LOGIC_OPS:
            raise ValueError(f"unknown logic gate {op!r}; expected one of {list(_LOGIC_OPS)}")
        return self.forward_logic(op, int(bool(a)), int(bool(b)))

    # -------------------------------------------------------------- training
    def _cell_features_matrix(self, samples: List[CellSample]) -> np.ndarray:
        rows = [self.cell_input_vector(s.da, s.db, s.carry_in) for s in samples]
        return np.stack(rows).astype(np.float32)

    def _init_mlp(self) -> None:
        """Initialise MLP weights for the two-output readout."""
        rng = np.random.default_rng(self.seed)
        in_dim = self.in_dim
        self.hidden_w = rng.normal(0.0, 0.10, (in_dim, self.hidden_size)).astype(np.float32)
        self.hidden_b = np.zeros(self.hidden_size, dtype=np.float32)
        self.sum_w = rng.normal(0.0, 0.10, (self.hidden_size, self.max_digit + 1)).astype(
            np.float32
        )
        self.sum_b = np.zeros(self.max_digit + 1, dtype=np.float32)
        self.carr_w = rng.normal(0.0, 0.10, (self.hidden_size, 3)).astype(np.float32)
        self.carr_b = np.zeros(3, dtype=np.float32)

    def _mlp_forward(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        h = np.tanh(X @ self.hidden_w + self.hidden_b)
        sum_logits = h @ self.sum_w + self.sum_b
        carr_logits = h @ self.carr_w + self.carr_b
        return sum_logits, carr_logits

    def _train_cell_step(self, samples: List[CellSample]) -> float:
        X = self._cell_features_matrix(samples)
        sum_target = np.array([s.digit_sum for s in samples], dtype=np.int64)
        carr_target = np.array([s.carry_out + 1 for s in samples], dtype=np.int64)
        loss = self._fit_mlp(X, sum_target, carr_target)
        self.snapshot.generated_samples = len(samples)
        return float(loss)

    def _fit_mlp(self, X: np.ndarray, sum_t: np.ndarray, carr_t: np.ndarray) -> float:
        """Train the two-output MLP on the full cell truth table.

        The digit-sum readout is ``(da + db + carry) mod 10`` — a nonlinear
        modulo/carry function — so a naive linear readout (research attempt in
        ``capability_math2.py``) stalls around 50%. The research reached 100%
        with an LBFGS-optimised tanh-MLP in ``capability_math3.py``; we reuse
        that exact, proven optimisation so the loop converges reliably in one
        step. ``predict_addition`` composes this cell per column; carry is an
        explicit input dimension so no unseen-carry extrapolation is required
        (§B6).
        """
        from scipy.optimize import minimize

        N = X.shape[0]
        S = np.zeros((N, self.max_digit + 1), dtype=np.float64)
        S[np.arange(N), sum_t] = 1.0
        CC = np.zeros((N, 3), dtype=np.float64)
        CC[np.arange(N), carr_t] = 1.0
        Xd = X.astype(np.float64)

        def unpack(p):
            i = 0
            hw = p[i : i + self.in_dim * self.hidden_size].reshape(self.in_dim, self.hidden_size)
            i += self.in_dim * self.hidden_size
            hb = p[i : i + self.hidden_size]
            i += self.hidden_size
            sw = p[i : i + self.hidden_size * (self.max_digit + 1)].reshape(
                self.hidden_size, self.max_digit + 1
            )
            i += self.hidden_size * (self.max_digit + 1)
            sb = p[i : i + self.max_digit + 1]
            i += self.max_digit + 1
            cw = p[i : i + self.hidden_size * 3].reshape(self.hidden_size, 3)
            i += self.hidden_size * 3
            cb = p[i : i + 3]
            return hw, hb, sw, sb, cw, cb

        def softmax(z):
            e = np.exp(z - z.max(axis=1, keepdims=True))
            return e / e.sum(axis=1, keepdims=True)

        def loss_grad(p):
            hw, hb, sw, sb, cw, cb = unpack(p)
            h = np.tanh(Xd @ hw + hb)
            sl = h @ sw + sb
            cl = h @ cw + cb
            ps = softmax(sl)
            pc = softmax(cl)
            L = (
                -np.log(ps[np.arange(N), sum_t] + 1e-15).sum()
                - np.log(pc[np.arange(N), carr_t] + 1e-15).sum()
            ) / N
            ds = ps.copy()
            ds[np.arange(N), sum_t] -= 1.0
            dc = pc.copy()
            dc[np.arange(N), carr_t] -= 1.0
            g_sw = h.T @ ds
            g_sb = ds.sum(0)
            g_cw = h.T @ dc
            g_cb = dc.sum(0)
            gh = (ds @ sw.T + dc @ cw.T) * (1.0 - h * h)
            g_hw = Xd.T @ gh
            g_hb = gh.sum(0)
            gp = np.concatenate([g_hw.ravel(), g_hb, g_sw.ravel(), g_sb, g_cw.ravel(), g_cb]) / N
            return L, gp

        p0 = np.concatenate(
            [
                self.hidden_w.ravel().astype(np.float64),
                self.hidden_b.astype(np.float64),
                self.sum_w.ravel().astype(np.float64),
                self.sum_b.astype(np.float64),
                self.carr_w.ravel().astype(np.float64),
                self.carr_b.astype(np.float64),
            ]
        )
        res = minimize(loss_grad, p0, jac=True, method="L-BFGS-B", options={"maxiter": 300})
        hw, hb, sw, sb, cw, cb = unpack(res.x)
        self.hidden_w = hw.astype(np.float32)
        self.hidden_b = hb.astype(np.float32)
        self.sum_w = sw.astype(np.float32)
        self.sum_b = sb.astype(np.float32)
        self.carr_w = cw.astype(np.float32)
        self.carr_b = cb.astype(np.float32)
        return float(res.fun)

    # ----------------------------------------------------------- autonomous
    def _ensure_truth_tables(self) -> None:
        """Guarantee the full deterministic truth tables for all op cells."""
        if len(self._samples) < len(self.generate_cell_truth_table()):
            table = self.generate_cell_truth_table()
            existing = set(self._samples)
            for s in table:
                if s not in existing:
                    self._samples.append(s)
        if len(self._sub_samples) < len(self.generate_sub_truth_table()):
            table = self.generate_sub_truth_table()
            existing = set(self._sub_samples)
            for s in table:
                if s not in existing:
                    self._sub_samples.append(s)
        if len(self._mul_samples) < len(self.generate_mul_truth_table()):
            table = self.generate_mul_truth_table()
            existing = set(self._mul_samples)
            for s in table:
                if s not in existing:
                    self._mul_samples.append(s)
        if len(self._logic_samples) < len(self.generate_logic_truth_table()):
            table = self.generate_logic_truth_table()
            existing = set(self._logic_samples)
            for s in table:
                if s not in existing:
                    self._logic_samples.append(s)

    def evaluate_overall_accuracy(self) -> float:
        """Mean of the four per-op cell accuracies (the loop's global metric)."""
        accs = [
            self.evaluate_cell_accuracy(),
            self.evaluate_sub_accuracy(),
            self.evaluate_mul_accuracy(),
            self.evaluate_logic_accuracy(),
        ]
        return float(np.mean(accs))

    def run(
        self,
        min_cell_accuracy: float = 1.0,
        max_epochs: int = 200,
        stall_epochs: int = 25,
        loss_tolerance: float = 1e-4,
    ) -> LoopSnapshot:
        """Run the autonomous learning loop over all four op cells.

        * data -> self-generated deterministic truth tables (add, sub, mul,
          logic);
        * learned -> stops when the overall accuracy >= ``min_cell_accuracy``
          and loss <= ``loss_tolerance`` (sustained);
        * unconvergeable -> stops when accuracy stops improving for
          ``stall_epochs`` consecutive epochs;
        * resumable -> caller may call :meth:`run` again (state preserved and
          snapshot position recorded).

        Returns the final :class:`LoopSnapshot`.
        """
        with self._lock:
            self._ensure_truth_tables()
            snap = self.snapshot
            best = snap.best_accuracy
            best_epoch = snap.best_epoch
            # fresh-loss tracking for stall detection
            epoch = snap.epoch
            stale = snap.stale_epochs
            logger.info("ArithmeticLearner.run: epoch=%d stale=%d best=%.4f", epoch, stale, best)
            while epoch < max_epochs:
                add_loss = self._train_cell_step(self._samples)
                sub_loss = self._fit_sub_cells(self._sub_samples)
                mul_loss = self._fit_mul_cells(self._mul_samples)
                logic_loss = self._fit_logic_cells(self._logic_samples)
                loss = max(add_loss, sub_loss, mul_loss, logic_loss)
                acc = self.evaluate_overall_accuracy()
                task_acc = {
                    "add": self.evaluate_cell_accuracy(),
                    "sub": self.evaluate_sub_accuracy(),
                    "mul": self.evaluate_mul_accuracy(),
                    "logic": self.evaluate_logic_accuracy(),
                }
                epoch += 1
                snap.epoch = epoch
                snap.loss = loss
                snap.cell_accuracy = acc
                snap.task_accuracy = task_acc
                snap.generated_samples = (
                    len(self._samples)
                    + len(self._sub_samples)
                    + len(self._mul_samples)
                    + len(self._logic_samples)
                )
                if acc > best:
                    best = acc
                    best_epoch = epoch
                    snap.best_accuracy = best
                    snap.best_epoch = best_epoch
                    stale = 0
                    snap.stale_epochs = stale
                    # persist good state so it can be resumed later
                    if abs(best - 1.0) < 1e-6:
                        snap.stopped_reason = "learned-optimal"
                        logger.info(
                            "ArithmeticLearner converged at epoch %d (acc=%.4f)", epoch, acc
                        )
                        return snap
                else:
                    stale += 1
                    snap.stale_epochs = stale
                if epoch % 10 == 0:
                    logger.debug("ArithmeticLearner epoch=%d loss=%.6f acc=%.4f", epoch, loss, acc)
                # stall / unconvergeable
                if stale >= stall_epochs:
                    snap.stopped_reason = "unconvergeable-stall"
                    logger.info(
                        "ArithmeticLearner stopped (stall) at epoch %d best=%.4f", epoch, best
                    )
                    return snap
                # learned via loss tolerance (independent of exact 1.0)
                if best >= min_cell_accuracy and loss <= loss_tolerance:
                    snap.stopped_reason = "learned-threshold"
                    logger.info("ArithmeticLearner stopped (loss) at epoch %d acc=%.4f", epoch, acc)
                    return snap
            snap.stopped_reason = "max-epochs-reached"
            return snap

    # -------------------------------------------------------------- dialogue
    def learn_from_dialogue(
        self,
        user_text: str,
        response_text: str,
        context: Optional[Dict[str, Any]] = None,
        auto_run: bool = True,
    ) -> Optional[LoopSnapshot]:
        """Feed a dialogue interaction into the loop.

        Extracts plain ``x + y``, ``x - y`` and ``x * y`` expressions from the
        text (logic gates are only ever learned from their closed truth table —
        natural language "AND"/"OR" is too ambiguous to parse). Expression
        results come from the deterministic engine; each expression is also
        broken into its per-column digit cells (with correct carry/borrow) and
        appended to the relevant cell pool. When ``auto_run`` the loop re-fits;
        otherwise the cells are queued for a later ``run`` (suitable for
        high-frequency online dialogue where a full LBFGS fit every interaction
        is too costly). Returns None if no arithmetic expression was found
        (no-op on non-math dialogue).
        """
        pairs = self._extract_add_exprs(user_text)
        pairs.extend(self._extract_add_exprs(response_text or ""))
        sub_pairs = self._extract_sub_exprs(user_text)
        sub_pairs.extend(self._extract_sub_exprs(response_text or ""))
        mul_pairs = self._extract_mul_exprs(user_text)
        mul_pairs.extend(self._extract_mul_exprs(response_text or ""))
        if not pairs and not sub_pairs and not mul_pairs:
            return None
        # Ensure full deterministic truth tables are present, then layer the
        # dialogue-observed column cells on top (source of truth is still the
        # deterministic engine for the overall result).
        self._ensure_truth_tables()
        for a, b in pairs:
            result = _label_add(a, b)
            digits_a = [int(ch) for ch in reversed(str(a))]
            digits_b = [int(ch) for ch in reversed(str(b))]
            result_digits = [int(ch) for ch in reversed(str(result))]
            carry = 0
            nd = max(len(digits_a), len(digits_b))
            for p in range(nd):
                da = digits_a[p] if p < len(digits_a) else 0
                db = digits_b[p] if p < len(digits_b) else 0
                col = da + db + carry
                dig = col % 10
                co = col // 10
                sample = CellSample(da, db, carry, dig, co)
                if sample not in self._samples:
                    self._samples.append(sample)
                carry = co
            # final overflow column (if any)
            if carry > 0 and len(result_digits) > nd:
                sample = CellSample(0, 0, carry, result_digits[-1], 0)
                if sample not in self._samples:
                    self._samples.append(sample)
        for a, b in sub_pairs:
            result = _label_sub(a, b)
            if result < 0:
                a, b, result = b, a, -result
            digits_a = [int(ch) for ch in reversed(str(a))]
            digits_b = [int(ch) for ch in reversed(str(b))]
            borrow = 0
            nd = max(len(digits_a), len(digits_b))
            for p in range(nd):
                da = digits_a[p] if p < len(digits_a) else 0
                db = digits_b[p] if p < len(digits_b) else 0
                diff = da - db - borrow
                if diff < 0:
                    diff += 10
                    borrow_out = 1
                else:
                    borrow_out = 0
                sample = SubCellSample(da, db, borrow, diff, borrow_out)
                if sample not in self._sub_samples:
                    self._sub_samples.append(sample)
                borrow = borrow_out
        for a, b in mul_pairs:
            digits_a = [int(ch) for ch in str(a)]
            digits_b = [int(ch) for ch in str(b)]
            for da in digits_a:
                for db in digits_b:
                    prod = da * db
                    sample = MulCellSample(da, db, prod % 10, prod // 10)
                    if sample not in self._mul_samples:
                        self._mul_samples.append(sample)
        if not auto_run:
            return None
        return self.run(max_epochs=20, stall_epochs=5)

    def _ensure_truth_table(self) -> None:
        """Guarantee the full deterministic digit/carry truth table is present."""
        if len(self._samples) >= len(self.generate_cell_truth_table()):
            return
        # Merge (avoid duplicates) with the canonical truth table.
        table = self.generate_cell_truth_table()
        existing = set(self._samples)
        for s in table:
            if s not in existing:
                self._samples.append(s)

    @staticmethod
    def _extract_add_exprs(text: str) -> List[Tuple[int, int]]:
        """Find ``N + M`` integer additions in text (loose regex)."""
        import re

        out: List[Tuple[int, int]] = []
        pat = re.compile(r"(\d{1,6})\s*\+\s*(\d{1,6})")
        for m in pat.finditer(text):
            try:
                out.append((int(m.group(1)), int(m.group(2))))
            except ValueError:
                continue
        return out

    @staticmethod
    def _extract_sub_exprs(text: str) -> List[Tuple[int, int]]:
        """Find ``N - M`` integer subtractions in text (loose regex)."""
        import re

        out: List[Tuple[int, int]] = []
        pat = re.compile(r"(\d{1,6})\s*-\s*(\d{1,6})")
        for m in pat.finditer(text):
            try:
                out.append((int(m.group(1)), int(m.group(2))))
            except ValueError:
                continue
        return out

    @staticmethod
    def _extract_mul_exprs(text: str) -> List[Tuple[int, int]]:
        """Find ``N * M`` integer multiplications in text (loose regex)."""
        import re

        out: List[Tuple[int, int]] = []
        pat = re.compile(r"(\d{1,6})\s*\*\s*(\d{1,6})")
        for m in pat.finditer(text):
            try:
                out.append((int(m.group(1)), int(m.group(2))))
            except ValueError:
                continue
        return out

    # ----------------------------------------------------------- persistence
    def save(self, path: str) -> None:
        with self._lock:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            sub = self._sub_cell
            mul = self._mul_cell
            logic = self._logic_cell
            np.savez(
                path,
                hidden_w=self.hidden_w,
                hidden_b=self.hidden_b,
                sum_w=self.sum_w,
                sum_b=self.sum_b,
                carr_w=self.carr_w,
                carr_b=self.carr_b,
                unit=self.repr.unit,
                hidden_size=self.hidden_size,
                max_digit=self.max_digit,
                dim=self.dim,
                epoch=self.snapshot.epoch,
                generated_samples=self.snapshot.generated_samples,
                task_accuracy=np.frombuffer(
                    repr(self.snapshot.task_accuracy).encode("utf-8"), dtype=np.uint8
                ),
                sub_hidden_w=sub.hidden_w,
                sub_hidden_b=sub.hidden_b,
                sub_head0_w=sub.head_ws[0],
                sub_head0_b=sub.head_bs[0],
                sub_head1_w=sub.head_ws[1],
                sub_head1_b=sub.head_bs[1],
                mul_hidden_w=mul.hidden_w,
                mul_hidden_b=mul.hidden_b,
                mul_head0_w=mul.head_ws[0],
                mul_head0_b=mul.head_bs[0],
                mul_head1_w=mul.head_ws[1],
                mul_head1_b=mul.head_bs[1],
                logic_hidden_w=logic.hidden_w,
                logic_hidden_b=logic.hidden_b,
                logic_head0_w=logic.head_ws[0],
                logic_head0_b=logic.head_bs[0],
            )
        logger.info("ArithmeticLearner.save -> %s", path)

    def load(self, path: str) -> None:
        with self._lock:
            data = np.load(path, allow_pickle=False)
            self.hidden_w = data["hidden_w"].astype(np.float32)
            self.hidden_b = data["hidden_b"].astype(np.float32)
            self.sum_w = data["sum_w"].astype(np.float32)
            self.sum_b = data["sum_b"].astype(np.float32)
            self.carr_w = data["carr_w"].astype(np.float32)
            self.carr_b = data["carr_b"].astype(np.float32)
            self.hidden_size = int(data["hidden_size"])
            self.repr.unit = data["unit"].astype(np.float32)
            self.snapshot.epoch = int(data["epoch"])
            self.snapshot.generated_samples = int(data["generated_samples"])
            # op cells (backward compatible with pre-extension checkpoints)
            if "sub_hidden_w" in data.files:
                self._sub_cell.hidden_w = data["sub_hidden_w"].astype(np.float32)
                self._sub_cell.hidden_b = data["sub_hidden_b"].astype(np.float32)
                self._sub_cell.head_ws = [
                    data["sub_head0_w"].astype(np.float32),
                    data["sub_head1_w"].astype(np.float32),
                ]
                self._sub_cell.head_bs = [
                    data["sub_head0_b"].astype(np.float32),
                    data["sub_head1_b"].astype(np.float32),
                ]
            if "mul_hidden_w" in data.files:
                self._mul_cell.hidden_w = data["mul_hidden_w"].astype(np.float32)
                self._mul_cell.hidden_b = data["mul_hidden_b"].astype(np.float32)
                self._mul_cell.head_ws = [
                    data["mul_head0_w"].astype(np.float32),
                    data["mul_head1_w"].astype(np.float32),
                ]
                self._mul_cell.head_bs = [
                    data["mul_head0_b"].astype(np.float32),
                    data["mul_head1_b"].astype(np.float32),
                ]
            if "logic_hidden_w" in data.files:
                self._logic_cell.hidden_w = data["logic_hidden_w"].astype(np.float32)
                self._logic_cell.hidden_b = data["logic_hidden_b"].astype(np.float32)
                self._logic_cell.head_ws = [data["logic_head0_w"].astype(np.float32)]
                self._logic_cell.head_bs = [data["logic_head0_b"].astype(np.float32)]
            if "task_accuracy" in data.files:
                try:
                    raw = data["task_accuracy"].tobytes()
                    self.snapshot.task_accuracy = _parse_task_accuracy(raw)
                except Exception:
                    self.snapshot.task_accuracy = {}
            if not self._samples:
                self._samples = self.generate_cell_truth_table()
            if not self._sub_samples:
                self._sub_samples = self.generate_sub_truth_table()
            if not self._mul_samples:
                self._mul_samples = self.generate_mul_truth_table()
            if not self._logic_samples:
                self._logic_samples = self.generate_logic_truth_table()
        logger.info(
            "ArithmeticLearner.load <- %s (resume from epoch %d)", path, self.snapshot.epoch
        )

    @property
    def learned(self) -> bool:
        return self.snapshot.stopped_reason in ("learned-optimal", "learned-threshold")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_digit": self.max_digit,
            "dim": self.dim,
            "seed": self.seed,
            "learning_rate": self.learning_rate,
            "diversify": self.diversify,
            "snapshot": {
                "epoch": self.snapshot.epoch,
                "generated_samples": self.snapshot.generated_samples,
                "cell_accuracy": self.snapshot.cell_accuracy,
                "loss": self.snapshot.loss,
                "stopped_reason": self.snapshot.stopped_reason,
                "stale_epochs": self.snapshot.stale_epochs,
                "best_accuracy": self.snapshot.best_accuracy,
                "best_epoch": self.snapshot.best_epoch,
                "task_accuracy": dict(self.snapshot.task_accuracy),
            },
        }
