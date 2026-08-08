import json
with open(r"D:\Projects\Unified-AI-Project\data\checkpoints\garden_checkpoint\snn.json") as f:
    meta = json.load(f)
idx_to_key = meta["idx_to_key"]
k2i = meta["key_to_idx"]
print(f"Total keys: {len(idx_to_key)}")
print(f"First 20: {idx_to_key[:20]}")
for k in ["m0", "m1", "m2", "m3", "m5", "op1", "op5", "true", "false", "or", "not", "hello"]:
    if k in k2i:
        print(f"  {k}: idx={k2i[k]}")
    else:
        print(f"  {k}: NOT IN VOCAB")
# Check what surface forms map to
import sys; sys.path.insert(0, r"D:\Projects\Unified-AI-Project\apps\backend\src")
from ai.garden.garden_engine import GARDENEngine
g = GARDENEngine(compatibility_mode=True)
g.load(r"D:\Projects\Unified-AI-Project\data\checkpoints\garden_checkpoint")
for q in ["2+3=5", "true OR false", "hello"]:
    keys = g.dictionary.encode(q)
    print(f"encode('{q}') = {list(keys.keys())[:10]}")
    valid = [k for k in keys if k in k2i]
    print(f"  in SNN vocab: {valid[:10]}")
