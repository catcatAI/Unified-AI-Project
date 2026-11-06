#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""Train the token-level SNN decoder (surrogate gradient) on core pairs.

This is the representation/objective fix described in
``docs/06-project-management/CORE_GAP_ANALYSIS.md``: tokens instead of
dictionary glosses, cross-entropy on the answer instead of associations.
It never trains on benchmark items — ``prepare_core_training_data.py`` already
removed those.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Union

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

from ai.ed3n.token_snn import (  # noqa: E402
    CharVocab,
    TokenConfig,
    TokenSNN,
    TokenVocab,
    _VALUE_ATOMS_BY_DECIMALS,
    resolve_device,
    tokenize,
)

DEFAULT_TRAIN = REPO_ROOT / "apps" / "backend" / "data" / "processed" / "core_train.jsonl"
DEFAULT_VAL = REPO_ROOT / "apps" / "backend" / "data" / "processed" / "core_val.jsonl"
OUT_DIR = REPO_ROOT / "apps" / "backend" / "data" / "models"
REPORT_DIR = REPO_ROOT / "data" / "intelligence_reports"


def _rows(path: Path) -> List[dict]:
    """Accept CSV, JSON arrays and JSONL (the repo has all three)."""
    if path.suffix.lower() == ".csv":
        import csv

        with path.open(encoding="utf-8", newline="") as f:
            return [dict(row) for row in csv.DictReader(f)]
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text.startswith("["):
        return [row for row in json.loads(text) if isinstance(row, dict)]
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def read_pairs(path: Path, limit: int = 0) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for row in _rows(path):
        prompt = str(row.get("input") or row.get("problem") or "").strip()
        answer = str(row.get("output") or row.get("answer") or "").strip()
        if prompt and answer:
            pairs.append((prompt, answer))
        if limit and len(pairs) >= limit:
            break
    return pairs


def fits(
    pairs: List[Tuple[str, str]], vocab: Union[CharVocab, TokenVocab], max_len: int
) -> List[Tuple[str, str]]:
    # Budget is in *vocab units*: characters for CharVocab, atoms for
    # TokenVocab (a 74-char question costs ~16 atoms).
    def size(prompt: str, answer: str) -> int:
        return 3 + len(vocab.encode(prompt)) + len(vocab.encode(answer))  # bos+nl+eos

    kept = [(p, a) for p, a in pairs if size(p, a) <= max_len]
    return kept


def exact_match(
    model: TokenSNN, pairs: List[Tuple[str, str]], sample: int, seed: int = 0
) -> Dict[str, float]:
    picks = pairs if len(pairs) <= sample else random.Random(seed).sample(pairs, sample)
    hits = 0
    # generate() re-runs the whole prefix per token, so one row costs
    # O(len^2) forward passes: measured ~8 s/row at 143 tokens on XPU, i.e. the
    # default 200-row probe is a silent 25-minute tail after training. Print
    # progress, otherwise a finished run looks hung.
    started = time.time()
    for i, (prompt, answer) in enumerate(picks, 1):
        if i % 25 == 0:
            print(
                f"    exact-match {i}/{len(picks)} ({time.time() - started:.0f}s)",
                flush=True,
            )
        # budget in vocab units: token vocabs make answers shorter in ids,
        # and an over-long budget lets the decode run past EOS into junk.
        budget = len(model.vocab.encode(answer)) + 8
        got = model.generate(prompt, max_new=min(model.config.max_len, budget))
        if got.strip() == answer.strip():
            hits += 1
    return {"n": len(picks), "exact": hits / max(1, len(picks))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default=str(DEFAULT_TRAIN))
    ap.add_argument("--val", default=str(DEFAULT_VAL))
    ap.add_argument(
        "--match-sample",
        type=int,
        default=200,
        help="rows for the final free-running exact match (default 200; 0 skips it). "
        "Each row costs O(len^2) forwards, so this is the slow tail of a run.",
    )
    ap.add_argument(
        "--eval-data",
        default="",
        help="separate held-out split (e.g. arithmetic_test.csv); never the benchmarks",
    )
    ap.add_argument("--eval-sample", type=int, default=500)
    ap.add_argument(
        "--eval-every",
        type=int,
        default=0,
        help="evaluate the held-out split every N epochs (learning curve)",
    )
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=3e-3)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-len", type=int, default=192)
    ap.add_argument(
        "--tail-weight",
        type=float,
        default=1.0,
        help="loss weight for the <al_out> state block (1.0 = off). Round-1 "
        # literal % must be escaped: argparse formats help with %-substitution,
        # so an unescaped percent crashes `--help` ("%o format")
        "measurement: that block is 34%% of answer tokens, trains to 77-80%% "
        "teacher-forced while the response sits at 14-26%%, so it carries the "
        "loss without teaching generation. Lower it to spend the gradient on "
        "the response. The loss is a weighted *mean*, so the LR scale does "
        "not change.",
    )
    ap.add_argument("--d-hidden", type=int, default=192)
    ap.add_argument(
        "--ss-final",
        type=float,
        default=0.0,
        help="scheduled-sampling ceiling (0.0 = off, plain teacher forcing). "
        "The mixing probability ramps linearly to this value across epochs: "
        "late training feeds the model its own predictions, the regime greedy "
        "decoding runs in. Round-2 evidence: response_tf 23%% teacher-forced "
        "but exact 0 free-running (exposure bias).",
    )
    ap.add_argument("--d-emb", type=int, default=96)
    ap.add_argument("--beta", type=float, default=0.9, help="membrane leak (used as-is)")
    ap.add_argument(
        "--readout",
        choices=("spike", "membrane"),
        default="membrane",
        help="what the head reads each step: membrane potential (SLAYER, measured "
        "winner, default) or binary spikes (the old head, for A/B control)",
    )
    ap.add_argument("--layers", type=int, default=1, help="stacked LIF layers")
    ap.add_argument(
        "--timesteps",
        type=int,
        default=1,
        help="SNN timesteps per token (input expansion; costs Kx compute)",
    )
    ap.add_argument(
        "--device",
        default="auto",
        help="torch device for training/inference: auto (xpu>cuda>cpu), xpu, cuda, cpu",
    )
    ap.add_argument(
        "--guard",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="stability rule (default on): a non-finite epoch, or one more than "
        "--diverge-factor times the best so far, restores the best finite weights "
        "and halves the lr. Oscillation is allowed; runaway is not.",
    )
    ap.add_argument(
        "--diverge-factor",
        type=float,
        default=3.0,
        help="how many times the best epoch counts as a runaway (default 3.0)",
    )
    ap.add_argument(
        "--theta-max",
        type=float,
        default=2.0,
        help="upper bound for the learned spike threshold (default 2.0; 0 disables). "
        "Beyond it the surrogate gradient is gone, so an unbounded threshold is a "
        "free way to stop learning while the loss still looks fine.",
    )
    ap.add_argument(
        "--leak-floor",
        type=float,
        default=0.0,
        help="floor for the effective membrane leak (default 0 = off). The leak falls "
        "monotonically while training, which shortens the memory horizon for free; "
        "flooring it keeps the recurrence integrating instead of wire-through.",
    )
    ap.add_argument(
        "--gain-cap",
        type=float,
        default=0.0,
        help="cap on the spectral radius of each w_rec (default 0 = off). Above 1 a "
        "perturbation grows per step and only the threshold keeps the stack bounded.",
    )
    ap.add_argument(
        "--lr-schedule",
        choices=("cosine", "constant"),
        default="cosine",
        help="base learning-rate shape; the guard may still lower it (default cosine)",
    )
    ap.add_argument(
        "--warmup",
        type=int,
        default=0,
        help="epochs of linear warmup before the schedule (default 0)",
    )
    ap.add_argument(
        "--min-lr",
        type=float,
        default=1e-5,
        help="floor for both the schedule and the guard's halving (default 1e-5)",
    )
    ap.add_argument(
        "--patience",
        type=int,
        default=0,
        help="stop when validation loss has not improved for N epochs; also makes "
        "the saved checkpoint the best *validation* epoch (default 0 = off)",
    )
    ap.add_argument("--out", default=str(OUT_DIR / "token_snn.pt"))
    ap.add_argument("--report", default=str(REPORT_DIR / "token_snn.json"))
    ap.add_argument(
        "--epoch-pause",
        type=float,
        default=0.0,
        help="seconds to sleep after each epoch. A safety valve: it drains "
        "the SYCL command queue between epochs. The 2026-10-29 bisection "
        "traced the xe CAT / DEVICE_LOST faults to the CSR override env vars "
        "that xpu_run.sh no longer sets, not to duty cycle -- with them gone "
        "a continuous soak ran clean, so this pause is optional.",
    )
    ap.add_argument(
        "--eval-on-cpu",
        action="store_true",
        help="run the post-training evaluation on CPU. A safety valve: the "
        "autoregressive eval does one host sync per token and was where a "
        "faulted run used to be lost. The device fault itself was traced to "
        "the CSR env vars (removed from xpu_run.sh); with them gone a full "
        "run including eval completed cleanly, so this stays optional.",
    )
    ap.add_argument(
        "--resume",
        action="store_true",
        help="load weights/vocab/config from --out before training (continue "
        "an interrupted run; refuses if the data vocab differs from the "
        "checkpoint).",
    )
    ap.add_argument(
        "--vocab",
        choices=("char", "token"),
        default="char",
        help="char = per-character ids (the original); token = word atoms "
        "(words carry their trailing spaces, numbers split to digits) — "
        "shorter sequences for long questions (CORE_GAP_ANALYSIS fix path)",
    )
    ap.add_argument(
        "--numeric-atoms",
        action="store_true",
        help="token vocab only: represent a contract value (one digit, dot, two "
        "decimals, |v| <= 1) as a single atom from a closed 201-symbol "
        "alphabet instead of 3-4 digit ids. The graded state block is six such "
        "values, so this turns its emission into copy-with-scale over a bounded "
        "alphabet rather than digit-carrying arithmetic (CORE_GAP §十八).",
    )
    ap.add_argument(
        "--value-decimals",
        type=int,
        choices=(2, 3),
        default=3,
        help="how many decimals the corpus writes its values with: 2 = the graded "
        "contract grid (201 atoms), 3 = the round-7 3-dp grid (2001 atoms). "
        "Only matters with --numeric-atoms; a mismatch makes that flag a no-op.",
    )
    args = ap.parse_args()

    train_path = Path(args.train)
    train = read_pairs(train_path, args.limit)
    val_path = Path(args.val) if args.val else None
    val = read_pairs(val_path, args.limit) if val_path and val_path.is_file() else []
    if not train:
        print(f"no pairs in {train_path}")
        return 1

    cfg = TokenConfig(
        d_emb=args.d_emb,
        d_hidden=args.d_hidden,
        max_len=args.max_len,
        beta=args.beta,
        readout=args.readout,
        layers=args.layers,
        timesteps=args.timesteps,
        theta_max=args.theta_max,
        leak_floor=args.leak_floor,
        gain_cap=args.gain_cap,
    )
    texts = [p + "\n" + a for p, a in train]
    if args.vocab == "token":
        # min_count 1: rare words must stay composable (knowledge answers
        # are often hapax); unseen *probe* words become <unk> either way.
        vocab = TokenVocab.build(
            texts,
            min_count=1,
            max_vocab=cfg.max_vocab,
            numeric_atoms=bool(args.numeric_atoms),
            value_decimals=int(args.value_decimals),
        )
        if args.numeric_atoms:
            # A precision mismatch makes the flag a silent no-op: the 2-dp grid
            # cannot match a 3-dp corpus, and the run then looks "tested" while
            # every value is still emitted digit by digit (measured: 0.721 with
            # the flag against 0.723 without). Say so instead of reporting 0.72.
            grid = set(_VALUE_ATOMS_BY_DECIMALS[int(args.value_decimals)])
            hit = sum(1 for atom in vocab.itos if atom in grid)
            corpus = used = 0
            for prompt, answer in train:
                for atom in tokenize(prompt + answer, True, int(args.value_decimals)):
                    corpus += 1
                    used += atom in grid
            print(f"numeric atoms: {hit} in vocab, {used}/{corpus} training atoms on grid")
            if used == 0:
                print(
                    "  no training value matches the "
                    f"{args.value_decimals}-dp grid; the flag does nothing — "
                    "use --value-decimals to match the corpus"
                )
    else:
        vocab = CharVocab.build(texts, min_count=cfg.min_count, max_vocab=cfg.max_vocab)
    train_fit = fits(train, vocab, cfg.max_len)
    val_fit = fits(val, vocab, cfg.max_len)
    print(
        f"vocab={len(vocab)} train={len(train)} (fit {len(train_fit)}) "
        f"val={len(val)} (fit {len(val_fit)}) len<={cfg.max_len}"
    )
    if not train_fit:
        # empty here used to surface as "max() iterable argument is empty"
        # inside dynamics(), three steps later and nowhere near the cause
        print(f"no training row fits max_len={cfg.max_len}; raise --max-len")
        return 1

    import torch

    device = resolve_device(torch, args.device)
    print(f"device={device}")
    model = TokenSNN(vocab, cfg, device=device)
    if args.resume:
        if Path(args.out).is_file():
            model = TokenSNN.load(args.out, map_location="cpu", device=device)
            if model.vocab.to_dict() != vocab.to_dict():
                print(
                    f"refusing --resume: vocab at {args.out} differs from the "
                    "training data vocab (dataset changed?); delete the "
                    "checkpoint to start fresh",
                )
                return 1
            print(f"resumed from {args.out}", flush=True)
        else:
            print(f"--resume: no checkpoint at {args.out}, starting fresh", flush=True)
    started = time.time()
    curve: List[dict] = []
    held_out = []
    if args.eval_data:
        held_out = fits(read_pairs(Path(args.eval_data)), vocab, cfg.max_len)
    on_epoch = None
    if args.eval_every and held_out:

        def on_epoch(row: dict) -> None:
            if (row["epoch"] + 1) % args.eval_every:
                return
            match = exact_match(model, held_out, args.eval_sample, seed=3)
            point = {"epoch": row["epoch"] + 1, "loss": row["loss"], **match}
            curve.append(point)
            print(
                f"    eval@{point['epoch']}: loss={point['loss']:.4f} "
                f"exact={point['exact']:.3f} (n={point['n']})"
            )

    # A run can learn for nineteen epochs and then diverge in the twentieth:
    # round-10 measured epoch 19 at loss 1.04 and epoch 20 at 7.02 with the
    # same lr, which is the scheduled-sampling feedback eating itself. Two rules
    # now stand between that and a lost run: the model's own guard rolls back to
    # the best finite weights and halves the lr instead of leaving them ruined,
    # and selection here is by *validation* loss, so the checkpoint that survives
    # is the one that generalises rather than the one that memorised hardest.
    best_path = Path(str(args.out) + ".best")
    best: Dict[str, float] = {"loss": float("inf"), "epoch": -1.0}
    val_curve: List[dict] = []
    stop = {"now": False}

    def val_loss() -> float:
        """Teacher-forced loss on the held-out split: one forward pass, no
        generation, so it is cheap enough to run every epoch."""
        import torch as _torch

        was = model.net.training
        model.net.eval()
        total, steps = 0.0, 0
        with _torch.no_grad():
            for start in range(0, len(val_fit), args.batch):
                chunk = list(val_fit[start : start + args.batch])
                ids, mask, _ = model.make_batch(chunk)
                got = float(model.loss(ids, mask).detach())
                if math.isfinite(got):
                    total += got
                    steps += 1
        if was:
            model.net.train()
        return total / steps if steps else float("nan")

    def schedule(epoch: int) -> float:
        """Warm up, then cosine down: the standard shape that keeps the first
        epochs from shocking a fresh stack and the last ones from oscillating."""
        if args.warmup and epoch < args.warmup:
            return args.lr * (epoch + 1) / args.warmup
        if args.lr_schedule == "constant":
            return args.lr
        span = max(1, args.epochs - max(0, args.warmup))
        done = min(1.0, max(0.0, (epoch - args.warmup) / span))
        return args.min_lr + 0.5 * (args.lr - args.min_lr) * (1 + math.cos(math.pi * done))

    def log_row(row: dict) -> None:
        loss = float(row["loss"])
        note = ""
        if row.get("rolled_back"):
            note = "  [rolled back: restored best weights, lr halved]"
        if row.get("skipped"):
            note += f"  [skipped {row['skipped']} non-finite batches]"
        print(
            f"  epoch {row['epoch'] + 1}: loss={loss:.4f} lr={row.get('lr', args.lr):.2e}{note}",
            flush=True,
        )
        if not math.isfinite(loss):
            print(f"    (non-finite loss — not saved over {args.out})", flush=True)
            return
        model.save(args.out)
        if args.patience or args.eval_every:
            got = val_loss()
            point = {"epoch": row["epoch"] + 1, "val_loss": round(got, 4)}
            val_curve.append(point)
            if math.isfinite(got):
                print(f"    val_loss={got:.4f}", flush=True)
                stop["last_val"] = got
                if got < best["loss"]:
                    best["loss"] = got
                    best["epoch"] = float(row["epoch"] + 1)
                    model.save(best_path)
                    stop["stale"] = 0
                else:
                    stop["stale"] = stop.get("stale", 0) + 1
                    if args.patience and stop["stale"] >= args.patience:
                        stop["now"] = True
                        print(
                            f"    early stop: no val improvement for " f"{args.patience} epochs",
                            flush=True,
                        )
        if best["epoch"] < 0:
            best["loss"] = loss
            best["epoch"] = float(row["epoch"] + 1)
            model.save(best_path)
        if args.epoch_pause > 0:
            time.sleep(args.epoch_pause)

    history = model.train_on(
        train_fit,
        epochs=args.epochs,
        batch_size=args.batch,
        lr=args.lr,
        log=log_row,
        on_epoch=on_epoch,
        tail_weight=args.tail_weight,
        ss_final=args.ss_final,
        lr_at=schedule,
        guard=args.guard,
        diverge_factor=args.diverge_factor,
        min_lr=args.min_lr,
        should_stop=lambda: stop["now"],
    )
    train_elapsed = time.time() - started
    last_loss = float(history[-1]["loss"]) if history else float("inf")
    # only compare like with like: when validation drove selection, the last
    # train loss says nothing about whether the saved epoch is the better one
    last_seen = stop.get("last_val", last_loss) if val_curve else last_loss
    if best_path.is_file() and math.isfinite(best["loss"]) and best["loss"] < last_seen:
        shutil.copyfile(best_path, args.out)
        label = "val_loss" if val_curve else "loss"
        final = f"{label}={last_seen:.4f}" if math.isfinite(last_seen) else "a stopped run"
        print(
            f"restored epoch {int(best['epoch'])} ({label}={best['loss']:.4f}) over {final}",
            flush=True,
        )
    best_path.unlink(missing_ok=True)
    dynamics = model.dynamics(train_fit, n=8)
    print(
        "  dynamics: "
        + f"verdict={dynamics['verdict']} beta={dynamics['beta']} "
        + " ".join(
            f"L{row['layer']}(rate={row['spike_rate']:.2f},sens={row['sensitive']:.3f})"
            for row in dynamics["per_layer"]
        ),
        flush=True,
    )

    # Persist the finished training run *before* evaluation: on the B570 the
    # eval phase has been observed to hang the device (xe CAT error / UR
    # DEVICE_LOST), which used to discard a completed run.
    model.save(args.out)
    print(f"saved {args.out} (pre-eval checkpoint)", flush=True)
    if args.eval_on_cpu:
        model.net.to("cpu")
        model.device = "cpu"
        print("eval on cpu", flush=True)

    # Train-side match is a memorisation check (it must not be reported as skill).
    if args.match_sample > 0:
        train_match = exact_match(model, train_fit, args.match_sample, seed=1)
        val_match = (
            exact_match(model, val_fit, args.match_sample, seed=2)
            if val_fit
            else {"n": 0, "exact": 0.0}
        )
    else:
        train_match = {"n": 0, "exact": 0.0}
        val_match = {"n": 0, "exact": 0.0}
    eval_match = {"n": 0, "exact": 0.0}
    eval_tf = {"tokens": 0, "tf_acc": 0.0}
    if held_out:
        eval_match = exact_match(model, held_out, args.eval_sample, seed=3)
        eval_tf = model.tf_accuracy(held_out)
    # Response vs state-block accuracy: the aggregate number alone is not
    # comparable across runs with a different answer mix (round 1's 61.76%
    # was inflated by the formulaic <al_out> block).
    split_set = held_out or val_fit
    eval_tf_split = model.split_tf_accuracy(split_set) if split_set else {}
    elapsed = time.time() - started  # total incl. evaluation
    report = {
        "train": str(train_path),
        "vocab_kind": args.vocab,
        "numeric_atoms": bool(args.numeric_atoms),
        "value_decimals": int(args.value_decimals),
        "pairs": {"train": len(train), "train_fit": len(train_fit), "val_fit": len(val_fit)},
        "vocab_size": len(vocab),
        "config": cfg.to_dict(),
        "epochs": args.epochs,
        "batch": args.batch,
        "lr": args.lr,
        "tail_weight": args.tail_weight,
        "ss_final": args.ss_final,
        "device": device,
        "seconds": round(elapsed, 1),
        "train_seconds": round(train_elapsed, 1),
        "loss_history": history,
        "best_loss": None if not math.isfinite(best["loss"]) else round(best["loss"], 4),
        "best_epoch": int(best["epoch"]) if best["epoch"] > 0 else None,
        "best_is_validation": bool(val_curve),
        "val_curve": val_curve,
        "rolled_back_epochs": [r["epoch"] + 1 for r in history if r.get("rolled_back")],
        "stopped_early": bool(history and history[-1].get("stopped")),
        "dynamics": dynamics,
        "train_exact_200": train_match,
        "val_exact_200": val_match,
        "eval": {"path": args.eval_data, "sample": args.eval_sample, **eval_match},
        "eval_tf_accuracy": eval_tf,
        "eval_tf_split": eval_tf_split,
        "learning_curve": curve,
        "note": (
            "train_exact_200 is memorisation (same rows); only val/frozen splits "
            "measure generalisation, and only a correct answer produced by this "
            "model counts as core intelligence."
        ),
    }
    model.save(args.out)  # unchanged state; keeps the path idempotent
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"saved {args.out}\n  train_exact={train_match['exact']:.3f} "
        f"val_exact={val_match['exact']:.3f} eval_exact={eval_match['exact']:.3f} "
        f"eval_tf_acc={eval_tf['tf_acc']:.3f} "
        f"resp_tf={eval_tf_split.get('response_tf', 0):.3f} "
        f"tail_tf={eval_tf_split.get('tail_tf', 0):.3f} "
        f"in {elapsed:.0f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
