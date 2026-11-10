#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""Build distillation targets from a llama.cpp teacher into a ``KdCache``.

One teacher forward per row is the whole cost, so it is paid once and stored.
The two rules that make the result trustworthy are *not* implemented here:

* which teacher token starts at which answer atom — :mod:`ai.ed3n.kd_teacher`;
* which student atom a teacher probability belongs to — :mod:`ai.ed3n.kd_targets`.

This script only glues them to the exact rows a run will train on: the same
vocabulary, the same ``max_len``, the same row filter. That matters because a
cache position is an index into the *student's* hidden states, so a cache built
over a differently filtered row list would attach every target to the wrong row
and still produce a falling loss.

Usage::

    PYTHONPATH=apps/backend/src ./.venv/bin/python scripts/build_kd_cache.py \\
        --limit 4000 --checkpoint apps/backend/data/models/token_snn_108m.pt \\
        --out /tmp/kd_core.npz
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from ai.ed3n.kd_cache import KdCache  # noqa: E402
from ai.ed3n.kd_targets import AtomPrefixIndex  # noqa: E402
from ai.ed3n.token_snn import SPECIALS, TokenVocab, encode_ids  # noqa: E402

DEFAULT_TRAIN = REPO_ROOT / "apps" / "backend" / "data" / "processed" / "core_train.jsonl"
DEFAULT_OUT = REPO_ROOT / "data" / "kd" / "kd_core.npz"
DEFAULT_TEACHER = REPO_ROOT / "data" / "models" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"


def _build_vocab(pairs: List[Tuple[str, str]], max_vocab: int) -> TokenVocab:
    # min_count=1 and max_vocab from the run: ``train_token_snn.py`` hard-codes
    # the first (rare words must stay composable) and takes the second from its
    # config. Reading min_count from a checkpoint's recorded config produced a
    # 31,081-atom vocabulary whose ids meant something else entirely.
    return TokenVocab.build([p + "\n" + a for p, a in pairs], min_count=1, max_vocab=max_vocab)


def main() -> int:
    ap = argparse.ArgumentParser(description="distil a teacher into a KdCache")
    ap.add_argument("--train", default=str(DEFAULT_TRAIN))
    ap.add_argument("--limit", type=int, default=0, help="rows to use (0 = all)")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--report", default="", help="write a JSON summary here")
    ap.add_argument("--max-len", type=int, default=192)
    ap.add_argument("--max-vocab", type=int, default=32768)
    ap.add_argument(
        "--checkpoint",
        default="",
        help="take the vocabulary from this checkpoint instead of rebuilding it "
        "(the cache must bind to the model that will train)",
    )
    ap.add_argument("--top-k", type=int, default=64)
    ap.add_argument("--teacher", default=str(DEFAULT_TEACHER))
    ap.add_argument("--n-ctx", type=int, default=512)
    ap.add_argument("--n-threads", type=int, default=6)
    ap.add_argument("--progress-every", type=int, default=500)
    args = ap.parse_args()

    from train_token_snn import fits, read_pairs

    train = read_pairs(Path(args.train), args.limit)
    if not train:
        print(f"no pairs in {args.train}")
        return 1

    if args.checkpoint:
        from ai.ed3n.token_snn import TokenSNN

        model = TokenSNN.load(args.checkpoint, map_location="cpu", device="cpu")
        vocab = model.vocab
        print(f"vocab from checkpoint: {len(vocab)} atoms")
    else:
        vocab = _build_vocab(train, args.max_vocab)
        print(f"vocab built from data: {len(vocab)} atoms")

    # The trainer trains on ``fits(...)``, so the cache must be built on the same
    # list. Row 7 of the cache then *is* row 7 of the batch index.
    rows = fits(train, vocab, args.max_len)
    print(f"train={len(train)} fit={len(rows)} max_len={args.max_len}")
    if not rows:
        print("no row fits; raise --max-len")
        return 1

    teacher_path = Path(args.teacher)
    if not teacher_path.is_file():
        print(f"teacher missing: {teacher_path}")
        return 1
    try:
        from ai.ed3n.kd_teacher import KdTeacher
    except Exception as exc:  # noqa: BLE001 — optional dependency
        print(f"cannot import the teacher: {exc}")
        return 1

    atoms = AtomPrefixIndex((vocab.stoi[a], a) for a in vocab.itos if a not in SPECIALS and a)
    teacher = KdTeacher(str(teacher_path), n_ctx=args.n_ctx, n_threads=args.n_threads)

    started = time.time()
    payloads: List[Tuple[Any, int, List[Tuple[int, Any]]]] = []
    positions = 0
    mapped = 0.0
    covered_rows = 0
    for index, (prompt, answer) in enumerate(rows):
        ids, start, _cut = encode_ids(vocab, prompt, answer, args.max_len)
        alignments, scores, _spans = teacher.align(prompt, answer)
        targets: List[Tuple[int, Any]] = []
        if scores is not None:
            for atom_index, target in teacher.targets(alignments, scores, atoms, top_k=args.top_k):
                position = start + atom_index - 1
                if position < 0 or position + 1 >= len(ids):
                    continue  # answer cut by max_len: no student position
                targets.append((position, target))
        positions += len(targets)
        if targets:
            covered_rows += 1
        # ``t.probs`` is renormalised to 1 per position, so summing it measures
        # the renormalisation, not the teacher's coverage. ``mapped_mass`` is the
        # fraction of the teacher's top-k that actually landed on an atom.
        mapped += sum(float(t.mapped_mass) for _p, t in targets)
        payloads.append((ids, start, targets))
        if args.progress_every and (index + 1) % args.progress_every == 0:
            elapsed = time.time() - started
            rate = (index + 1) / max(1e-9, elapsed)
            eta = (len(rows) - index - 1) / max(1e-9, rate)
            print(
                f"  {index + 1}/{len(rows)} rows  positions={positions} "
                f"mass={mapped / max(1, positions):.3f}  {rate:.1f} rows/s "
                f"eta={eta / 60:.1f} min",
                flush=True,
            )

    coverage = mapped / max(1, positions)
    cache = KdCache.build(
        payloads,
        vocab.itos,
        meta={
            "teacher": teacher_path.name,
            "teacher_bytes": teacher_path.stat().st_size,
            "top_k": args.top_k,
            "max_len": args.max_len,
            "train": str(Path(args.train).name),
            "rows_total": len(train),
            "checkpoint": Path(args.checkpoint).name if args.checkpoint else "",
            # Survives with the cache so a trainer report can quote the teacher's
            # actual coverage instead of re-measuring a renormalised q (which is
            # 1.0 by construction).
            "teacher_mapped_mass": round(coverage, 4),
        },
    )
    cache.validate()
    path = cache.save(Path(args.out))
    stats = cache.stats()
    elapsed = time.time() - started
    summary: Dict[str, Any] = {
        "out": str(path),
        "rows": cache.n_rows,
        "rows_with_targets": covered_rows,
        "positions": positions,
        "positions_per_row": positions / max(1, cache.n_rows),
        "mapped_mass": coverage,
        "seconds": round(elapsed, 1),
        "mb": round(path.stat().st_size / 1e6, 1),
        "vocab": len(vocab),
        "meta": cache.meta,
        **{f"sample_{k}": round(v, 4) for k, v in stats.items() if k != "sampled_rows"},
        "sample_rows": round(stats["sampled_rows"], 4),
    }
    print(json.dumps(summary, indent=2))
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
