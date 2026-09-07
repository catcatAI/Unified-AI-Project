#!/usr/bin/env python3
"""
首個真實 held-out MSE 測量 — 硬件規格自適應（分批+sleep，<2GB）

CLIP ViT-B/32（本地快取，CPU）編碼真實 CIFAR-10 500 圖（10 類各 50），
400/100 切分：訓練集最小二乘擬合 512→64 投影，測試集報 held-out MSE。
替代已作廢的模擬算術值（0.079/0.121/0.221）——此數為真實測量。

資源：500 圖分批編碼 + sleep 0.05/批 + 85% RAM 暫停，模型常駐 ~350MB。
"""

import os
import sys
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))


def main():
    import numpy as np

    from core.backbone.hardware import HardwareProfile
    hw = HardwareProfile.detect()
    tier = HardwareProfile.get_tier(hw)
    print(f"真實 MSE 500 硬件規格自適應: GPU={hw['gpu']} RAM={hw['ram_gb']:.1f} tier={tier}")

    import torch
    from transformers import CLIPModel, CLIPProcessor
    import PIL.Image

    model_id = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(model_id, local_files_only=True)
    proc = CLIPProcessor.from_pretrained(model_id, local_files_only=True)
    model.eval()

    data_root = os.path.join(os.path.dirname(__file__), "..", "data/multimodal/cifar10")
    classes = sorted(d for d in os.listdir(data_root) if os.path.isdir(os.path.join(data_root, d)))
    files = []
    for cls in classes:
        cdir = os.path.join(data_root, cls)
        names = sorted(f for f in os.listdir(cdir) if f.endswith(".npy"))[:50]
        files.extend((cls, os.path.join(cdir, f)) for f in names)
    print(f"  真實 CIFAR {len(files)} 圖（{len(classes)} 類各 50）")

    batch = 16
    embs = []
    t0 = time.time()
    for bi in range(0, len(files), batch):
        try:
            import psutil
            if psutil.virtual_memory().percent > 85:
                print(f"  ⚠️ RAM {psutil.virtual_memory().percent:.1f}% >85% 暫停 1s")
                time.sleep(1)
        except Exception:
            pass
        imgs = []
        for _, fp in files[bi:bi + batch]:
            arr = np.load(fp)
            imgs.append(PIL.Image.fromarray(arr.astype("uint8")))
        inp = proc(images=imgs, return_tensors="pt")
        with torch.no_grad():
            out = model.get_image_features(**inp).pooler_output
        embs.append(out.numpy())
        time.sleep(0.05)
    X = np.concatenate(embs, axis=0)
    print(f"  編碼完成 {X.shape} ({time.time()-t0:.1f}s, {(time.time()-t0)/len(files):.2f}s/圖)")

    # 400/100 切分：最小二乘 512→64（以 PCA 式目標計 residual；此處以自身降維重建為目標）
    # 誠實定義：目標 = 以訓練集均值為中心的 64 維 PCA 投影，測重建 MSE（held-out）
    rng = np.random.RandomState(42)
    idx = rng.permutation(len(X))
    Xtr, Xte = X[idx[:400]], X[idx[400:]]
    mu = Xtr.mean(axis=0)
    _, _, Vt = np.linalg.svd(Xtr - mu, full_matrices=False)
    V64 = Vt[:64].T  # 512×64 投影基（訓練集擬合）
    rec_tr = mu + (Xtr - mu) @ V64 @ V64.T
    rec_te = mu + (Xte - mu) @ V64 @ V64.T
    mse_tr = float(((Xtr - rec_tr) ** 2).mean())
    mse_te = float(((Xte - rec_te) ** 2).mean())
    var = float(((Xte - mu) ** 2).mean())
    print(f"  訓練重建 MSE(400): {mse_tr:.4f}")
    print(f"  Held-out 重建 MSE(100): {mse_te:.4f}（基線方差 {var:.4f}，保留 {1 - mse_te/var:.1%}）")
    print("  ✅ 首個真實 held-out MSE（非模擬算術值）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
