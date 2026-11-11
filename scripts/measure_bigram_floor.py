#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""同一刀上的 interpolated bigram floor — 判斷「學生到底有沒有贏過看一個 token」。

`probe_training_readiness.py` 的 `baseline.bigram_floor`（4.584 nats）是在**全集**
切片上量的。訓練的 A/B 用的是 `--limit 4000`（3,263 列通過 `max_len=192`），
所以把那個 4.584 拿去跟 A/B 的 held-out val_loss 比，是兩個不同切片的數字。

這支腳本用**同一個** `_interpolated_bigram_floor`，但配上與 A/B 完全相同的切片、
詞表與長度上限，讓「val 3.41–3.48 是否低於 floor」變成可重跑的比較：

    python scripts/measure_bigram_floor.py --limit 4000 --max-len 192 --max-vocab 12000

輸出（2026-11-09 實測）：`vocab=12005 train_fit=3263 val_fit=3375`
`floor=4.6433 nats (best lambda=0.7)`。

λ 在驗證集上挑最大的那個（與探針一致）：這讓 floor 是「最強的單 token 上下文
模型」，避免用弱基線證明學生有學到東西。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from ai.ed3n.token_snn import TokenVocab, encode_ids  # noqa: E402
from probe_training_readiness import _interpolated_bigram_floor  # noqa: E402
from train_token_snn import DEFAULT_TRAIN, DEFAULT_VAL, fits, read_pairs  # noqa: E402


def atom_rows(pairs, vocab: TokenVocab, max_len: int) -> List[List[int]]:
    rows: List[List[int]] = []
    for prompt, answer in pairs:
        ids, start, _end = encode_ids(vocab, prompt, answer, max_len)
        atoms = ids[start:-1]  # answer atoms, eos excluded (same convention as the probe)
        if len(atoms) > 1:
            rows.append(atoms)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="interpolated bigram floor on one training slice")
    ap.add_argument("--limit", type=int, default=4000, help="pairs per split (same as the run)")
    ap.add_argument("--max-len", type=int, default=192)
    ap.add_argument("--max-vocab", type=int, default=12000)
    ap.add_argument("--train", default=str(DEFAULT_TRAIN))
    ap.add_argument("--val", default=str(DEFAULT_VAL))
    args = ap.parse_args()

    train = read_pairs(Path(args.train), args.limit)
    val = read_pairs(Path(args.val), args.limit)
    if not train or not val:
        print("no pairs: run scripts/prepare_core_training_data.py first")
        return 1

    vocab = TokenVocab.build(
        [p + "\n" + a for p, a in train], min_count=1, max_vocab=args.max_vocab
    )
    train_fit = fits(train, vocab, args.max_len)
    val_fit = fits(val, vocab, args.max_len)
    train_rows = atom_rows(train_fit, vocab, args.max_len)
    val_rows = atom_rows(val_fit, vocab, args.max_len)

    lam, floor = _interpolated_bigram_floor(train_rows, val_rows)
    print(
        f"vocab={len(vocab)} train_fit={len(train_fit)} val_fit={len(val_fit)} "
        f"answer_atoms={sum(len(r) for r in val_rows)}"
    )
    print(f"floor={floor:.4f} nats (best lambda={lam})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
