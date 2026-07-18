"""Quick direct primitive optimization: 50 iterations per image."""

import sys, os, json, time
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.multimodal.primitives.differentiable_renderer import DifferentiableRenderer
from ai.multimodal.primitives.primitive_types import DrawingInstructions, TOTAL_DIM
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer
from ai.multimodal.evaluation.generation_evaluator import GenerationEvaluator


def main():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "cifar10")
    idx = json.load(open(os.path.join(data_dir, "index.json")))

    images, labels = [], []
    for cls in idx["classes"][:3]:
        cls_dir = os.path.join(data_dir, cls)
        for f in sorted(os.listdir(cls_dir))[:3]:
            if f.endswith(".npy"):
                images.append(np.load(os.path.join(cls_dir, f)))
                labels.append(cls)

    print("Loaded %d images" % len(images), flush=True)

    diff_renderer = DifferentiableRenderer((32, 32))  # Small for speed
    pil_renderer = PrimitiveRenderer((128, 128))
    evaluator = GenerationEvaluator()

    target_arrs = [np.array(Image.fromarray(img).resize((32, 32), Image.LANCZOS),
                            dtype=np.float32) / 255.0 for img in images]

    save_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "samples_direct")
    os.makedirs(save_dir, exist_ok=True)

    print("Optimizing...", flush=True)
    for i in range(len(images)):
        target = target_arrs[i]
        t0 = time.time()

        vec = np.random.uniform(0.2, 0.8, TOTAL_DIM).astype(np.float32)
        vec[0:3] = target.mean(axis=(0, 1))

        for it in range(50):
            eps = 0.02
            probe_dims = np.random.choice(TOTAL_DIM, size=20, replace=False)
            d_vec = np.zeros(TOTAL_DIM, dtype=np.float32)
            for dim in probe_dims:
                vp = vec.copy()
                vp[dim] = min(1.0, vp[dim] + eps)
                vm = vec.copy()
                vm[dim] = max(0.0, vm[dim] - eps)
                d_vec[dim] = (np.mean((diff_renderer.render(vp) - target) ** 2) -
                              np.mean((diff_renderer.render(vm) - target) ** 2)) / (2 * eps)
            vec -= 0.005 * d_vec
            vec = np.clip(vec, 0, 1)

        # Evaluate at 128x128
        rendered_diff = Image.fromarray((diff_renderer.render(vec) * 255).astype(np.uint8)).resize((128, 128), Image.LANCZOS)
        instructions = DrawingInstructions.from_vector(vec)
        rendered_pil = pil_renderer.render(instructions)
        orig = Image.fromarray(images[i]).resize((128, 128), Image.LANCZOS)

        sim_diff = evaluator._clip_image_similarity(rendered_diff, orig)
        sim_pil = evaluator._clip_image_similarity(rendered_pil, orig)

        comp = Image.new("RGB", (384, 128))
        comp.paste(orig, (0, 0))
        comp.paste(rendered_diff, (128, 0))
        comp.paste(rendered_pil, (256, 0))
        comp.save(os.path.join(save_dir, "%02d_%s.png" % (i, labels[i])))

        print("  [%d] %s: diff=%.2f pil=%.2f (%.1fs)" % (i, labels[i], sim_diff, sim_pil, time.time() - t0), flush=True)

    print("Done!", flush=True)


if __name__ == "__main__":
    main()
