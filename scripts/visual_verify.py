"""Visual verification: render images from concept space → primitives → image."""
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
from PIL import Image
from ai.multimodal.primitives.geometric_vocabulary import GeometricVocabulary
from ai.multimodal.primitives.concept_space import ConceptSpaceMapper
from ai.multimodal.primitives.concept_mapper import ConceptMapper
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer
from ai.multimodal.primitives.primitive_types import DrawingInstructions

CLASSES=["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
OUTPUT_DIR="data/multimodal/gvv/visual_test"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load components
    print("Loading vocabulary...")
    vocab = GeometricVocabulary.load("models/geometric_vocabulary.json")
    concept_space = ConceptSpaceMapper.load("models/concept_space.json")
    mapper = ConceptMapper(vocab)
    mapper.set_concept_space(concept_space)

    renderer = PrimitiveRenderer((128, 128))

    # Test 1: Render each class's mean primitive vector
    print("\n=== Test 1: Class mean vectors ===")
    for name, concept in vocab._concept_distributions.items():
        mean_vec = concept.param_means
        instructions = DrawingInstructions.from_vector(mean_vec, canvas_size=(128, 128))
        img = renderer.render(instructions)
        path = os.path.join(OUTPUT_DIR, f"mean_{name}.png")
        img.save(path)
        print(f"  Saved {path}")

    # Test 2: Sample from each class's distribution
    print("\n=== Test 2: Sampled vectors ===")
    for name in CLASSES:
        vec = vocab.initialize_from_concept(name)
        instructions = DrawingInstructions.from_vector(vec, canvas_size=(128, 128))
        img = renderer.render(instructions)
        path = os.path.join(OUTPUT_DIR, f"sample_{name}.png")
        img.save(path)
        print(f"  Saved {path}")

    # Test 3: Random vectors (baseline)
    print("\n=== Test 3: Random vectors ===")
    rng = np.random.default_rng(42)
    for i in range(3):
        vec = rng.uniform(0, 1, 263).astype(np.float32)
        instructions = DrawingInstructions.from_vector(vec, canvas_size=(128, 128))
        img = renderer.render(instructions)
        path = os.path.join(OUTPUT_DIR, f"random_{i}.png")
        img.save(path)
        print(f"  Saved {path}")

    # Test 4: Load actual CIFAR-10 images for comparison
    print("\n=== Test 4: Actual CIFAR-10 images ===")
    import glob
    cifar_dir="D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
    for ci, cls in enumerate(CLASSES):
        cls_dir = os.path.join(cifar_dir, cls)
        files = sorted(glob.glob(os.path.join(cls_dir, "*.npy")))[:3]
        for fi, f in enumerate(files):
            arr = np.load(f)
            if arr.shape == (3072,):
                arr = arr.reshape(3, 32, 32).transpose(1, 2, 0)
            elif arr.shape == (3, 32, 32):
                arr = arr.transpose(1, 2, 0)
            pil_img = Image.fromarray(arr).resize((128, 128), Image.LANCZOS)
            path = os.path.join(OUTPUT_DIR, f"real_{cls}_{fi}.png")
            pil_img.save(path)
        print(f"  Saved 3 {cls} images")

    print(f"\nAll images saved to {OUTPUT_DIR}/")
    print("Visual inspection needed to assess quality.")


if __name__ == "__main__":
    main()
