"""Scale vocabulary: optimize 500 CIFAR-10 images, build vocabulary, test recognition."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
import glob
from PIL import Image
from ai.multimodal.primitives.differentiable_renderer import DifferentiableRenderer
from ai.multimodal.primitives.primitive_types import DrawingInstructions, TOTAL_DIM
from ai.multimodal.primitives.geometric_vocabulary import GeometricVocabulary
from ai.multimodal.recognition.geometric_recognizer import GeometricRecognizer

CIFAR_DIR = "D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
N_ITERS = 12
LR = 0.008
N_PROBES = 8


def load_images_per_class(n_per_class=50):
    images = []
    labels = []
    for ci, cls in enumerate(CLASSES):
        cls_dir = os.path.join(CIFAR_DIR, cls)
        files = sorted(glob.glob(os.path.join(cls_dir, "*.npy")))[:n_per_class]
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


def optimize_one(target, renderer):
    vec = np.random.uniform(0.2, 0.8, TOTAL_DIM).astype(np.float32)
    vec[0:3] = target.mean(axis=(0, 1))
    best_vec = vec.copy()
    best_loss = float('inf')
    eps = 0.015

    for it in range(N_ITERS):
        rendered = renderer.render(vec)
        loss = float(np.mean((rendered - target) ** 2))
        if loss < best_loss:
            best_loss = loss
            best_vec = vec.copy()

        d_vec = np.zeros(TOTAL_DIM, dtype=np.float32)
        probe_dims = np.random.choice(TOTAL_DIM, size=N_PROBES, replace=False)
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
        vec -= LR * d_vec
        vec = np.clip(vec, 0, 1)

    return best_vec, best_loss


def main():
    n_per_class = 50
    total = n_per_class * 10
    print(f"Loading {total} CIFAR-10 images ({n_per_class}/class)...")
    images, labels = load_images_per_class(n_per_class)
    print(f"Loaded {len(images)} images")

    renderer = DifferentiableRenderer((128, 128))
    optimized_vecs = []
    losses = []
    t_start = time.time()

    for i in range(len(images)):
        t0 = time.time()
        opt_vec, opt_loss = optimize_one(images[i], renderer)
        optimized_vecs.append(opt_vec)
        losses.append(opt_loss)
        elapsed = time.time() - t0
        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(images)}] loss={opt_loss:.4f} ({elapsed:.1f}s/img, total={time.time()-t_start:.0f}s)")

    # Save optimized vectors
    np.save(os.path.join(CIFAR_DIR, "optimized_vectors.npy"), np.array(optimized_vecs))
    np.save(os.path.join(CIFAR_DIR, "optimized_labels.npy"), np.array(labels))
    print(f"\nSaved {len(optimized_vecs)} vectors, avg loss={np.mean(losses):.4f}")

    # Build vocabulary
    print("\nBuilding vocabulary...")
    from ai.multimodal.primitives.geometric_vocabulary import GeometricVocabulary
    vocab = GeometricVocabulary()
    class_names = [CLASSES[l] for l in labels]
    params_array = np.array(optimized_vecs, dtype=np.float32)
    vocab.build_from_optimized(params_array, class_names)
    vocab.save("models/geometric_vocabulary.json")
    print(f"Vocabulary: {len(vocab._visual_words)} words, {len(vocab._concept_distributions)} concepts")

    # Test recognition
    print("\nTesting recognition...")
    recognizer = GeometricRecognizer(vocab)
    correct = 0
    for i in range(len(images)):
        result = recognizer.recognize(images[i], n_iterations=5)
        if result["predicted_class"] == CLASSES[labels[i]]:
            correct += 1
    acc = correct / len(images)
    print(f"Recognition accuracy: {correct}/{len(images)} = {acc:.1%}")
    print(f"Total time: {time.time()-t_start:.0f}s")


if __name__ == "__main__":
    main()
