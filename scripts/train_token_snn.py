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
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

from ai.ed3n.token_snn import CharVocab, TokenConfig, TokenSNN  # noqa: E402

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


def fits(pairs: List[Tuple[str, str]], vocab: CharVocab, max_len: int) -> List[Tuple[str, str]]:
    def size(prompt: str, answer: str) -> int:
        return 2 + len(prompt) + len(answer) + 1  # bos + newline + eos

    kept = [(p, a) for p, a in pairs if size(p, a) <= max_len]
    return kept


def exact_match(
    model: TokenSNN, pairs: List[Tuple[str, str]], sample: int, seed: int = 0
) -> Dict[str, float]:
    picks = pairs if len(pairs) <= sample else random.Random(seed).sample(pairs, sample)
    hits = 0
    for prompt, answer in picks:
        got = model.generate(prompt, max_new=min(model.config.max_len, len(answer) + 8))
        if got.strip() == answer.strip():
            hits += 1
    return {"n": len(picks), "exact": hits / max(1, len(picks))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default=str(DEFAULT_TRAIN))
    ap.add_argument("--val", default=str(DEFAULT_VAL))
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
    ap.add_argument("--d-hidden", type=int, default=192)
    ap.add_argument("--d-emb", type=int, default=96)
    ap.add_argument("--out", default=str(OUT_DIR / "token_snn.pt"))
    ap.add_argument("--report", default=str(REPORT_DIR / "token_snn.json"))
    args = ap.parse_args()

    train_path = Path(args.train)
    train = read_pairs(train_path, args.limit)
    val_path = Path(args.val) if args.val else None
    val = read_pairs(val_path, args.limit) if val_path and val_path.is_file() else []
    if not train:
        print(f"no pairs in {train_path}")
        return 1

    cfg = TokenConfig(d_emb=args.d_emb, d_hidden=args.d_hidden, max_len=args.max_len)
    vocab = CharVocab.build(
        [p + "\n" + a for p, a in train], min_count=cfg.min_count, max_vocab=cfg.max_vocab
    )
    train_fit = fits(train, vocab, cfg.max_len)
    val_fit = fits(val, vocab, cfg.max_len)
    print(
        f"vocab={len(vocab)} train={len(train)} (fit {len(train_fit)}) "
        f"val={len(val)} (fit {len(val_fit)}) len<={cfg.max_len}"
    )

    model = TokenSNN(vocab, cfg)
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

    history = model.train_on(
        train_fit,
        epochs=args.epochs,
        batch_size=args.batch,
        lr=args.lr,
        log=lambda row: print(f"  epoch {row['epoch'] + 1}: loss={row['loss']:.4f}"),
        on_epoch=on_epoch,
    )
    elapsed = time.time() - started

    # Train-side match is a memorisation check (it must not be reported as skill).
    train_match = exact_match(model, train_fit, 200, seed=1)
    val_match = exact_match(model, val_fit, 200, seed=2) if val_fit else {"n": 0, "exact": 0.0}
    eval_match = {"n": 0, "exact": 0.0}
    if held_out:
        eval_match = exact_match(model, held_out, args.eval_sample, seed=3)
    report = {
        "train": str(train_path),
        "pairs": {"train": len(train), "train_fit": len(train_fit), "val_fit": len(val_fit)},
        "vocab_size": len(vocab),
        "config": cfg.to_dict(),
        "epochs": args.epochs,
        "batch": args.batch,
        "lr": args.lr,
        "seconds": round(elapsed, 1),
        "loss_history": history,
        "train_exact_200": train_match,
        "val_exact_200": val_match,
        "eval": {"path": args.eval_data, "sample": args.eval_sample, **eval_match},
        "learning_curve": curve,
        "note": (
            "train_exact_200 is memorisation (same rows); only val/frozen splits "
            "measure generalisation, and only a correct answer produced by this "
            "model counts as core intelligence."
        ),
    }
    model.save(args.out)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"saved {args.out}\n  train_exact={train_match['exact']:.3f} "
        f"val_exact={val_match['exact']:.3f} eval_exact={eval_match['exact']:.3f} "
        f"in {elapsed:.0f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
