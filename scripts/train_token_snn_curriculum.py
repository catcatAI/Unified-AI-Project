#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""Graduated curriculum for the token-SNN arithmetic learner (CPU-friendly).

Findings this script acts on (2026-10-25 diagnostics):
  * The mixed 30k four-operator set plateaus at loss ~1.70 / 0% exact when
    trained from scratch — too hard, too diverse for the first objective.
  * 10k single-operator pairs (a+b, a,b 0..99) reach 77% exact on unseen
    pairs in 87 s: the architecture *can* learn a generalizing algorithm.
  * A naive hard-jump stage (40 epochs, no replay) underfits and catastrophically
    forgets (held-out 0-99 drops 68% -> 4%).

So: stages grow in digit span, each stage trains to convergence, earlier data
is replayed to prevent forgetting. Synthetic pairs are leak-guarded against
arithmetic_test_dataset.csv (held-out distribution, never trained on) and the
official benchmark is never touched.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from ai.ed3n.token_snn import CharVocab, TokenConfig, TokenSNN  # noqa: E402
from train_token_snn import exact_match, fits, read_pairs  # noqa: E402

EVAL_CSV = REPO_ROOT / "apps" / "backend" / "data" / "raw_datasets" / "arithmetic_test_dataset.csv"
REPORT_DIR = REPO_ROOT / "data" / "intelligence_reports"
OUT_DIR = REPO_ROOT / "apps" / "backend" / "data" / "models"


def eval_pool() -> tuple[set, list]:
    """Held-out distribution: full problem-text pool + its '+' rows."""
    texts, plus = set(), []
    for prompt, answer in read_pairs(EVAL_CSV):
        texts.add(prompt.strip())
        if re.fullmatch(r"\d+ \+ \d+", prompt.strip()):
            plus.append((prompt.strip(), answer.strip()))
    return texts, plus


def leak_guard(pairs, texts: set) -> list:
    return [(p, a) for p, a in pairs if p.strip() not in texts]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs-a", type=int, default=100)
    ap.add_argument("--epochs-b", type=int, default=150)
    ap.add_argument("--stage-b", type=int, default=30000, help="stage-B pair count (0..999)")
    ap.add_argument("--replay", type=int, default=10000, help="stage-A pairs replayed in stage B")
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--d-hidden", type=int, default=192)
    ap.add_argument("--max-len", type=int, default=24)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--out", default=str(OUT_DIR / "token_snn_curriculum.pt"))
    ap.add_argument("--report", default=str(REPORT_DIR / "token_snn_curriculum.json"))
    args = ap.parse_args()

    texts, eval_plus = eval_pool()
    stage_a = leak_guard(
        [(f"{a} + {b}", str(a + b)) for a in range(100) for b in range(100)], texts
    )
    rnd = random.Random(0)
    rnd.shuffle(stage_a)
    train_a, held_a = stage_a[:9000], stage_a[9000:]

    stage_b_pool = leak_guard(
        [(f"{a} + {b}", str(a + b)) for a in range(1000) for b in range(1000)], texts
    )
    held_a_set = set(held_a)
    rnd_b = random.Random(1)
    train_b = rnd_b.sample([x for x in stage_b_pool if x not in held_a_set], args.stage_b)
    replay = rnd_b.sample(train_a, min(args.replay, len(train_a)))
    stage_b_mix = train_b + replay
    train_b_set = set(train_b)
    held_b = rnd_b.sample([x for x in stage_b_pool if x not in train_b_set], 300)
    extra = leak_guard(
        random.Random(2).sample(
            [(f"{a} + {b}", str(a + b)) for a in range(1000, 4000) for b in range(100, 999)],
            3000,
        ),
        texts,
    )

    cfg = TokenConfig(d_emb=96, d_hidden=args.d_hidden, max_len=args.max_len)
    vocab = CharVocab.build(
        [p + "\n" + a for p, a in stage_a + stage_b_pool],
        min_count=cfg.min_count,
        max_vocab=cfg.max_vocab,
    )
    a_fit = fits(train_a, vocab, cfg.max_len)
    b_fit = fits(stage_b_mix, vocab, cfg.max_len)
    held_a_fit = fits(held_a, vocab, cfg.max_len)
    held_b_fit = fits(held_b, vocab, cfg.max_len)
    extra_fit = fits(extra, vocab, cfg.max_len)
    eval_plus_fit = fits(eval_plus, vocab, cfg.max_len)
    print(
        f"vocab={len(vocab)} A={len(a_fit)} Bmix={len(b_fit)} "
        f"heldA={len(held_a_fit)} heldB={len(held_b_fit)}",
        flush=True,
    )

    model = TokenSNN(vocab, cfg, device=args.device)
    started = time.time()
    curve: list[dict] = []

    def ev(name: str, pairs, n: int = 300) -> dict:
        if not pairs:
            return {"name": name, "n": 0, "exact": 0.0}
        m = exact_match(model, pairs, n, seed=7)
        row = {"name": name, **m}
        print(f"  {name}: exact={m['exact']:.3f} (n={m['n']})", flush=True)
        curve.append({**row, "seconds": round(time.time() - started, 1)})
        return row

    print("stage A (0-99, to convergence):", flush=True)
    hist_a = model.train_on(
        a_fit,
        epochs=args.epochs_a,
        batch_size=args.batch,
        lr=5e-3,
        log=lambda r: (
            print(f"  A ep{r['epoch'] + 1}: loss={r['loss']:.4f}", flush=True)
            if (r["epoch"] + 1) % 25 == 0
            else None
        ),
    )
    ev("A held-out 0-99", held_a_fit)

    print("stage B (0-999 + replay, long):", flush=True)
    hist_b = model.train_on(
        b_fit,
        epochs=args.epochs_b,
        batch_size=args.batch,
        lr=3e-3,
        log=lambda r: (
            print(
                f"  B ep{r['epoch'] + 1}: loss={r['loss']:.4f} {time.time() - started:.0f}s",
                flush=True,
            )
            if (r["epoch"] + 1) % 25 == 0
            else None
        ),
    )
    print("FINAL:", flush=True)
    ev("held-out 0-99 (retained)", held_a_fit)
    ev("held-out 0-999 sample", held_b_fit)
    ev("arithmetic_test '+' rows (held-out distribution)", eval_plus_fit, n=200)
    ev("EXTRAPOLATION 4digit+3digit (never trained)", extra_fit)

    model.save(args.out)
    report = {
        "config": cfg.to_dict(),
        "args": vars(args),
        "vocab_size": len(vocab),
        "pairs": {"a": len(a_fit), "b_mix": len(b_fit)},
        "loss_history": {"a": hist_a, "b": hist_b},
        "eval_curve": curve,
        "seconds": round(time.time() - started, 1),
        "note": (
            "Synthetic addition curriculum; arithmetic_test.csv is held out "
            "(leak-guarded) and the official benchmark is never touched. "
            "Only exact answers produced by this model count as core."
        ),
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"saved {args.out} + {args.report} in {report['seconds']}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
