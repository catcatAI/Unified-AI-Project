"""Rebuild vocabulary with 50 visual words and test recognition."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
from ai.multimodal.primitives.geometric_vocabulary import GeometricVocabulary
from ai.multimodal.recognition.geometric_recognizer import GeometricRecognizer

CIFAR_DIR = "D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]

def main():
    vectors = np.load(os.path.join(CIFAR_DIR, "optimized_vectors.npy"))
    labels = np.load(os.path.join(CIFAR_DIR, "optimized_labels.npy"))
    print(f"Loaded {len(vectors)} vectors, shape={vectors.shape}")

    # Build vocabulary with 50 visual words
    print("\nBuilding vocabulary (50 words)...")
    t0 = time.time()
    vocab = GeometricVocabulary(n_visual_words=50)
    vocab.build_from_optimized(vectors, labels)
    print(f"Vocabulary built in {time.time()-t0:.1f}s: {len(vocab._visual_words)} words, {len(vocab._concept_distributions)} concepts")

    vocab.save("models/geometric_vocabulary.json")
    print("Saved to models/geometric_vocabulary.json")

    # Test recognition
    print("\nTesting recognition...")
    recognizer = GeometricRecognizer(vocab)
    correct = 0
    per_class = {c: [0, 0] for c in CLASSES}
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
