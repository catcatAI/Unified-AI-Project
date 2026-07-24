"""Trace which stages handle test inputs in HYBRID mode."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.garden.garden_engine import GARDENEngine

e = GARDENEngine(compatibility_mode=True)
ckpt = os.path.join(os.path.dirname(__file__), "..", "data", "checkpoints", "garden_checkpoint")
if os.path.isdir(ckpt):
    e.load(ckpt)

# Wrap each stage to trace calls
trace = []
orig = {}
for name in ("_try_math_eval", "_try_logic_eval", "_try_reasoning",
             "_try_chain_reasoning", "_try_knowledge"):
    orig[name] = getattr(e, name)

def make_wrapper(stage_name, original):
    def wrapper(text):
        result = original(text)
        hit = result is not None
        trace.append((stage_name, text[:50], hit))
        return result
    return wrapper

for name in ("_try_math_eval", "_try_logic_eval", "_try_reasoning",
             "_try_chain_reasoning", "_try_knowledge"):
    setattr(e, name, make_wrapper(name, orig[name]))

# Test cases from each dataset
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "data", "raw_datasets")

test_cases = []
# Math
csv_path = os.path.join(DATA_DIR, "arithmetic_test_dataset.csv")
if os.path.exists(csv_path):
    import csv
    with open(csv_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            test_cases.append(("math", row["problem"], row["answer"]))
            if len(test_cases) >= 5:
                break

# Logic
lp = os.path.join(DATA_DIR, "logic_test.json")
if os.path.exists(lp):
    with open(lp, "r", encoding="utf-8") as f:
        data = json.load(f)
    for d in data[:5]:
        test_cases.append(("logic", d["proposition"], str(d["answer"])))

# Reasoning
rp = os.path.join(DATA_DIR, "reasoning_train.json")
if os.path.exists(rp):
    with open(rp, "r", encoding="utf-8") as f:
        data = json.load(f)
    for d in data[:5]:
        test_cases.append(("reasoning", d["input"], d["output"]))

print("=" * 70)
print("  STAGE TRACING — which stage handles each input?")
print("=" * 70)

for domain, inp, expected in test_cases:
    trace.clear()
    result = e.process(inp)
    stages_hit = [s for s, _, h in trace if h]
    print(f"\n[{domain}] Input: {inp[:60]}")
    print(f"  Expected: {expected[:60]}")
    print(f"  Got:      {result[:60]}")
    print(f"  Stages called: {[s for s, _, _ in trace]}")
    print(f"  Stages hit:    {stages_hit}")
    snn_ran = not any(h for s, _, h in trace if s in ("math", "logic", "reasoning", "chain", "knowledge") and h)
    print(f"  SNN would run: {snn_ran}")
