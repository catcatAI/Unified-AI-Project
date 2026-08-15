#!/usr/bin/env python
"""Resume-only GARDEN training helper.

Loads the already-built dataset pipeline, re-runs domain deconfliction to
rebuild the ``garden`` sample batch (it is derived from the same deterministic
filter applied in Step 3a), then hands off to ``_step5_train_garden`` which
resumes from ``garden_batch_done`` and persists after every 500-sample batch.

Usage:  TRAIN_NO_CORPUS=1 python scripts/resume_garden_train.py
"""
from __future__ import annotations

import asyncio
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
    _step5_train_garden,
    is_deterministic_match,
)
import json  # noqa: E402


def main() -> None:
    t_start = time.time()

    resume_state: dict = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            resume_state = json.load(f)
    batch_done = int(resume_state.get("garden_batch_done", 0))
    print(f"Resume state: garden_batch_done={batch_done}")

    if os.path.isdir(os.path.join(CKPT_DIR, "garden_checkpoint")) and batch_done > 0:
        print("GARDEN checkpoint exists — resuming in place.")
    else:
        print("WARNING: no garden checkpoint / batch_done=0 — starting from scratch.")

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
    print(f"  Total samples: {len(all_samples)}")

    print("\n[2] Initializing coordinator + deconflicting...")
    _model_bus, _qcls, coordinator = _step1_setup()
    batches = asyncio.run(coordinator.deconflict_samples(all_samples))
    for m, b in sorted(batches.items()):
        batches[m] = [s for s in b if not is_deterministic_match(s["input"], s["output"])]
        print(f"  {m:15s} -> {len(batches[m]):5d} samples")
    garden_samples = batches.get("garden", [])
    print(f"  GARDEN train set: {len(garden_samples)} samples (resume from idx {batch_done})")

    def save_state(step: int, data=None) -> None:
        if "completed_steps" not in resume_state:
            resume_state["completed_steps"] = []
        if step not in resume_state["completed_steps"]:
            resume_state["completed_steps"].append(step)
        if data:
            resume_state.update(data)
        resume_state["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(resume_state, f, ensure_ascii=False, indent=2)

    print("\n[3] Training GARDEN (resume)...")
    _step5_train_garden(coordinator, batches, resume_state, save_state)

    elapsed = time.time() - t_start
    print(f"\nDone. Elapsed: {elapsed:.1f}s")
    print(f"garden_batch_done now: {resume_state.get('garden_batch_done')}/{len(garden_samples)}")


if __name__ == "__main__":
    main()
