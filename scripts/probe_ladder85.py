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

Every arm is a content-addressed unit (``scripts/incremental.py``): the key is
the digest of everything that can change its result, so

* re-running an unchanged protocol computes **nothing** (all units are reused);
* adding a seed computes only that seed's arms;
* raising ``--epochs`` resumes each arm from its longest cached prefix and
  trains only the new epochs — the optimizer state is saved with the unit and
  ``TokenSNN.train_on`` continues the epoch/shuffle sequence, so an extended run
  is bitwise equal to an unbroken one (measured, not assumed);
* editing the trainer, the widening tool, this file, the parent checkpoint or
  the corpus invalidates the units, because those units came from other code or
  other data.

``--adopt-report`` seeds the cache from an existing ``report.json`` after
recomputing each arm's two measurements from its checkpoint, so a run produced
before the cache existed can still be reused.
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
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from ai.ed3n.token_snn import TokenConfig, TokenSNN  # noqa: E402
from expand_token_snn import expand_model  # noqa: E402
from incremental import UnitCache, digest, file_digest, impl_digest  # noqa: E402
from train_token_snn import exact_match, fits, read_pairs  # noqa: E402

DATA = REPO_ROOT / "apps" / "backend" / "data"
PARENT = DATA / "models" / "token_snn_distill.pt"
TRAIN = DATA / "processed" / "distill_train.jsonl"
VAL = DATA / "processed" / "distill_val.jsonl"
HOLDOUT = DATA / "processed" / "distill_val_holdout.jsonl"
OUT_DIR = REPO_ROOT / "data" / "ladder85"
CACHE_DIR = OUT_DIR / "cache"
REPORT = OUT_DIR / "report.json"

#: The code whose behaviour a unit's numbers depend on. Editing any of it
#: invalidates the unit, because the unit was produced by different code.
IMPL_FILES: Tuple[Path, ...] = (
    REPO_ROOT / "apps" / "backend" / "src" / "ai" / "ed3n" / "token_snn.py",
    REPO_ROOT / "scripts" / "expand_token_snn.py",
    REPO_ROOT / "scripts" / "train_token_snn.py",
    Path(__file__).resolve(),
)

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


def rows_digest(
    train_pairs: Sequence[Tuple[str, str]],
    val_pairs: Sequence[Tuple[str, str]],
    holdout_pairs: Sequence[Tuple[str, str]],
) -> Dict[str, str]:
    """Content hashes of the three row sets (a corpus edit is a new unit)."""
    return {
        "train": digest([list(pair) for pair in train_pairs]),
        "val": digest([list(pair) for pair in val_pairs]),
        "holdout": digest([list(pair) for pair in holdout_pairs]),
    }


def display_path(path: Path) -> str:
    """Repo-relative when inside the repo, absolute otherwise.

    ``--out-dir`` may be relative or outside the tree; the report must still
    record a path that resolves, and ``relative_to`` raises on both.
    """
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def resolve_artifact(value: str) -> Path:
    """An artifact path from a unit: absolute already, or relative to the repo."""
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def parse_arms(text: str) -> List[str]:
    """The selected arms, in the caller's order. Refuses an unknown name: a
    typo must not silently produce a report that looks complete."""
    arms = [name.strip() for name in str(text).split(",") if name.strip()]
    unknown = [name for name in arms if name not in ARMS]
    if unknown:
        raise ValueError(f"unknown arm(s): {', '.join(unknown)}; known: {', '.join(ARMS)}")
    if not arms:
        raise ValueError("no arms selected")
    return arms


def arm_plan(
    parent_digest: str,
    arm: str,
    seed: int,
    rows: Dict[str, str],
    protocol: Dict[str, Any],
    impl: str,
) -> Dict[str, Any]:
    """Everything that can change one arm's numbers. One definition, two users:
    the compute path and the cache lookup. If this dict misses an input, a stale
    unit is reused; the contract tests change each field and demand a new key."""
    return {
        "parent": parent_digest,
        "arm": arm,
        "seed": int(seed),
        "rows": dict(rows),
        "protocol": dict(protocol),
        "impl": impl,
    }


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
        return TokenSNN(vocab=parent.vocab, config=config, device="cpu")
    raise ValueError(f"unknown arm {name!r}")


def _unit_paths(out_dir: Path, name: str, seed: int, epochs: int) -> Tuple[Path, Path]:
    stem = Path(out_dir) / "units" / f"{name}_{seed}_{epochs}"
    return Path(str(stem) + ".pt"), Path(str(stem) + "_opt.pt")


def prefix_unit(cache: UnitCache, plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The longest cached prefix of ``plan`` (same arm, fewer epochs, same
    everything else) that can actually be continued.

    A prefix without an optimizer state can be *reused* but not *extended*:
    continuing from it would silently start Adam from zero and stop being the
    same run, so it is not a candidate here.
    """
    target = int(plan["protocol"]["epochs"])
    base = dict(plan)
    base["protocol"] = dict(plan["protocol"])
    del base["protocol"]["epochs"]
    best: Optional[Dict[str, Any]] = None
    for key in cache.keys():
        unit = cache.load(key)
        if unit is None:
            continue
        other = dict(unit.plan)
        other_protocol = dict(other.get("protocol") or {})
        if "epochs" not in other_protocol:
            continue
        other_epochs = int(other_protocol.pop("epochs"))
        other["protocol"] = other_protocol
        if other != base or other_epochs >= target:
            continue
        if cache.verify(unit):
            continue
        if not unit.artifact("opt_state"):
            continue
        if best is None or other_epochs > int(best["epochs"]):
            best = {"unit": unit, "epochs": other_epochs}
    return best


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
    resume_from: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Train (or extend) one arm. ``resume_from`` continues that unit's weights
    and optimizer state from its recorded epoch count."""
    import torch

    tensor_ce200 = list(train_pairs[:200])
    prefix_unit_obj = (resume_from or {}).get("unit")
    start_epoch = int((resume_from or {}).get("epochs", 0))
    if prefix_unit_obj is not None:
        checkpoint = resolve_artifact(prefix_unit_obj.artifact("checkpoint")["path"])
        opt_artifact = prefix_unit_obj.artifact("opt_state")
        blob = torch.load(
            resolve_artifact(opt_artifact["path"]), map_location="cpu", weights_only=True
        )
        # The optimizer file also carries the stability rule's memory, because
        # resuming without it re-enters the next epoch with different weights
        # and a different learning rate after a rollback.
        opt_state = blob.get("opt") if isinstance(blob, dict) and "opt" in blob else blob
        guard_state = blob.get("guard") if isinstance(blob, dict) else None
        model = TokenSNN.load(checkpoint, device="cpu")
        start_ce = float(prefix_unit_obj.payload["start_val_ce"])
        start_ce200 = float(prefix_unit_obj.payload["start_train_ce200"])
        curve: List[Dict[str, Any]] = list(prefix_unit_obj.payload.get("curve") or [])
        spent_before = float(prefix_unit_obj.payload.get("cumulative_seconds", 0.0))
    else:
        opt_state = None
        guard_state = None
        model = build_arm(name, seed, parent)
        start_ce = mean_ce(model, val_pairs, batch)
        start_ce200 = mean_ce(model, tensor_ce200, batch)
        curve = [{"epoch": 0, "val_ce": start_ce, "train_ce200": start_ce200, "seconds": 0.0}]
        spent_before = 0.0
        if name == "warm":
            model.save(out_dir / f"warm_init_{seed}.pt")

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
                "seconds": round(spent_before + (time.time() - started), 1),
            }
        )
        print(
            f"    {name}/seed{seed} epoch {curve[-1]['epoch']}: "
            f"train={curve[-1]['train_loss']:.4f} val={curve[-1]['val_ce']:.4f} "
            f"({curve[-1]['seconds']:.0f}s)",
            flush=True,
        )

    optimizer_state: Dict[str, Any] = {}
    guard_out: Dict[str, Any] = {}
    model.train_on(
        list(train_pairs),
        epochs=epochs - start_epoch,
        batch_size=batch,
        lr=lr,
        seed=seed,
        on_epoch=on_epoch,
        tail_weight=1.0,
        ss_final=0.0,
        guard=True,
        start_epoch=start_epoch,
        opt_state=opt_state,
        opt_state_out=optimizer_state,
        guard_state=guard_state,
        guard_state_out=guard_out,
    )
    seconds = time.time() - started
    final_ce = mean_ce(model, val_pairs, batch)
    final_ce200 = mean_ce(model, tensor_ce200, batch)
    holdout = exact_count(model, holdout_pairs)

    checkpoint_path, opt_path = _unit_paths(out_dir, name, seed, epochs)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(checkpoint_path)
    torch.save({"opt": optimizer_state, "guard": guard_out}, opt_path)

    new_rows = epochs - start_epoch
    return {
        "arm": name,
        "label": ARM_LABELS[name],
        "seed": int(seed),
        "epochs": int(epochs),
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
        "cumulative_seconds": round(spent_before + seconds, 1),
        "computed_epochs": int(new_rows),
        "resumed_from_epoch": int(start_epoch),
        "ms_per_row": round(1000.0 * seconds / max(1, len(train_pairs) * new_rows), 2),
        "checkpoint": display_path(checkpoint_path),
        "opt_state": display_path(opt_path),
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


def _protocol(args: argparse.Namespace, epochs: int) -> Dict[str, Any]:
    """The registered protocol of one arm. ``epochs`` is the arm's total."""
    return {
        "epochs": int(epochs),
        "batch": int(args.batch),
        "lr": float(args.lr),
        "factor": FACTOR,
        "noise": NOISE,
        "tail_weight": 1.0,
        "ss_final": 0.0,
        "guard": True,
        "optimizer": "adam",
        "clip_grad_norm": 1.0,
    }


def run(args: argparse.Namespace) -> Dict[str, Any]:
    import torch

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    cache = UnitCache(Path(args.cache), base=REPO_ROOT)
    parent = TokenSNN.load(PARENT, device="cpu")
    parent_digest = _sha256_file(PARENT)
    train_pairs, val_pairs, holdout_pairs = _pairs(parent)
    row_digests = rows_digest(train_pairs, val_pairs, holdout_pairs)
    impl = impl_digest(IMPL_FILES)
    seeds = [int(s) for s in str(args.seeds).split(",") if s.strip()]
    arms = parse_arms(args.arms)

    overlap = {
        "train_and_val": len(set(train_pairs) & set(val_pairs)),
        "train_and_holdout": len(set(train_pairs) & set(holdout_pairs)),
        "val_and_holdout": len(set(val_pairs) & set(holdout_pairs)),
    }
    orders = {str(seed): shuffle_digest(len(train_pairs), seed, 0) for seed in seeds}
    steps = math.ceil(len(train_pairs) / args.batch) * args.epochs

    rows: List[Dict[str, Any]] = []
    reused: List[str] = []
    computed: List[str] = []
    extended: List[str] = []
    partial_path = out_dir / "report.partial.json"
    started = time.time()
    for seed in seeds:
        for name in arms:
            plan = arm_plan(
                parent_digest, name, seed, row_digests, _protocol(args, args.epochs), impl
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

            resume = None if args.no_resume else prefix_unit(cache, plan)
            if resume:
                extended.append(f"{label}@{resume['epochs']}->{args.epochs}")
                print(
                    f"extend {label}: {resume['epochs']} -> {args.epochs} epochs "
                    f"({resume['unit'].key[:19]})",
                    flush=True,
                )
            else:
                print(f"compute {label} ...", flush=True)
            row = run_arm(
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
            row["reused"] = False
            row["seconds_this_run"] = row["seconds"]
            if not args.no_store:
                unit = cache.store(
                    plan,
                    row,
                    artifacts=[
                        ("checkpoint", resolve_artifact(row["checkpoint"])),
                        ("opt_state", resolve_artifact(row["opt_state"])),
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
            "arm_list": arms,
            "optimizer_steps_per_arm": steps,
            "guard": True,
            "tail_weight": 1.0,
            "ss_final": 0.0,
            "impl_digest": impl,
            "rows_digest": row_digests,
        },
        "instrument": {
            "overlap": overlap,
            "shuffle_digest_epoch0": orders,
            "identity": identity,
            "threads": os.environ.get("OMP_NUM_THREADS"),
            "torch": torch.__version__,
            "cpu_count": os.cpu_count(),
        },
        "cache": {
            "reused": reused,
            "computed": computed,
            "extended": extended,
            "units_dir": display_path(args.cache),
        },
        "arms": rows,
        "decision": decision,
        "seconds": round(time.time() - started, 1),
        "parent_unchanged": _sha256_file(PARENT) == parent_digest,
    }
    return report


def adopt(report_path: Path, args: argparse.Namespace) -> Dict[str, Any]:
    """Register an existing report's arms as units, after checking them.

    A cache seeded from a report must be checked, not trusted: each arm's two
    measurements are recomputed from its checkpoint, and a mismatch refuses the
    adoption. The optimizer state was not saved by pre-cache runs, so adopted
    units can be reused but not extended.
    """
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if report.get("stage") != "probe_ladder85":
        raise SystemExit("not a probe_ladder85 report")
    cache = UnitCache(Path(args.cache), base=REPO_ROOT)
    parent = TokenSNN.load(PARENT, device="cpu")
    parent_digest = _sha256_file(PARENT)
    train_pairs, val_pairs, holdout_pairs = _pairs(parent)
    row_digests = rows_digest(train_pairs, val_pairs, holdout_pairs)
    impl = impl_digest(IMPL_FILES)
    protocol_base = report["protocol"]
    adopted, refused = [], []
    for row in report["arms"]:
        epochs = int(row.get("epochs", protocol_base.get("epochs", 0)))
        protocol = _protocol(
            argparse.Namespace(
                batch=int(protocol_base["batch"]),
                lr=float(protocol_base["lr"]),
            ),
            epochs,
        )
        plan = arm_plan(parent_digest, row["arm"], int(row["seed"]), row_digests, protocol, impl)
        checkpoint = resolve_artifact(row["checkpoint"])
        if not checkpoint.is_file():
            refused.append(f"{row['arm']}/seed{row['seed']}: checkpoint missing")
            continue
        model = TokenSNN.load(checkpoint, device="cpu")
        measured = mean_ce(model, val_pairs, protocol_base["batch"])
        holdout = exact_count(model, holdout_pairs)
        problems = []
        if abs(measured - float(row["final_val_ce"])) > 1e-4:
            problems.append(f"val CE {measured:.6f} != {row['final_val_ce']:.6f}")
        if abs(holdout["hits"] - float(row["holdout_hits"])) > 1e-9:
            problems.append(f"hold-out {holdout['hits']:.0f} != {row['holdout_hits']:.0f}")
        if problems:
            refused.append(f"{row['arm']}/seed{row['seed']}: " + "; ".join(problems))
            continue
        payload = dict(row)
        payload["epochs"] = epochs
        payload["reused"] = True
        payload.pop("opt_state", None)
        # No optimizer state was saved by pre-cache runs: this unit can be
        # reused but not extended, and ``prefix_unit`` skips it for that reason.
        cache.store(
            plan, payload, artifacts=[("checkpoint", checkpoint)], seconds=float(row["seconds"])
        )
        adopted.append(f"{row['arm']}/seed{row['seed']}")
    return {"adopted": adopted, "refused": refused}


def overlap_problem(overlap: Dict[str, int], holdout_rows: int) -> Optional[str]:
    """I0-2 as registered (§85.2/§85.6): the hold-out set is *inside* val.

    ``val_and_holdout`` therefore equals the hold-out size by construction; what
    must be zero is the training corpus touching either evaluation set. Treating
    the nested pair as a leak would reject a correct run.
    """
    if int(overlap.get("train_and_val", 0)) != 0:
        return f"train/val overlap is not zero: {overlap}"
    if int(overlap.get("train_and_holdout", 0)) != 0:
        return f"train/hold-out overlap is not zero: {overlap}"
    if int(overlap.get("val_and_holdout", 0)) != int(holdout_rows):
        return (
            f"the hold-out is not a subset of val: {overlap.get('val_and_holdout')} "
            f"of {holdout_rows} rows"
        )
    return None


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
    if "rows_digest" in protocol:
        if rows_digest(train_pairs, val_pairs, holdout_pairs) != protocol["rows_digest"]:
            return False, "row contents changed since the report was written"

    overlap = report["instrument"]["overlap"]
    problem = overlap_problem(overlap, int(protocol["rows"]["holdout"]))
    if problem:
        return False, problem

    errors: List[str] = []
    for row in report["arms"]:
        path = resolve_artifact(row["checkpoint"])
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
        "--adopt-report",
        type=Path,
        metavar="REPORT",
        help="seed the cache from an existing report, after re-measuring its arms",
    )
    parser.add_argument(
        "--check",
        type=Path,
        metavar="REPORT",
        help="recompute the measurements and the branch of an existing report",
    )
    args = parser.parse_args()
    try:
        parse_arms(args.arms)
    except ValueError as error:
        parser.error(str(error))

    if args.check:
        ok, message = check(args.check)
        print(message if ok else f"FAIL: {message}")
        return 0 if ok else 1
    if args.adopt_report:
        outcome = adopt(args.adopt_report, args)
        print(json.dumps(outcome, indent=1, ensure_ascii=False))
        return 0 if not outcome["refused"] else 1

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
            f"{name:14s} params={row['params']:,.0f} start={row['start_val_ce']:.4f} "
            f"final={row['final_val_ce']:.4f} (sd {row['final_val_ce_sd']:.4f}) "
            f"holdout={row['holdout_hits']:.0f}/{row['holdout_n']:.0f} "
            f"{row['ms_per_row']:.1f} ms/row"
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
