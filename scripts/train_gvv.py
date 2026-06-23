"""
End-to-end training and evaluation of Geometric Visual Vocabulary (GVV).

Phase 6-9: Build vocabulary, train concept mapper, test generation + recognition.

Usage: python scripts/train_gvv.py
"""
import sys
import os
import time
import json
import glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
from PIL import Image

from ai.multimodal.primitives.geometric_vocabulary import GeometricVocabulary
from ai.multimodal.primitives.concept_mapper import ConceptMapper
from ai.multimodal.primitives.instance_optimizer import InstanceOptimizer
from ai.multimodal.recognition.geometric_recognizer import GeometricRecognizer
from ai.multimodal.primitives.differentiable_renderer import DifferentiableRenderer
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer
from ai.multimodal.primitives.primitive_types import DrawingInstructions, TOTAL_DIM

CIFAR_DIR = "D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES = ["airplane", "automobile", "bird", "cat", "deer",
           "dog", "frog", "horse", "ship", "truck"]
MODEL_DIR = "D:/Projects/Unified-AI-Project/models"
DATA_DIR = "D:/Projects/Unified-AI-Project/data/multimodal/gvv"
CANVAS_SIZE = (128, 128)


def load_cifar_images(n_per_class=10):
    """Load n images per class from CIFAR-10."""
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
            pil = Image.fromarray(arr).resize(CANVAS_SIZE, Image.LANCZOS)
            images.append(np.array(pil, dtype=np.float32) / 255.0)
            labels.append(ci)
    return np.array(images), np.array(labels)


def optimize_all_images(images, labels, n_iterations=20):
    """Batch optimize all images to get primitive vectors."""
    # Check if we already have optimized vectors
    existing_path = os.path.join(CIFAR_DIR, "optimized_vectors.npy")
    existing_labels = os.path.join(CIFAR_DIR, "optimized_labels.npy")
    if os.path.exists(existing_path) and os.path.exists(existing_labels):
        print("Loading existing optimized vectors...")
        opt_vecs = np.load(existing_path)
        opt_labels = np.load(existing_labels)
        print(f"  Loaded {len(opt_vecs)} vectors (labels: {len(opt_labels)})")
        return opt_vecs, opt_labels

    renderer = DifferentiableRenderer(CANVAS_SIZE)
    optimized = []

    print(f"Optimizing {len(images)} images ({n_iterations} iterations each)...")
    t0 = time.time()

    for i in range(len(images)):
        img = images[i]
        vec = np.full(TOTAL_DIM, 0.5, dtype=np.float32)
        vec[0:3] = img.mean(axis=(0, 1))

        # Pixel MSE optimization
        best_vec = vec.copy()
        best_loss = float('inf')
        eps = 0.015
        n_probes = 8

        for it in range(n_iterations):
            rendered = renderer.render(vec)
            loss = float(np.mean((rendered - img) ** 2))

            if loss < best_loss:
                best_loss = loss
                best_vec = vec.copy()

            d_vec = np.zeros(TOTAL_DIM, dtype=np.float32)
            probe_dims = np.random.choice(TOTAL_DIM, size=n_probes, replace=False)
            for dim in probe_dims:
                v_plus = vec.copy()
                v_plus[dim] = min(1.0, v_plus[dim] + eps)
                r_plus = renderer.render(v_plus)
                l_plus = float(np.mean((r_plus - img) ** 2))

                v_minus = vec.copy()
                v_minus[dim] = max(0.0, v_minus[dim] - eps)
                r_minus = renderer.render(v_minus)
                l_minus = float(np.mean((r_minus - img) ** 2))

                d_vec[dim] = (l_plus - l_minus) / (2 * eps)

            vec -= 0.008 * d_vec
            vec = np.clip(vec, 0, 1)

        optimized.append(best_vec)

        if (i + 1) % 10 == 0:
            elapsed = time.time() - t0
            print(f"  [{i+1}/{len(images)}] loss={best_loss:.4f} ({elapsed:.0f}s)")

    print(f"Optimization done ({time.time()-t0:.0f}s)")
    return np.array(optimized), labels


def build_concept_embeddings():
    """Build CLIP embeddings for concept names."""
    try:
        from ai.multimodal.semantic_visual import SemanticVisualEncoder
        encoder = SemanticVisualEncoder()
    except Exception:
        print("CLIP unavailable, using random embeddings for concepts")
        rng = np.random.default_rng(42)
        return {cls: rng.random(512).astype(np.float32) for cls in CLASSES}

    embeddings = {}
    for cls in CLASSES:
        import io
        # Create a simple image with the concept name
        # For now, use a placeholder — in production, encode the text
        # CLIP text encoding requires tokenizer, which may not be available
        embeddings[cls] = np.zeros(512, dtype=np.float32)

    return embeddings


def evaluate_generation(optimizer, concept_mapper, images, labels, n_eval=10):
    """Evaluate text-to-image generation."""
    print("\n=== Generation Evaluation ===")
    pil_renderer = PrimitiveRenderer(CANVAS_SIZE)

    sims = []
    for i in range(min(n_eval, len(images))):
        # Generate from concept
        concept_name = CLASSES[labels[i]]
        concept = optimizer._vocabulary.get_concept(concept_name)

        if concept is None:
            continue

        # Initialize from concept
        init_vec = optimizer._vocabulary.initialize_from_concept(concept_name)

        # Optimize for this specific image
        result = optimizer.optimize_for_image(
            images[i], concept_name=concept_name,
            n_iterations=20, verbose=False
        )

        # Compute pixel similarity
        rendered_arr = np.array(result["rendered"], dtype=np.float32) / 255.0
        orig_arr = images[i]
        mse = float(np.mean((rendered_arr - orig_arr) ** 2))
        cos_sim = float(np.dot(rendered_arr.flatten(), orig_arr.flatten()) /
                        (np.linalg.norm(rendered_arr.flatten()) * np.linalg.norm(orig_arr.flatten()) + 1e-8))

        sims.append(cos_sim)

        # Save comparison
        comp = Image.new("RGB", (256, 128))
        orig_pil = Image.fromarray((orig_arr * 255).astype(np.uint8))
        comp.paste(orig_pil, (0, 0))
        comp.paste(result["rendered"], (128, 0))
        comp.save(os.path.join(DATA_DIR, "gen", f"{i:02d}_{concept_name}_sim{cos_sim:.3f}.png"))

        if (i + 1) % 5 == 0:
            print(f"  [{i+1}/{n_eval}] concept={concept_name} cos_sim={cos_sim:.4f} mse={mse:.4f}")

    print(f"Average generation cosine similarity: {np.mean(sims):.4f}")
    return np.mean(sims)


def evaluate_recognition(recognizer, images, labels, n_eval=20):
    """Evaluate image recognition."""
    print("\n=== Recognition Evaluation ===")

    correct = 0
    total = min(n_eval, len(images))

    for i in range(total):
        result = recognizer.recognize(images[i], n_iterations=10)
        predicted = result["predicted_class"]
        actual = CLASSES[labels[i]]

        if predicted == actual:
            correct += 1

        if (i + 1) % 5 == 0:
            print(f"  [{i+1}/{total}] actual={actual} predicted={predicted} "
                  f"conf={result['confidence']:.3f}")

    accuracy = correct / total
    print(f"Recognition accuracy: {correct}/{total} = {accuracy:.2%}")
    return accuracy


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "gen"), exist_ok=True)

    # 1. Load images
    print("Loading CIFAR-10 images...")
    images, labels = load_cifar_images(n_per_class=10)
    print(f"Loaded {len(images)} images ({len(CLASSES)} classes)")

    # 2. Optimize all images
    optimized, used_labels = optimize_all_images(images, labels, n_iterations=20)

    # Save optimized vectors
    np.save(os.path.join(DATA_DIR, "optimized_vectors.npy"), optimized)
    np.save(os.path.join(DATA_DIR, "optimized_labels.npy"), used_labels)

    # 3. Build vocabulary
    print("\nBuilding geometric vocabulary...")
    vocab = GeometricVocabulary(n_visual_words=20)
    vocab.build_from_optimized(optimized, used_labels, CLASSES)
    vocab.save(os.path.join(MODEL_DIR, "geometric_vocabulary.json"))

    # 4. Build concept mapper
    print("\nBuilding concept mapper...")
    concept_embeddings = build_concept_embeddings()
    mapper = ConceptMapper(vocab)
    for cls, emb in concept_embeddings.items():
        mapper.register_concept_embedding(cls, emb)
    mapper.save(os.path.join(MODEL_DIR, "concept_mapper.json"))

    # 5. Create optimizer and recognizer
    optimizer = InstanceOptimizer(vocab, mapper, CANVAS_SIZE)
    recognizer = GeometricRecognizer(vocab, canvas_size=CANVAS_SIZE)

    # 6. Evaluate generation
    gen_sim = evaluate_generation(optimizer, mapper, images, labels, n_eval=10)

    # 7. Evaluate recognition
    rec_acc = evaluate_recognition(recognizer, images, labels, n_eval=20)

    # 8. Summary
    print("\n=== Summary ===")
    print(f"Vocabulary: {len(vocab.get_visual_words())} visual words, "
          f"{len(vocab._concept_distributions)} concepts")
    print(f"Generation cosine similarity: {gen_sim:.4f}")
    print(f"Recognition accuracy: {rec_acc:.2%}")

    # Save results
    results = {
        "n_visual_words": len(vocab.get_visual_words()),
        "n_concepts": len(vocab._concept_distributions),
        "generation_cos_sim": float(gen_sim),
        "recognition_accuracy": float(rec_acc),
    }
    with open(os.path.join(DATA_DIR, "results.json"), "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {DATA_DIR}/results.json")
    print(f"Generated images in {DATA_DIR}/gen/")


if __name__ == "__main__":
    main()
