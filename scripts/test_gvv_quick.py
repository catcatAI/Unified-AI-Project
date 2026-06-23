"""
Quick GVV test: build vocabulary + test generation + test recognition.

Uses existing optimized vectors (50 images) to avoid re-optimizing.
"""
import sys
import os
import time
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
from PIL import Image

from ai.multimodal.primitives.geometric_vocabulary import GeometricVocabulary
from ai.multimodal.primitives.concept_mapper import ConceptMapper
from ai.multimodal.primitives.instance_optimizer import InstanceOptimizer
from ai.multimodal.recognition.geometric_recognizer import GeometricRecognizer
from ai.multimodal.primitives.primitive_types import DrawingInstructions, TOTAL_DIM
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer

CIFAR_DIR = "D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES = ["airplane", "automobile", "bird", "cat", "deer",
           "dog", "frog", "horse", "ship", "truck"]
MODEL_DIR = "D:/Projects/Unified-AI-Project/models"
DATA_DIR = "D:/Projects/Unified-AI-Project/data/multimodal/gvv"
CANVAS_SIZE = (128, 128)


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "gen"), exist_ok=True)

    # 1. Load existing optimized vectors
    print("Loading existing optimized vectors...")
    opt_vecs = np.load(os.path.join(CIFAR_DIR, "optimized_vectors.npy"))
    opt_labels = np.load(os.path.join(CIFAR_DIR, "optimized_labels.npy"))
    print(f"Loaded {len(opt_vecs)} vectors, {len(opt_labels)} labels")

    # 2. Build vocabulary
    print("\n=== Building Vocabulary ===")
    t0 = time.time()
    vocab = GeometricVocabulary(n_visual_words=10)
    vocab.build_from_optimized(opt_vecs, opt_labels, CLASSES)
    print(f"Vocabulary built in {time.time()-t0:.1f}s")
    print(f"  {len(vocab.get_visual_words())} visual words")
    for name, dist in vocab._concept_distributions.items():
        print(f"  {name}: {dist.n_images} images, {len(dist.visual_word_ids)} words used")

    # Save vocabulary
    vocab.save(os.path.join(MODEL_DIR, "geometric_vocabulary.json"))

    # 3. Build concept mapper (with dummy CLIP embeddings for now)
    print("\n=== Building Concept Mapper ===")
    mapper = ConceptMapper(vocab)
    # Register dummy embeddings — in production, encode concept names with CLIP
    rng = np.random.default_rng(42)
    for cls in CLASSES:
        # Use random but fixed embeddings for testing
        emb = rng.random(512).astype(np.float32)
        mapper.register_concept_embedding(cls, emb)
    mapper.save(os.path.join(MODEL_DIR, "concept_mapper.json"))

    # 4. Quick generation test
    print("\n=== Quick Generation Test ===")
    pil_renderer = PrimitiveRenderer(CANVAS_SIZE)
    gen_similarities = []

    for i in range(min(5, len(opt_vecs))):
        concept_name = CLASSES[opt_labels[i]]
        init_vec = vocab.initialize_from_concept(concept_name)

        # Render the initialized vector
        instructions = DrawingInstructions.from_vector(init_vec, CANVAS_SIZE)
        rendered = pil_renderer.render(instructions)

        # Render the optimized vector
        instructions_opt = DrawingInstructions.from_vector(opt_vecs[i], CANVAS_SIZE)
        rendered_opt = pil_renderer.render(instructions_opt)

        # Compare
        r_arr = np.array(rendered, dtype=np.float32).flatten()
        o_arr = np.array(rendered_opt, dtype=np.float32).flatten()
        cos_sim = float(np.dot(r_arr, o_arr) / (np.linalg.norm(r_arr) * np.linalg.norm(o_arr) + 1e-8))
        gen_similarities.append(cos_sim)

        # Save
        comp = Image.new("RGB", (256, 128))
        comp.paste(rendered, (0, 0))
        comp.paste(rendered_opt, (128, 0))
        comp.save(os.path.join(DATA_DIR, "gen", f"{i:02d}_{concept_name}.png"))

        print(f"  [{i}] {concept_name}: init→opt cos_sim={cos_sim:.4f}")

    print(f"Average generation similarity (init vs optimized): {np.mean(gen_similarities):.4f}")

    # 5. Quick recognition test
    print("\n=== Quick Recognition Test ===")
    recognizer = GeometricRecognizer(vocab, canvas_size=CANVAS_SIZE)

    correct = 0
    for i in range(min(20, len(opt_vecs))):
        # Use recognize_from_vector (direct, no re-optimization)
        result = recognizer.recognize_from_vector(opt_vecs[i])
        actual = CLASSES[opt_labels[i]]
        match = "✓" if result['predicted_class'] == actual else "✗"
        if result['predicted_class'] == actual:
            correct += 1
        if i < 10:
            print(f"  [{i}] {actual} → {result['predicted_class']} conf={result['confidence']:.3f} {match}")

    n_eval = min(20, len(opt_vecs))
    print(f"Recognition accuracy: {correct}/{n_eval} = {correct/n_eval:.0%}")

    # 6. Summary
    print("\n=== Summary ===")
    print(f"Vocabulary: {len(vocab.get_visual_words())} visual words, {len(vocab._concept_distributions)} concepts")
    print(f"Average init→opt similarity: {np.mean(gen_similarities):.4f}")

    results = {
        "n_visual_words": len(vocab.get_visual_words()),
        "n_concepts": len(vocab._concept_distributions),
        "avg_init_opt_similarity": float(np.mean(gen_similarities)),
    }
    with open(os.path.join(DATA_DIR, "results.json"), "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {DATA_DIR}/results.json")


if __name__ == "__main__":
    main()
