#!/usr/bin/env python3
"""
SLS 真實對比訓練（項目原生 SharedLatentSpace，吃稠密向量）— 硬件規格自適應

本地 CLIP 500 真實圖（快取 /tmp，未命中 91s）→ SLS register vision/512
→ 同類正對 + 跨類負對 → semantic_contrastive_train → held-out 100 驗收
（與線性探針 0.326/82% 同口徑對照）。

資源：訓練秒級 numpy；sleep+85% 門；<1GB。
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))

CACHE = "/tmp/clip_emb_500.npz"


def main():
    import numpy as np

    from core.backbone.hardware import HardwareProfile
    hw = HardwareProfile.detect()
    print(f"SLS 真實對比 硬件規格自適應: GPU={hw['gpu']} RAM={hw['ram_gb']:.1f}")

    from ai.multimodal.shared_latent_space import get_shared_latent_space

    z = np.load(CACHE)
    X, y = z["X"].astype(np.float64), z["y"]
    rng = np.random.RandomState(42)
    idx = rng.permutation(len(X))
    tr, te = idx[:400], idx[400:]
    Xtr, ytr, Xte, yte = X[tr], y[tr], X[te], y[te]

    sls = get_shared_latent_space()
    sls.reset()
    sls.register_modality("vision", X.shape[1])

    # 正對（同類）/負對（跨類）各 2000
    pos, neg = [], []
    while len(pos) < 2000:
        i, j = rng.randint(400), rng.randint(400)
        if ytr[i] == ytr[j] and i != j:
            pos.append(("vision", Xtr[i], "vision", Xtr[j]))
    while len(neg) < 2000:
        i, j = rng.randint(400), rng.randint(400)
        if ytr[i] != ytr[j]:
            neg.append(("vision", Xtr[i], "vision", Xtr[j]))
    print(f"  正對 {len(pos)} 負對 {len(neg)}")

    t0 = time.time()
    rep = sls.train(pos, neg, epochs=10, lr=0.01, margin=0.5)
    print(f"  SLS 訓練 10 epoch ({time.time()-t0:.1f}s) final_loss {rep.get('final_loss')}")

    Zte = np.array([sls.project("vision", v) for v in Xte])
    Zte /= np.linalg.norm(Zte, axis=1, keepdims=True) + 1e-9
    n = len(yte)
    same, cross, hits = [], [], 0
    for i in range(n):
        d = ((Zte[i] - Zte) ** 2).sum(axis=1) ** 0.5
        d[i] = 1e9
        j = int(np.argmin(d))
        hits += 1 if yte[j] == yte[i] else 0
        for j2 in range(i + 1, n):
            (same if yte[i] == yte[j2] else cross).append(float(d[j2]))
    import statistics
    s, c, r = statistics.mean(same), statistics.mean(cross), hits / n
    print(f"  SLS held-out(100)：同類距 {s:.3f} 跨類距 {c:.3f} top1 召回 {r:.0%}（線性基線 0.326/82%）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
