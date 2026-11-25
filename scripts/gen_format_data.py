#!/usr/bin/env python3
"""Generate format training data.

Train the model to format deterministic engine results as natural language.
Input: question + engine result
Output: natural language response
"""
import json
import random
import sys
from pathlib import Path

REPO = Path("/home/cxuo/文件/GitHub/Unified-AI-Project")
sys.path.insert(0, str(REPO / "apps/backend/src"))

from ai.arithmetic.deterministic_router import try_deterministic

TRAIN = REPO / "apps/backend/data/processed/core_train.jsonl"
OUT = REPO / "apps/backend/data/processed/core_train_format.jsonl"
VAL_OUT = REPO / "apps/backend/data/processed/core_val_format.jsonl"

random.seed(42)

# Format templates
FORMAT_TEMPLATES = [
    "Based on my knowledge, {result}.",
    "The answer is: {result}.",
    "{result}.",
    "I found that {result}.",
    "According to my calculation, {result}.",
]

rows = []
with open(TRAIN) as f:
    for i, line in enumerate(f):
        if i >= 20000:  # Limit for speed
            break
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        prompt = row.get("input", "").strip()
        if not prompt:
            continue

        result = try_deterministic(prompt)
        if result is not None:
            # Engine can answer: train model to format
            template = random.choice(FORMAT_TEMPLATES)
            formatted = template.format(result=result)
            rows.append({
                "input": prompt,
                "output": formatted,
                "source": "format",
                "engine_result": result,
            })

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

print(f"Total: {len(rows)}")
print(f"Train: {len(train_rows)}, Val: {len(val_rows)}")
print(f"Sample: {rows[0]}")