#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""Bounded cellular machine as a third baseline on the MVE-1 task.

CORE_GAP §二十一 measured the SNN's leak at ``beta = 0.832`` — six atoms of
memory — and showed the block starts ~120 atoms after the inputs, so no decoder
at that position can recover them. That diagnosis needs a control that is
*not* the same leaky integrator: a bounded cellular machine, where the container
is finite by construction and the dynamics have no global reset, only local
fatigue.

Same-class conditions, enforced by construction:

* **Same container size, taken from the project.** The lattice holds exactly
  ``TokenConfig.max_len`` cells (192) — one cell per token the language model is
  allowed to see — laid out as ``rows x cols`` with a von Neumann neighbourhood
  and wrap-around. Nothing here is copied from an external 3x3 toy.
* **Same input.** ``TokenVocab`` with ``numeric_atoms`` from the same checkpoint,
  the same ``_encode(prompt, "<al_out>")`` prefix, the same 192-token window and
  the same train file / instrument rows as the SNN and the transformer runs.
* **Same output and same grader.** The readout predicts the six contract values
  and is scored with the probe's own unit (±0.005, all six fields) plus the same
  R²/MAE columns, so the numbers drop into the same table as
  ``mve1_value_head.json``.

Dynamics (per cell: activation, fatigue, threshold)::

    act = W_rec·x - theta - f + W_in[:, token] + noise
    x   = sigmoid(4·act)
    f   = 0.90·f + 0.10·x          # fatigue accumulates, decays locally
    theta = theta + 0.01·(x - 0.10) # threshold homeostasis

There is no ``tick % N == 0`` wipe: a saturated region is pushed back by its own
fatigue instead of being cleared, so the machine can hold a pattern for a long
time without a timer, and it cannot be emptied by one.

Two readings come out of it:

1. **retention** — a ridge readout of the six ``<al_in>`` values fitted at each
   lag from the values' own position to the block start. This is the direct
   comparison with the SNN's 6-atom memory.
2. **task** — the same readout trained on the block values, scored on the 200
   holdout rows.

Usage::

    scripts/compare_cellular_baseline.py --checkpoint data/checkpoints/ai_al_round9.pt
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = REPO_ROOT / "scripts"
_SRC = REPO_ROOT / "apps" / "backend" / "src"
for _p in (str(_SCRIPTS), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import probe_emergence_boundary as probe  # noqa: E402  (single scoring path)
from ai.ed3n.token_snn import TokenSNN  # noqa: E402

REPORT = REPO_ROOT / "data" / "intelligence_reports" / "mve1_cellular_baseline.json"
_FIELDS = probe._FIELD_KEYS


# -- the machine ------------------------------------------------------------


class BoundedCellMachine:
    """A finite lattice of fatiguing cells; no timer, no global clear."""

    def __init__(
        self,
        cells: int,
        vocab_size: int,
        seed: int = 0,
        gain: float = 2.0,
        fatigue: float = 0.98,
        noise: float = 0.01,
        homeostat: float = 0.002,
        spectral: float = 1.05,
        latch: int = 0,
        in_gain: float = 4.0,
    ) -> None:
        self.cells = int(cells)
        self.cols = int(math.ceil(math.sqrt(self.cells)))
        self.rows = int(math.ceil(self.cells / self.cols))
        # padding cells keep the lattice rectangular; they are never read
        self.pad = self.rows * self.cols - self.cells
        rng = np.random.default_rng(seed)
        # local coupling: self + 4 von Neumann neighbours, wrap-around, with
        # *mixed signs*. An all-excitatory lattice synchronises: the first run
        # ended in a uniform field (activation std 0.012 across 384 cells), so
        # the container held one number instead of a pattern. Excitatory and
        # inhibitory neighbours are what a cell assembly needs to keep contrast.
        w = np.zeros((self.rows, self.cols, self.rows, self.cols), dtype=np.float32)
        for r in range(self.rows):
            for c in range(self.cols):
                for dr, dc in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                    sign = 1.0 if (dr, dc) == (0, 0) else float(rng.choice((-1.0, 1.0)))
                    w[r, c, (r + dr) % self.rows, (c + dc) % self.cols] = sign
        # edge-of-chaos operating point: the coupling is scaled to a chosen
        # spectral radius instead of an ad-hoc 1/sqrt(5). A contracting lattice
        # (radius << 1) forgets by construction, which is what the first run
        # measured — its "memory" was the fixed point, not the input.
        base = w.reshape(self.rows * self.cols, -1) * (1.0 / math.sqrt(5.0))
        radius = float(np.max(np.abs(np.linalg.eigvals(base)))) or 1.0
        self.w_rec = (base * (spectral / radius)).astype(np.float32)
        # input scaling is a first-class knob, not a rounding detail: at
        # 1/sqrt(cells) a token moved the activation by ~0.01 while the
        # recurrent drive moved it by ~0.18, so the container held its own bias
        # and the across-row spread was 0.004 (measured). The input has to be
        # comparable to the recurrent drive or the machine is a decoration.
        self.w_in = rng.normal(0.0, in_gain * 0.5, (self.cells, vocab_size))
        self.w_in = self.w_in.astype(np.float32)
        self._rng = np.random.default_rng(seed ^ 0x5EED)
        # per-cell bias keeps the lattice heterogeneous even when the input is
        # constant, so a uniform fixed point is not the only attractor
        self.bias = rng.normal(0.0, 0.15, self.cells).astype(np.float32)
        self.gain = gain
        self.fatigue = fatigue
        self.noise = noise
        self.homeostat = homeostat
        # latch: a slow integrator per cell (tau steps). 0 disables it — the
        # pure "fatigue instead of global reset" machine of the design note.
        self.latch = int(latch)
        self.reset()

    def reset(self) -> None:
        self.x = np.full(self.cells, 0.1, dtype=np.float32)
        self.f = np.zeros(self.cells, dtype=np.float32)
        self.theta = np.zeros(self.cells, dtype=np.float32)
        self.m = np.zeros(self.cells, dtype=np.float32)

    def _pad(self, vec: np.ndarray, value: float) -> np.ndarray:
        return np.concatenate([vec, np.full(self.pad, value, dtype=np.float32)])

    def step(self, token_id: int) -> None:
        grid = self._pad(self.x, 0.1).reshape(self.rows, self.cols)
        coupling = (self.w_rec @ grid.reshape(-1))[: self.cells]
        act = coupling + self.bias - self.theta - self.f + self.w_in[:, token_id]
        if self.noise:
            act = act + self._rng.normal(0.0, self.noise, act.shape).astype(np.float32)
        self.x = (1.0 / (1.0 + np.exp(-self.gain * act))).astype(np.float32)
        self.f = (self.fatigue * self.f + (1.0 - self.fatigue) * self.x).astype(np.float32)
        self.theta = (self.theta + self.homeostat * (self.x - 0.10)).astype(np.float32)
        if self.latch:
            rate = 1.0 / float(self.latch)
            self.m = ((1.0 - rate) * self.m + rate * self.x).astype(np.float32)

    def features(self) -> np.ndarray:
        """The whole container, one block per state variable."""
        parts = [self.x, self.f, self.theta]
        if self.latch:
            parts.append(self.m)
        return np.concatenate(parts).astype(np.float32)


def _states(
    machine: BoundedCellMachine, ids: Sequence[int], indices: Sequence[int]
) -> Dict[int, np.ndarray]:
    """Run the prefix once and return the container state at each index."""
    wanted = {min(max(int(i), 0), len(ids) - 1) for i in indices}
    machine.reset()
    found: Dict[int, np.ndarray] = {}
    for step, token in enumerate(ids):
        machine.step(int(token))
        if step in wanted:
            found[step] = machine.features()
        if step >= max(wanted):
            break
    return found


# -- data -------------------------------------------------------------------


def _load_rows(
    model: Any, set_path: Path
) -> Tuple[List[Tuple[np.ndarray, List[str], int, str]], List[Dict[str, Any]]]:
    payload = json.loads(set_path.read_text(encoding="utf-8"))
    rows = probe._select(payload, "all")
    usable = [
        e for e in rows if probe._value_targets(model.vocab, str(e.get("gold", ""))) is not None
    ]
    entries: List[Dict[str, Any]] = []
    for entry in usable:
        ids, start, _end = model._encode(str(entry["prompt"]), probe._MARKER)
        entries.append({"entry": entry, "ids": ids, "start": start})
    return entries, usable


def _train_pairs(model: Any, train_path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for prompt, gold, intent in probe._train_value_pairs(train_path):
        if probe._value_targets(model.vocab, gold) is None:
            continue
        ids, start, _end = model._encode(prompt, probe._MARKER)
        out.append(
            {
                "ids": ids,
                "prompt": prompt,
                "start": start,
                "gold": [float(probe._parse_block(gold)[f]) for f in _FIELDS],
                "state": [float(probe._parse_input_line(prompt)[f]) for f in _FIELDS],
                "intent": intent,
            }
        )
    return out


def _values_at_end_of_state_line(prompt: str, model: Any, width: int) -> int:
    """Index of the last atom of the ``<al_in>`` line (where the values sit)."""
    return min(len(model.vocab.encode(str(prompt).split(" | ", 1)[0])), width - 1)


# -- readout ----------------------------------------------------------------


def _standardise(x: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = x.mean(axis=0)
    std = x.std(axis=0) + 1e-6
    return (x - mean) / std, mean, std


def _fit_readout(
    x: np.ndarray, y: np.ndarray, seed: int = 0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float, float]:
    """Standardise, then choose the ridge strength on a training slice."""
    z, mean, std = _standardise(x)
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(z))
    cut = max(1, int(0.8 * len(z)))
    tr, va = order[:cut], order[cut:]
    best: Tuple[float, float] = (-1e9, 1.0)
    for lam in (0.1, 1.0, 10.0, 100.0, 1000.0):
        w = _ridge(z[tr], y[tr], lam)
        pred = np.concatenate([z[va], np.ones((len(va), 1), dtype=z.dtype)], axis=1) @ w
        score = float(
            np.mean(
                [
                    1
                    - ((pred[:, i] - y[va][:, i]) ** 2).sum()
                    / max(1e-9, ((y[va][:, i] - y[va][:, i].mean()) ** 2).sum())
                    for i in range(y.shape[1])
                ]
            )
        )
        if score > best[0]:
            best = (score, lam)
    return _ridge(z, y, best[1]), mean, std, best[1], best[0]


def _ridge(x: np.ndarray, y: np.ndarray, lam: float) -> np.ndarray:
    xt = np.concatenate([x, np.ones((len(x), 1), dtype=x.dtype)], axis=1)
    a = xt.T @ xt + lam * np.eye(xt.shape[1], dtype=x.dtype)
    return np.linalg.solve(a, xt.T @ y)


def _score(pred: np.ndarray, gold: np.ndarray) -> Dict[str, Any]:
    err = np.abs(pred - gold)
    field_ok = err <= 0.005
    out = {
        "n": int(len(pred)),
        "row_exact": round(float(field_ok.all(axis=1).mean()), 4),
        "row_hits": int(field_ok.all(axis=1).sum()),
        "field_top1": {f: round(float(field_ok[:, i].mean()), 4) for i, f in enumerate(_FIELDS)},
        "field_mae": {f: round(float(err[:, i].mean()), 4) for i, f in enumerate(_FIELDS)},
        "field_r2": {},
    }
    for i, f in enumerate(_FIELDS):
        ss_tot = float(((gold[:, i] - gold[:, i].mean()) ** 2).sum())
        ss_res = float(((pred[:, i] - gold[:, i]) ** 2).sum())
        out["field_r2"][f] = round(1 - ss_res / ss_tot, 4) if ss_tot > 1e-9 else 0.0
    return out


def run(
    checkpoint: Path,
    set_path: Path,
    train_path: Path,
    report: Path,
    seed: int = 0,
    lags: Sequence[float] = (0.0, 0.25, 0.5, 0.75, 1.0),
    spectral: float = 1.05,
    gain: float = 2.0,
    fatigue: float = 0.98,
    latch: int = 0,
    in_gain: float = 4.0,
) -> int:
    started = time.time()
    model = TokenSNN.load(str(checkpoint), device="cpu")
    entries, usable = _load_rows(model, set_path)
    train = _train_pairs(model, train_path)
    if not entries or not train:
        raise SystemExit("no rows: check --checkpoint / --set / --train")

    cells = int(model.config.max_len)  # the project's own container bound
    machine = BoundedCellMachine(
        cells,
        len(model.vocab),
        seed=seed,
        gain=gain,
        fatigue=fatigue,
        spectral=spectral,
        latch=latch,
        in_gain=in_gain,
    )
    labels = [probe._set_label(e["entry"]) for e in entries]
    seen = [
        probe._parse_input_line(str(e["entry"]["prompt"])).get("intent")
        in {t for t in {r["intent"] for r in train}}
        for e in entries
    ]

    # 1. retention: how long the six <al_in> values stay decodable in the container
    xs_lag: Dict[float, List[np.ndarray]] = {lag: [] for lag in lags}
    real_lag: Dict[float, List[int]] = {lag: [] for lag in lags}
    ys_state: List[List[float]] = []
    ys_gold: List[List[float]] = []
    for row in train:
        stop = _values_at_end_of_state_line(row["prompt"], model, len(row["ids"]))
        span = max(0, min(row["start"], len(row["ids"]) - 1) - stop)
        indices = [stop + int(round(lag * span)) for lag in lags]
        states = _states(machine, row["ids"], indices)
        for lag, idx in zip(lags, indices):
            feats = states.get(idx)
            if feats is not None:
                xs_lag[lag].append(feats)
                real_lag[lag].append(idx - stop)
        ys_state.append(row["state"])
        ys_gold.append(row["gold"])
    ret_y = np.asarray(ys_state, dtype=np.float32)
    retention: Dict[str, Any] = {}
    for lag in lags:
        x = np.asarray(xs_lag[lag], dtype=np.float32)
        w = _ridge(x, ret_y, lam=1.0)
        pred = np.concatenate([x, np.ones((len(x), 1), dtype=x.dtype)], axis=1) @ w
        r2 = {}
        for i, f in enumerate(_FIELDS):
            ss_tot = float(((ret_y[:, i] - ret_y[:, i].mean()) ** 2).sum())
            ss_res = float(((pred[:, i] - ret_y[:, i]) ** 2).sum())
            r2[f] = round(1 - ss_res / ss_tot, 4) if ss_tot > 1e-9 else 0.0
        retention[f"frac_{lag}"] = {
            "mean_atoms_after_values": round(float(np.mean(real_lag[lag])), 1),
            "mean_r2": round(float(np.mean(list(r2.values()))), 4),
            "r2": r2,
        }

    # 2. task: readout at the block start, trained on the training rows only
    x_train = np.asarray(
        [
            _states(machine, row["ids"], [row["start"]])[
                min(max(row["start"], 0), len(row["ids"]) - 1)
            ]
            for row in train
        ],
        dtype=np.float32,
    )
    y_train = np.asarray(ys_gold, dtype=np.float32)
    x_eval = np.asarray(
        [
            _states(machine, e["ids"], [e["start"]])[min(max(e["start"], 0), len(e["ids"]) - 1)]
            for e in entries
        ],
        dtype=np.float32,
    )
    y_eval = np.asarray(
        [[float(probe._parse_block(str(e["entry"]["gold"]))[f]) for f in _FIELDS] for e in entries],
        dtype=np.float32,
    )
    contrast = {
        "across_rows_std": round(float(x_train.std(axis=0).mean()), 5),
        "within_row_std": round(float(x_train.std(axis=1).mean()), 5),
        "ratio": round(
            float(x_train.std(axis=0).mean()) / max(1e-9, float(x_train.std(axis=1).mean())), 4
        ),
    }
    w, mean, std, lam, val_r2 = _fit_readout(x_train, y_train, seed=seed)
    x_eval = (x_eval - mean) / std
    pred = np.concatenate([x_eval, np.ones((len(x_eval), 1), dtype=x_eval.dtype)], axis=1) @ w
    rounded = np.round(pred, 2)
    scored = _score(rounded, y_eval)
    holdout = np.asarray([lab == "holdout" for lab in labels])
    seen_arr = np.asarray(seen)
    scored_hold = _score(rounded[holdout], y_eval[holdout])
    if seen_arr[holdout].any():
        scored_hold_seen = _score(rounded[holdout & seen_arr], y_eval[holdout & seen_arr])
    else:
        scored_hold_seen = {"n": 0, "row_exact": 0.0, "row_hits": 0}

    # 3. the "bounded but not dead" checks, in the machine's own terms
    machine.reset()
    for _ in range(64):
        machine.step(int(model.vocab.stoi["<pad>"]))
    idle_mean = float(machine.x.mean())
    idle_std = float(machine.x.std())
    for _ in range(64):
        machine.step(int(model.vocab.stoi.get("1", model.vocab.unk_id)))
    busy_mean = float(machine.x.mean())
    busy_std = float(machine.x.std())

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "checkpoint": str(checkpoint),
        "machine": {
            "family": "bounded cellular machine (fatigue + threshold, no global reset)",
            "cells": cells,
            "lattice": f"{machine.rows}x{machine.cols}",
            "container_source": "TokenConfig.max_len — one cell per token slot",
            "state_per_cell": ["x", "fatigue", "threshold"],
            "spectral": spectral,
            "gain": gain,
            "fatigue": fatigue,
            "latch": latch,
            "in_gain": in_gain,
            "readout_features": len(machine.features()),
            "trained_parameters": int((len(machine.features()) + 1) * len(_FIELDS)),
            "dynamics_parameters": 0,
        },
        "readout": {"lambda": lam, "train_validation_r2": round(val_r2, 4)},
        "train_rows": len(train),
        "eval_rows": len(entries),
        "retention": retention,
        "task_all": scored,
        "task_holdout": scored_hold,
        "task_holdout_seen_intent": scored_hold_seen,
        "container_contrast": contrast,
        "alive": {
            "idle_mean": round(idle_mean, 4),
            "idle_std": round(idle_std, 4),
            "busy_mean": round(busy_mean, 4),
            "busy_std": round(busy_std, 4),
        },
        "comparison": {
            "snn_hidden_state_block_start_r2": "<= 0 (CORE_GAP §二十一)",
            "contract_feature_ridge_row_exact": 0.0,
            "operator_head_row_exact_seen": 0.525,
        },
        "elapsed_s": round(time.time() - started, 1),
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    retention_r2 = {k: v["mean_r2"] for k, v in retention.items()}
    print(
        f"cells={cells} ({machine.rows}x{machine.cols}) train={len(train)} eval={len(entries)}\n"
        f"retention mean R2 by lag: {retention_r2}\n"
        f"task: row_exact={scored['row_exact']} holdout={scored_hold['row_exact']} "
        f"(seen {scored_hold_seen['row_exact']}) mean R2="
        f"{np.mean(list(scored['field_r2'].values())):.3f}\n"
        f"alive: idle mean={idle_mean:.3f} std={idle_std:.3f} | "
        f"busy mean={busy_mean:.3f} std={busy_std:.3f}\nwrote {report}"
    )
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--checkpoint", default="data/checkpoints/ai_al_round9.pt")
    ap.add_argument("--set", dest="set_path", default=str(probe.SET_OUT))
    ap.add_argument("--train", default=str(probe.DEFAULT_TRAIN))
    ap.add_argument("--report", default=str(REPORT))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--spectral", type=float, default=1.05, help="coupling spectral radius")
    ap.add_argument("--gain", type=float, default=2.0, help="sigmoid gain")
    ap.add_argument("--fatigue", type=float, default=0.98, help="fatigue retention")
    ap.add_argument("--latch", type=int, default=0, help="slow-integrator tau in steps (0=off)")
    ap.add_argument("--in-gain", type=float, default=4.0, help="input coupling scale")
    ap.add_argument("--label", default="", help="suffix for the report file")
    args = ap.parse_args(argv)
    report = Path(args.report)
    if args.label:
        report = report.with_name(f"{report.stem}_{args.label}{report.suffix}")
    return run(
        Path(args.checkpoint),
        Path(args.set_path),
        Path(args.train),
        report,
        seed=args.seed,
        spectral=args.spectral,
        gain=args.gain,
        fatigue=args.fatigue,
        latch=args.latch,
        in_gain=args.in_gain,
    )


if __name__ == "__main__":
    raise SystemExit(main())
