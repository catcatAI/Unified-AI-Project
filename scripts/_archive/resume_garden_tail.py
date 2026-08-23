#!/usr/bin/env python
"""Finish the tail of GARDEN training (batches past 10500) in small chunks.

The last chunk (10500 -> 11180) grows V close to the memory ceiling (the
machine has 7GB RAM; TF-IDF index build + W matrix peak there).  This helper
loads the resumed checkpoint, consumes the remaining samples in small batches
(250 each, saving after every chunk), and never rebuilds the TF-IDF index for
the full growing vocabulary in one shot.

Usage:  TRAIN_NO_CORPUS=1 python scripts/resume_garden_tail.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from scripts.train_pipeline import (  # noqa: E402
    CKPT_DIR,
    STATE_FILE,
    _ensure_corpus,
    _ensure_daily_data,
    _step1_setup,
    _step2_load_datasets,
    _step3_generate_knowledge,
    is_deterministic_match,
)

CHUNK = 250


def main() -> None:
    t_start = time.time()

    resume_state: dict = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            resume_state = json.load(f)
    batch_done = int(resume_state.get("garden_batch_done", 0))
    print(f"Resume state: garden_batch_done={batch_done}")

    print("\n[1] Loading datasets...")
    _ensure_daily_data()
    _ensure_corpus()
    (
        dataset_samples,
        alpaca_samples,
        template_samples,
        kb_samples,
        presets_samples,
        trpg_samples,
        secondary_samples,
    ) = _step2_load_datasets()
    knowledge_samples = _step3_generate_knowledge()
    all_samples = (
        dataset_samples
        + alpaca_samples
        + template_samples
        + kb_samples
        + presets_samples
        + trpg_samples
        + secondary_samples
        + knowledge_samples
    )

    print("\n[2] Deconflicting...")
    _model_bus, _qcls, coordinator = _step1_setup()
    batches = asyncio.run(coordinator.deconflict_samples(all_samples))
    for m in batches:
        batches[m] = [s for s in batches[m] if not is_deterministic_match(s["input"], s["output"])]
    garden_samples = batches.get("garden", [])
    print(f"  GARDEN train set: {len(garden_samples)} samples, resume from idx {batch_done}")

    from ai.garden.garden_engine import GARDENEngine

    print("\n[3] Loading checkpoint...")
    garden_ckpt = os.path.join(CKPT_DIR, "garden_checkpoint")
    engine = GARDENEngine(compatibility_mode=True)
    engine.load(garden_ckpt)
    print(
        f"  V={engine.snn.vocab_size} dict={len(engine.dictionary.entries)} "
        f"batch_done={batch_done}"
    )

    remaining = garden_samples[batch_done:]
    print(f"\n[4] Processing tail: {len(remaining)} samples in chunks of {CHUNK}")

    total = batch_done
    for i in range(0, len(remaining), CHUNK):
        chunk = remaining[i : i + CHUNK]
        t0 = time.time()
        result = engine.learn_batch(
            samples=[{"input": s["input"], "output": s["output"]} for s in chunk],
            confidence=0.7,
            train_associations=True,
        )
        total += result["samples_processed"]
        elapsed = time.time() - t0
        # Persist immediately after each chunk so an OOM kill loses at most one chunk.
        engine.save(garden_ckpt)
        batch_done = min(batch_done + len(chunk), len(garden_samples))
        resume_state["garden_batch_done"] = batch_done
        resume_state["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(resume_state, f, ensure_ascii=False, indent=2)
        print(
            f"  chunk {i // CHUNK + 1}: processed={result.get('samples_processed')} "
            f"new_concepts={result.get('new_concepts')} "
            f"V={engine.snn.vocab_size} dict={len(engine.dictionary.entries)} "
            f"{elapsed:.1f}s"
        )
        # Force GC to keep peak memory low across chunks.
        import gc

        gc.collect()

    print(f"\n[5] Final: V={engine.snn.vocab_size} dict={len(engine.dictionary.entries)}")
    print(f"  garden_batch_done={resume_state.get('garden_batch_done')}/{len(garden_samples)}")
    print(f"  Elapsed: {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    main()
