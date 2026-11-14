#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
# =============================================================================
"""Where the answer's gradient actually reaches (§49.16, apparatus diagnostic).

P (§49) ended with a loss equal to the entropy of "which of twelve names": the
model learned the marginal and nothing conditional on the testimony. This probe
asks a narrower, mechanical question before any new registration: when the
answer's cross-entropy is back-propagated, how far back through the turns does a
non-negligible gradient actually get?

It is not a capability measurement and it has no threshold. It reports, per
turn boundary, ``|dL/dh_t|`` (``h`` retained, one backward, training sessions
only), the earliest turn above a floor, and the decay per turn. Two arms in one
run - the stage-L carrier (never trained on the task) and the stage-P checkpoint
(trained) - so "gradient cannot reach the evidence" can be separated from "the
task was not learned".

Why this is worth a file rather than a one-off: the number decides the next
variable. If the gradient reaches only the last turn or two, then more epochs,
more width, or better selection cannot help - the evidence never receives
credit - and the next registration has to change the *path length* (a readout at
each turn), not the structure. If it reaches every turn, that explanation is
wrong and the next variable is capacity or data.

A second mode (§50.13) asks the other half of the same question: if the gradient
does arrive, is the answer even *in* the final state? ``--state-probe`` fits a
linear readout on run-boundary hidden states and scores it on sessions the model
was never trained on. It separates "the state carries the conclusion and the
head does not read it" from "the state never carried it", which no amount of
extra epochs would fix. Both are diagnostics: no threshold, no score.

Usage::

    ./.venv/bin/python scripts/probe_credit_assignment.py --device cpu
    ./.venv/bin/python scripts/probe_credit_assignment.py --device cpu \\
        --json data/pantry_stage/credit_assignment.json
    ./.venv/bin/python scripts/probe_credit_assignment.py --state-probe --device cpu \\
        --arm q1=data/pantry_stage/q_overfit/<report>.pt --json data/pantry_stage/state_probe.json

The corpus is loaded by ``train_pantry_deduction`` itself, so the probe cannot
drift away from the registered splits; both digests are printed and stored.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DRIVER = REPO_ROOT / "scripts" / "train_pantry_deduction.py"
REPORTS = REPO_ROOT / "data" / "pantry_stage"

# A gradient below this is not "small", it is absent: float32 underflows to a
# true zero long before here, and Adam's per-parameter step is ~lr for anything
# above 1e-6.
GRAD_FLOOR = 1e-6


def load_driver() -> Any:
    spec = importlib.util.spec_from_file_location("pantry_deduction_credit", DRIVER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["pantry_deduction_credit"] = module
    spec.loader.exec_module(module)
    return module


def turnwise_forward(
    driver: Any,
    core: Any,
    sessions: Sequence[Dict[str, Any]],
) -> Tuple[Any, Any, List[Any]]:
    """Run whole sessions keeping every turn-boundary hidden state.

    This mirrors ``run_session`` (``ai_step`` per turn, ``al_step`` between
    turns) but retains the graph, and therefore the gradients, at each boundary.
    It deliberately does not re-implement the tokenisation: ``turn_tokens`` and
    ``turn_gaps`` are the registered helpers.
    """
    torch = core._torch
    turns = [driver.turn_tokens(session) for session in sessions]
    gaps = [driver.turn_gaps(session) for session in sessions]
    answers = [driver.answer_ids(session) for session in sessions]

    state = core.init_state(len(sessions))
    hidden = state.tensors["h"]
    boundary: List[Any] = []
    for index in range(len(turns[0])):
        if index > 0:
            state.tensors["h"] = hidden
            dt = torch.as_tensor(
                [row[index] for row in gaps], dtype=hidden.dtype, device=hidden.device
            )
            state = core.al_step(dt, state)
            hidden = state.tensors["h"]
        # §59 changed ``_run_turn`` to return the real-length state plus the
        # stacked per-token states and their mask; this probe is the GRU
        # credit-assignment diagnostic and only needs the first.
        hidden, _stacked, _valid = driver._run_turn(core, [row[index] for row in turns], hidden)
        state.tensors["h"] = hidden
        state.bump()
        hidden.retain_grad()
        boundary.append(hidden)

    loss = driver._answer_loss(core, hidden, answers)
    return loss, hidden, boundary


def grad_profile(
    core: Any,
    boundary: Sequence[Any],
    floor: float = GRAD_FLOOR,
) -> Dict[str, Any]:
    """Per-turn gradient norms, earliest turn above ``floor``, decay per turn."""
    norms = []
    for index, hidden in enumerate(boundary):
        grad = hidden.grad
        norms.append(0.0 if grad is None else float(grad.norm()))

    above = [index for index, norm in enumerate(norms) if norm > floor]
    earliest = above[0] if above else None
    reaches = None if earliest is None else len(norms) - earliest
    ratios = [
        (norms[index] / norms[index + 1])
        for index in range(len(norms) - 1)
        if norms[index] > 0.0 and norms[index + 1] > 0.0
    ]
    shrink = None
    if ratios:
        # geometric mean of the per-turn ratio: one number for "how many orders
        # per turn", which is what decides whether a readout every turn is
        # enough or every byte is needed.
        product = 1.0
        for ratio in ratios:
            product *= ratio
        shrink = product ** (1.0 / len(ratios))
    return {
        "turns": len(norms),
        "norms": norms,
        "earliest_turn_above_floor": earliest,
        "turns_reached": reaches,
        "shrink_per_turn": shrink,
        "floor": floor,
    }


def measure(
    driver: Any,
    core: Any,
    sessions: Sequence[Dict[str, Any]],
    tag: str,
) -> Dict[str, Any]:
    core.train(True)
    loss, hidden, boundary = turnwise_forward(driver, core, sessions)
    for parameter in core.parameters():
        parameter.grad = None
    loss.backward()
    profile = grad_profile(core, boundary)
    profile["tag"] = tag
    profile["loss"] = float(loss.detach())
    profile["head_grad"] = (
        None if core.head.weight.grad is None else float(core.head.weight.grad.norm())
    )
    profile["weights_hash"] = core.weights_hash()
    return profile


def _torch() -> Any:
    try:
        import torch
    except ImportError as error:  # pragma: no cover - torch is present in the venv
        raise SystemExit(f"the state probe needs torch: {error}") from error
    return torch


def state_features(
    driver: Any,
    core: Any,
    sessions: Sequence[Dict[str, Any]],
    boundaries: Sequence[int],
    batch: int = 32,
) -> Dict[int, Any]:
    """Hidden states at the requested turn boundaries, one forward pass each chunk.

    Uses the trainer's own ``run_session``, so these are the states the answer
    loss is computed from; a hand-rolled forward pass here would describe a
    different computation than the one being diagnosed.
    """
    torch = core._torch
    collected: Dict[int, List[Any]] = {int(boundary): [] for boundary in boundaries}
    core.eval()
    with torch.no_grad():
        for chunk in driver._chunks(list(sessions), batch):
            kept: List[Any] = []
            driver.run_session(
                core,
                [driver.turn_tokens(session) for session in chunk],
                [driver.turn_gaps(session) for session in chunk],
                boundaries=kept,
            )
            for boundary in collected:
                collected[boundary].append(kept[boundary].detach().to("cpu"))
    return {boundary: torch.cat(pieces, dim=0) for boundary, pieces in collected.items()}


def ridge_readout(train_x: Any, train_y: Any, test_x: Any, *, ridge: float = 1.0) -> Any:
    """Closed-form least-squares readout with an unpenalised bias.

    Standardisation uses training statistics only, so the held-out score cannot
    borrow anything from the test split. ``ridge`` keeps the normal equations
    solvable when the 64-dim states are highly correlated (they are).
    """
    torch = _torch()
    mean = train_x.mean(dim=0, keepdim=True)
    scale = train_x.std(dim=0, keepdim=True).clamp_min(1e-6)
    train_x = (train_x - mean) / scale
    test_x = (test_x - mean) / scale

    design = torch.cat([train_x, torch.ones((train_x.shape[0], 1), dtype=train_x.dtype)], dim=1)
    design_test = torch.cat([test_x, torch.ones((test_x.shape[0], 1), dtype=test_x.dtype)], dim=1)
    penalty = torch.eye(design.shape[1], dtype=design.dtype) * ridge
    penalty[-1, -1] = 0.0  # the bias is not shrunk
    weights = torch.linalg.solve(design.T @ design + penalty, design.T @ train_y)
    return design_test @ weights


def _one_hot(labels: Sequence[int], classes: int) -> Any:
    torch = _torch()
    out = torch.zeros((len(labels), classes), dtype=torch.float32)
    for index, label in enumerate(labels):
        out[index, int(label)] = 1.0
    return out


def _labels(sessions: Sequence[Dict[str, Any]], target: str) -> List[str]:
    if target == "culprit":
        return [session["ground_truth_oracle"]["culprit"] for session in sessions]
    if target == "chain":
        return [session["session_meta"]["chain"] for session in sessions]
    raise SystemExit(f"unknown --probe-target {target!r}; use culprit or chain")


def state_spread(states: Any) -> Dict[str, Any]:
    """How much the state varies across sessions - the assumption a readout needs.

    If every session's ``h`` is nearly the same vector, no readout can separate
    them and the finding is upstream of the probe. Reported as mean pairwise
    cosine similarity and the participation ratio of the centred spectrum
    (how many directions actually carry variance out of 64).
    """
    torch = _torch()
    centred = states - states.mean(dim=0, keepdim=True)
    singular = torch.linalg.svdvals(centred)
    energy = singular**2
    total = float(energy.sum())
    participation = float(energy.sum() ** 2 / (energy**2).sum()) if total > 0 else 0.0
    unit = states / states.norm(dim=1, keepdim=True).clamp_min(1e-9)
    cosine = unit @ unit.T
    count = states.shape[0]
    off_diagonal = (float(cosine.sum()) - count) / max(1, count * (count - 1))
    return {
        "sessions": count,
        "mean_pairwise_cosine": round(off_diagonal, 4),
        "participation_ratio": round(participation, 2),
        "dims": int(states.shape[1]),
    }


def state_probe(
    driver: Any,
    core: Any,
    train_sessions: Sequence[Dict[str, Any]],
    heldout_sessions: Sequence[Dict[str, Any]],
    *,
    boundaries: Sequence[int],
    ridge: float = 1.0,
    batch: int = 32,
    target: str = "culprit",
) -> Dict[str, Any]:
    """Can a linear readout decode the culprit from a turn's state?

    Fitted on the training split, scored on the held-out split: above chance
    means the conclusion is linearly present in the state of sessions the model
    never saw, so the bottleneck is downstream (head/decoder). At chance means
    the state does not distinguish the sessions at all, which no readout and no
    extra epoch can repair.

    The shuffled-label pass is the null: same features, same fit, permuted
    labels. That is what "chance" actually looks like on 64 correlated dims.
    """
    torch = _torch()
    all_labels = _labels(train_sessions, target) + _labels(heldout_sessions, target)
    names = sorted(set(all_labels))
    classes = len(names)
    index_of = {name: index for index, name in enumerate(names)}
    train_labels = [index_of[label] for label in _labels(train_sessions, target)]
    heldout_labels = [index_of[label] for label in _labels(heldout_sessions, target)]
    train_y = _one_hot(train_labels, classes)
    generator = torch.Generator().manual_seed(20261114)
    shuffled = torch.randperm(len(train_labels), generator=generator).tolist()
    shuffled_y = _one_hot([train_labels[index] for index in shuffled], classes)

    rows = []
    train_features = state_features(driver, core, train_sessions, boundaries, batch)
    heldout_features = state_features(driver, core, heldout_sessions, boundaries, batch)
    for boundary in boundaries:
        train_x = train_features[boundary]
        heldout_x = heldout_features[boundary]
        predicted = [
            int(value)
            for value in ridge_readout(train_x, train_y, heldout_x, ridge=ridge).argmax(1)
        ]
        null_predicted = [
            int(value)
            for value in ridge_readout(train_x, shuffled_y, heldout_x, ridge=ridge).argmax(1)
        ]
        correct = sum(1 for p, t in zip(predicted, heldout_labels) if p == t)
        null_correct = sum(1 for p, t in zip(null_predicted, heldout_labels) if p == t)
        rows.append(
            {
                "boundary": boundary,
                "heldout_n": len(heldout_labels),
                "correct": correct,
                "accuracy": round(correct / max(1, len(heldout_labels)), 4),
                "null_correct": null_correct,
                "null_accuracy": round(null_correct / max(1, len(heldout_labels)), 4),
                "chance": round(1.0 / classes, 4),
                "heldout_spread": state_spread(heldout_x),
            }
        )
    return {
        "target": target,
        "classes": classes,
        "train_n": len(train_labels),
        "heldout_n": len(heldout_labels),
        "ridge": ridge,
        "boundaries": rows,
        "note": (
            "diagnostic only (§50.13): a linear readout fitted on train states, scored on "
            "held-out states. Above chance = the conclusion is in the state and the head is "
            "the bottleneck; at chance = the state does not carry it. Not a capability score"
        ),
    }


def _newest_scored_report() -> Optional[Path]:
    """The newest non-smoke, non-control, non-calibration report (§49.10)."""
    newest = sorted(REPORTS.glob("pantry_deduction_*.json"))
    for candidate in reversed(newest):
        payload = json.loads(candidate.read_text(encoding="utf-8"))
        if payload.get("control_arm") == "rand" or payload.get("smoke"):
            continue
        if payload.get("overfit"):
            # a 32-session calibration must never stand in for "the trained model"
            continue
        return candidate
    return None


def _state_probe_main(driver: Any, corpus: Dict[str, Any], args: Any) -> int:
    arms: List[Tuple[str, Path]] = []
    for spec in args.arm:
        if "=" not in spec:
            raise SystemExit(f"--arm needs LABEL=PATH, got {spec!r}")
        label, path = spec.split("=", 1)
        arms.append((label, Path(path)))
    if not arms:
        arms.append(("stage_l", Path(REPO_ROOT / driver.L_CHECKPOINT)))
        report = _newest_scored_report()
        if report is not None:
            payload = json.loads(report.read_text(encoding="utf-8"))
            arms.append(("trained", Path(payload["checkpoint"])))

    boundaries = [int(part) for part in args.probe_boundaries.split(",") if part.strip()]
    out: Dict[str, Any] = {
        "corpus": {
            "train_digest": corpus["meta"]["train_digest"],
            "heldout_digest": corpus["meta"]["heldout_digest"],
            "train_sessions": len(corpus["train"]),
            "heldout_sessions": len(corpus["heldout"]),
        },
        "device": args.device,
        "arms": [],
    }
    for label, path in arms:
        if not Path(path).exists():
            raise SystemExit(f"missing checkpoint for arm {label}: {path}")
        core = driver.build_core(device=args.device)
        core.load_weights(str(path), strict_config=True)
        block = state_probe(
            driver,
            core,
            corpus["train"],
            corpus["heldout"],
            boundaries=boundaries,
            ridge=args.ridge,
            batch=args.probe_batch,
            target=args.probe_target,
        )
        block["tag"] = label
        block["checkpoint"] = str(path)
        block["weights_hash"] = core.weights_hash()
        out["arms"].append(block)

    if args.json:
        target = Path(args.json)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    print(
        f"corpus: train {out['corpus']['train_sessions']} / "
        f"held-out {out['corpus']['heldout_sessions']}  device={args.device}"
    )
    for block in out["arms"]:
        print(
            f"\n[{block['tag']}] target={block['target']}  {block['classes']} classes  "
            f"fit on {block['train_n']}  scored on {block['heldout_n']}  "
            f"chance {block['boundaries'][0]['chance']}"
        )
        print(f"  {'turn':>4s} {'acc':>7s} {'null':>7s} {'cos':>7s} {'pr':>6s}")
        for row in block["boundaries"]:
            spread = row["heldout_spread"]
            print(
                f"  {row['boundary']:4d} {row['accuracy']:7.4f} "
                f"{row['null_accuracy']:7.4f} {spread['mean_pairwise_cosine']:7.4f} "
                f"{spread['participation_ratio']:6.2f}"
            )
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Where the answer's gradient reaches (§49.16)")
    parser.add_argument("--checkpoint", default=None, help="trained arm (default: newest P report)")
    parser.add_argument(
        "--start", default=None, help="stage-L carrier (default: the registered one)"
    )
    parser.add_argument("--batch", type=int, default=8, help="training sessions per arm")
    parser.add_argument("--device", default="cpu", help="diagnostic runs on cpu by default")
    parser.add_argument("--json", default=None, help="write the profile here")
    parser.add_argument(
        "--state-probe",
        action="store_true",
        help="§50.13: fit a linear readout on turn states, score it on held-out sessions",
    )
    parser.add_argument(
        "--arm",
        action="append",
        default=[],
        metavar="LABEL=PATH",
        help="state-probe arm (repeatable); default: stage_l plus the newest scored checkpoint",
    )
    parser.add_argument("--ridge", type=float, default=1.0, help="readout ridge penalty")
    parser.add_argument(
        "--probe-target",
        default="culprit",
        choices=("culprit", "chain"),
        help="what the readout predicts; 'chain' is the probe's own positive control",
    )
    parser.add_argument(
        "--probe-boundaries", default="6,7,8,9,10", help="comma-separated turn boundaries"
    )
    parser.add_argument("--probe-batch", type=int, default=32, help="sessions per forward chunk")
    args = parser.parse_args(argv)

    driver = load_driver()

    corpus = driver.load_corpus()
    sessions = corpus["train"][: args.batch]

    if args.state_probe:
        return _state_probe_main(driver, corpus, args)

    checkpoint = Path(args.checkpoint) if args.checkpoint else None
    if checkpoint is None:
        report = _newest_scored_report()
        if report is not None:
            checkpoint = Path(json.loads(report.read_text(encoding="utf-8"))["checkpoint"])
    if checkpoint is not None and not Path(checkpoint).exists():
        raise SystemExit(f"missing checkpoint: {checkpoint}")

    start = Path(args.start) if args.start else Path(REPO_ROOT / driver.L_CHECKPOINT)
    if not start.exists():
        raise SystemExit(f"missing the stage-L checkpoint: {start}")

    arms: List[Dict[str, Any]] = []
    for tag, path in (("stage_l", start), ("trained", checkpoint)):
        if path is None:
            continue
        core = driver.build_core(device=args.device)
        core.load_weights(str(path), strict_config=True)
        arms.append(measure(driver, core, sessions, tag))

    report = {
        "corpus": {
            "train_digest": corpus["meta"]["train_digest"],
            "heldout_digest": corpus["meta"]["heldout_digest"],
            "sessions": len(sessions),
            "turns": len(sessions[0]["turns"]),
        },
        "device": args.device,
        "arms": arms,
    }
    if args.json:
        target = Path(args.json)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(
        f"corpus: train {report['corpus']['train_digest'][:16]}… "
        f"sessions={len(sessions)} turns={report['corpus']['turns']}"
    )
    for arm in arms:
        print(f"\n[{arm['tag']}] loss={arm['loss']:.4f}  head|grad|={arm['head_grad']:.3e}")
        for index, norm in enumerate(arm["norms"]):
            print(f"  turn {index:2d}  |dL/dh| = {norm:.3e}")
        reached = arm["turns_reached"]
        shrink = arm["shrink_per_turn"]
        print(
            f"  reaches {reached} turn(s) above {arm['floor']:.0e}"
            + (f"; shrinks {shrink:.2e}x per turn backwards" if shrink else "; shrink n/a")
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
