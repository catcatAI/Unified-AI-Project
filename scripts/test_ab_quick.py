"""Quick A→B test: enhanced decomposer + PixelRefiner (no generator)."""
import sys, os, json
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.multimodal.primitives.decomposer import decompose_enhanced
from ai.multimodal.primitives.primitive_encoder import PrimitiveEncoder
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer
from ai.multimodal.primitives.pixel_refiner import PixelRefiner
from ai.multimodal.evaluation.generation_evaluator import GenerationEvaluator


def main():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "cifar10")
    idx = json.load(open(os.path.join(data_dir, "index.json")))

    images, labels = [], []
    for cls in idx["classes"][:5]:
        cls_dir = os.path.join(data_dir, cls)
        for f in sorted(os.listdir(cls_dir))[:4]:
            if f.endswith(".npy"):
                images.append(np.load(os.path.join(cls_dir, f)))
                labels.append(cls)

    print(f"Loaded {len(images)} images")

    # 1. Decompose
    instructions = [decompose_enhanced(img) for img in images]

    # 2. Train encoder
    encoder = PrimitiveEncoder()
    encoder.train(instructions, epochs=200, lr=0.002)

    # 3. Generate rough images (direct encode→decode, no generator)
    renderer = PrimitiveRenderer((128, 128))
    rough_images = []
    for i in range(len(images)):
        enc = encoder.encode(instructions[i])
        decoded = encoder.decode(enc)
        rough = renderer.render(decoded)
        rough_images.append(rough)

    # 4. Train PixelRefiner
    target_images = [Image.fromarray(img).resize((128, 128), Image.LANCZOS) for img in images]
    refiner = PixelRefiner(hidden_dim=1024, img_size=128)
    result = refiner.train(rough_images, target_images, epochs=50, lr=0.005, batch_size=8)
    print(f"Refiner loss: {result['final_loss']:.6f}")

    # 5. Evaluate
    evaluator = GenerationEvaluator()
    save_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "samples_ab")
    os.makedirs(save_dir, exist_ok=True)

    for i in range(min(10, len(images))):
        rough = rough_images[i]
        refined = refiner.refine(rough)
        orig = target_images[i]

        rough_m = evaluator.evaluate(rough)
        refined_m = evaluator.evaluate(refined)
        orig_m = evaluator.evaluate(orig)
        rough_sim = evaluator._clip_image_similarity(rough, orig)
        refined_sim = evaluator._clip_image_similarity(refined, orig)

        comparison = Image.new("RGB", (384, 128))
        comparison.paste(orig, (0, 0))
        comparison.paste(rough, (128, 0))
        comparison.paste(refined, (256, 0))
        comparison.save(os.path.join(save_dir, f"{i:02d}_{labels[i]}.png"))

        print(f"  [{i}] {labels[i]}: "
              f"A_bright={rough_m['mean_brightness']:.2f} B_bright={refined_m['mean_brightness']:.2f} orig={orig_m['mean_brightness']:.2f} | "
              f"A_sim={rough_sim:.2f} B_sim={refined_sim:.2f}")

    # Save
    model_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "weights")
    os.makedirs(model_dir, exist_ok=True)
    encoder.save(os.path.join(model_dir, "primitive_encoder.json"))
    refiner.save(os.path.join(model_dir, "pixel_refiner.json"))
    print(f"\nSaved to {model_dir}")


if __name__ == "__main__":
    main()
