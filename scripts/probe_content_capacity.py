#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# LAYER: learning
# =============================================================================
"""How much content can the token-SNN actually hold?

The core score answers "is it correct on the frozen tasks"; it does not answer
the question that decides whether a bigger training run is worth paying for:
**how many distinct input->answer pairs can this model store before it stops
reproducing them?** A model that saturates at a few hundred rows will not become
an assistant by training longer, and a model whose capacity grows with width
tells us the next run should buy width rather than epochs.

This probe measures three things and refuses to guess the rest:

A. **Envelope (no training).** Rows that fit ``--max-len``, how many are
   truncated mid-answer, vocabulary size, ``<unk>`` share of validation answer
   atoms, unique prompts, contradictory supervision, and the parameter budget
   per candidate width. These are hard ceilings: no amount of training adds a
   row that does not fit or a word that is not in the vocabulary.

B. **Memorisation capacity (training).** For a nested sample of N rows
   (128 < 512 < 2048, the same rows at every size), train a fresh model with a
   fixed per-row exposure (``--epochs``) and measure **teacher-forced whole
   answer accuracy on the training rows**. That is a storage measure, not a
   skill measure: the prompt is in front of the model and the gold prefix is
   fed, so a high value means "the answer is in the weights", nothing more.
   Greedy exact match is also reported on a small sample, because storage that
   cannot be decoded is not usable storage.

C. **Held-out transfer at the same sizes.** The same check on ``core_val``
   rows the run never trained on. It must be read next to B: capacity without
   transfer is a lookup table, transfer without capacity is a prior. Neither
   alone is "the model learned the domain".

The decision rule is written down before the run in
``docs/06-project-management/BETA_TRAINING_PLAN.md`` (section A): capacity is
the largest N whose teacher-forced whole-answer accuracy is >= 0.90. If even
128 fails, the answer is "this configuration cannot store 128 pairs at this
budget"; if every size passes, the answer is ">= 2048, the grid did not reach
the knee" — both are results, and neither is silently rounded up.

No benchmark item is touched: this probe trains on ``core_train.jsonl`` only,
which ``prepare_core_training_data.py`` already leak-checked, and evaluates on
``core_val.jsonl``. It writes no checkpoint unless ``--out`` is given, and it
never writes into ``apps/backend/data/models``.

Usage
    ./.venv/bin/python scripts/probe_content_capacity.py --inventory
    ./.venv/bin/python scripts/probe_content_capacity.py --sizes 128,512,2048
    ./.venv/bin/python scripts/probe_content_capacity.py --configs small,medium
    ./.venv/bin/python scripts/probe_content_capacity.py --check data/capacity/report.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from ai.ed3n.token_snn import TokenConfig, TokenSNN, TokenVocab, resolve_device  # noqa: E402
from train_token_snn import fits, read_pairs  # noqa: E402

PROCESSED = REPO_ROOT / "apps" / "backend" / "data" / "processed"
TRAIN = PROCESSED / "core_train.jsonl"
VAL = PROCESSED / "core_val.jsonl"
DEFAULT_OUT = REPO_ROOT / "data" / "capacity"

#: Stated before the run (BETA_TRAINING_PLAN.md §A). Whole-answer teacher-forced
#: accuracy at which a row counts as *stored*.
STORED = 0.90
#: Fixed per-row exposure: every size gets the same number of passes, so the
#: curve is "can N rows be stored with E epochs each", not "with E total".
EPOCHS = 8
#: Optimisation floor per arm, in update steps. ``epochs`` alone made the small
#: arm meaningless: 128 rows at batch 32 is four steps per epoch, so eight
#: "epochs" is 32 steps — a measurement of the optimiser, not of storage. The
#: floor keeps every arm at >= this many steps; larger N still gets its full
#: per-row exposure. Recorded as a pre-run amendment in BETA_TRAINING_PLAN.md §A
#: after the first launch was stopped (no capacity verdict was produced).
MIN_STEPS = 800
BATCH = 32
LR = 3e-3
SEED = 0

#: Two widths, both healthy under the documented guards: the small reference
#: (the width every earlier probe used) and one that spends ~8x the parameters
#: to ask whether capacity follows width.
CONFIGS: Dict[str, Tuple[int, int]] = {
    "small": (96, 192),
    "medium": (256, 1024),
}

#: Documented "run long and stay alive" guards (TRAINING_INTERNALS.md §4). They
#: cost a little early loss and keep the recurrence from being switched off.
GUARDS = {"theta_max": 1.0, "leak_floor": 0.85, "gain_cap": 1.0}


# ---------------------------------------------------------------------------
# envelope
# ---------------------------------------------------------------------------
def analytic_params(vocab_size: int, d_emb: int, d_hidden: int) -> int:
    """Parameter count of the 1-layer membrane-readout stack, exactly.

    Mirrors ``_make_net``: embed (no bias), w_in (bias), w_rec (no bias),
    out_norm, head (bias), plus the two scalars beta/theta. Verified against the
    108M checkpoint in ``tests/test_probe_content_capacity.py``.
    """
    embed = vocab_size * d_emb
    w_in = d_emb * d_hidden + d_hidden
    w_rec = d_hidden * d_hidden
    out_norm = 2 * d_hidden
    head = d_hidden * vocab_size + vocab_size
    return embed + w_in + w_rec + out_norm + head + 2


def _digest(text: str) -> bytes:
    return hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest()


def nested_sample(pairs: Sequence[Tuple[str, str]], sizes: Sequence[int]) -> Dict[int, List[int]]:
    """Indices for each N, nested by a content hash (not by file order).

    ``core_train.jsonl`` is grouped by source, so "the first 512 rows" would be
    one template family. Hashing the prompt+answer spreads the sample across
    families and makes the small sample a subset of the large one, so the curve
    compares *the same rows plus more* rather than three different populations.
    """
    order = sorted(
        range(len(pairs)), key=lambda i: (_digest(pairs[i][0] + "\x1f" + pairs[i][1]), i)
    )
    biggest = max(sizes)
    if biggest > len(order):
        raise ValueError(f"asked for {biggest} rows but the corpus has {len(order)}")
    return {n: order[:n] for n in sizes}


def inventory(
    train: Sequence[Tuple[str, str]],
    val: Sequence[Tuple[str, str]],
    max_len: int,
    vocab: TokenVocab,
) -> Dict[str, Any]:
    sizes = [3 + len(vocab.encode(p)) + len(vocab.encode(a)) for p, a in train]
    val_sizes = [3 + len(vocab.encode(p)) + len(vocab.encode(a)) for p, a in val]
    kept = sum(1 for n in sizes if n <= max_len)
    over = [n for n in sizes if n > max_len]
    prompts: Dict[str, set] = {}
    for prompt, answer in train:
        prompts.setdefault(prompt, set()).add(answer)
    contradictory = sum(1 for answers in prompts.values() if len(answers) > 1)
    widths = {
        name: {
            "d_emb": d_emb,
            "d_hidden": d_hidden,
            "params": analytic_params(len(vocab), d_emb, d_hidden),
            "fp32_mb": round(analytic_params(len(vocab), d_emb, d_hidden) * 4 / 1e6, 1),
            "train_mb_with_adam": round(analytic_params(len(vocab), d_emb, d_hidden) * 12 / 1e6, 1),
        }
        for name, (d_emb, d_hidden) in CONFIGS.items()
    }
    return {
        "train_rows": len(train),
        "val_rows": len(val),
        "val_rows_fitting_max_len": sum(1 for n in val_sizes if n <= max_len),
        "vocab_size": len(vocab),
        "max_len": max_len,
        "rows_fitting_max_len": kept,
        "rows_over_max_len": len(over),
        "median_atoms": sorted(sizes)[len(sizes) // 2] if sizes else 0,
        "unique_prompts": len(prompts),
        "prompts_with_multiple_answers": contradictory,
        "widths": widths,
    }


def encoded_unk_share(vocab: TokenVocab, pairs: Sequence[Tuple[str, str]]) -> float:
    """Share of *encoded* validation answer atoms that map to <unk>."""
    total = unk = 0
    for _, answer in pairs:
        ids = vocab.encode(answer)
        total += len(ids)
        unk += sum(1 for i in ids if i == vocab.unk_id)
    return round(unk / max(1, total), 4)


# ---------------------------------------------------------------------------
# measurement
# ---------------------------------------------------------------------------
def tf_whole(pairs: Sequence[Tuple[str, str]], model: TokenSNN, limit: int = 0) -> Dict[str, Any]:
    """Teacher-forced whole-answer accuracy: every answer token correct.

    One forward pass per batch, no generation. ``hits`` counts rows whose answer
    region is entirely argmax-correct; ``tf_acc`` is the token-level companion.
    """
    torch = model.torch
    picks = list(pairs if not limit else pairs[:limit])
    was = model.net.training
    model.net.eval()
    rows_hit = tok_hit = tok_all = 0
    with torch.no_grad():
        for start in range(0, len(picks), BATCH):
            chunk = picks[start : start + BATCH]
            ids, mask, _ = model.make_batch(chunk)
            pred = model.net(ids)[:, :-1, :].argmax(dim=-1)
            target = ids[:, 1:]
            keep = mask[:, 1:]
            right = (pred == target) & keep
            per_row = right.sum(dim=1)
            need = keep.sum(dim=1)
            rows_hit += int(((per_row == need) & (need > 0)).sum().item())
            tok_hit += int(right.sum().item())
            tok_all += int(keep.sum().item())
    if was:
        model.net.train()
    return {
        "n": len(picks),
        "whole": round(rows_hit / max(1, len(picks)), 4),
        "tf_acc": round(tok_hit / max(1, tok_all), 4),
    }


def greedy_exact(
    pairs: Sequence[Tuple[str, str]], model: TokenSNN, sample: int = 32
) -> Dict[str, Any]:
    """Greedy exact match on a bounded sample (storage you can decode)."""
    picks = list(pairs[:sample])
    hits = 0
    for prompt, answer in picks:
        budget = len(model.vocab.encode(answer)) + 8
        got = model.generate(prompt, max_new=min(model.config.max_len, budget))
        hits += int(got.strip() == answer.strip())
    return {"n": len(picks), "exact": round(hits / max(1, len(picks)), 4)}


def effective_epochs(size: int, batch: int, epochs: int, min_steps: int) -> int:
    """Epochs that give ``size`` at least ``min_steps`` update steps."""
    batches = max(1, math.ceil(size / batch))
    return max(epochs, math.ceil(min_steps / batches))


def _schedule(epoch: int, epochs: int, lr: float) -> float:
    done = min(1.0, (epoch + 1) / max(1, epochs))
    return 0.5 * lr * (1 + math.cos(math.pi * done))


def peak_rss_mb() -> float:
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)


def run_one(
    size: int,
    indices: Sequence[int],
    train: Sequence[Tuple[str, str]],
    val: Sequence[Tuple[str, str]],
    vocab: TokenVocab,
    name: str,
    d_emb: int,
    d_hidden: int,
    epochs: int,
    min_steps: int,
    device: str,
    out_dir: Optional[Path],
) -> Dict[str, Any]:
    import torch

    cfg = TokenConfig(d_emb=d_emb, d_hidden=d_hidden, max_len=192, max_vocab=12000, **GUARDS)
    torch.manual_seed(SEED)
    model = TokenSNN(vocab, cfg, device=device)
    rows = [train[i] for i in indices]
    run_epochs = effective_epochs(size, BATCH, epochs, min_steps)
    started = time.time()
    curve: List[Dict[str, Any]] = []

    def on_epoch(row: Dict[str, Any]) -> None:
        point = {"epoch": int(row["epoch"]) + 1, "loss": round(float(row["loss"]), 4)}
        point.update(tf_whole(rows, model, limit=min(size, 256)))
        curve.append(point)

    history = model.train_on(
        rows,
        epochs=run_epochs,
        batch_size=BATCH,
        lr=LR,
        seed=SEED,
        lr_at=lambda e: _schedule(e, run_epochs, LR),
        guard=True,
        on_epoch=on_epoch,
    )
    elapsed = time.time() - started
    train_check = tf_whole(rows, model)
    val_sample = list(val[: min(128, len(val))])
    val_check = tf_whole(val_sample, model)
    result: Dict[str, Any] = {
        "config": name,
        "d_emb": d_emb,
        "d_hidden": d_hidden,
        "params": sum(int(p.numel()) for p in model.net.parameters()),
        "size": size,
        "epochs": run_epochs,
        "epochs_requested": epochs,
        "steps": math.ceil(size / BATCH) * run_epochs,
        "batch": BATCH,
        "lr": LR,
        "seed": SEED,
        "guards": GUARDS,
        "device": str(model.device),
        "seconds": round(elapsed, 1),
        "final_loss": round(float(history[-1]["loss"]), 4) if history else None,
        "train": train_check,
        "train_exact": greedy_exact(rows, model),
        "val": val_check,
        "val_exact": greedy_exact(val_sample, model, sample=16),
        "curve": curve,
        "peak_rss_mb": peak_rss_mb(),
        "stored": bool(train_check["whole"] >= STORED),
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{name}_{size}.pt"
        model.save(path)
        result["checkpoint"] = str(path)
    return result


def capacity_of(runs: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Apply the pre-registered rule; do not round a failure up to a pass.

    Capacity is where the *contiguous* passing prefix ends: the first size that
    fails is the boundary, and a later pass does not move it (with nested
    samples a later pass would mean the curve is not monotone, which is
    reported rather than smoothed away).
    """
    by_config: Dict[str, Any] = {}
    for run in runs:
        by_config.setdefault(run["config"], []).append(run)
    for name, rows in by_config.items():
        rows.sort(key=lambda r: r["size"])
        sizes = [r["size"] for r in rows]
        flags = [bool(r["stored"]) for r in rows]
        first_fail = next((i for i, ok in enumerate(flags) if not ok), None)
        non_monotonic = first_fail is not None and any(flags[first_fail + 1 :])
        if first_fail == 0:
            verdict = f"not-even-{sizes[0]}"
        elif first_fail is None:
            verdict = f"at-least-{sizes[-1]}"
        else:
            verdict = f"between-{sizes[first_fail - 1]}-and-{sizes[first_fail]}"
        by_config[name] = {
            "sizes": sizes,
            "stored_sizes": [r["size"] for r in rows if r["stored"]],
            "failed_sizes": [r["size"] for r in rows if not r["stored"]],
            "capacity": verdict,
            "non_monotonic": non_monotonic,
            "params": rows[0]["params"],
        }
    return by_config


# ---------------------------------------------------------------------------
# report check (the arithmetic must be auditable without rerunning training)
# ---------------------------------------------------------------------------
def check_report(report: Dict[str, Any]) -> List[str]:
    problems: List[str] = []
    runs = report.get("runs") or []
    if not runs:
        return ["report has no runs"]
    for run in runs:
        label = f"{run.get('config')}/{run.get('size')}"
        train = run.get("train") or {}
        if not train.get("n"):
            problems.append(f"{label}: train measured on 0 rows")
        elif run.get("stored") != (train.get("whole", 0) >= STORED):
            problems.append(f"{label}: stored flag disagrees with the rule")
        if int(train.get("n", 0)) != int(run.get("size", -1)):
            problems.append(f"{label}: train.n {train.get('n')} != size {run.get('size')}")
        curve = run.get("curve") or []
        if len(curve) != int(run.get("epochs", -1)):
            problems.append(f"{label}: {len(curve)} curve points for {run.get('epochs')} epochs")
        if not (0.0 <= float(train.get("whole", -1)) <= 1.0):
            problems.append(f"{label}: whole-answer accuracy outside [0,1]")
        if run.get("params", 0) < 1000:
            problems.append(f"{label}: implausible parameter count {run.get('params')}")
    derived = capacity_of(runs)
    declared = report.get("capacity") or {}
    for name, row in derived.items():
        if name not in declared:
            problems.append(f"capacity for {name} missing from the report")
        elif declared[name].get("capacity") != row["capacity"]:
            problems.append(
                f"capacity for {name} says {declared[name].get('capacity')!r}, "
                f"recomputed {row['capacity']!r}"
            )
        elif bool(declared[name].get("non_monotonic")) != row["non_monotonic"]:
            problems.append(f"capacity for {name}: non_monotonic flag disagrees with the runs")
    return problems


# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train", default=str(TRAIN))
    ap.add_argument("--val", default=str(VAL))
    ap.add_argument("--max-len", type=int, default=192)
    ap.add_argument("--max-vocab", type=int, default=12000)
    ap.add_argument("--sizes", default="128,512,2048", help="comma-separated row counts")
    ap.add_argument("--configs", default="small,medium", help="comma-separated widths")
    ap.add_argument("--epochs", type=int, default=EPOCHS)
    ap.add_argument(
        "--min-steps",
        type=int,
        default=MIN_STEPS,
        help="per-arm optimisation floor (update steps); see BETA_TRAINING_PLAN.md §A",
    )
    ap.add_argument("--device", default="auto")
    ap.add_argument("--inventory", action="store_true", help="envelope only, no training")
    ap.add_argument("--out", default="", help="directory for checkpoints (default: none)")
    ap.add_argument("--report", default=str(DEFAULT_OUT / "report.json"))
    ap.add_argument("--check", default="", help="validate an existing report and exit")
    args = ap.parse_args(argv)

    if args.check:
        report = json.loads(Path(args.check).read_text(encoding="utf-8"))
        problems = check_report(report)
        for problem in problems:
            print(f"  ❌ {problem}")
        if not problems:
            print(f"  ✅ {args.check}: arithmetic and capacity rule agree with the runs")
        return 1 if problems else 0

    train = read_pairs(Path(args.train))
    val = read_pairs(Path(args.val))
    if not train:
        print(f"no pairs in {args.train}")
        return 1
    # One vocabulary for every run, built from the whole training corpus:
    # a per-size vocabulary would change the ids between arms and turn the
    # curve into a comparison of tokenizers.
    vocab = TokenVocab.build(
        [p + "\n" + a for p, a in train], min_count=1, max_vocab=args.max_vocab
    )
    train_fit = fits(train, vocab, args.max_len)
    val_fit = fits(val, vocab, args.max_len)
    # The envelope is measured on the *whole* corpus: passing only the rows
    # that already fit would report ``over=0`` by construction and hide the
    # rows the vocabulary/max_len budget silently drops.
    env = inventory(train, val, args.max_len, vocab)
    env["val_encoded_unk_share"] = encoded_unk_share(vocab, val)
    env["device_requested"] = args.device
    print(
        f"envelope: train={env['train_rows']} fit={env['rows_fitting_max_len']} "
        f"over={env['rows_over_max_len']} vocab={env['vocab_size']} "
        f"val_unk={env['val_encoded_unk_share']:.4f} "
        f"unique_prompts={env['unique_prompts']}"
    )
    for name, row in env["widths"].items():
        print(
            f"  width {name}: d_emb={row['d_emb']} d_hidden={row['d_hidden']} "
            f"params={row['params']:,} fp32={row['fp32_mb']}MB train~{row['train_mb_with_adam']}MB"
        )
    if args.inventory:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(
            json.dumps({"envelope": env, "runs": []}, indent=2), encoding="utf-8"
        )
        print(f"wrote {args.report}")
        return 0

    import torch

    device = resolve_device(torch, args.device)
    sizes = [int(x) for x in args.sizes.split(",") if x.strip()]
    configs = [x.strip() for x in args.configs.split(",") if x.strip()]
    picked = nested_sample(train_fit, sizes)
    out_dir = Path(args.out) if args.out else None
    print(f"device={device} sizes={sizes} configs={configs} epochs={args.epochs}")

    runs: List[Dict[str, Any]] = []
    for name in configs:
        if name not in CONFIGS:
            print(f"unknown config {name!r}; choose from {sorted(CONFIGS)}")
            return 2
        d_emb, d_hidden = CONFIGS[name]
        for size in sizes:
            print(f"\n-- {name} N={size} d_emb={d_emb} d_hidden={d_hidden}", flush=True)
            result = run_one(
                size=size,
                indices=picked[size],
                train=train_fit,
                val=val_fit,
                vocab=vocab,
                name=name,
                d_emb=d_emb,
                d_hidden=d_hidden,
                epochs=args.epochs,
                min_steps=args.min_steps,
                device=device,
                out_dir=out_dir,
            )
            runs.append(result)
            print(
                f"   train whole={result['train']['whole']:.3f} "
                f"tf={result['train']['tf_acc']:.3f} exact={result['train_exact']['exact']:.3f} "
                f"| val whole={result['val']['whole']:.3f} "
                f"| {result['seconds']:.0f}s loss={result['final_loss']}"
            )

    capacity = capacity_of(runs)
    report = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "protocol": {
            "stored_threshold": STORED,
            "epochs_per_size": args.epochs,
            "min_steps": args.min_steps,
            "batch": BATCH,
            "lr": LR,
            "seed": SEED,
            "guards": GUARDS,
            "max_len": args.max_len,
            "max_vocab": args.max_vocab,
            "sizes": sizes,
            "configs": configs,
            "measure": "teacher-forced whole-answer accuracy on the training rows",
            "effective_epochs": "max(epochs, ceil(min_steps / ceil(size/batch)))",
            "note": (
                "capacity is a storage measure, not a skill measure; the val columns "
                "are the transfer check and are read next to it, never instead of it"
            ),
        },
        "envelope": env,
        "runs": runs,
        "capacity": capacity,
        "peak_rss_mb": peak_rss_mb(),
    }
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\ncapacity (100% of the pre-registered rule, no rounding up):")
    for name, row in capacity.items():
        print(
            f"  {name}: {row['capacity']}  params={row['params']:,}  "
            f"stored={row['stored_sizes']} failed={row['failed_sizes']}"
        )
    print(f"wrote {path}")
    problems = check_report(report)
    if problems:
        for problem in problems:
            print(f"  ❌ {problem}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
