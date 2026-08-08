"""Fix existing saturated checkpoint by row-normalizing the weight matrix."""
import sys, numpy as np
sys.path.insert(0, r"D:\Projects\Unified-AI-Project\apps\backend\src")

from ai.garden.snn_core import _get_backend

# Load existing weights
npy_path = r"D:\Projects\Unified-AI-Project\data\checkpoints\garden_checkpoint\snn.pt.npy"
W = np.load(npy_path)
V = 10000  # vocab_size from checkpoint

print(f"Before: shape={W.shape}, nnz={np.count_nonzero(W)}, density={np.count_nonzero(W)/W.size*100:.1f}%")
print(f"Before: mean={W.mean():.6f}, max={W.max():.4f}")
live = W[:V, :V]
print(f"Before live: nnz={np.count_nonzero(live)}, density={np.count_nonzero(live)/(V*V)*100:.1f}%")

# Prune tiny weights (< 0.01) to increase sparsity
live[live < 0.01] = 0.0

# Row normalization: each row sums to at most 1.0
row_sums = np.abs(live).sum(axis=1, keepdims=True)
row_sums = np.maximum(row_sums, 1.0)
live_norm = live / row_sums

# Write back
W[:V, :V] = live_norm

print(f"\nAfter: nnz={np.count_nonzero(live_norm)}, density={np.count_nonzero(live_norm)/(V*V)*100:.1f}%")
print(f"After: mean={live_norm.mean():.6f}, max={live_norm.max():.4f}")
row_sum_check = np.abs(live_norm).sum(axis=1)
print(f"After row sums: min={row_sum_check.min():.4f}, max={row_sum_check.max():.4f}, mean={row_sum_check.mean():.4f}")

# Save
np.save(npy_path, W)
print(f"\nSaved to {npy_path}")
