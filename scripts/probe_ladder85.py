#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# LAYER: learning
# =============================================================================
"""§85: is widening a trained token-SNN a ladder, or just a bigger restart?

Three arms, one budget, one corpus, three seeds:

* ``warm``          - the 2.5M checkpoint widened x4 (``expand_token_snn``), then trained;
* ``cold``          - the same 12M width from a fresh initialisation, same budget;
* ``width_control`` - the 2.5M checkpoint continued at its own width.

``warm`` is compared with ``width_control``: both start from weights that have
already been trained, so the only difference is the width. That is the question
§85 registered. ``cold`` is a reference (is the warm start at least better than
random init?), never the decision arm.

The decision rule, margins and the branch names are frozen in
``docs/06-project-management/CORE_GAP_ANALYSIS.md`` §85.5 before any scored
run; this file implements exactly that rule and refuses to invent a new one.
``--check`` recomputes the two measurements from the saved checkpoints and the
branch from its own numbers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import sys
import time
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from ai.ed3n.token_snn import TokenConfig, TokenSNN  # noqa: E402
from expand_token_snn import expand_model  # noqa: E402
from train_token_snn import exact_match, fits, read_pairs  # noqa: E402

DATA = REPO_ROOT / "apps" / "backend" / "data"
PARENT = DATA / "models" / "token_snn_distill.pt"
TRAIN = DATA / "processed" / "distill_train.jsonl"
VAL = DATA / "processed" / "distill_val.jsonl"
HOLDOUT = DATA / "processed" / "distill_val_holdout.jsonl"
OUT_DIR = REPO_ROOT / "data" / "ladder85"
REPORT = OUT_DIR / "report.json"

#: Registered in §85.3: x4 width, symmetry-breaking noise on the new copies.
FACTOR = 4
NOISE = 1e-3
#: Registered in §85.5: 2.5x the measured seed spread (0.012-0.062 nats), and
#: about two standard deviations of a 248-item count at 11%.
MARGIN_CE = 0.15
MARGIN_ITEMS = 5.0

ARMS: Tuple[str, ...] = ("warm", "cold", "width_control")
ARM_LABELS = {
    "warm": "2.5M -> 12M (widened, then trained)",
    "cold": "12M from random init, same budget",
    "width_control": "2.5M continued at its own width",
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _vocab_digest(model: TokenSNN) -> str:
    payload = json.dumps(model.vocab.to_dict(), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _params(model: TokenSNN) -> int:
    return int(sum(p.numel() for p in model.net.parameters()))


def _mean(values: Sequence[float]) -> float:
    return float(sum(values) / len(values)) if values else float("nan")


def _stdev(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = _mean(values)
    return float(math.sqrt(sum((v - avg) ** 2 for v in values) / (len(values) - 1)))


def mean_ce(model: TokenSNN, pairs: Sequence[Tuple[str, str]], batch: int = 8) -> float:
    """Teacher-forced cross-entropy per row (the §85 primary cell)."""
    import torch

    was_training = model.net.training
    model.net.eval()
    total, steps = 0.0, 0
    try:
        with torch.no_grad():
            for start in range(0, len(pairs), batch):
                chunk = list(pairs[start : start + batch])
                ids, mask, _ = model.make_batch(chunk)
                value = float(model.loss(ids, mask).detach())
                if math.isfinite(value):
                    total += value
                    steps += 1
    finally:
        if was_training:
            model.net.train()
    return total / steps if steps else float("nan")


def exact_count(model: TokenSNN, pairs: Sequence[Tuple[str, str]]) -> Dict[str, float]:
    """Hits on the frozen hold-out, with the production metric and its printing
    silenced (9 arms x 10 progress lines is noise, not information)."""
    with redirect_stdout(StringIO()):
        report = exact_match(model, list(pairs), 0, seed=3)
    return {
        "hits": float(report["exact"]) * report["n"],
        "n": float(report["n"]),
        "rate": float(report["exact"]),
    }


def shuffle_digest(rows: int, seed: int, epoch: int = 0) -> str:
    """The batch order ``TokenSNN.train_on`` will use (same rule, recomputed)."""
    order = list(range(rows))
    random.Random(seed + epoch).shuffle(order)
    return hashlib.sha256(",".join(str(i) for i in order).encode("utf-8")).hexdigest()


def build_arm(name: str, seed: int, parent: TokenSNN) -> TokenSNN:
    import torch

    if name == "warm":
        return expand_model(parent, factor=FACTOR, noise=NOISE, seed=seed)
    if name == "width_control":
        # A fresh copy: the parent instance is never trained, so it can stay the
        # untouched reference the identity check compares against.
        return TokenSNN.load(PARENT, device="cpu")
    if name == "cold":
        torch.manual_seed(seed)
        config = TokenConfig(**parent.config.to_dict())
        config.d_hidden = int(parent.config.d_hidden) * FACTOR
        return TokenSNN(parent.vocab, config, device="cpu")
    raise ValueError(f"unknown arm {name!r}")


def run_arm(
    name: str,
    seed: int,
    parent: TokenSNN,
    train_pairs: Sequence[Tuple[str, str]],
    val_pairs: Sequence[Tuple[str, str]],
    holdout_pairs: Sequence[Tuple[str, str]],
    epochs: int,
    batch: int,
    lr: float,
    out_dir: Path,
) -> Dict[str, Any]:
    model = build_arm(name, seed, parent)
    tensor_ce200 = list(train_pairs[:200])
    start_ce = mean_ce(model, val_pairs, batch)
    start_ce200 = mean_ce(model, tensor_ce200, batch)
    if name == "warm":
        model.save(out_dir / f"warm_init_{seed}.pt")

    curve: List[Dict[str, Any]] = [
        {"epoch": 0, "val_ce": start_ce, "train_ce200": start_ce200, "seconds": 0.0}
    ]
    started = time.time()

    def on_epoch(row: Dict[str, Any]) -> None:
        curve.append(
            {
                "epoch": int(row["epoch"]) + 1,
                "train_loss": float(row["loss"]),
                "lr": float(row.get("lr", lr)),
                "rolled_back": bool(row.get("rolled_back")),
                "val_ce": mean_ce(model, val_pairs, batch),
                "train_ce200": mean_ce(model, tensor_ce200, batch),
                "seconds": round(time.time() - started, 1),
            }
        )
        print(
            f"    {name}/seed{seed} epoch {curve[-1]['epoch']}: "
            f"train={curve[-1]['train_loss']:.4f} val={curve[-1]['val_ce']:.4f} "
            f"({curve[-1]['seconds']:.0f}s)",
            flush=True,
        )

    model.train_on(
        list(train_pairs),
        epochs=epochs,
        batch_size=batch,
        lr=lr,
        seed=seed,
        on_epoch=on_epoch,
        tail_weight=1.0,
        ss_final=0.0,
        guard=True,
    )
    seconds = time.time() - started
    final_ce = mean_ce(model, val_pairs, batch)
    final_ce200 = mean_ce(model, tensor_ce200, batch)
    holdout = exact_count(model, holdout_pairs)
    model.save(out_dir / f"{name}_{seed}.pt")

    return {
        "arm": name,
        "label": ARM_LABELS[name],
        "seed": int(seed),
        "params": _params(model),
        "config": model.config.to_dict(),
        "vocab_digest": _vocab_digest(model),
        "start_val_ce": start_ce,
        "start_train_ce200": start_ce200,
        "final_val_ce": final_ce,
        "final_train_ce200": final_ce200,
        "holdout_hits": holdout["hits"],
        "holdout_n": holdout["n"],
        "holdout_rate": holdout["rate"],
        "curve": curve,
        "seconds": round(seconds, 1),
        "ms_per_row": round(1000.0 * seconds / max(1, len(train_pairs) * epochs), 2),
        "checkpoint": str((out_dir / f"{name}_{seed}.pt").relative_to(REPO_ROOT)),
    }


def summarise(arm_rows: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in arm_rows:
        grouped.setdefault(row["arm"], []).append(row)
    summary: Dict[str, Dict[str, float]] = {}
    for name, rows in grouped.items():
        finals = [float(r["final_val_ce"]) for r in rows]
        starts = [float(r["start_val_ce"]) for r in rows]
        summary[name] = {
            "seeds": float(len(rows)),
            "start_val_ce": _mean(starts),
            "final_val_ce": _mean(finals),
            "start_train_ce200": _mean([float(r["start_train_ce200"]) for r in rows]),
            "final_train_ce200": _mean([float(r["final_train_ce200"]) for r in rows]),
            "final_val_ce_sd": _stdev(finals),
            "final_val_ce_min": min(finals),
            "final_val_ce_max": max(finals),
            "holdout_hits": _mean([float(r["holdout_hits"]) for r in rows]),
            "holdout_n": _mean([float(r["holdout_n"]) for r in rows]),
            "ms_per_row": _mean([float(r["ms_per_row"]) for r in rows]),
            "seconds": _mean([float(r["seconds"]) for r in rows]),
            "params": _mean([float(r["params"]) for r in rows]),
        }
    return summary


def decide(arm_rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """The §85.5 rule, applied to the per-seed rows. No new thresholds."""
    summary = summarise(arm_rows)
    missing = [name for name in ("warm", "width_control") if name not in summary]
    if missing:
        return {
            "branch": "UNDECIDED",
            "reason": f"missing arms: {', '.join(missing)}",
            "summary": summary,
        }
    warm, control = summary["warm"], summary["width_control"]
    # Positive means the warm arm is better than the width control.
    delta_ce = control["final_val_ce"] - warm["final_val_ce"]
    delta_items = warm["holdout_hits"] - control["holdout_hits"]

    # N0 is "the widened child did not learn", and it is measured on the
    # *training* loss on purpose: a child that inherits an over-fit parent can
    # learn (train CE falls) while its validation CE rises, and reading that as
    # "unusable" would make N3 unreachable by construction.
    learned = warm["final_train_ce200"] <= warm["start_train_ce200"] - MARGIN_CE
    if not learned:
        branch = "N0-unusable"
        reason = (
            f"warm train CE {warm['start_train_ce200']:.4f} -> "
            f"{warm['final_train_ce200']:.4f} did not fall by {MARGIN_CE} nats"
        )
    elif delta_ce >= MARGIN_CE and delta_items >= MARGIN_ITEMS:
        branch = "N1-ladder-pays"
        reason = (
            f"warm beats the width control by {delta_ce:.4f} nats (>= {MARGIN_CE}) "
            f"and {delta_items:.0f} hold-out items (>= {MARGIN_ITEMS:.0f})"
        )
    elif delta_ce <= -MARGIN_CE and delta_items <= -MARGIN_ITEMS:
        branch = "N3-ladder-hurts"
        reason = (
            f"warm is worse than the width control by {-delta_ce:.4f} nats "
            f"and {-delta_items:.0f} hold-out items"
        )
    elif abs(delta_ce) < MARGIN_CE and abs(delta_items) < MARGIN_ITEMS:
        branch = "N2-no-resolvable-gain"
        reason = (
            f"CE difference {delta_ce:+.4f} nats (< {MARGIN_CE}) and "
            f"{delta_items:+.0f} hold-out items (< {MARGIN_ITEMS:.0f})"
        )
    else:
        branch = "N4-inconsistent"
        reason = (
            f"instruments disagree: CE {delta_ce:+.4f} nats, " f"hold-out {delta_items:+.0f} items"
        )

    reference: Dict[str, Any] = {}
    if "cold" in summary:
        cold = summary["cold"]
        reference = {
            "warm_minus_cold_ce": cold["final_val_ce"] - warm["final_val_ce"],
            "warm_minus_cold_items": warm["holdout_hits"] - cold["holdout_hits"],
            "reading": (
                "the warm start is better than random init"
                if cold["final_val_ce"] - warm["final_val_ce"] >= MARGIN_CE
                else "the warm start is not better than random init at this budget"
            ),
        }
    return {
        "branch": branch,
        "reason": reason,
        "delta_ce_warm_minus_control": delta_ce,
        "delta_items_warm_minus_control": delta_items,
        "margins": {"ce_nats": MARGIN_CE, "holdout_items": MARGIN_ITEMS},
        "summary": summary,
        "cold_reference": reference,
    }


def _pairs(
    model: TokenSNN,
) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]], List[Tuple[str, str]]]:
    vocab, max_len = model.vocab, model.config.max_len
    train_pairs = fits(read_pairs(TRAIN), vocab, max_len)
    val_pairs = fits(read_pairs(VAL), vocab, max_len)
    holdout_pairs = fits(read_pairs(HOLDOUT), vocab, max_len)
    return train_pairs, val_pairs, holdout_pairs


def run(args: argparse.Namespace) -> Dict[str, Any]:
    import torch

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    parent = TokenSNN.load(PARENT, device="cpu")
    parent_digest = _sha256_file(PARENT)
    train_pairs, val_pairs, holdout_pairs = _pairs(parent)
    seeds = [int(s) for s in str(args.seeds).split(",") if s.strip()]

    overlap = {
        "train_and_val": len(set(train_pairs) & set(val_pairs)),
        "train_and_holdout": len(set(train_pairs) & set(holdout_pairs)),
        "val_and_holdout": len(set(val_pairs) & set(holdout_pairs)),
    }
    orders = {str(seed): shuffle_digest(len(train_pairs), seed, 0) for seed in seeds}
    steps = math.ceil(len(train_pairs) / args.batch) * args.epochs

    rows: List[Dict[str, Any]] = []
    partial_path = out_dir / "report.partial.json"
    started = time.time()
    for seed in seeds:
        for name in ARMS:
            print(f"arm {name} seed {seed} ...", flush=True)
            rows.append(
                run_arm(
                    name=name,
                    seed=seed,
                    parent=parent,
                    train_pairs=train_pairs,
                    val_pairs=val_pairs,
                    holdout_pairs=holdout_pairs,
                    epochs=args.epochs,
                    batch=args.batch,
                    lr=args.lr,
                    out_dir=out_dir,
                )
            )
            partial_path.write_text(
                json.dumps({"arms": rows, "decision": decide(rows)}, indent=1, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )

    decision = decide(rows)
    identity = []
    for seed in seeds:
        init_path = out_dir / f"warm_init_{seed}.pt"
        if init_path.is_file():
            child = TokenSNN.load(init_path, device="cpu")
            identity.append(
                {
                    "seed": seed,
                    "parent_val_ce": mean_ce(parent, val_pairs, args.batch),
                    "child_val_ce": mean_ce(child, val_pairs, args.batch),
                }
            )
    report = {
        "stage": "probe_ladder85",
        "registration": "docs/06-project-management/CORE_GAP_ANALYSIS.md §85",
        "protocol": {
            "parent": str(PARENT.relative_to(REPO_ROOT)),
            "parent_sha256": parent_digest,
            "parent_params": _params(parent),
            "train": str(TRAIN.relative_to(REPO_ROOT)),
            "val": str(VAL.relative_to(REPO_ROOT)),
            "holdout": str(HOLDOUT.relative_to(REPO_ROOT)),
            "rows": {
                "train": len(train_pairs),
                "val": len(val_pairs),
                "holdout": len(holdout_pairs),
            },
            "factor": FACTOR,
            "noise": NOISE,
            "epochs": args.epochs,
            "batch": args.batch,
            "lr": args.lr,
            "seed_list": seeds,
            "optimizer_steps_per_arm": steps,
            "guard": True,
            "tail_weight": 1.0,
            "ss_final": 0.0,
        },
        "instrument": {
            "overlap": overlap,
            "shuffle_digest_epoch0": orders,
            "identity": identity,
            "threads": os.environ.get("OMP_NUM_THREADS"),
            "torch": torch.__version__,
            "cpu_count": os.cpu_count(),
        },
        "arms": rows,
        "decision": decision,
        "seconds": round(time.time() - started, 1),
        "parent_unchanged": _sha256_file(PARENT) == parent_digest,
    }
    return report


def check(report_path: Path) -> Tuple[bool, str]:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if report.get("stage") != "probe_ladder85":
        return False, "not a probe_ladder85 report"
    protocol = report["protocol"]
    if _sha256_file(PARENT) != protocol["parent_sha256"]:
        return False, "the parent checkpoint changed since the report was written"

    parent = TokenSNN.load(PARENT, device="cpu")
    train_pairs, val_pairs, holdout_pairs = _pairs(parent)
    if len(train_pairs) != protocol["rows"]["train"]:
        return False, "training rows changed since the report was written"
    if len(val_pairs) != protocol["rows"]["val"]:
        return False, "validation rows changed since the report was written"
    if len(holdout_pairs) != protocol["rows"]["holdout"]:
        return False, "hold-out rows changed since the report was written"

    overlap = report["instrument"]["overlap"]
    if any(overlap.values()):
        return False, f"train/val/hold-out overlap is not zero: {overlap}"

    errors: List[str] = []
    for row in report["arms"]:
        path = REPO_ROOT / row["checkpoint"]
        if not path.is_file():
            errors.append(f"missing checkpoint {row['checkpoint']}")
            continue
        model = TokenSNN.load(path, device="cpu")
        if _vocab_digest(model) != row["vocab_digest"]:
            errors.append(f"{row['arm']}/{row['seed']}: vocab changed")
        if _params(model) != row["params"]:
            errors.append(f"{row['arm']}/{row['seed']}: parameter count changed")
        measured = mean_ce(model, val_pairs, protocol["batch"])
        if abs(measured - row["final_val_ce"]) > 1e-4:
            errors.append(
                f"{row['arm']}/{row['seed']}: val CE {measured:.6f} != "
                f"reported {row['final_val_ce']:.6f}"
            )
        holdout = exact_count(model, holdout_pairs)
        if abs(holdout["hits"] - row["holdout_hits"]) > 1e-9:
            errors.append(
                f"{row['arm']}/{row['seed']}: hold-out hits {holdout['hits']:.0f} != "
                f"reported {row['holdout_hits']:.0f}"
            )

    for point in report["instrument"]["identity"]:
        init_path = OUT_DIR / f"warm_init_{point['seed']}.pt"
        if not init_path.is_file():
            errors.append(f"missing warm_init_{point['seed']}.pt")
            continue
        child = TokenSNN.load(init_path, device="cpu")
        measured = mean_ce(child, val_pairs, protocol["batch"])
        if abs(measured - point["parent_val_ce"]) > 1e-4:
            errors.append(
                f"identity seed {point['seed']}: step-0 CE {measured:.6f} != "
                f"parent {point['parent_val_ce']:.6f}"
            )

    recomputed = decide(report["arms"])
    if recomputed["branch"] != report["decision"]["branch"]:
        errors.append(f"branch {recomputed['branch']} != reported {report['decision']['branch']}")
    if not report.get("parent_unchanged"):
        errors.append("the report itself says the parent changed during the run")

    if errors:
        return False, "; ".join(errors[:5])
    return True, (
        f"probe_ladder85 check OK ({recomputed['branch']}, "
        f"{len(report['arms'])} arms recomputed)"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default="0,1,2")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument(
        "--check",
        type=Path,
        metavar="REPORT",
        help="recompute the measurements and the branch of an existing report",
    )
    args = parser.parse_args()

    if args.check:
        ok, message = check(args.check)
        print(message if ok else f"FAIL: {message}")
        return 0 if ok else 1

    report = run(args)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    decision = report["decision"]
    print("\n" + "=" * 70)
    for name in ARMS:
        row = decision["summary"].get(name)
        if not row:
            continue
        print(
            f"{name:14s} params={row['params']:,.0f} start={row['start_val_ce']:.4f} "
            f"final={row['final_val_ce']:.4f} (sd {row['final_val_ce_sd']:.4f}) "
            f"holdout={row['holdout_hits']:.0f}/{row['holdout_n']:.0f} "
            f"{row['ms_per_row']:.1f} ms/row"
        )
    print(f"branch: {decision['branch']} — {decision['reason']}")
    print(f"report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
