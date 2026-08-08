"""Debug SNN load to find why density=0."""
import sys, os, numpy as np
sys.path.insert(0, r"D:\Projects\Unified-AI-Project\apps\backend\src")

from ai.garden.garden_engine import GARDENEngine

g = GARDENEngine(compatibility_mode=True)
g.load(r"D:\Projects\Unified-AI-Project\data\checkpoints\garden_checkpoint")
snn = g.snn

print(f"vocab_size={snn.vocab_size}")
print(f"_W is None={snn._W is None}")
if snn._W is not None:
    print(f"_W shape={snn._W.shape} nnz={np.count_nonzero(snn._W)}")
    V = snn.vocab_size
    if V > 0:
        live = snn._W[:V, :V]
        print(f"live [{V}x{V}] nnz={np.count_nonzero(live)} density={np.count_nonzero(live)/(V*V)*100:.2f}%")
    else:
        print("vocab_size=0, can't compute live density")
print(f"len(idx_to_key)={len(snn._idx_to_key)}")
print(f"len(key_to_idx)={len(snn._idx_to_key)}")
print(f"total_steps={snn.total_steps} hebbian={snn.total_hebbian_updates}")
stats = snn.get_stats()
print(f"stats matrix_density={stats['matrix_density']}")
print(f"stats total_steps={stats['total_steps']}")
