"""Test recognition WITHOUT per-image optimization — use raw image features."""
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
import glob
from PIL import Image
from ai.multimodal.primitives.geometric_vocabulary import GeometricVocabulary

CIFAR_DIR="D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES=["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]


def load_test_images(n_per_class=10, skip_first=50):
    images=[]
    labels=[]
    for ci, cls in enumerate(CLASSES):
        cls_dir = os.path.join(CIFAR_DIR, cls)
        files = sorted(glob.glob(os.path.join(cls_dir, "*.npy")))[skip_first:skip_first+n_per_class]
        for f in files:
            arr = np.load(f)
            if arr.shape == (3072,):
                arr = arr.reshape(3, 32, 32).transpose(1, 2, 0)
            elif arr.shape == (3, 32, 32):
                arr = arr.transpose(1, 2, 0)
            pil_img = Image.fromarray(arr).resize((128, 128), Image.LANCZOS)
            arr = np.array(pil_img, dtype=np.float32) / 255.0
            images.append(arr)
            labels.append(ci)
    return images, labels


def recognize_by_matching(image, vocab):
    """Recognize by finding concept whose distribution best explains the image."""
    img_flat = image.flatten()
    best_class=None
    best_score = -float('inf')

    for name, concept in vocab._concept_distributions.items():
        # Compare image statistics to concept distribution
        # Use concept param_means as a template
        mean = concept.param_means
        std = concept.param_stds + 1e-8

        # Z-score: how well does the image fit this concept's distribution?
        z = (img_flat[:len(mean)] - mean[:len(img_flat)]) / std[:len(img_flat)]
        score = -float(np.mean(z ** 2))  # negative MSE (higher = better fit)

        if score > best_score:
            best_score = score
            best_class = name

    return best_class, best_score


def main():
    print("Loading held-out test images...")
    images, labels = load_test_images(n_per_class=10, skip_first=50)
    print(f"Loaded {len(images)} images")

    vocab = GeometricVocabulary.load("models/geometric_vocabulary.json")

    # Method 1: Direct image-to-concept matching
    print("\n=== Method 1: Direct image-to-concept matching ===")
    correct=0
    per_class={c: [0, 0] for c in CLASSES}
    for i in range(len(images)):
        pred, score = recognize_by_matching(images[i], vocab)
        actual = CLASSES[labels[i]]
        per_class[actual][1] += 1
        if pred == actual:
            correct += 1
            per_class[actual][0] += 1
    acc = correct / len(images)
    print(f"Overall: {correct}/{len(images)} = {acc:.1%}")
    for cls in CLASSES:
        c, t = per_class[cls]
        print(f"  {cls:12s}: {c}/{t} = {c/t:.1%}" if t > 0 else f"  {cls}: 0")

    # Method 2: Color histogram matching (simple baseline)
    print("\n=== Method 2: Color histogram matching ===")
    correct=0
    per_class={c: [0, 0] for c in CLASSES}
    for i in range(len(images)):
        img = images[i]
        # Compute color histogram
        hist_r = np.histogram(img[:,:,0], bins=8, range=(0,1))[0]
        hist_g = np.histogram(img[:,:,1], bins=8, range=(0,1))[0]
        hist_b = np.histogram(img[:,:,2], bins=8, range=(0,1))[0]
        hist = np.concatenate([hist_r, hist_g, hist_b]).astype(float)
        hist = hist / (hist.sum() + 1e-8)

        best_class=None
        best_sim = -1
        for name, concept in vocab._concept_distributions.items():
            # Use concept param_means as a rough color template
            # Just compare first 24 dims (8 bins x 3 channels)
            concept_hist = concept.param_means[:24]
            concept_hist = np.abs(concept_hist) / (np.abs(concept_hist).sum() + 1e-8)
            sim = float(np.dot(hist, concept_hist))
            if sim > best_sim:
                best_sim = sim
                best_class = name

        actual = CLASSES[labels[i]]
        per_class[actual][1] += 1
        if best_class == actual:
            correct += 1
            per_class[actual][0] += 1
    acc = correct / len(images)
    print(f"Overall: {correct}/{len(images)} = {acc:.1%}")
    for cls in CLASSES:
        c, t = per_class[cls]
        print(f"  {cls:12s}: {c}/{t} = {c/t:.1%}" if t > 0 else f"  {cls}: 0")


if __name__ == "__main__":
    main()
