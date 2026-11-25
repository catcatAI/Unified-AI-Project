#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [α] [B] [L3]
# =============================================================================
"""Generate Chain-of-Thought augmented training data.

Adds step-by-step reasoning to QA pairs to force the model to "think"
rather than "pattern match".
"""

import json
import re
from pathlib import Path

REPO = Path("/home/cxuo/文件/GitHub/Unified-AI-Project")
TRAIN = REPO / "apps/backend/data/processed/core_train.jsonl"
VAL = REPO / "apps/backend/data/processed/core_val.jsonl"
OUT_TRAIN = REPO / "apps/backend/data/processed/core_train_cot.jsonl"
OUT_VAL = REPO / "apps/backend/data/processed/core_val_cot.jsonl"


def add_cot(prompt: str, answer: str) -> str:
    """Add chain-of-thought reasoning to an answer."""
    # Math problems: add step-by-step
    if re.search(r"\d+\s*[+\-*/]\s*\d+", prompt):
        # Try to extract the computation
        m = re.search(r"(\d+)\s*([+\-*/])\s*(\d+)", prompt)
        if m:
            a, op, b = m.group(1), m.group(2), m.group(3)
            a, b = int(a), int(b)
            if op == "+":
                result = a + b
                steps = (
                    f"Let me compute step by step.\n{a} + {b} = {result}.\nThe answer is {result}."
                )
            elif op == "-":
                result = a - b
                steps = (
                    f"Let me compute step by step.\n{a} - {b} = {result}.\nThe answer is {result}."
                )
            elif op == "*":
                result = a * b
                steps = (
                    f"Let me compute step by step.\n{a} * {b} = {result}.\nThe answer is {result}."
                )
            elif op == "/":
                if b != 0:
                    result = a / b
                    if result == int(result):
                        result = int(result)
                    steps = f"Let me compute step by step.\n{a} / {b} = {result}.\nThe answer is {result}."
                else:
                    return answer
            else:
                return answer
            return steps
    # Knowledge questions: add "The answer is:" prefix
    if len(answer) < 200:
        return f"Let me think about this.\n{answer}\nThe answer is: {answer.split('.')[0] if '.' in answer else answer}"
    return answer


def process_file(inp: Path, out: Path):
    rows = []
    with open(inp) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            prompt = row.get("input", "")
            answer = row.get("output", "")
            cot_answer = add_cot(prompt, answer)
            rows.append(
                {
                    "input": prompt,
                    "output": cot_answer,
                    "source": row.get("source", "") + "_cot",
                }
            )
    with open(out, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Processed {len(rows)} rows -> {out}")


process_file(TRAIN, OUT_TRAIN)
process_file(VAL, OUT_VAL)
