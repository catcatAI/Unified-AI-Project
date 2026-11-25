#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [α] [B] [L3]
# =============================================================================
"""Generate routing/boundary training data (fast version).

Uses keyword-based routing instead of try_deterministic to avoid slow model loading.
"""

import json
import random
import re
from pathlib import Path

REPO = Path("/home/cxuo/文件/GitHub/Unified-AI-Project")
TRAIN = REPO / "apps/backend/data/processed/core_train.jsonl"
OUT = REPO / "apps/backend/data/processed/core_train_routing.jsonl"
VAL_OUT = REPO / "apps/backend/data/processed/core_val_routing.jsonl"

random.seed(42)

BOUNDARY_RESPONSES = [
    "I'm not sure about that. Let me think...",
    "That's an interesting question, but I don't have a definitive answer.",
    "I don't know the answer to that. Could you rephrase?",
    "Hmm, I'm not certain. What else can I help with?",
    "I'm not able to answer that right now.",
]


def route_question(prompt):
    """Simple keyword-based routing (mirrors deterministic_router logic)."""
    p = prompt.lower().strip()
    # Math: contains numbers and operators
    if re.search(r"\d+\s*[+\-*/]\s*\d+", p):
        return "math"
    # Logic: contains boolean operators
    if any(kw in p for kw in ["true", "false", "and", "or", "not", "xor", "> ", "< ", "=="]):
        if any(c.isdigit() for c in p):
            return "logic"
    # Knowledge: factual questions
    if any(
        kw in p
        for kw in ["what is", "who is", "where is", "when is", "capital", "population", "president"]
    ):
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
        ]
    ):
        return "reasoning"
    return None


# Load training data
rows = []
with open(TRAIN) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))

# Generate routing/boundary training pairs
routing_pairs = []
for row in rows:
    prompt = row.get("input", "").strip()
    if not prompt:
        continue

    engine = route_question(prompt)

    if engine is not None:
        # Engine can answer: train model to format
        routing_pairs.append(
            {
                "input": prompt,
                "output": f"Based on my knowledge, the answer involves {engine}.",
                "source": "routing_format",
            }
        )
    else:
        boundary = random.choice(BOUNDARY_RESPONSES)
        routing_pairs.append(
            {
                "input": prompt,
                "output": boundary,
                "source": "routing_boundary",
            }
        )

random.shuffle(routing_pairs)

split = int(len(routing_pairs) * 0.95)
train_rows = routing_pairs[:split]
val_rows = routing_pairs[split:]

with open(OUT, "w") as f:
    for r in train_rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

with open(VAL_OUT, "w") as f:
    for r in val_rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

n_format = sum(1 for r in routing_pairs if r["source"] == "routing_format")
n_boundary = sum(1 for r in routing_pairs if r["source"] == "routing_boundary")
print(f"Total: {len(routing_pairs)}")
print(f"  Format: {n_format}")
print(f"  Boundary: {n_boundary}")
print(f"Train: {len(train_rows)}, Val: {len(val_rows)}")
