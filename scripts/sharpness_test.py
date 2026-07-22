"""Edge sharpness post-processing comparison."""
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
import glob
from PIL import Image, ImageFilter

CIFAR_DIR="D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES=["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
IMG_DIM=3072
LATENT_DIM=128
OUTPUT_DIR="data/multimodal/gvv/sharpness_test"


def load_cifar(n_per_class=50):
    images, labels=[], []
    for ci, cls in enumerate(CLASSES):
        cls_dir = os.path.join(CIFAR_DIR, cls)
        files = sorted(glob.glob(os.path.join(cls_dir, "*.npy")))[:n_per_class]
        for f in files:
            arr = np.load(f)
            if arr.ndim == 3: arr = arr.reshape(-1)
            images.append(arr.astype(np.float32) / 255.0)
            labels.append(ci)
    return np.array(images), np.array(labels)


def sharpness_score(img_arr):
    """Higher = sharper edges."""
    img = img_arr.reshape(32, 32, 3)
    # Sobel-like edge detection
    dx = np.diff(img, axis=1)
    dy = np.diff(img, axis=0)
    return np.mean(dx**2) + np.mean(dy**2)


def main():
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    all_imgs, all_labels = load_cifar(50)
    rng = np.random.default_rng(42)
    train_idx, test_idx=[], []
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

    # Train MSE baseline (10 epochs - fast)
    print("Training MSE baseline (10 epochs)...")
    decoder = Decoder()
    opt = torch.optim.Adam(decoder.parameters(), lr=0.001)
    t0 = time.time()
    for epoch in range(10):
        perm = torch.randperm(len(X_train))
        for i in range(0, len(X_train), 64):
            idx = perm[i:i+64]
            x, y = X_train[idx], Y_train[idx]
            loss = F.mse_loss(decoder(x), y)
            opt.zero_grad()
            loss.backward()
            opt.step()
    print(f"  Training: {time.time()-t0:.0f}s")

    decoder.eval()
    with torch.no_grad():
        recon = decoder(X_test).numpy()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Post-processing methods
    def unsharp_mask(img_arr, strength=2.0):
        """Sharpen via unsharp mask."""
        img = img_arr.reshape(32, 32, 3)
        pil = Image.fromarray((img * 255).astype(np.uint8))
        sharp = pil.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
        return np.array(sharp).astype(np.float32) / 255.0

    def contrast_enhance(img_arr, factor=1.5):
        """Enhance contrast."""
        img = img_arr.reshape(32, 32, 3)
        pil = Image.fromarray((img * 255).astype(np.uint8))
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(pil)
        enhanced = enhancer.enhance(factor)
        return np.array(enhanced).astype(np.float32) / 255.0

    def edge_enhance(img_arr):
        """Enhance edges."""
        img = img_arr.reshape(32, 32, 3)
        pil = Image.fromarray((img * 255).astype(np.uint8))
        edge = pil.filter(ImageFilter.EDGE_ENHANCE_MORE)
        return np.array(edge).astype(np.float32) / 255.0

    def combined_enhance(img_arr):
        """Contrast + Unsharp mask."""
        img = img_arr.reshape(32, 32, 3)
        pil = Image.fromarray((img * 255).astype(np.uint8))
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(pil)
        enhanced = enhancer.enhance(1.3)
        sharp = enhanced.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=2))
        return np.array(sharp).astype(np.float32) / 255.0

    print("\n=== Sharpness Comparison ===")
    for i in range(10):
        orig = test_imgs[i]
        raw = recon[i]

        sharp_raw = sharpness_score(raw)
        sharp_orig = sharpness_score(orig)

        enhanced = combined_enhance(raw)
        sharp_enhanced = sharpness_score(enhanced)

        # Save
        orig_img = (orig.reshape(32, 32, 3) * 255).astype(np.uint8)
        raw_img = (raw.reshape(32, 32, 3) * 255).astype(np.uint8)
        enh_img = (enhanced.reshape(32, 32, 3) * 255).astype(np.uint8)

        combo = Image.new('RGB', (96, 32))
        combo.paste(Image.fromarray(orig_img), (0, 0))
        combo.paste(Image.fromarray(raw_img), (32, 0))
        combo.paste(Image.fromarray(enh_img), (64, 0))
        combo.save(os.path.join(OUTPUT_DIR, f"compare_{i}.png"))

        print(f"  Image {i}: raw_sharp={sharp_raw:.4f} enhanced_sharp={sharp_enhanced:.4f} (orig={sharp_orig:.4f})")

    # Class centers
    print("\n=== Class Centers ===")
    class_centers = np.zeros((10, LATENT_DIM), dtype=np.float32)
    for c in range(10):
        mask = train_labels == c
        class_centers[c] = train_latent[mask].mean(axis=0)
    cc_t = torch.tensor(class_centers, dtype=torch.float32)
    with torch.no_grad():
        gen = decoder(cc_t).numpy()

    for ci, cls in enumerate(CLASSES):
        raw = gen[ci]
        enhanced = combined_enhance(raw)
        m = (raw.reshape(32, 32, 3) * 255).astype(np.uint8)
        e = (enhanced.reshape(32, 32, 3) * 255).astype(np.uint8)
        combo = Image.new('RGB', (64, 32))
        combo.paste(Image.fromarray(m), (0, 0))
        combo.paste(Image.fromarray(e), (32, 0))
        combo.save(os.path.join(OUTPUT_DIR, f"class_{cls}.png"))
        print(f"  {cls}: raw_sharp={sharpness_score(raw):.4f} enhanced_sharp={sharpness_score(enhanced):.4f}")

    print(f"\nImages → {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
