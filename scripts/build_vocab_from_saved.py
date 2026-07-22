"""Build vocabulary from saved optimized vectors and test recognition."""
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
from ai.multimodal.primitives.geometric_vocabulary import GeometricVocabulary
from ai.multimodal.recognition.geometric_recognizer import GeometricRecognizer

CIFAR_DIR="D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES=["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]

def main():
    vectors = np.load(os.path.join(CIFAR_DIR, "optimized_vectors.npy"))
    labels = np.load(os.path.join(CIFAR_DIR, "optimized_labels.npy"))
    print(f"Loaded {len(vectors)} vectors, shape={vectors.shape}, labels={len(labels)}")

    # Build vocabulary
    print("\nBuilding vocabulary...")
    t0 = time.time()
    vocab = GeometricVocabulary()
    params_array = vectors.astype(np.float32)
    labels_array = labels.astype(int)
    vocab.build_from_optimized(params_array, labels_array)
    print(f"Vocabulary built in {time.time()-t0:.1f}s: {len(vocab._visual_words)} words, {len(vocab._concept_distributions)} concepts")

    # Save vocabulary
    os.makedirs("models", exist_ok=True)
    vocab.save("models/geometric_vocabulary.json")
    print("Saved to models/geometric_vocabulary.json")

    # Test recognition (all 500 vectors — no optimization needed, just match)
    print("\nTesting recognition (direct vector match)...")
    recognizer = GeometricRecognizer(vocab)
    correct=0
    per_class={c: [0, 0] for c in CLASSES}
    for i in range(len(vectors)):
        result = recognizer.recognize_from_vector(vectors[i])
        pred = result["predicted_class"]
        actual = CLASSES[int(labels[i])]
        per_class[actual][1] += 1
        if pred == actual:
            correct += 1
            per_class[actual][0] += 1
    acc = correct / len(vectors)
    print(f"\nOverall: {correct}/{len(vectors)} = {acc:.1%}")
    print("\nPer-class:")
    for cls in CLASSES:
        c, t = per_class[cls]
        print(f"  {cls:12s}: {c}/{t} = {c/t:.1%}" if t > 0 else f"  {cls}: 0")


if __name__ == "__main__":
    main()
