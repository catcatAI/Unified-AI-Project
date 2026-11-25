#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [α] [B] [L3]
# =============================================================================
"""Generate classification training data using actual deterministic router."""

import json
import random
import sys
import time
from pathlib import Path

REPO = Path("/home/cxuo/文件/GitHub/Unified-AI-Project")
sys.path.insert(0, str(REPO / "apps/backend/src"))

from ai.arithmetic.deterministic_router import (
    try_math,
    try_logic,
    try_knowledge,
    try_reasoning,
    try_neural_bridge,
)

TRAIN = REPO / "apps/backend/data/processed/core_train.jsonl"
OUT = REPO / "apps/backend/data/processed/core_train_cls2.jsonl"
VAL_OUT = REPO / "apps/backend/data/processed/core_val_cls2.jsonl"

random.seed(42)


def route_question(prompt):
    """Use actual deterministic router to determine engine."""
    if try_math(prompt) is not None:
        return "math"
    if try_logic(prompt) is not None:
        return "logic"
    if try_knowledge(prompt) is not None:
        return "knowledge"
    if try_reasoning(prompt) is not None:
        return "reasoning"
    if try_neural_bridge(prompt) is not None:
        return "neural_bridge"
    return "none"


rows = []
with open(TRAIN) as f:
    for i, line in enumerate(f):
        if i >= 50000:  # Limit for speed
            break
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        prompt = row.get("input", "").strip()
        if not prompt:
            continue
        label = route_question(prompt)
        rows.append({"input": prompt, "label": label})
        if (i + 1) % 5000 == 0:
            print(f"Processed {i+1} rows", flush=True)

random.shuffle(rows)
split = int(len(rows) * 0.95)
train_rows = rows[:split]
val_rows = rows[split:]

with open(OUT, "w") as f:
    for r in train_rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

with open(VAL_OUT, "w") as f:
    for r in val_rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

from collections import Counter

labels = Counter(r["label"] for r in rows)
print(f"Total: {len(rows)}")
print(f"Labels: {dict(labels)}")
print(f"Train: {len(train_rows)}, Val: {len(val_rows)}")
