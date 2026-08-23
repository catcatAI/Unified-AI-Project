"""Learned Representation v5: CLIP encoder + learned decoder.

Use CLIP as encoder (proven 90% accuracy), train decoder to map from CLIP → image.
This gives us:
- Recognition: image → CLIP → classify (90%)
- Generation: CLIP latent → decoder → image (learned)
"""
import sys
import os
import time
import io
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
import glob
from PIL import Image
from ai.multimodal.semantic_visual import SemanticVisualEncoder

CIFAR_DIR="D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES=["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
IMG_DIM=32 * 32 * 3
CLIP_DIM=512


def load_cifar(n_per_class=50):
    images=[]
    labels=[]
    for ci, cls in enumerate(CLASSES):
        cls_dir = os.path.join(CIFAR_DIR, cls)
        files = sorted(glob.glob(os.path.join(cls_dir, "*.npy")))[:n_per_class]
        for f in files:
            arr = np.load(f)
            if arr.ndim == 3:
                arr = arr.reshape(-1)
            images.append(arr.astype(np.float32) / 255.0)
            labels.append(ci)
    return np.array(images), np.array(labels)


def encode_images(encoder, pil_images):
    """Encode PIL images with CLIP."""
    vecs=[]
    for i, img in enumerate(pil_images):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        vec = encoder.encode(buf.getvalue())
        vecs.append(vec if vec is not None else np.zeros(CLIP_DIM, dtype=np.float32))
        if (i + 1) % 100 == 0:
            print(f"  Encoded {i+1}/{len(pil_images)}")
    return np.array(vecs, dtype=np.float32)


def main():
    print("Loading CLIP...")
    clip_encoder = SemanticVisualEncoder()
    from ai.multimodal.semantic_visual import _lazy_init_clip
    model, _ = _lazy_init_clip()
    if model is None:
        print("CLIP failed!")
        return

    print("Loading CIFAR-10 (50/class)...")
    all_imgs, all_labels = load_cifar(50)
    print(f"Total: {len(all_imgs)}")

    # Stratified split
    rng = np.random.default_rng(42)
    train_idx=[]
    test_idx=[]
    for c in range(10):
        idxs = np.where(all_labels == c)[0]
        rng.shuffle(idxs)
        train_idx.extend(idxs[:40])
        test_idx.extend(idxs[40:50])
    train_imgs = all_imgs[train_idx]
    train_labels = all_labels[train_idx]
    test_imgs = all_imgs[test_idx]
    test_labels = all_labels[test_idx]

    # Convert to PIL for CLIP encoding
    print("Converting to PIL...")
    train_pil=[Image.fromarray((img.reshape(32, 32, 3) * 255).astype(np.uint8)).resize((224, 224))
                 for img in train_imgs]
    test_pil=[Image.fromarray((img.reshape(32, 32, 3) * 255).astype(np.uint8)).resize((224, 224))
                for img in test_imgs]

    # Encode with CLIP
    print("Encoding training images with CLIP...")
    train_clip = encode_images(clip_encoder, train_pil)
    print(f"Train CLIP: {train_clip.shape}")

    print("Encoding test images with CLIP...")
    test_clip = encode_images(clip_encoder, test_pil)
    print(f"Test CLIP: {test_clip.shape}")

    # Classifier (analytical)
    print("\n=== Classifier ===")
    Y = np.zeros((len(train_clip), 10), dtype=np.float32)
    for i, l in enumerate(train_labels):
        Y[i, l] = 1.0
    W_clf = np.linalg.solve(train_clip.T @ train_clip + 1e-4 * np.eye(CLIP_DIM),
                            train_clip.T @ Y)
    preds = np.argmax(test_clip @ W_clf, axis=1)
    correct = np.sum(preds == test_labels)
    print(f"Recognition: {correct}/{len(test_labels)} = {correct/len(test_labels):.1%}")

    # Decoder: CLIP features → image (analytical solution)
    print("\n=== Decoder (analytical: CLIP → image) ===")
    reg=10.0
    CtC = train_clip.T @ train_clip + reg * np.eye(CLIP_DIM)
    CtI = train_clip.T @ train_imgs  # (512, 3072)
    W_dec = np.linalg.solve(CtC, CtI).T  # (3072, 512)
    b_dec = train_imgs.mean(axis=0) - train_clip.mean(axis=0) @ W_dec.T

    # Test reconstruction
    print("\n=== Reconstruction ===")
    output_dir="data/multimodal/gvv/learned_test"
    os.makedirs(output_dir, exist_ok=True)

    total_mse=0.0
    for i in range(10):
        raw = test_clip[i] @ W_dec.T + b_dec
        recon = np.clip(raw, 0, 1).reshape(32, 32, 3)
        orig = test_imgs[i].reshape(32, 32, 3)
        mse = np.mean((recon - orig) ** 2)
        total_mse += mse
        Image.fromarray((orig * 255).astype(np.uint8)).save(os.path.join(output_dir, f"orig_{i}.png"))
        Image.fromarray((recon * 255).astype(np.uint8)).save(os.path.join(output_dir, f"recon_{i}.png"))
        print(f"  Image {i}: MSE={mse:.4f}")
    print(f"Average MSE: {total_mse/10:.4f}")

    # Generate from class centers
    print("\n=== Generation from Class Centers ===")
    for ci, cls in enumerate(CLASSES):
        mask = train_labels == ci
        center = train_clip[mask].mean(axis=0)
        raw = center @ W_dec.T + b_dec
        gen = np.clip(raw, 0, 1).reshape(32, 32, 3)
        Image.fromarray((gen * 255).astype(np.uint8)).save(os.path.join(output_dir, f"gen_{cls}.png"))
        print(f"  Generated {cls}")

    # Random generation
    for i in range(5):
        z = rng.standard_normal(CLIP_DIM).astype(np.float32)
        z = z / np.linalg.norm(z) * np.sqrt(CLIP_DIM)
        raw = z @ W_dec.T + b_dec
        gen = np.clip(raw, 0, 1).reshape(32, 32, 3)
        Image.fromarray((gen * 255).astype(np.uint8)).save(os.path.join(output_dir, f"gen_random_{i}.png"))
    print("Generated 5 random images")
    print(f"\nAll → {output_dir}/")


if __name__ == "__main__":
    main()
