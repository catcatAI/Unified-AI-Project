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

# embedding 快取：data/.cache/（git 忽略，/tmp 易失不用）
CACHE = {"visual": "data/.cache/clip_emb_500.npz", "audio": "data/.cache/whisper_emb_400.npz"}


def main():
    import argparse

    import numpy as np

    ap = argparse.ArgumentParser(description="SLS real contrastive (visual/audio)")
    ap.add_argument("--modality", choices=["visual", "audio"], default="visual")
    ap.add_argument("--checkpoint", default=None,
                    help="save trained SLS weights (default: data/checkpoints/sls_<modality>.npz; empty string disables)")
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--hard-pairs", default="", help="e.g. '3,5': extra pairs focused on these classes")
    ap.add_argument("--hard-extra", type=int, default=1000)
    ap.add_argument("--margin", type=float, default=0.5)
    ap.add_argument("--cache", default="", help="embedding cache path override")
    args = ap.parse_args()
    mod = "vision" if args.modality == "visual" else "audio"

    from core.backbone.hardware import HardwareProfile
    hw = HardwareProfile.detect()
    print(f"SLS 真實對比[{args.modality}] 硬件規格自適應: GPU={hw['gpu']} RAM={hw['ram_gb']:.1f}")

    from ai.multimodal.shared_latent_space import get_shared_latent_space

    z = np.load(args.cache or CACHE[args.modality])
    X, y = z["X"].astype(np.float64), z["y"]
    rng = np.random.RandomState(42)
    idx = rng.permutation(len(X))
    nte = len(X) // 5
    tr, te = idx[:-nte], idx[-nte:]
    Xtr, ytr, Xte, yte = X[tr], y[tr], X[te], y[te]

    sls = get_shared_latent_space()
    sls.reset()
    sls.register_modality(mod, X.shape[1])

    # 正對（同類）/負對（跨類）各 2000
    pos, neg = [], []
    while len(pos) < 2000:
        i, j = rng.randint(len(tr)), rng.randint(len(tr))
        if ytr[i] == ytr[j] and i != j:
            pos.append((mod, Xtr[i], mod, Xtr[j]))
    while len(neg) < 2000:
        i, j = rng.randint(len(tr)), rng.randint(len(tr))
        if ytr[i] != ytr[j]:
            neg.append((mod, Xtr[i], mod, Xtr[j]))
    print(f"  正對 {len(pos)} 負對 {len(neg)}")
    # hard-negative 加料：指定類內正對 + 類間負對（難類聚焦）
    if args.hard_pairs:
        hp = [int(c) for c in args.hard_pairs.split(",")]
        pools = {c: [k for k in range(len(tr)) if ytr[k] == c] for c in hp}
        extra_p, extra_n = 0, 0
        guard = 0
        while (extra_p < args.hard_extra or extra_n < args.hard_extra) and guard < args.hard_extra * 20:
            guard += 1
            c1, c2 = hp[rng.randint(len(hp))], hp[rng.randint(len(hp))]
            if not pools[c1] or not pools[c2]:
                continue
            i, j = pools[c1][rng.randint(len(pools[c1]))], pools[c2][rng.randint(len(pools[c2]))]
            if i == j:
                continue
            if c1 == c2 and extra_p < args.hard_extra:
                pos.append((mod, Xtr[i], mod, Xtr[j]))
                extra_p += 1
            elif c1 != c2 and extra_n < args.hard_extra:
                neg.append((mod, Xtr[i], mod, Xtr[j]))
                extra_n += 1
        print(f"  hard 加料 +{extra_p} 正 +{extra_n} 負（類 {hp}）")

    t0 = time.time()
    rep = sls.train(pos, neg, epochs=args.epochs, lr=0.01, margin=args.margin)
    print(f"  SLS 訓練 {args.epochs} epoch ({time.time()-t0:.1f}s) final_loss {rep.get('final_loss')}")

    Zte = np.array([sls.project(mod, v) for v in Xte])
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
    print(f"  SLS held-out({len(te)})：同類距 {s:.3f} 跨類距 {c:.3f} top1 召回 {r:.0%}（線性基線 0.326/82%）")

    # 存檔接線：訓後存權重，重置後加載驗往返（P1 模式；存檔在忽略區）
    ckpt = args.checkpoint
    if ckpt is None:
        ckpt = os.path.join(os.path.dirname(__file__), "..", "data/checkpoints",
                            f"sls_{args.modality}.npz")
    if ckpt:
        try:
            ok_save = sls.save_weights(ckpt)
            sls.reset()
            sls.register_modality(mod, X.shape[1])
            ok_load = sls.load_weights(ckpt)
            v0 = sls.project(mod, Xte[0])
            v0n = v0 / (np.linalg.norm(v0) + 1e-9)  # Zte 存的是歸一後，對齊再比
            same_proj = bool(np.allclose(v0n, Zte[0], atol=1e-5))
            print(f"   Checkpoint: save={ok_save} load={ok_load} "
                  f"({os.path.getsize(ckpt)//1024}KB) roundtrip={'✅' if same_proj else '❌'}")
        except Exception as e:
            print(f"   Checkpoint ❌: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
