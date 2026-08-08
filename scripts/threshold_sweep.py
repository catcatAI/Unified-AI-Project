import numpy as np, json, sys, time
sys.path.insert(0, r"D:\Projects\Unified-AI-Project\apps\backend\src")
from ai.garden.garden_engine import GARDENEngine

g = GARDENEngine(compatibility_mode=True)
g.load(r"D:\Projects\Unified-AI-Project\data\checkpoints\garden_checkpoint")
snn = g.snn
V = snn.vocab_size
W = snn._W[:V, :V]

test_cases = [
    ("2+3=5", "math"),
    ("10-3=7", "math"),
    ("true OR false", "logic"),
    ("NOT false", "logic"),
    ("hello", "general"),
    ("what is AI", "knowledge"),
]

print(f"SNN: V={V}, density={float((W > 0).mean())*100:.1f}%")
print(f"Weights: mean={float(W[W > 0].mean()):.6f}, max={float(W.max()):.6f}")
print()

for query, label in test_cases:
    keys = g.dictionary.encode(query)
    valid = [k for k in keys if k in snn._key_to_idx]
    if not valid:
        print(f"[{label:10s}] '{query}' -> no valid keys")
        continue
    active_idx = [snn._key_to_idx[k] for k in valid]
    incoming = W[active_idx].sum(axis=0) / len(active_idx)
    print(f"[{label:10s}] '{query}' keys={valid} incoming: max={float(incoming.max()):.6f} "
          f"above_0.0001={int((incoming > 0.0001).sum())} above_0.0003={int((incoming > 0.0003).sum())}")

# Test SNN forward with correct keys
print("\n--- SNN forward with different thresholds ---")
for thr in [0.0001, 0.0002, 0.0003, 0.0005, 0.001]:
    snn.base_threshold = thr
    for query, label in test_cases[:4]:
        t0 = time.time()
        out = snn.forward(g.dictionary.encode(query))
        elapsed = time.time() - t0
        top3 = sorted(out.items(), key=lambda x: -x[1])[:3]
        print(f"  thr={thr:.4f} [{label:6s}] active={len(out):4d} top3={[(k,round(v,4)) for k,v in top3]} ({elapsed:.3f}s)")
    # Differentiation check
    out_math = set(snn.forward(g.dictionary.encode("2+3=5")).keys())
    out_logic = set(snn.forward(g.dictionary.encode("true OR false")).keys())
    overlap = len(out_math & out_logic)
    total = max(min(len(out_math), len(out_logic)), 1)
    print(f"  -> math vs logic overlap: {overlap}/{total}")
    print()
