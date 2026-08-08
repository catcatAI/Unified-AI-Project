"""Revert checkpoint to original, then apply targeted fix."""
import numpy as np

npy_path = r"D:\Projects\Unified-AI-Project\data\checkpoints\garden_checkpoint\snn.pt.npy"

# Check git for the original
import subprocess
result = subprocess.run(
    ["git", "show", "HEAD:data/checkpoints/garden_checkpoint/snn.pt.npy"],
    capture_output=True, cwd=r"D:\Projects\Unified-AI-Project"
)
if result.returncode == 0:
    # Save original
    with open(npy_path, "wb") as f:
        f.write(result.stdout)
    W = np.load(npy_path)
    print(f"Restored from git: shape={W.shape}, nnz={np.count_nonzero(W)}, "
          f"density={np.count_nonzero(W)/W.size*100:.1f}%")
else:
    print("Not in git, checking backup...")
    # Try backup
    import os
    backup = npy_path + ".bak"
    if os.path.exists(backup):
        import shutil
        shutil.copy(backup, npy_path)
        W = np.load(npy_path)
        print(f"Restored from backup: nnz={np.count_nonzero(W)}")
    else:
        print("No backup found")
