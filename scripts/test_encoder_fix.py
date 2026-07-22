"""Quick test: verify encoder fix (b_decode initialization)."""
import sys
import os
import json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.multimodal.primitives.primitive_types import DrawingInstructions, Point, Line, Plane
from ai.multimodal.primitives.primitive_encoder import PrimitiveEncoder
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer
from ai.multimodal.evaluation.generation_evaluator import GenerationEvaluator


def decompose(img_arr):
    arr = img_arr.astype(np.float32)
    h, w = arr.shape[:2]
    q = (arr / 64).astype(int)
    q = np.clip(q, 0, 3)
    counts={}
    for p in q.reshape(-1, 3):
        key = (int(p[0]), int(p[1]), int(p[2]))
        counts[key] = counts.get(key, 0) + 1
    dom = max(counts.items(), key=lambda x: x[1])[0]
    dom_color = tuple(max(0, min(255, int(c * 64 + 32))) for c in dom)

    gray = arr.mean(axis=2)
    coords = np.argwhere(gray > gray.mean() + gray.std())
    points=[]
    if len(coords) > 0:
        step = max(1, len(coords) // 5)
        for y, x in coords[::step][:5]:
            r, g, b = int(arr[y, x, 0]), int(arr[y, x, 1]), int(arr[y, x, 2])
            points.append(Point(float(x)/w, float(y)/h, (r, g, b), 0.06))

    planes=[Plane(
        [Point(0,0,(0,0,0),0), Point(1,0,(0,0,0),0), Point(1,1,(0,0,0),0), Point(0,1,(0,0,0),0)],
        dom_color, (0,0,0), 0.0
    )]
    return DrawingInstructions(points=points, planes=planes, background_color=dom_color)


def main():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "cifar10")
    idx = json.load(open(os.path.join(data_dir, "index.json")))

    images, labels=[], []
    for cls in idx["classes"][:5]:
        cls_dir = os.path.join(data_dir, cls)
        for f in sorted(os.listdir(cls_dir))[:4]:
            if f.endswith(".npy"):
                images.append(np.load(os.path.join(cls_dir, f)))
                labels.append(cls)

    print(f"Loaded {len(images)} images from {len(set(labels))} classes")

    instructions=[decompose(img) for img in images]

    print("Training PrimitiveEncoder (150 epochs, lr=0.002)...")
    encoder = PrimitiveEncoder()
    result = encoder.train(instructions, epochs=150, lr=0.002)
    print(f"  Best loss: {result['best_loss']:.6f} ({result['epochs_trained']} epochs)")

    renderer = PrimitiveRenderer((128, 128))
    evaluator = GenerationEvaluator()

    print("\nDecode quality:")
    for i in range(5):
        emb = encoder.encode(instructions[i])
        decoded = encoder.decode(emb)
        orig = renderer.render(instructions[i])
        dec = renderer.render(decoded)
        orig_m = evaluator.evaluate(orig)
        dec_m = evaluator.evaluate(dec)
        print(f"  [{i}] {labels[i]}: "
              f"brightness {orig_m['mean_brightness']:.2f} -> {dec_m['mean_brightness']:.2f}, "
              f"colors {orig_m['color_coverage']:.2f} -> {dec_m['color_coverage']:.2f}, "
              f"edges {orig_m['edge_density']:.2f} -> {dec_m['edge_density']:.2f}")


if __name__ == "__main__":
    main()
