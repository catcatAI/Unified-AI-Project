"""Direct SNN-ONLY test - no GARDENEngine process/generate."""
import sys, time, numpy as np
sys.path.insert(0, r"D:\Projects\Unified-AI-Project\apps\backend\src")

from ai.garden.garden_engine import GARDENEngine

TEST_QUERIES = [
    ("2+3=5", "math"),
    ("10-3=7", "math"),
    ("4*5=20", "math"),
    ("100/10=10", "math"),
    ("true OR false", "logic"),
    ("NOT false", "logic"),
    ("true AND true", "logic"),
    ("hello", "general"),
    ("what is AI", "knowledge"),
    ("你好", "general"),
]

print("Loading GARDEN...")
g = GARDENEngine(compatibility_mode=True)
g.load(r"D:\Projects\Unified-AI-Project\data\checkpoints\garden_checkpoint")
snn = g.snn
stats = snn.get_stats()
print(f"SNN: V={stats['vocab_size']}, density={stats['matrix_density']*100:.1f}%, "
      f"hebbian={stats['total_hebbian_updates']}, steps={stats['total_steps']}")
print(f"Dict: {len(g.dictionary.entries)} entries\n")

snn_hits = 0
total = len(TEST_QUERIES)

for query, domain in TEST_QUERIES:
    t0 = time.time()
    # Step 1: encode
    keys = g.dictionary.encode(query)
    valid_keys = {k: keys[k] for k in keys if k in snn._key_to_idx}
    # Step 2: SNN forward (with timeout guard)
    snn_result = {}
    if valid_keys:
        snn_result = snn.forward(valid_keys)
    elapsed = time.time() - t0

    out_keys = list(snn_result.keys())
    words = []
    for k in out_keys[:10]:
        if k in g.dictionary.entries:
            for form in g.dictionary.entries[k].surface_forms.values():
                if form:
                    words.append(form.split()[0])
                    break
    snn_str = " ".join(words[:8])
    has_activation = "+" if out_keys else "x"
    if out_keys: snn_hits += 1

    print(f"[{has_activation}] {query:20s} ({domain:8s}) encode={len(keys):2d} valid={len(valid_keys):2d} "
          f"snn_out={len(out_keys):3d} -> {snn_str[:50]}  ({elapsed:.3f}s)")

print(f"\nSNN-ONLY activation: {snn_hits}/{total} ({snn_hits/total*100:.0f}%)")
