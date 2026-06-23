"""Test recognition with more optimization iterations (better feature extraction)."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
import glob
from PIL import Image
from ai.multimodal.primitives.differentiable_renderer import DifferentiableRenderer
from ai.multimodal.primitives.primitive_types import TOTAL_DIM
from ai.multimodal.primitives.geometric_vocabulary import GeometricVocabulary
from ai.multimodal.recognition.geometric_recognizer import GeometricRecognizer

CIFAR_DIR = "D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]


def load_test_images(n_per_class=10, skip_first=50):
    images = []
    labels = []
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


def optimize_one(target, renderer, n_iters=30, n_probes=15):
    vec = np.random.uniform(0.2, 0.8, TOTAL_DIM).astype(np.float32)
    vec[0:3] = target.mean(axis=(0, 1))
    best_vec = vec.copy()
    best_loss = float('inf')
    eps = 0.015

    for it in range(n_iters):
        rendered = renderer.render(vec)
        loss = float(np.mean((rendered - target) ** 2))
        if loss < best_loss:
            best_loss = loss
            best_vec = vec.copy()
        d_vec = np.zeros(TOTAL_DIM, dtype=np.float32)
        probe_dims = np.random.choice(TOTAL_DIM, size=n_probes, replace=False)
        for dim in probe_dims:
            v_plus = vec.copy()
            v_plus[dim] = min(1.0, v_plus[dim] + eps)
            r_plus = renderer.render(v_plus)
            l_plus = np.mean((r_plus - target) ** 2)
            v_minus = vec.copy()
            v_minus[dim] = max(0.0, v_minus[dim] - eps)
            r_minus = renderer.render(v_minus)
            l_minus = np.mean((r_minus - target) ** 2)
            d_vec[dim] = (l_plus - l_minus) / (2 * eps)
        vec -= 0.008 * d_vec
        vec = np.clip(vec, 0, 1)
    return best_vec, best_loss


def main():
    print("Loading held-out test images...")
    images, labels = load_test_images(n_per_class=10, skip_first=50)
    print(f"Loaded {len(images)} images")

    vocab = GeometricVocabulary.load("models/geometric_vocabulary.json")
    recognizer = GeometricRecognizer(vocab)

    # Test with different iteration counts
    for n_iters in [30, 50]:
        print(f"\n=== Recognition with {n_iters} optimization iterations ===")
        renderer = DifferentiableRenderer((128, 128))
        correct = 0
        per_class = {c: [0, 0] for c in CLASSES}
        t_start = time.time()

        for i in range(len(images)):
            opt_vec, opt_loss = optimize_one(images[i], renderer, n_iters=n_iters, n_probes=15)
            result = recognizer.recognize_from_vector(opt_vec)
            pred = result["predicted_class"]
            actual = CLASSES[labels[i]]
            per_class[actual][1] += 1
            if pred == actual:
                correct += 1
                per_class[actual][0] += 1
            if (i + 1) % 10 == 0:
                print(f"  [{i+1}/{len(images)}] running_acc={correct/(i+1):.1%} avg_loss={opt_loss:.4f}")

        acc = correct / len(images)
        elapsed = time.time() - t_start
        print(f"Overall: {correct}/{len(images)} = {acc:.1%} ({elapsed:.0f}s, {elapsed/len(images):.1f}s/img)")
        for cls in CLASSES:
            c, t = per_class[cls]
            print(f"  {cls:12s}: {c}/{t} = {c/t:.1%}" if t > 0 else f"  {cls}: 0")


if __name__ == "__main__":
    main()
