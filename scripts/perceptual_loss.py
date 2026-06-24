"""Perceptual Loss - fast version (no re-id in loss)."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
import glob
from PIL import Image

CIFAR_DIR = "D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
IMG_DIM = 3072
LATENT_DIM = 128
OUTPUT_DIR = "data/multimodal/gvv/perceptual_test"


def load_cifar(n_per_class=50):
    images, labels = [], []
    for ci, cls in enumerate(CLASSES):
        cls_dir = os.path.join(CIFAR_DIR, cls)
        files = sorted(glob.glob(os.path.join(cls_dir, "*.npy")))[:n_per_class]
        for f in files:
            arr = np.load(f)
            if arr.ndim == 3: arr = arr.reshape(-1)
            images.append(arr.astype(np.float32) / 255.0)
            labels.append(ci)
    return np.array(images), np.array(labels)


def main():
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    all_imgs, all_labels = load_cifar(50)
    rng = np.random.default_rng(42)
    train_idx, test_idx = [], []
    for c in range(10):
        idxs = np.where(all_labels == c)[0]
        rng.shuffle(idxs)
        train_idx.extend(idxs[:40])
        test_idx.extend(idxs[40:50])
    train_imgs, train_labels = all_imgs[train_idx], all_labels[train_idx]
    test_imgs, test_labels = all_imgs[test_idx], all_labels[test_idx]

    mean = train_imgs.mean(axis=0)
    centered = train_imgs - mean
    U, S, Vt = np.linalg.svd(centered, full_matrices=False)
    proj = Vt[:LATENT_DIM]
    train_latent = centered @ proj.T
    test_latent = (test_imgs - mean) @ proj.T

    X_train = torch.tensor(train_latent, dtype=torch.float32)
    Y_train = torch.tensor(train_imgs, dtype=torch.float32)
    X_test = torch.tensor(test_latent, dtype=torch.float32)

    class Decoder(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(LATENT_DIM, 256), nn.ReLU(),
                nn.Linear(256, 512), nn.ReLU(),
                nn.Linear(512, IMG_DIM), nn.Sigmoid(),
            )
        def forward(self, x):
            return self.net(x)

    def train_and_eval(name, loss_fn):
        decoder = Decoder()
        opt = torch.optim.Adam(decoder.parameters(), lr=0.001)
        t0 = time.time()
        for epoch in range(25):
            perm = torch.randperm(len(X_train))
            for i in range(0, len(X_train), 64):
                idx = perm[i:i+64]
                x, y = X_train[idx], Y_train[idx]
                loss = loss_fn(decoder(x), y)
                opt.zero_grad()
                loss.backward()
                opt.step()
        t = time.time() - t0
        decoder.eval()
        with torch.no_grad():
            recon = decoder(X_test).numpy()
        mse = np.mean((recon - test_imgs) ** 2)
        print(f"  {name}: MSE={mse:.4f} ({t:.0f}s)")
        return decoder, recon

    # MSE
    print("=== MSE ===")
    dec_mse, recon_mse = train_and_eval("MSE", lambda r, o: F.mse_loss(r, o))

    # MSE + Edge sharpness
    print("=== MSE + Edge ===")
    def edge_loss(r, o):
        mse = F.mse_loss(r, o)
        r2d = r.view(-1, 32, 32, 3).permute(0, 3, 1, 2)
        dx = r2d[:, :, :, 1:] - r2d[:, :, :, :-1]
        dy = r2d[:, :, 1:, :] - r2d[:, :, :-1, :]
        edge = -(torch.mean(dx**2) + torch.mean(dy**2))
        return mse + 0.5 * edge
    dec_edge, recon_edge = train_and_eval("MSE+Edge", edge_loss)

    # MSE + Edge + Variance
    print("=== MSE + Edge + Variance ===")
    def full_loss(r, o):
        mse = F.mse_loss(r, o)
        r2d = r.view(-1, 32, 32, 3).permute(0, 3, 1, 2)
        dx = r2d[:, :, :, 1:] - r2d[:, :, :, :-1]
        dy = r2d[:, :, 1:, :] - r2d[:, :, :-1, :]
        edge = -(torch.mean(dx**2) + torch.mean(dy**2))
        var = -torch.mean(torch.var(r, dim=1))
        return mse + 0.5 * edge + 0.1 * var
    dec_full, recon_full = train_and_eval("MSE+Edge+Var", full_loss)

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for i in range(10):
        orig = (test_imgs[i].reshape(32, 32, 3) * 255).astype(np.uint8)
        m = (recon_mse[i].reshape(32, 32, 3) * 255).astype(np.uint8)
        e = (recon_edge[i].reshape(32, 32, 3) * 255).astype(np.uint8)
        f = (recon_full[i].reshape(32, 32, 3) * 255).astype(np.uint8)
        combo = Image.new('RGB', (128, 32))
        combo.paste(Image.fromarray(orig), (0, 0))
        combo.paste(Image.fromarray(m), (32, 0))
        combo.paste(Image.fromarray(e), (64, 0))
        combo.paste(Image.fromarray(f), (96, 0))
        combo.save(os.path.join(OUTPUT_DIR, f"compare_{i}.png"))

    # Class centers
    class_centers = np.zeros((10, LATENT_DIM), dtype=np.float32)
    for c in range(10):
        mask = train_labels == c
        class_centers[c] = train_latent[mask].mean(axis=0)
    cc_t = torch.tensor(class_centers, dtype=torch.float32)
    with torch.no_grad():
        gen_mse = dec_mse(cc_t).numpy()
        gen_edge = dec_edge(cc_t).numpy()
        gen_full = dec_full(cc_t).numpy()
    for ci, cls in enumerate(CLASSES):
        m = (gen_mse[ci].reshape(32, 32, 3) * 255).astype(np.uint8)
        e = (gen_edge[ci].reshape(32, 32, 3) * 255).astype(np.uint8)
        f = (gen_full[ci].reshape(32, 32, 3) * 255).astype(np.uint8)
        combo = Image.new('RGB', (96, 32))
        combo.paste(Image.fromarray(m), (0, 0))
        combo.paste(Image.fromarray(e), (32, 0))
        combo.paste(Image.fromarray(f), (64, 0))
        combo.save(os.path.join(OUTPUT_DIR, f"class_{cls}.png"))

    print(f"\nImages → {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
