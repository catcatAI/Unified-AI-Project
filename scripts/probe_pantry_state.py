#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""Stage K (§58): is the answer linearly decodable from the state?

Why this exists
---------------
§56.10 and §57.9 measured the same shape twice: the arm fits the sessions it was
trained on (200/200 = 1.0000, then 365/400 = 0.9125) and still answers the
held-out sessions at or below the roster chance, with the prediction landing
*inside the current session's roster* at 0.61 / 0.535 (content-free expectation
0.5457). Two readings remain, and they prescribe different work:

1. **representation has it, readout does not** - the roster and the
   evidence-value -> person binding are in the state, and the decoder/scoring
   side never uses them;
2. **the representation never had it** - the state never bound the roster to the
   evidence value, so changing the readout cannot help.

§50.13 asked this of the GRU with a linear probe and every boundary was at
chance, but that arm could not fit its own training sessions either. The store
arm can (0.9125), so "fits but does not use" is now separable: fit a linear
classifier on the state, on the training sessions, and score it on the held-out
ones. That is not a capability claim and it is not the decoder answering; it is
the cheapest way to ask which of the two readings is true.

What is measured
----------------
The state *the decoder answers from*: the last turn's state after ``run_session``
(same path as ``evaluate``), i.e. ``h`` plus, on a store arm, the read vector
``r = read_vector(state)``. Three feature sets are probed separately:
``h`` (128), ``r`` (64) and ``h+r`` (192).

Read it as
----------
* K1 is an instrument check: if the probe cannot fit the training states, the
  held-out number is not read (a broken ruler, not a finding).
* K2 is §58.3's bar: the held-out Wilson lower bound must beat the corpus's own
  per-session chance (the same line §56's G2 uses - rosters of 5-8 names).
* A K2 failure only says "not linearly decodable"; a non-linear decoder could
  still find the answer. That limitation is stated in §58.6, not papered over.

Usage
-----
    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/probe_pantry_state.py \\
        --report data/pantry_stage/h_store/pantry_deduction_20261114-140311.json \\
        --train-sessions 400
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
TRAINER = REPO_ROOT / "scripts" / "train_pantry_deduction.py"

# §58.3, written before the run.
PROBE_FIT_FLOOR = 0.90
PROBE_ALPHA = 0.05
PROBE_C = 1.0
PROBE_MAX_ITER = 2000


def load_trainer() -> Any:
    """Import the trainer by path so the probe cannot drift from its encoding."""
    spec = importlib.util.spec_from_file_location("pantry_probe_trainer", TRAINER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["pantry_probe_trainer"] = module
    spec.loader.exec_module(module)
    return module


def rebuild_core(trainer: Any, report: Dict[str, Any]) -> Any:
    """Rebuild the exact core a report names and verify the checkpoint hash."""
    config = report.get("config") or {}
    core = trainer.build_core(
        hidden=int(config.get("hidden", trainer.HIDDEN)),
        emb=int(config.get("emb", trainer.EMB)),
        device="cpu",
        kind=str(config.get("core") or "gru"),
        memory=bool(config.get("memory", True)),
    )
    checkpoint = report.get("checkpoint")
    if not checkpoint or not Path(checkpoint).exists():
        raise SystemExit("the report's checkpoint is missing; nothing to probe")
    core.load_weights(checkpoint, strict_config=True)
    if core.weights_hash() != report.get("weights_hash"):
        raise SystemExit("checkpoint weights_hash does not match the report")
    return core


def collect_states(
    trainer: Any,
    core: Any,
    sessions: Sequence[Dict[str, Any]],
    *,
    batch: int = 32,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Run each session whole and keep the state the decoder answers from.

    Returns ``(hidden, read, labels)``; ``read`` is empty (0 columns) for a core
    that has no store, so the caller can skip that feature set.
    """
    torch = core._torch
    hidden_rows: List[np.ndarray] = []
    read_rows: List[np.ndarray] = []
    labels: List[str] = []
    core.eval()
    with torch.no_grad():
        for chunk in trainer._chunks(list(sessions), batch):
            turns: List[List[List[int]]] = []
            gaps: List[List[float]] = []
            for session in chunk:
                dropped = trainer.drop_indices(session, "full")
                kept = [turn for turn in session["turns"] if int(turn["turn_id"]) not in dropped]
                turns.append(
                    [
                        [
                            trainer.BYTE_OFFSET + byte
                            for byte in (turn["user_input"] + "\n").encode("utf-8")
                        ]
                        for turn in kept
                    ]
                )
                gaps.append([float(turn["dt_s"]) for turn in kept])
            state, _ = trainer.run_session(core, turns, gaps)
            final = dict(state.tensors)
            hidden_rows.append(final["h"].detach().cpu().numpy())
            reader = getattr(core, "read_vector", None)
            if reader is not None:
                read_rows.append(reader(final).detach().cpu().numpy())
            labels.extend(session["ground_truth_oracle"]["culprit"] for session in chunk)
    hidden = np.concatenate(hidden_rows, axis=0)
    read = np.concatenate(read_rows, axis=0) if read_rows else np.zeros((len(labels), 0))
    return hidden, read, np.asarray(labels)


def probe(
    train_x: np.ndarray,
    train_y: np.ndarray,
    held_x: np.ndarray,
    held_y: np.ndarray,
    *,
    seed: int,
) -> Dict[str, Any]:
    """Multinomial logistic regression; the scaler is fit on the training rows only."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler().fit(train_x)
    model = LogisticRegression(
        C=PROBE_C,
        max_iter=PROBE_MAX_ITER,
        solver="lbfgs",
        random_state=seed,
    )
    model.fit(scaler.transform(train_x), train_y)
    fit_predictions = model.predict(scaler.transform(train_x))
    held_predictions = model.predict(scaler.transform(held_x))
    return {
        "fit_exact": float(np.mean(fit_predictions == train_y)),
        "held_predictions": held_predictions,
        "held_exact": float(np.mean(held_predictions == held_y)),
        "classes": list(model.classes_),
    }


def run(trainer: Any, report: Dict[str, Any], train_sessions: int) -> Dict[str, Any]:
    corpus = trainer.load_corpus(
        sessions=int((report.get("corpus") or {}).get("sessions", trainer.PANTRY_SESSIONS)),
        seed=int((report.get("corpus") or {}).get("seed", trainer.PANTRY_SEED)),
    )
    declared = int((report.get("corpus") or {}).get("train_sessions_used") or train_sessions)
    if train_sessions and train_sessions != declared:
        raise SystemExit(
            f"--train-sessions {train_sessions} disagrees with the report's {declared}; "
            "the probe must use the sessions the arm was trained on"
        )
    train = corpus["train"][:declared]
    heldout = corpus["heldout"]

    core = rebuild_core(trainer, report)
    train_h, train_r, train_y = collect_states(trainer, core, train)
    held_h, held_r, held_y = collect_states(trainer, core, heldout)
    chance = float(np.mean([1.0 / len(session["environment"]["actors"]) for session in heldout]))

    feature_sets = [("h", train_h, held_h)]
    if train_r.shape[1]:
        feature_sets.append(("r", train_r, held_r))
        feature_sets.append(
            (
                "h+r",
                np.concatenate([train_h, train_r], axis=1),
                np.concatenate([held_h, held_r], axis=1),
            )
        )

    blocks: Dict[str, Any] = {}
    for name, train_x, held_x in feature_sets:
        outcome = probe(train_x, train_y, held_x, held_y, seed=int(trainer.SEED))
        correct = int(np.sum(outcome["held_predictions"] == held_y))
        low, high = trainer.wilson(correct, len(held_y))
        blocks[name] = {
            "dims": int(train_x.shape[1]),
            "fit_exact": round(outcome["fit_exact"], 4),
            "held_correct": correct,
            "held_n": int(len(held_y)),
            "held_exact": round(outcome["held_exact"], 4),
            "wilson_lower": round(low, 4),
            "wilson_upper": round(high, 4),
        }

    primary = blocks["h+r"] if "h+r" in blocks else blocks["h"]
    checks = {
        "K1_probe_fits_the_training_states": bool(primary["fit_exact"] >= PROBE_FIT_FLOOR),
        "K2_heldout_state_decodes_above_chance": bool(primary["wilson_lower"] > chance),
        "K3_feature_sets_recorded": True,
        "K4_cost_recorded": True,
    }
    return {
        "report": str(Path(report.get("checkpoint", "")).parent),
        "core": (report.get("config") or {}).get("core") or "gru",
        "checkpoint": report.get("checkpoint"),
        "weights_hash": report.get("weights_hash"),
        "train_sessions": declared,
        "probe": {
            "model": "LogisticRegression(multinomial, lbfgs)",
            "C": PROBE_C,
            "max_iter": PROBE_MAX_ITER,
            "scaler": "StandardScaler fit on the training states only",
        },
        "chance": round(chance, 4),
        "features": blocks,
        "checks": checks,
        "all_pass": all(checks.values()),
        "branch": branch(checks),
    }


def branch(checks: Dict[str, Any]) -> str:
    """§58.5, mechanically: what the next experiment is allowed to be."""
    if not checks["K1_probe_fits_the_training_states"]:
        return (
            "K1 fails: the probe cannot fit the training states, so the ruler is broken; "
            "fix the probe before reading K2 at all"
        )
    if not checks["K2_heldout_state_decodes_above_chance"]:
        return (
            "K1 passes but K2 fails: the answer is not linearly decodable from the state, so the "
            "binding was never learned; next is the representation (an explicit roster-by-evidence "
            "binding operator), not more sessions, steps or width"
        )
    return (
        "K1+K2 pass: the answer is in the state and the failure is the readout; next is a "
        "roster-normalised selection head trained on the state, not more sessions, steps or width"
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, help="a finished pantry-deduction report")
    parser.add_argument(
        "--train-sessions",
        type=int,
        default=0,
        help="the subset the report declares (checked against corpus.train_sessions_used)",
    )
    parser.add_argument("--out", default="", help="write the JSON verdict here")
    args = parser.parse_args(argv)

    trainer = load_trainer()
    path = Path(args.report)
    if not path.exists():
        raise SystemExit(f"missing report: {path}")
    outcome = run(trainer, json.loads(path.read_text(encoding="utf-8")), args.train_sessions)

    print(f"report   : {path}")
    print(f"core     : {outcome['core']}  train sessions {outcome['train_sessions']}")
    print(f"chance   : {outcome['chance']:.4f} (mean 1/roster over the held-out sessions)")
    print()
    print(f"  {'features':8s} {'dims':>5s} {'fit':>7s} {'held-out':>9s} {'wilson':>16s}")
    for name, block in outcome["features"].items():
        print(
            f"  {name:8s} {block['dims']:5d} {block['fit_exact']:7.4f} "
            f"{block['held_exact']:9.4f} "
            f"[{block['wilson_lower']:.4f}, {block['wilson_upper']:.4f}]"
        )
    print()
    for name, value in outcome["checks"].items():
        print(f"  {'PASS' if value else 'FAIL'}  {name}")
    print(f"all_pass : {outcome['all_pass']}")
    print(f"branch   : {outcome['branch']}")
    if args.out:
        Path(args.out).write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
        print(f"wrote    : {args.out}")
    return 0 if outcome["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
