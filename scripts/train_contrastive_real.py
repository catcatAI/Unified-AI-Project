#!/usr/bin/env python3
"""
真實對比訓練（退役模擬 `train_contrastive_pilot` 的真替身）— 硬件規格自適應

真實 CIFAR-10 500 圖（10 類各 50）→ 本地 CLIP 編碼（快取 /tmp，未命中則編碼 91s）
→ 線性 512→64 + triplet margin（numpy 全批量梯度，~200 步，秒級）
→ held-out 100 驗收：同/跨類間隔 + top-1 同類檢索召回。

資源：編碼 91s 一次（快取後秒級）；訓練 <10s <500MB；sleep+85% 門。
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))

CACHE = {"visual": "/tmp/clip_emb_500.npz", "audio": "/tmp/whisper_emb_400.npz"}


def get_embeddings(modality="visual"):
    import numpy as np

    cache = CACHE[modality]
    if os.path.exists(cache):
        z = np.load(cache)
        print(f"  embedding 快取命中 {cache} ({os.path.getsize(cache)//1024}KB)")
        return z["X"], z["y"]
    if modality == "audio":
        return _encode_audio(cache)
    return _encode_visual(cache)


def _encode_audio(cache):
    import csv

    import numpy as np

    import torch
    from scipy.io import wavfile
    from scipy.signal import resample
    from transformers import WhisperModel, WhisperProcessor

    model_id = "openai/whisper-tiny"
    model = WhisperModel.from_pretrained(model_id, local_files_only=True)
    proc = WhisperProcessor.from_pretrained(model_id, local_files_only=True)
    model.eval()
    rows = list(csv.DictReader(open("data/multimodal/ESC-50-master/meta/esc50.csv")))
    cats = sorted(set(r["category"] for r in rows))[:10]
    embs, labels = [], []
    t0 = time.time()
    for ci, cat in enumerate(cats):
        files = [r["filename"] for r in rows if r["category"] == cat][:40]
        for fp in files:
            try:
                import psutil
                if psutil.virtual_memory().percent > 85:
                    print("  ⚠️ RAM >85% 暫停 1s")
                    time.sleep(1)
            except Exception:
                pass
            sr, y = wavfile.read(os.path.join("data/multimodal/ESC-50-master/audio", fp))
            y = y.astype(np.float64)
            if y.ndim > 1:
                y = y.mean(axis=1)
            y16 = resample(y, int(len(y) * 16000 / sr)).astype(np.float32)
            inp = proc(y16, sampling_rate=16000, return_tensors="pt")
            with torch.no_grad():
                h = model.encoder(inp.input_features).last_hidden_state.mean(dim=1).numpy()
            embs.append(h[0])
            labels.append(ci)
            time.sleep(0.02)
    X = np.array(embs).astype(np.float64)
    y = np.array(labels)
    np.savez(cache, X=X, y=y)
    print(f"  音頻編碼 {X.shape} ({time.time()-t0:.1f}s)，已快取")
    return X, y


def _encode_visual(cache):
    import numpy as np

    import torch
    from transformers import CLIPModel, CLIPProcessor
    import PIL.Image

    model_id = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(model_id, local_files_only=True)
    proc = CLIPProcessor.from_pretrained(model_id, local_files_only=True)
    model.eval()
    data_root = os.path.join(os.path.dirname(__file__), "..", "data/multimodal/cifar10")
    classes = sorted(d for d in os.listdir(data_root) if os.path.isdir(os.path.join(data_root, d)))
    embs, labels = [], []
    t0 = time.time()
    for ci, cls in enumerate(classes):
        cdir = os.path.join(data_root, cls)
        names = sorted(f for f in os.listdir(cdir) if f.endswith(".npy"))[:50]
        for bi in range(0, len(names), 16):
            try:
                import psutil
                if psutil.virtual_memory().percent > 85:
                    print("  ⚠️ RAM >85% 暫停 1s")
                    time.sleep(1)
            except Exception:
                pass
            imgs = [PIL.Image.fromarray(np.load(os.path.join(cdir, f)).astype("uint8"))
                    for f in names[bi:bi + 16]]
            inp = proc(images=imgs, return_tensors="pt")
            with torch.no_grad():
                v = model.get_image_features(**inp).pooler_output.numpy()
            embs.append(v)
            labels += [ci] * len(imgs)
            time.sleep(0.05)
    X = np.concatenate(embs).astype(np.float64)
    y = np.array(labels)
    np.savez(cache, X=X, y=y)
    print(f"  編碼 {X.shape} ({time.time()-t0:.1f}s)，已快取")
    return X, y


def metrics(Z, y):
    import numpy as np

    n = len(y)
    same, cross, hits = [], [], 0
    for i in range(n):
        d = ((Z[i] - Z) ** 2).sum(axis=1) ** 0.5
        d[i] = 1e9
        j = int(np.argmin(d))
        hits += 1 if y[j] == y[i] else 0
        for j2 in range(i + 1, n):
            (same if y[i] == y[j2] else cross).append(float(d[j2]))
    import statistics
    return statistics.mean(same), statistics.mean(cross), hits / n


def main():
    import argparse

    import numpy as np

    ap = argparse.ArgumentParser(description="real contrastive training (visual/audio)")
    ap.add_argument("--modality", choices=["visual", "audio"], default="visual")
    ap.add_argument("--iters", type=int, default=200)
    args = ap.parse_args()

    from core.backbone.hardware import HardwareProfile
    hw = HardwareProfile.detect()
    print(f"真實對比訓練[{args.modality}] 硬件規格自適應: GPU={hw['gpu']} RAM={hw['ram_gb']:.1f}")

    X, y = get_embeddings(args.modality)
    Xn = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
    rng = np.random.RandomState(42)
    idx = rng.permutation(len(X))
    nte = len(X) // 5
    tr, te = idx[:-nte], idx[-nte:]
    Xtr, ytr, Xte, yte = Xn[tr], y[tr], Xn[te], y[te]

    s0, c0, r0 = metrics(Xte, yte)
    print(f"  訓練前 held-out({len(te)})：同類距 {s0:.3f} 跨類距 {c0:.3f} top1 召回 {r0:.0%}")

    # 線性 D→64 + triplet margin（錨/正/負三元組，numpy 梯度）
    W = rng.randn(X.shape[1], 64) * 0.05
    lr, margin, iters = 0.5, 0.5, args.iters
    t0 = time.time()
    for it in range(iters):
        Z = Xtr @ W
        Zn = Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-9)
        # 每錨採 1 正 4 負
        grad = np.zeros_like(W)
        loss = 0.0
        for i in range(0, len(Zn), 40):
            a = Zn[i:i + 40]
            pos_m = (ytr[i:i + 40, None] == ytr[None, :])
            neg_m = ~pos_m
            for k in range(len(a)):
                pi = np.where(pos_m[k])[0]
                ni = np.where(neg_m[k])[0]
                if len(pi) == 0 or len(ni) == 0:
                    continue
                p = pi[rng.randint(len(pi))]
                nn = ni[rng.choice(len(ni), size=min(4, len(ni)), replace=False)]
                for n_ in nn:
                    dap = float(((a[k] - Zn[p]) ** 2).sum() ** 0.5)
                    dan = float(((a[k] - Zn[n_]) ** 2).sum() ** 0.5)
                    mgn = margin + dap - dan
                    if mgn > 0:
                        loss += mgn
                        ga = 2 * (Zn[n_] - Zn[p]) / (dan + dap + 1e-9)
                        grad += np.outer(Xtr[i + k], ga) / len(a)
        W -= lr * grad / len(Xtr)
        if (it + 1) % 50 == 0:
            print(f"  iter {it+1}/{iters} loss {loss:.1f} ({time.time()-t0:.1f}s)")
    print(f"  訓練 {iters} 步 ({time.time()-t0:.1f}s)")

    Zte = (Xte @ W)
    Zte /= np.linalg.norm(Zte, axis=1, keepdims=True) + 1e-9
    s1, c1, r1 = metrics(Zte, yte)
    print(f"  訓練後 held-out({len(te)})：同類距 {s1:.3f} 跨類距 {c1:.3f} top1 召回 {r1:.0%}")
    print(f"  間隔 {c0-s0:.3f} → {c1-s1:.3f}，召回 {r0:.0%} → {r1:.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
