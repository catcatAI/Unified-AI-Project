#!/usr/bin/env python
"""Sample-based training analysis.

Trains ED3N + GARDEN on a small per-domain sample and prints per-batch
diagnostics so problems can be caught BEFORE a full multi-hour pass.

Usage:
    TRAIN_NO_CORPUS=1 python scripts/sample_train_analysis.py [--per-domain N]

Mirrors the training pipeline (same data loading + step functions) but:
  - loads only a capped per-domain sample,
  - forces a fresh run (no resume of the full pass),
  - prints analysis metrics after each GARDEN learn_batch.
"""
# =============================================================================
# ANGELA-MATRIX: [L3] [β] [B] [L5]
# =============================================================================

import argparse
import asyncio
import importlib.util
import os
import random
import sys
import time
from typing import Dict, List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src")))
os.environ.setdefault("ANGELA_CONFIG_ROOT", os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "configs"))

_TP_PATH = os.path.join(os.path.dirname(__file__), "train_pipeline.py")
_spec = importlib.util.spec_from_file_location("train_pipeline", _TP_PATH)
tp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tp)


def load_all_samples() -> List[Dict]:
    """Load the full dataset exactly like the pipeline (minus downloads)."""
    tp._ensure_daily_data()
    (
        dataset_samples,
        alpaca_samples,
        template_samples,
        kb_samples,
        presets_samples,
        trpg_samples,
        secondary_samples,
    ) = tp._step2_load_datasets()
    knowledge_samples = tp._step3_generate_knowledge()
    return (
        dataset_samples
        + alpaca_samples
        + template_samples
        + kb_samples
        + presets_samples
        + trpg_samples
        + secondary_samples
        + knowledge_samples
    )


def sample_by_domain(samples: List[Dict], per_domain: int) -> List[Dict]:
    """Stratified sample: up to `per_domain` samples per domain."""
    by_domain: Dict[str, List[Dict]] = {}
    for s in samples:
        by_domain.setdefault(str(s.get("domain", "unknown")), []).append(s)
    out: List[Dict] = []
    for domain, domain_samples in sorted(by_domain.items()):
        rng = random.Random(42)
        chosen = rng.sample(domain_samples, min(per_domain, len(domain_samples)))
        out.extend(chosen)
        print(f"  domain={domain:12s} total={len(domain_samples):6d} sampled={len(chosen)}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-domain", type=int, default=100)
    args = parser.parse_args()

    print("=" * 60)
    print("  SAMPLE TRAIN ANALYSIS (per-domain diagnostics)")
    print("=" * 60)
    t_start = time.time()

    all_samples = load_all_samples()
    print(f"  Full dataset: {len(all_samples)} samples")
    sampled = sample_by_domain(all_samples, args.per_domain)
    print(f"  Sampled: {len(sampled)} samples")

    from ai.core.training_coordinator import TrainingCoordinator

    coordinator = TrainingCoordinator()
    batches = asyncio.run(coordinator.deconflict_samples(sampled))
    for model_id, batch in sorted(batches.items()):
        print(f"  deconflicted {model_id:15s} -> {len(batch):5d} samples")

    # Deterministic filter (mirror of pipeline step 3a)
    det_filtered = {m: 0 for m in batches}
    for model_id in batches:
        original = len(batches[model_id])
        batches[model_id] = [
            s
            for s in batches[model_id]
            if not tp.is_deterministic_match(s["input"], s["output"])
        ]
        det_filtered[model_id] = original - len(batches[model_id])
        print(f"  {model_id:15s} -> det-filtered {det_filtered[model_id]} ({original} -> {len(batches[model_id])})")

    # ---- ED3N training ----
    print("\n=== ED3N training ===")
    ed3n_engine, ed3n_examples = tp._step4_train_ed3n(coordinator, batches)
    print(f"  ED3N dict entries: {len(ed3n_engine.dictionary.entries)}")

    # ---- GARDEN training with per-batch analysis ----
    print("\n=== GARDEN training ===")
    from ai.garden.garden_engine import GARDENEngine

    garden_engine = GARDENEngine(compatibility_mode=True)
    garden_engine.load_presets()
    garden_samples = batches.get("garden", [])
    BATCH = 200
    for i in range(0, len(garden_samples), BATCH):
        batch = garden_samples[i : i + BATCH]
        t0 = time.time()
        result = garden_engine.learn_batch(
            samples=[{"input": s["input"], "output": s["output"]} for s in batch],
            train_associations=True,
        )
        elapsed = time.time() - t0
        # GARDEN analysis metrics
        snn = getattr(garden_engine, "snn", None) or getattr(garden_engine, "snn_core", None)
        print(
            f"  batch {i // BATCH + 1:2d}/{len(range(0, len(garden_samples), BATCH))}: "
            f"processed={result.get('samples_processed', 0)} "
            f"new_concepts={result.get('new_concepts', 0)} "
            f"engine_handled={result.get('engine_handled_count', 0)} "
            f"V={getattr(snn, 'vocab_size', len(garden_engine.dictionary.entries)) if snn else '?'} "
            f"dict={len(garden_engine.dictionary.entries)} "
            f"{elapsed:.1f}s"
        )

    # Save the sampled result for load/inference verification
    from ai.ed3n.ed3n_engine import ED3NEngine

    ed3n_engine.save(os.path.join(tp.CKPT_DIR, "ed3n_sample.json"))
    garden_engine.save(os.path.join(tp.CKPT_DIR, "garden_sample_checkpoint"))
    print(f"\n  Saved sample checkpoints to {tp.CKPT_DIR}")

    print(f"\n  Elapsed: {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    main()
