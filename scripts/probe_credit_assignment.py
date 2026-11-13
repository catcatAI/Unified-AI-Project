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

Usage::

    ./.venv/bin/python scripts/probe_credit_assignment.py --device cpu
    ./.venv/bin/python scripts/probe_credit_assignment.py --device cpu \\
        --json data/pantry_stage/credit_assignment.json

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
        hidden = driver._run_turn(core, [row[index] for row in turns], hidden)
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


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Where the answer's gradient reaches (§49.16)")
    parser.add_argument("--checkpoint", default=None, help="trained arm (default: newest P report)")
    parser.add_argument(
        "--start", default=None, help="stage-L carrier (default: the registered one)"
    )
    parser.add_argument("--batch", type=int, default=8, help="training sessions per arm")
    parser.add_argument("--device", default="cpu", help="diagnostic runs on cpu by default")
    parser.add_argument("--json", default=None, help="write the profile here")
    args = parser.parse_args(argv)

    driver = load_driver()

    corpus = driver.load_corpus()
    sessions = corpus["train"][: args.batch]

    checkpoint = Path(args.checkpoint) if args.checkpoint else None
    if checkpoint is None:
        newest = sorted(REPORTS.glob("pantry_deduction_*.json"))
        for candidate in reversed(newest):
            payload = json.loads(candidate.read_text(encoding="utf-8"))
            if payload.get("control_arm") != "rand" and not payload.get("smoke"):
                checkpoint = Path(payload["checkpoint"])
                break
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
