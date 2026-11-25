#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [α] [B] [L3]
# =============================================================================
"""Generate calculator input/output training data.

Feed the model with calculator I/O pairs to see if it learns computation.
"""

import json
import random
from pathlib import Path

REPO = Path("/home/cxuo/文件/GitHub/Unified-AI-Project")
OUT = REPO / "apps/backend/data/processed/core_train_calc.jsonl"
VAL = REPO / "apps/backend/data/processed/core_val_calc.jsonl"

random.seed(42)


def gen_problems(n):
    problems = []
    ops = ["+", "-", "*", "/"]
    for _ in range(n):
        # Simple arithmetic
        a = random.randint(0, 100)
        b = random.randint(0, 100)
        op = random.choice(ops)
        if op == "/":
            if b == 0:
                b = 1
            # Ensure divisible
            a = a * b
        expr = f"{a} {op} {b}"
        try:
            result = eval(expr)
            if isinstance(result, float):
                if result == int(result):
                    result = int(result)
                else:
                    result = round(result, 4)
            problems.append((expr, str(result)))
        except (ValueError, ZeroDivisionError, SyntaxError):
            pass
    return problems


def gen_order_of_ops(n):
    problems = []
    for _ in range(n):
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        c = random.randint(1, 10)
        # a op1 b op2 c
        op1 = random.choice(["+", "-", "*"])
        op2 = random.choice(["+", "-", "*"])
        expr = f"{a} {op1} {b} {op2} {c}"
        try:
            result = eval(expr)
            if isinstance(result, float) and result == int(result):
                result = int(result)
            problems.append((f"What is {expr}?", str(result)))
        except (ValueError, ZeroDivisionError, SyntaxError):
            pass
    return problems


def gen_parenthesized(n):
    problems = []
    for _ in range(n):
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        c = random.randint(1, 10)
        expr = f"({a} + {b}) * {c}"
        result = (a + b) * c
        problems.append((f"Calculate ({a} + {b}) * {c}", str(result)))
        expr2 = f"{a} + ({b} * {c})"
        result2 = a + (b * c)
        problems.append((f"Calculate {a} + ({b} * {c})", str(result2)))
    return problems


# Generate training data
all_problems = []
all_problems.extend(gen_problems(20000))
all_problems.extend(gen_order_of_ops(20000))
all_problems.extend(gen_parenthesized(10000))

# Format as QA pairs
rows = []
for expr, result in all_problems:
    # Format 1: direct
    rows.append({"input": expr, "output": result, "source": "calc_direct"})
    # Format 2: question
    rows.append({"input": f"What is {expr}?", "output": result, "source": "calc_question"})
    # Format 3: calculate
    rows.append({"input": f"Calculate {expr}", "output": result, "source": "calc_calculate"})

# Shuffle
random.shuffle(rows)

# Split train/val (95/5)
split = int(len(rows) * 0.95)
train_rows = rows[:split]
val_rows = rows[split:]

with open(OUT, "w") as f:
    for r in train_rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

with open(VAL, "w") as f:
    for r in val_rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"Generated {len(rows)} problems")
print(f"Train: {len(train_rows)}, Val: {len(val_rows)}")
print(f"Output: {OUT}")
