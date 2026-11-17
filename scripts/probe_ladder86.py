#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# LAYER: learning
# =============================================================================
"""§86: the same ladder question, decided on seeds that had never been run.

§85 could not decide ``N1`` vs ``N3``. Its ``N0`` gate measured
``distill_train``'s first 200 rows, where the parent is already at CE 0.8799 —
a memorised slice, with no room to fall — so the gate fired for a reason that
cannot be told apart from "the arm learned nothing". The five-item margin was
1.1 seed-sd (4.5), so the co-primary ruler could not have resolved the
difference either (85.10, 85.13).

§86 changes the instrument, never the experiment: the arms, corpus, order, lr,
step count, widening factor and noise are §85's, and ``run_arm`` is *imported*,
not copied (a copy would drift). What changes is registered in
``docs/06-project-management/CORE_GAP_ANALYSIS.md`` §86.3:

* seeds **3, 4, 5** — never run before, so this is not a re-reading of §85's
  numbers;
* ``N0`` is **retired**, not re-tuned: it used one label for two different
  statements ("the arm did not train" and "the arm trained and its training
  loss rose"), and §85 measured the second one. Whether the code trained is a
  mechanical fact (1,286 optimizer steps, finite per-epoch losses), checked in
  ``I0``, not inferred from a loss;
* the CE margin stays **0.15 nats** (3.6 sd); the item margin rises to **9
  items** (2 sd — 85.13's prescription);
* two continuous rulers are added as *descriptions*: ``holdout_ce`` (the same
  248 rows as the exact ruler) and ``train_ce_full`` (all 5,144 training rows
  at step 0 and at the end), and the parent's hold-out exact is reported as the
  memory baseline.

Removing a gate is not a way to make a branch easier: §85's data with ``N0``
removed is ``N4`` — neither ``N1`` nor ``N3``.

``--check`` reloads every checkpoint and recomputes all four rulers and the
branch from the margins recorded in the report, so a report is never trusted
because it says so.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import probe_ladder85 as p85  # noqa: E402
from ai.ed3n.token_snn import TokenSNN  # noqa: E402
from incremental import UnitCache, impl_digest  # noqa: E402

OUT_DIR = REPO_ROOT / "data" / "ladder86"
CACHE_DIR = OUT_DIR / "cache"
REPORT = OUT_DIR / "report.json"

#: Everything a §86 unit's numbers depend on. §86's own file is included: the
#: new rulers are code, and editing them must invalidate the units built with
#: them (exactly as editing ``probe_ladder85.py`` invalidates §85's).
IMPL_FILES: Tuple[Path, ...] = tuple(p85.IMPL_FILES) + (Path(__file__).resolve(),)

#: Registered in §86.5. The CE margin is deliberately *unchanged* from §85
#: (0.15 nats was already 3.6 sd); only the item margin moves, and it moves up.
MARGIN_CE = 0.15
MARGIN_ITEMS = 9.0
MARGINS: Dict[str, float] = {"ce_nats": MARGIN_CE, "holdout_items": MARGIN_ITEMS}

#: Registered in §86.3: the arms and their names are §85's.
ARMS = p85.ARMS
ARM_LABELS = p85.ARM_LABELS

RULERS: Tuple[str, ...] = ("val_ce", "holdout_ce", "train_ce_full")

#: Where each ruler lives on an arm row. ``train_ce_full`` is stored as the
#: arm's *end* value (the start lives in ``train_ce_full_start``), so the two
#: names are not the same and ``--check`` must not guess.
RULER_ROW_KEYS: Dict[str, str] = {
    "val_ce": "val_ce",
    "holdout_ce": "holdout_ce",
    "train_ce_full": "train_ce_full_end",
}


def measure_ce(
    model: TokenSNN,
    train_pairs: Sequence[Tuple[str, str]],
    val_pairs: Sequence[Tuple[str, str]],
    holdout_pairs: Sequence[Tuple[str, str]],
    batch: int,
) -> Dict[str, float]:
    """The three continuous §86 rulers, from one loaded model.

    ``val_ce`` and ``holdout_ce`` are the same function as §85's primary cell
    (``mean_ce``: mean of per-batch mean losses, batch 8), so the two reports
    are comparable. ``train_ce_full`` uses that same function on all 5,144
    training rows — it is *not* the per-epoch ``train_loss`` in the curve
    (token-weighted, tail-weighted), and the two must never be compared
    (86.2).
    """
    return {
        "val_ce": p85.mean_ce(model, val_pairs, batch),
        "holdout_ce": p85.mean_ce(model, holdout_pairs, batch),
        "train_ce_full": p85.mean_ce(model, train_pairs, batch),
    }


def measure_all(
    model: TokenSNN,
    train_pairs: Sequence[Tuple[str, str]],
    val_pairs: Sequence[Tuple[str, str]],
    holdout_pairs: Sequence[Tuple[str, str]],
    batch: int,
) -> Dict[str, float]:
    """Every §86 ruler, including the exact one (248 generations: slow)."""
    measured = measure_ce(model, train_pairs, val_pairs, holdout_pairs, batch)
    holdout = p85.exact_count(model, holdout_pairs)
    measured.update(
        {
            "holdout_hits": float(holdout["hits"]),
            "holdout_n": float(holdout["n"]),
            "holdout_rate": float(holdout["rate"]),
        }
    )
    return measured


def start_model(name: str, seed: int, parent: TokenSNN, out_dir: Path) -> TokenSNN:
    """The arm's step-0 weights.

    ``warm``'s step 0 is the widened child saved before training; ``cold``'s is
    the same deterministic fresh initialisation ``build_arm`` makes (it calls
    ``torch.manual_seed(seed)`` before constructing, so this is the same model,
    not a lookalike); ``width_control``'s is the parent itself, which is never
    trained here.
    """
    if name == "warm":
        init_path = Path(out_dir) / f"warm_init_{seed}.pt"
        if not init_path.is_file():
            raise SystemExit(f"missing {init_path}: the warm arm's step 0 is the widened child")
        return TokenSNN.load(init_path, device="cpu")
    if name == "cold":
        return p85.build_arm("cold", seed, parent)
    if name == "width_control":
        return parent
    raise ValueError(f"unknown arm {name!r}")


def summarise(arm_rows: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Per-arm means and spread. Every ruler is reported with its own sd: 85.13
    asked for the per-seed spread, not just the mean."""
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in arm_rows:
        grouped.setdefault(row["arm"], []).append(row)
    summary: Dict[str, Dict[str, float]] = {}
    for name, rows in grouped.items():
        finals = [float(r["val_ce"]) for r in rows]
        hits = [float(r["holdout_hits"]) for r in rows]
        holdout_ce = [float(r["holdout_ce"]) for r in rows]
        train_start = [float(r["train_ce_full_start"]) for r in rows]
        train_end = [float(r["train_ce_full_end"]) for r in rows]
        summary[name] = {
            "seeds": float(len(rows)),
            "params": p85._mean([float(r["params"]) for r in rows]),
            "val_ce": p85._mean(finals),
            "val_ce_sd": p85._stdev(finals),
            "val_ce_min": min(finals),
            "val_ce_max": max(finals),
            "holdout_hits": p85._mean(hits),
            "holdout_n": p85._mean([float(r["holdout_n"]) for r in rows]),
            "holdout_hits_sd": p85._stdev(hits),
            "holdout_ce": p85._mean(holdout_ce),
            "holdout_ce_sd": p85._stdev(holdout_ce),
            "train_ce_full_start": p85._mean(train_start),
            "train_ce_full_end": p85._mean(train_end),
            "train_ce_full_delta": p85._mean([e - s for e, s in zip(train_end, train_start)]),
            "ms_per_row": p85._mean([float(r["ms_per_row"]) for r in rows]),
            "seconds": p85._mean([float(r["seconds"]) for r in rows]),
        }
    return summary


def paired(arm_rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Warm minus control, seed by seed.

    Signs follow §85 so the two reports read the same way: a positive
    ``delta_ce`` and a positive ``delta_items`` both mean **warm is better**.
    """
    by_seed: Dict[int, Dict[str, Dict[str, Any]]] = {}
    for row in arm_rows:
        by_seed.setdefault(int(row["seed"]), {})[row["arm"]] = row
    rows: List[Dict[str, Any]] = []
    for seed in sorted(by_seed):
        pair = by_seed[seed]
        if "warm" not in pair or "width_control" not in pair:
            continue
        warm, control = pair["warm"], pair["width_control"]
        rows.append(
            {
                "seed": seed,
                "delta_ce": float(control["val_ce"]) - float(warm["val_ce"]),
                "delta_items": float(warm["holdout_hits"]) - float(control["holdout_hits"]),
                "delta_holdout_ce": float(control["holdout_ce"]) - float(warm["holdout_ce"]),
            }
        )
    ce = [r["delta_ce"] for r in rows]
    items = [r["delta_items"] for r in rows]
    holdout_ce = [r["delta_holdout_ce"] for r in rows]
    return {
        "per_seed": rows,
        "delta_ce": p85._mean(ce),
        "delta_ce_sd": p85._stdev(ce),
        "delta_items": p85._mean(items),
        "delta_items_sd": p85._stdev(items),
        "delta_holdout_ce": p85._mean(holdout_ce),
        "delta_holdout_ce_sd": p85._stdev(holdout_ce),
        "sign_agreement": {
            "ce": sum(1 for v in ce if v > 0),
            "items": sum(1 for v in items if v > 0),
            "n": len(rows),
        },
    }


def _resolved(delta: float, margin: float) -> str:
    if delta >= margin:
        return "warm-better"
    if delta <= -margin:
        return "warm-worse"
    return "unresolved"


def decide(
    arm_rows: Sequence[Dict[str, Any]],
    margins: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """The §86.5 table, applied to the per-seed rows.

    ``margins`` is a parameter rather than a module read so ``--check`` can
    verify a report against the margins *that report* was registered with. A
    rule that silently moved with the code would make every old report look
    wrong.
    """
    margins = dict(MARGINS if margins is None else margins)
    ce_margin = float(margins["ce_nats"])
    item_margin = float(margins["holdout_items"])
    summary = summarise(arm_rows)
    missing = [name for name in ("warm", "width_control") if name not in summary]
    if missing:
        return {
            "branch": "UNDECIDED",
            "reason": f"missing arms: {', '.join(missing)}",
            "margins": margins,
            "summary": summary,
        }

    pair = paired(arm_rows)
    delta_ce = pair["delta_ce"]
    delta_items = pair["delta_items"]
    ce_state = _resolved(delta_ce, ce_margin)
    items_state = _resolved(delta_items, item_margin)

    if ce_state == "warm-better" and items_state == "warm-better":
        branch = "N1-ladder-pays"
        reason = (
            f"warm beats the width control by {delta_ce:+.4f} nats (>= {ce_margin}) "
            f"and {delta_items:+.0f} hold-out items (>= {item_margin:.0f})"
        )
    elif ce_state == "warm-worse" and items_state == "warm-worse":
        branch = "N3-ladder-hurts"
        reason = (
            f"warm is worse than the width control by {-delta_ce:.4f} nats "
            f"and {-delta_items:.0f} hold-out items"
        )
    elif ce_state == "unresolved" and items_state == "unresolved":
        branch = "N2-no-resolvable-gain"
        reason = (
            f"CE difference {delta_ce:+.4f} nats (< {ce_margin}) and "
            f"{delta_items:+.0f} hold-out items (< {item_margin:.0f}): "
            "not resolvable at this budget, which is not equality"
        )
    else:
        branch = "N4-inconsistent"
        reason = (
            f"the rulers disagree: CE {delta_ce:+.4f} nats ({ce_state}, "
            f"margin {ce_margin}) vs hold-out {delta_items:+.0f} items "
            f"({items_state}, margin {item_margin:.0f})"
        )

    reference: Dict[str, Any] = {}
    if "cold" in summary:
        cold = summary["cold"]
        reference = {
            "warm_minus_cold_ce": cold["val_ce"] - summary["warm"]["val_ce"],
            "warm_minus_cold_items": summary["warm"]["holdout_hits"] - cold["holdout_hits"],
            "reading": (
                "the warm start is better than random init"
                if cold["val_ce"] - summary["warm"]["val_ce"] >= ce_margin
                else "the warm start is not better than random init at this budget"
            ),
        }

    return {
        "branch": branch,
        "reason": reason,
        "margins": margins,
        "delta_ce_warm_minus_control": delta_ce,
        "delta_items_warm_minus_control": delta_items,
        "ce_ruler": {"state": ce_state, "delta": delta_ce, "margin": ce_margin},
        "item_ruler": {"state": items_state, "delta": delta_items, "margin": item_margin},
        "paired": pair,
        "summary": summary,
        "cold_reference": reference,
        "reading_note": (
            "N4 states which ruler resolved and which did not. The exact ruler's "
            "resolution at n=3 is 2 sd = 9 items (85.13); crossing nothing there is "
            "'unresolved', never 'equal', and never 'the CE side wins'."
        ),
    }


def run(args: argparse.Namespace) -> Dict[str, Any]:
    import torch

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    cache = UnitCache(Path(args.cache), base=REPO_ROOT)
    parent = TokenSNN.load(p85.PARENT, device="cpu")
    parent_digest = p85._sha256_file(p85.PARENT)
    train_pairs, val_pairs, holdout_pairs = p85._pairs(parent)
    row_digests = p85.rows_digest(train_pairs, val_pairs, holdout_pairs)
    impl = impl_digest(IMPL_FILES)
    seeds = [int(s) for s in str(args.seeds).split(",") if s.strip()]
    arms = p85.parse_arms(args.arms)

    overlap = {
        "train_and_val": len(set(train_pairs) & set(val_pairs)),
        "train_and_holdout": len(set(train_pairs) & set(holdout_pairs)),
        "val_and_holdout": len(set(val_pairs) & set(holdout_pairs)),
    }
    orders = {str(seed): p85.shuffle_digest(len(train_pairs), seed, 0) for seed in seeds}
    steps = int(math.ceil(len(train_pairs) / args.batch) * args.epochs)

    parent_baseline = measure_all(parent, train_pairs, val_pairs, holdout_pairs, args.batch)

    rows: List[Dict[str, Any]] = []
    reused: List[str] = []
    computed: List[str] = []
    extended: List[str] = []
    partial_path = out_dir / "report.partial.json"
    started = time.time()
    for seed in seeds:
        for name in arms:
            plan = p85.arm_plan(
                parent_digest, name, seed, row_digests, p85._protocol(args, args.epochs), impl
            )
            label = f"{name}/seed{seed}"
            unit = None if args.no_resume else cache.lookup(plan)
            if unit is not None:
                row = dict(unit.payload)
                row["reused"] = True
                row["unit"] = unit.key
                row["seconds_this_run"] = 0.0
                reused.append(label)
                print(f"reused {label} ({unit.seconds:.0f}s already spent)", flush=True)
                rows.append(row)
                partial_path.write_text(
                    json.dumps({"arms": rows, "decision": decide(rows)}, indent=1, sort_keys=True)
                    + "\n",
                    encoding="utf-8",
                )
                continue

            resume = None if args.no_resume else p85.prefix_unit(cache, plan)
            if resume:
                extended.append(f"{label}@{resume['epochs']}->{args.epochs}")
                print(
                    f"extend {label}: {resume['epochs']} -> {args.epochs} epochs "
                    f"({resume['unit'].key[:19]})",
                    flush=True,
                )
            else:
                print(f"compute {label} ...", flush=True)

            row = p85.run_arm(
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
                resume_from=resume,
            )

            # The four §86 rulers, from the saved weights. Training is already
            # over, so this cannot perturb it; §86.6-6 verifies that the two
            # pre-existing rulers still reproduce §85's numbers.
            final_model = TokenSNN.load(p85.resolve_artifact(row["checkpoint"]), device="cpu")
            end = measure_ce(final_model, train_pairs, val_pairs, holdout_pairs, args.batch)
            begin = measure_ce(
                start_model(name, seed, parent, out_dir),
                train_pairs,
                val_pairs,
                holdout_pairs,
                args.batch,
            )
            if abs(end["val_ce"] - float(row["final_val_ce"])) > 1e-4:
                raise SystemExit(
                    f"{label}: the new ruler and run_arm disagree on val CE "
                    f"({end['val_ce']:.6f} vs {row['final_val_ce']:.6f})"
                )
            # ``run_arm`` already generated the 248 hold-out answers; reusing
            # them keeps the extra cost to forward-only CE passes.
            row.update(
                {
                    "val_ce": end["val_ce"],
                    "holdout_ce": end["holdout_ce"],
                    "train_ce_full_end": end["train_ce_full"],
                    "train_ce_full_start": begin["train_ce_full"],
                    "holdout_ce_start": begin["holdout_ce"],
                    "val_ce_start": begin["val_ce"],
                    "margins": dict(MARGINS),
                }
            )
            row["reused"] = False
            row["seconds_this_run"] = row["seconds"]
            if not args.no_store:
                unit = cache.store(
                    plan,
                    row,
                    artifacts=[
                        ("checkpoint", p85.resolve_artifact(row["checkpoint"])),
                        ("opt_state", p85.resolve_artifact(row["opt_state"])),
                    ],
                    seconds=float(row["seconds"]),
                )
                row["unit"] = unit.key
            computed.append(label)
            rows.append(row)
            partial_path.write_text(
                json.dumps({"arms": rows, "decision": decide(rows)}, indent=1, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )

    decision = decide(rows)

    identity = []
    for seed in seeds:
        init_path = out_dir / f"warm_init_{seed}.pt"
        if not init_path.is_file():
            continue
        child = TokenSNN.load(init_path, device="cpu")
        identity.append(
            {
                "seed": seed,
                "init_checkpoint": p85.display_path(init_path),
                "parent_val_ce": p85.mean_ce(parent, val_pairs, args.batch),
                "child_val_ce": p85.mean_ce(child, val_pairs, args.batch),
                "parent_train_ce_full": parent_baseline["train_ce_full"],
                "child_train_ce_full": p85.mean_ce(child, train_pairs, args.batch),
            }
        )

    return {
        "stage": "probe_ladder86",
        "registration": "docs/06-project-management/CORE_GAP_ANALYSIS.md §86",
        "protocol": {
            "parent": p85.display_path(p85.PARENT),
            "parent_sha256": parent_digest,
            "parent_params": p85._params(parent),
            "train": p85.display_path(p85.TRAIN),
            "val": p85.display_path(p85.VAL),
            "holdout": p85.display_path(p85.HOLDOUT),
            "rows": {
                "train": len(train_pairs),
                "val": len(val_pairs),
                "holdout": len(holdout_pairs),
            },
            "factor": p85.FACTOR,
            "noise": p85.NOISE,
            "epochs": args.epochs,
            "batch": args.batch,
            "lr": args.lr,
            "seed_list": seeds,
            "arm_list": arms,
            "optimizer_steps_per_arm": steps,
            "guard": True,
            "tail_weight": 1.0,
            "ss_final": 0.0,
            "margins": dict(MARGINS),
            "ruler_definitions": {
                "val_ce": "mean_ce(distill_val 281 rows, batch 8)",
                "holdout_ce": "mean_ce(distill_val_holdout 248 rows, batch 8)",
                "train_ce_full": "mean_ce(distill_train 5144 rows, batch 8)",
            },
            "impl_digest": impl,
            "rows_digest": row_digests,
        },
        "instrument": {
            "overlap": overlap,
            "shuffle_digest_epoch0": orders,
            "identity": identity,
            "parent_baseline": parent_baseline,
            "threads": os.environ.get("OMP_NUM_THREADS"),
            "torch": torch.__version__,
            "cpu_count": os.cpu_count(),
        },
        "cache": {
            "reused": reused,
            "computed": computed,
            "extended": extended,
            "units_dir": p85.display_path(args.cache),
        },
        "arms": rows,
        "decision": decision,
        "seconds": round(time.time() - started, 1),
        "parent_unchanged": p85._sha256_file(p85.PARENT) == parent_digest,
    }


def check(report_path: Path) -> Tuple[bool, str]:
    """Recompute every ruler and the branch from the saved weights.

    A report is a claim; this turns it back into a measurement. The margins
    come from the report (§86.5), so an old report is verified against the rule
    it was registered with, not against whatever the code says today.
    """
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if report.get("stage") != "probe_ladder86":
        return False, "not a probe_ladder86 report"
    protocol = report["protocol"]
    if p85._sha256_file(p85.PARENT) != protocol["parent_sha256"]:
        return False, "the parent checkpoint changed since the report was written"

    parent = TokenSNN.load(p85.PARENT, device="cpu")
    train_pairs, val_pairs, holdout_pairs = p85._pairs(parent)
    for name, counted in (
        ("train", len(train_pairs)),
        ("val", len(val_pairs)),
        ("holdout", len(holdout_pairs)),
    ):
        if counted != protocol["rows"][name]:
            return False, f"{name} rows changed since the report was written"
    if p85.rows_digest(train_pairs, val_pairs, holdout_pairs) != protocol["rows_digest"]:
        return False, "row contents changed since the report was written"

    problem = p85.overlap_problem(report["instrument"]["overlap"], int(protocol["rows"]["holdout"]))
    if problem:
        return False, problem

    errors: List[str] = []
    for row in report["arms"]:
        path = p85.resolve_artifact(row["checkpoint"])
        if not path.is_file():
            errors.append(f"missing checkpoint {row['checkpoint']}")
            continue
        model = TokenSNN.load(path, device="cpu")
        if p85._vocab_digest(model) != row["vocab_digest"]:
            errors.append(f"{row['arm']}/{row['seed']}: vocab changed")
        if p85._params(model) != row["params"]:
            errors.append(f"{row['arm']}/{row['seed']}: parameter count changed")
        measured = measure_all(model, train_pairs, val_pairs, holdout_pairs, protocol["batch"])
        for ruler, key in RULER_ROW_KEYS.items():
            reported = float(row[key])
            if abs(measured[ruler] - reported) > 1e-4:
                errors.append(
                    f"{row['arm']}/{row['seed']}: {ruler} {measured[ruler]:.6f} != "
                    f"reported {reported:.6f}"
                )
        if abs(measured["holdout_hits"] - float(row["holdout_hits"])) > 1e-9:
            errors.append(
                f"{row['arm']}/{row['seed']}: hold-out hits "
                f"{measured['holdout_hits']:.0f} != reported {row['holdout_hits']:.0f}"
            )

    for point in report["instrument"]["identity"]:
        init_path = p85.resolve_artifact(
            point.get("init_checkpoint", f"data/ladder86/warm_init_{point['seed']}.pt")
        )
        if not init_path.is_file():
            errors.append(f"missing {init_path}")
            continue
        child = TokenSNN.load(init_path, device="cpu")
        if abs(p85.mean_ce(child, val_pairs, protocol["batch"]) - point["parent_val_ce"]) > 1e-4:
            errors.append(f"identity seed {point['seed']}: step-0 val CE changed")
        if (
            abs(p85.mean_ce(child, train_pairs, protocol["batch"]) - point["child_train_ce_full"])
            > 1e-4
        ):
            errors.append(f"identity seed {point['seed']}: step-0 train CE changed")

    recomputed = decide(report["arms"], margins=protocol["margins"])
    if recomputed["branch"] != report["decision"]["branch"]:
        errors.append(f"branch {recomputed['branch']} != reported {report['decision']['branch']}")
    if not report.get("parent_unchanged"):
        errors.append("the report itself says the parent changed during the run")

    if errors:
        return False, "; ".join(errors[:5])
    return True, (
        f"probe_ladder86 check OK ({recomputed['branch']}, "
        f"{len(report['arms'])} arms recomputed)"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default="3,4,5")
    parser.add_argument("--arms", default=",".join(ARMS))
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    parser.add_argument("--cache", default=str(CACHE_DIR))
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="ignore cached units and compute every arm from scratch",
    )
    parser.add_argument(
        "--no-store",
        action="store_true",
        help="compute without writing units (a scratch run)",
    )
    parser.add_argument(
        "--check",
        type=Path,
        metavar="REPORT",
        help="recompute every ruler and the branch of an existing report",
    )
    args = parser.parse_args()
    try:
        p85.parse_arms(args.arms)
    except ValueError as error:
        parser.error(str(error))

    if args.check:
        ok, message = check(args.check)
        print(message if ok else f"FAIL: {message}")
        return 0 if ok else 1

    report = run(args)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    decision = report["decision"]
    print("\n" + "=" * 70)
    for name in report["protocol"].get("arm_list", ARMS):
        row = decision["summary"].get(name)
        if not row:
            continue
        print(
            f"{name:14s} params={row['params']:,.0f} val={row['val_ce']:.4f} "
            f"(sd {row['val_ce_sd']:.4f}) holdout={row['holdout_hits']:.0f}/{row['holdout_n']:.0f} "
            f"holdout_ce={row['holdout_ce']:.4f} train={row['train_ce_full_start']:.4f}->"
            f"{row['train_ce_full_end']:.4f} {row['ms_per_row']:.1f} ms/row"
        )
    baseline = report["instrument"]["parent_baseline"]
    print(
        f"parent baseline: val={baseline['val_ce']:.4f} holdout="
        f"{baseline['holdout_hits']:.0f}/{baseline['holdout_n']:.0f} "
        f"train={baseline['train_ce_full']:.4f}"
    )
    cache = report["cache"]
    print(
        f"cache: {len(cache['reused'])} reused, {len(cache['computed'])} computed "
        f"({len(cache['extended'])} extended), {report['seconds']:.1f}s this run"
    )
    print(f"branch: {decision['branch']} — {decision['reason']}")
    print(f"report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
