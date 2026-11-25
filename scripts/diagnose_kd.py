#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# LAYER: learning
# =============================================================================
"""Diagnostic: why doesn't KD help? Analyse the teacher's soft targets.

Measures, from an existing KdCache:
  * teacher entropy per position (how confident is the teacher?)
  * top-1 agreement with the gold answer atom (is the teacher right?)
  * distribution of mapped_mass per position
  * how many positions have the gold atom in the teacher's top-k

No training, no model loading. Pure analysis of the cache + training rows.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from train_token_snn import fits, read_pairs  # noqa: E402
from ai.ed3n.token_snn import TokenSNN, encode_ids  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="KD diagnostic")
    ap.add_argument("--cache", default="data/kd/kd_scaleup_7b_40k.npz")
    ap.add_argument("--checkpoint", default="data/checkpoints/scaleup_phase1_memnorm.pt")
    ap.add_argument("--train", default="apps/backend/data/processed/core_train.jsonl")
    ap.add_argument("--limit", type=int, default=40000)
    ap.add_argument("--max-len", type=int, default=192)
    ap.add_argument("--out", default="data/intelligence_reports/kd_diagnostic.json")
    args = ap.parse_args()

    # Load cache
    from ai.ed3n.kd_cache import KdCache

    cache = KdCache.load(Path(args.cache))
    print(f"cache: {cache.n_rows} rows, vocab_sha={cache.meta.get('vocab_sha256', '?')[:12]}")

    # Load model vocab (from checkpoint, same as cache)
    model = TokenSNN.load(args.checkpoint, map_location="cpu", device="cpu")
    vocab = model.vocab
    print(f"vocab: {len(vocab)} atoms")

    # Load training rows (same filter as cache build)
    train = read_pairs(Path(args.train), args.limit)
    rows = fits(train, vocab, args.max_len)
    print(f"train={len(train)} fit={len(rows)} cache_rows={cache.n_rows}")
    assert len(rows) == cache.n_rows, f"row count mismatch: {len(rows)} vs {cache.n_rows}"

    # Analyse
    entropies = []
    top1_matches_gold = 0
    gold_in_topk = 0
    n_positions = 0
    teacher_top1_confidence = []
    gold_prob_when_present = []
    n_rows_analysed = 0

    for row_idx in range(cache.n_rows):
        prompt, answer = rows[row_idx]
        kd_row = cache.row(row_idx)
        if len(kd_row) == 0:
            continue
        n_rows_analysed += 1
        # encode to get answer start and gold atoms
        ids, start, _end = encode_ids(vocab, prompt, answer, args.max_len)
        answer_atoms = ids[start:-1]  # gold answer atoms (eos excluded)

        for pos_i, position in enumerate(kd_row.positions):
            n_positions += 1
            atom_ids = kd_row.atom_ids[kd_row.atom_ptr[pos_i] : kd_row.atom_ptr[pos_i + 1]]
            probs = kd_row.probs[kd_row.atom_ptr[pos_i] : kd_row.atom_ptr[pos_i + 1]]

            # teacher entropy (over the mapped atoms, scaled by mapped_mass)
            # probs already scaled by mapped_mass; renormalise for entropy
            p = probs / (probs.sum() + 1e-12)
            entropy = -float(np.sum(p * np.log(p + 1e-12)))
            entropies.append(entropy)

            top1_atom = int(atom_ids[np.argmax(probs)]) if len(atom_ids) > 0 else -1
            teacher_top1_confidence.append(float(probs.max()) if len(probs) > 0 else 0.0)

            # gold atom at this position
            atom_offset = position - start + 1  # position is start+atom_index-1
            # position = start + k - 1 where k is answer atom index (1-based)
            k = position - start + 1
            if 0 <= k - 1 < len(answer_atoms):
                gold_atom = answer_atoms[k - 1]
                if top1_atom == gold_atom:
                    top1_matches_gold += 1
                if gold_atom in atom_ids:
                    gold_in_topk += 1
                    idx = np.where(atom_ids == gold_atom)[0]
                    if len(idx) > 0:
                        gold_prob_when_present.append(float(probs[idx[0]]))

    entropies = np.array(entropies)
    confidences = np.array(teacher_top1_confidence)

    summary = {
        "cache": args.cache,
        "checkpoint": args.checkpoint,
        "rows_analysed": n_rows_analysed,
        "positions": n_positions,
        "teacher_entropy_mean": round(float(entropies.mean()), 4),
        "teacher_entropy_median": round(float(np.median(entropies)), 4),
        "teacher_entropy_p95": round(float(np.percentile(entropies, 95)), 4),
        "teacher_top1_confidence_mean": round(float(confidences.mean()), 4),
        "teacher_top1_confidence_median": round(float(np.median(confidences)), 4),
        "top1_matches_gold_rate": round(top1_matches_gold / max(1, n_positions), 4),
        "gold_in_topk_rate": round(gold_in_topk / max(1, n_positions), 4),
        "gold_prob_when_present_mean": round(float(np.mean(gold_prob_when_present)), 4) if gold_prob_when_present else 0.0,
        "n_with_gold_in_topk": gold_in_topk,
        "n_top1_matches_gold": top1_matches_gold,
    }

    print(json.dumps(summary, indent=2, ensure_ascii=False))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
