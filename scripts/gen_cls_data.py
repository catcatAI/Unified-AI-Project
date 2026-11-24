#!/usr/bin/env python3
"""Generate classification training data for routing."""

import json
import random
import re
from pathlib import Path
from collections import Counter

REPO = Path("/home/cxuo/文件/GitHub/Unified-AI-Project")
TRAIN = REPO / "apps/backend/data/processed/core_train.jsonl"
OUT = REPO / "apps/backend/data/processed/core_train_cls.jsonl"
VAL_OUT = REPO / "apps/backend/data/processed/core_val_cls.jsonl"

random.seed(42)


def route_question(prompt):
    p = prompt.lower().strip()
    # Math: contains numbers and arithmetic operators
    if re.search(r"\d+\s*[+\-*/]\s*\d+", p):
        return "math"
    # Logic: comparison or boolean
    if any(
        kw in p
        for kw in [
            "> ",
            "< ",
            ">=",
            "<=",
            "==",
            "!=",
            "is greater",
            "is less",
            "is equal",
            "true or false",
        ]
    ):
        return "logic"
    if any(kw in p for kw in [" and ", " or ", " not "]) and any(c.isdigit() for c in p):
        return "logic"
    # Knowledge: factual questions
    if any(
        kw in p
        for kw in [
            "capital of",
            "population of",
            "president of",
            "who invented",
            "who discovered",
            "what is the",
            "how many",
            "how much",
        ]
    ):
        return "knowledge"
    if any(kw in p for kw in ["capital", "population", "president", "country", "city"]):
        return "knowledge"
    # Reasoning: comparison, causal
    if any(
        kw in p
        for kw in [
            "taller",
            "shorter",
            "bigger",
            "smaller",
            "faster",
            "slower",
            "why",
            "because",
            "cause",
            "compare",
            "which is",
        ]
    ):
        return "reasoning"
    return "none"


rows = []
with open(TRAIN) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        prompt = row.get("input", "").strip()
        if not prompt:
            continue
        label = route_question(prompt)
        rows.append({"input": prompt, "label": label})

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

labels = Counter(r["label"] for r in rows)
print(f"Total: {len(rows)}")
print(f"Labels: {dict(labels)}")
print(f"Train: {len(train_rows)}, Val: {len(val_rows)}")
