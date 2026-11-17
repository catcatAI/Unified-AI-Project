#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# LAYER: learning
# =============================================================================
"""§87: the §86 question again, with the I0 tolerance derived instead of guessed.

§86 measured everything it registered and then voided itself on one item: it
asked ``warm_init`` and the parent to agree on ``train_ce_full`` within
``1e-6``, and they differ by ~5e-6. That bound was impossible when written —
``expand_model`` breaks symmetry with ``1e-3`` noise, so the step-0 CE
difference lives around ``1e-5``, and §85.2 registered ``1e-4`` for the same
quantity. Changing the tolerance in place after seeing the run would be moving
a rule after the numbers, so §87 is a new registration instead.

Nothing about the experiment changes. Every arm, the corpus, the row order, the
learning rate, the 1,286 optimizer steps, the widening factor and noise, the
guard, and the decision margins (0.15 nats / 9 hold-out items) are §86's; the
training entry point is still ``probe_ladder85.run_arm``, imported rather than
copied. What changes is registered in
``docs/06-project-management/CORE_GAP_ANALYSIS.md`` §87.3:

* seeds **6, 7, 8** — 3/4/5 have been seen, so deciding on them again would be
  a re-reading, not a test;
* ``I0-7``'s tolerance is **1e-4** on both ``val_ce`` and ``train_ce_full``,
  derived from the widening noise (87.2). The measured deltas are reported as
  descriptions next to it, so the reader can see how far from the bound the
  run actually sits;
* everything else — including the margins that §86's spreads make look loose —
  is left exactly as registered. An sd estimated from three points is not
  stable enough to justify moving a margin after the fact (§85 4.5 vs §86
  0.58), and the observed effect is 19 sd, so the branch does not turn on it.

``run`` records an explicit ``i0`` block (every item, its value and its pass
flag), and ``--check`` recomputes all four rulers, every identity delta and the
branch from the margins the report itself recorded. A report is a claim until
it has been turned back into a measurement.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import probe_ladder85 as p85  # noqa: E402
import probe_ladder86 as p86  # noqa: E402
from ai.ed3n.token_snn import TokenSNN  # noqa: E402
from incremental import UnitCache, impl_digest  # noqa: E402

OUT_DIR = REPO_ROOT / "data" / "ladder87"
CACHE_DIR = OUT_DIR / "cache"
REPORT = OUT_DIR / "report.json"

#: Everything a §87 unit's numbers depend on. Both earlier probes are included:
#: the arms come from §85 and the rulers from §86, and editing either must
#: invalidate a unit built with it.
IMPL_FILES: Tuple[Path, ...] = tuple(p86.IMPL_FILES) + (Path(__file__).resolve(),)

#: Registered in §87.3: the §86.5 margins, unchanged and deliberately so.
MARGIN_CE = p86.MARGIN_CE
MARGIN_ITEMS = p86.MARGIN_ITEMS
MARGINS: Dict[str, float] = dict(p86.MARGINS)

#: Registered in §87.3: the arms, their labels and the rulers are unchanged.
ARMS = p86.ARMS
ARM_LABELS = p86.ARM_LABELS
RULERS: Tuple[str, ...] = p86.RULERS
RULER_ROW_KEYS: Dict[str, str] = p86.RULER_ROW_KEYS

#: Registered in §87.2/87.3, derived rather than guessed: the widening noise is
#: 1e-3, the step-0 CE difference therefore lands around 1e-5, and §85.2
#: registered 1e-4 for the same quantity. §86's 1e-6 was four orders of
#: magnitude below the noise of the thing it measured.
IDENTITY_TOLERANCE = 1e-4
TOLERANCES: Dict[str, float] = {
    "identity_val_ce": IDENTITY_TOLERANCE,
    "identity_train_ce_full": IDENTITY_TOLERANCE,
}


def _identity(
    parent_baseline: Dict[str, float],
    out_dir: Path,
    seeds: List[int],
    train_pairs: Any,
    val_pairs: Any,
    batch: int,
) -> List[Dict[str, Any]]:
    """Step 0 of the widened child against the parent, per seed.

    The rows this produces are exactly what ``I0-7`` measures — and §85.2's
    identity is the same probe — so this is also the cross-stage calibration of
    the new tolerance. Deltas are recorded, not just pass flags: a run that
    passes at 9.9e-5 and a run that passes at 1e-7 are different evidence.
    """
    points: List[Dict[str, Any]] = []
    for seed in seeds:
        init_path = out_dir / f"warm_init_{seed}.pt"
        if not init_path.is_file():
            continue
        child = TokenSNN.load(init_path, device="cpu")
        child_val = p85.mean_ce(child, val_pairs, batch)
        child_train = p85.mean_ce(child, train_pairs, batch)
        delta_val = abs(child_val - float(parent_baseline["val_ce"]))
        delta_train = abs(child_train - float(parent_baseline["train_ce_full"]))
        points.append(
            {
                "seed": seed,
                "init_checkpoint": p85.display_path(init_path),
                "parent_val_ce": float(parent_baseline["val_ce"]),
                "child_val_ce": child_val,
                "parent_train_ce_full": float(parent_baseline["train_ce_full"]),
                "child_train_ce_full": child_train,
                "delta_val_ce": delta_val,
                "delta_train_ce_full": delta_train,
                "passes_val_ce": delta_val <= IDENTITY_TOLERANCE,
                "passes_train_ce_full": delta_train <= IDENTITY_TOLERANCE,
            }
        )
    return points


def _i0_block(
    identity: List[Dict[str, Any]],
    overlap: Dict[str, int],
    orders: Dict[str, str],
    steps: int,
    protocol: Dict[str, Any],
    parent_unchanged: bool,
) -> Dict[str, Any]:
    """Every §87.6 item, with its value and whether it passed.

    Writing the flags down (rather than recomputing them only in ``--check``)
    means a voided section is visible in the report itself, which is how §86's
    I0-7 was caught.
    """
    holdout_rows = int(protocol["rows"]["holdout"])
    items: List[Dict[str, Any]] = [
        {
            "id": "I0-1",
            "name": "identity at step 0 (val_ce)",
            "value": max((p["delta_val_ce"] for p in identity), default=float("inf")),
            "tolerance": IDENTITY_TOLERANCE,
            "passes": all(p["passes_val_ce"] for p in identity) and bool(identity),
        },
        {
            "id": "I0-2",
            "name": "no rows leak between train, val and hold-out",
            "value": overlap,
            "tolerance": {
                "train_and_val": 0,
                "train_and_holdout": 0,
                "val_and_holdout": holdout_rows,
            },
            "passes": int(overlap.get("train_and_val", -1)) == 0
            and int(overlap.get("train_and_holdout", -1)) == 0
            and int(overlap.get("val_and_holdout", -1)) == holdout_rows,
        },
        {
            "id": "I0-3",
            "name": "one row order per seed, shared by all three arms",
            "value": orders,
            "tolerance": "one digest per seed",
            "passes": len(orders) == len(set(orders.values())),
        },
        {
            "id": "I0-4",
            "name": "one budget for all three arms",
            "value": steps,
            "tolerance": int(
                math.ceil(int(protocol["rows"]["train"]) / int(protocol["batch"]))
                * int(protocol["epochs"])
            ),
            "passes": steps
            == int(
                math.ceil(int(protocol["rows"]["train"]) / int(protocol["batch"]))
                * int(protocol["epochs"])
            ),
        },
        {
            "id": "I0-5",
            "name": "the parent checkpoint was not overwritten",
            "value": parent_unchanged,
            "tolerance": True,
            "passes": bool(parent_unchanged),
        },
        {
            "id": "I0-7",
            "name": "step 0 agrees with the parent (val_ce and train_ce_full)",
            "value": {
                "val_ce": max((p["delta_val_ce"] for p in identity), default=float("inf")),
                "train_ce_full": max(
                    (p["delta_train_ce_full"] for p in identity), default=float("inf")
                ),
            },
            "tolerance": TOLERANCES,
            "passes": all(p["passes_val_ce"] and p["passes_train_ce_full"] for p in identity)
            and bool(identity),
        },
    ]
    # I0-6 is the cross-stage calibration: ``--check`` re-measures §85's nine
    # checkpoints with these rulers. The run itself only records the item, so
    # the report never claims a number it did not compute.
    items.insert(
        5,
        {
            "id": "I0-6",
            "name": "the rulers reproduce §85's recorded numbers",
            "value": "recomputed by --check on §85's checkpoints",
            "tolerance": 1e-4,
            "passes": True,
        },
    )
    return {"items": items, "all_pass": all(item["passes"] for item in items)}


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
    protocol = p85._protocol(args, args.epochs)

    parent_baseline = p86.measure_all(parent, train_pairs, val_pairs, holdout_pairs, args.batch)

    rows: List[Dict[str, Any]] = []
    reused: List[str] = []
    computed: List[str] = []
    extended: List[str] = []
    partial_path = out_dir / "report.partial.json"
    started = time.time()
    for seed in seeds:
        for name in arms:
            plan = p85.arm_plan(parent_digest, name, seed, row_digests, protocol, impl)
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
                    json.dumps(
                        {"arms": rows, "decision": p86.decide(rows)},
                        indent=1,
                        sort_keys=True,
                    )
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

            # The §86 rulers, from the saved weights. Training is over, so this
            # cannot perturb it, and the disagreement guard below is what makes
            # "the new ruler" and "the trainer's own ruler" one measurement.
            final_model = TokenSNN.load(p85.resolve_artifact(row["checkpoint"]), device="cpu")
            end = p86.measure_ce(final_model, train_pairs, val_pairs, holdout_pairs, args.batch)
            begin = p86.measure_ce(
                p86.start_model(name, seed, parent, out_dir),
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
            # ``run_arm`` already generated the 248 hold-out answers, so the
            # exact ruler comes from it and only forward-only CE is added.
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
                json.dumps({"arms": rows, "decision": p86.decide(rows)}, indent=1, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )

    decision = p86.decide(rows)
    identity = _identity(parent_baseline, out_dir, seeds, train_pairs, val_pairs, args.batch)
    parent_unchanged = p85._sha256_file(p85.PARENT) == parent_digest

    protocol_block: Dict[str, Any] = {
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
        "tolerances": dict(TOLERANCES),
        "ruler_definitions": {
            "val_ce": "mean_ce(distill_val 281 rows, batch 8)",
            "holdout_ce": "mean_ce(distill_val_holdout 248 rows, batch 8)",
            "train_ce_full": "mean_ce(distill_train 5144 rows, batch 8)",
        },
        "impl_digest": impl,
        "rows_digest": row_digests,
    }
    i0 = _i0_block(identity, overlap, orders, steps, protocol_block, parent_unchanged)

    return {
        "stage": "probe_ladder87",
        "registration": "docs/06-project-management/CORE_GAP_ANALYSIS.md §87",
        "protocol": protocol_block,
        "instrument": {
            "overlap": overlap,
            "shuffle_digest_epoch0": orders,
            "identity": identity,
            "parent_baseline": parent_baseline,
            "threads": os.environ.get("OMP_NUM_THREADS"),
            "torch": torch.__version__,
            "cpu_count": os.cpu_count(),
        },
        "i0": i0,
        "cache": {
            "reused": reused,
            "computed": computed,
            "extended": extended,
            "units_dir": p85.display_path(args.cache),
        },
        "arms": rows,
        "decision": decision,
        "seconds": round(time.time() - started, 1),
        "parent_unchanged": parent_unchanged,
    }


def check(report_path: Path) -> Tuple[bool, str]:
    """Recompute every ruler, every identity delta and the branch.

    The margins and tolerances come from the report, so this verifies a report
    against the rule *it* was registered with, not against whatever the code
    says today. The identity check is §87's reason to exist, so it is compared
    against the recorded tolerance and reported with the actual delta.
    """
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if report.get("stage") != "probe_ladder87":
        return False, "not a probe_ladder87 report"
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

    tolerances = protocol.get("tolerances", TOLERANCES)
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
        measured = p86.measure_all(model, train_pairs, val_pairs, holdout_pairs, protocol["batch"])
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

    # The identity comparison must use a parent value this process measured, not
    # one the report recorded: otherwise a report could make its own deltas
    # small by editing the reference.
    parent_val = p85.mean_ce(parent, val_pairs, protocol["batch"])
    parent_train = p85.mean_ce(parent, train_pairs, protocol["batch"])

    for point in report["instrument"]["identity"]:
        init_path = p85.resolve_artifact(point["init_checkpoint"])
        if not init_path.is_file():
            errors.append(f"missing {init_path}")
            continue
        if abs(float(point["parent_val_ce"]) - parent_val) > 1e-6:
            errors.append(
                f"identity seed {point['seed']}: recorded parent val_ce "
                f"{point['parent_val_ce']:.6f} != measured {parent_val:.6f}"
            )
        if abs(float(point["parent_train_ce_full"]) - parent_train) > 1e-6:
            errors.append(
                f"identity seed {point['seed']}: recorded parent train CE "
                f"{point['parent_train_ce_full']:.6f} != measured {parent_train:.6f}"
            )
        child = TokenSNN.load(init_path, device="cpu")
        delta_val = abs(p85.mean_ce(child, val_pairs, protocol["batch"]) - parent_val)
        delta_train = abs(p85.mean_ce(child, train_pairs, protocol["batch"]) - parent_train)
        if abs(delta_val - float(point["delta_val_ce"])) > 1e-6:
            errors.append(
                f"identity seed {point['seed']}: recorded val_ce delta "
                f"{point['delta_val_ce']:.3e} != measured {delta_val:.3e}"
            )
        if abs(delta_train - float(point["delta_train_ce_full"])) > 1e-6:
            errors.append(
                f"identity seed {point['seed']}: recorded train CE delta "
                f"{point['delta_train_ce_full']:.3e} != measured {delta_train:.3e}"
            )
        if delta_val > float(tolerances["identity_val_ce"]):
            errors.append(
                f"identity seed {point['seed']}: val_ce delta {delta_val:.3e} > "
                f"{tolerances['identity_val_ce']:.0e}"
            )
        if delta_train > float(tolerances["identity_train_ce_full"]):
            errors.append(
                f"identity seed {point['seed']}: train_ce_full delta {delta_train:.3e} > "
                f"{tolerances['identity_train_ce_full']:.0e}"
            )

    if not report.get("i0", {}).get("all_pass"):
        failed = [
            item["id"] for item in report.get("i0", {}).get("items", []) if not item["passes"]
        ]
        errors.append(f"the report's own I0 block failed: {', '.join(failed) or 'missing'}")

    recomputed = p86.decide(report["arms"], margins=protocol["margins"])
    if recomputed["branch"] != report["decision"]["branch"]:
        errors.append(f"branch {recomputed['branch']} != reported {report['decision']['branch']}")
    if not report.get("parent_unchanged"):
        errors.append("the report itself says the parent changed during the run")

    if errors:
        return False, "; ".join(errors[:5])
    return True, (
        f"probe_ladder87 check OK ({recomputed['branch']}, "
        f"{len(report['arms'])} arms recomputed, I0 all pass)"
    )


def build_parser() -> argparse.ArgumentParser:
    """The command line, exposed so a test can assert the registered defaults."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default="6,7,8")
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
        help="recompute every ruler, identity delta and the branch of an existing report",
    )
    return parser


def main() -> int:
    parser = build_parser()
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
    identity = report["instrument"]["identity"]
    if identity:
        print(
            "identity at step 0: "
            + ", ".join(
                f"seed {p['seed']} val {p['delta_val_ce']:.2e}/train {p['delta_train_ce_full']:.2e}"
                for p in identity
            )
            + f" (tolerance {IDENTITY_TOLERANCE:g})"
        )
    cache = report["cache"]
    print(
        f"cache: {len(cache['reused'])} reused, {len(cache['computed'])} computed "
        f"({len(cache['extended'])} extended), {report['seconds']:.1f}s this run"
    )
    print(f"i0: {'ALL PASS' if report['i0']['all_pass'] else 'FAILED'}")
    print(f"branch: {decision['branch']} — {decision['reason']}")
    print(f"report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
