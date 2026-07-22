"""Test A→B pipeline: enhanced decomposer + PixelRefiner.
DEPRECATED: This script uses the OLD architecture.
For GVV architecture, see test_gvv_quick.py
"""
import sys
import os
import json
import time
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.multimodal.primitives.decomposer import decompose_spatial as decompose_enhanced
from ai.multimodal.primitives.primitive_encoder import PrimitiveEncoder
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer
try:
    from ai.multimodal.primitives.pixel_refiner import PixelRefiner
except ImportError:
    PixelRefiner=None
try:
    from ai.multimodal.generator.sequence_generator import SequenceGenerator
except ImportError:
    SequenceGenerator=None
from ai.multimodal.evaluation.generation_evaluator import GenerationEvaluator


def main():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "cifar10")
    idx = json.load(open(os.path.join(data_dir, "index.json")))

    images, labels=[], []
    for cls in idx["classes"][:4]:
        cls_dir = os.path.join(data_dir, cls)
        for f in sorted(os.listdir(cls_dir))[:2]:
            if f.endswith(".npy"):
                images.append(np.load(os.path.join(cls_dir, f)))
                labels.append(cls)

    print(f"Loaded {len(images)} images")

    # 1. Decompose with enhanced decomposer
    print("\n[1] Enhanced decomposition...")
    instructions=[decompose_enhanced(img) for img in images]
    for i in range(3):
        print(f"  [{i}] {labels[i]}: {len(instructions[i].points)}pts {len(instructions[i].lines)}lines {len(instructions[i].planes)}planes")

    # 2. Train encoder
    print("\n[2] Training PrimitiveEncoder...")
    encoder = PrimitiveEncoder()
    enc_result = encoder.train(instructions, epochs=200, lr=0.002)
    print(f"  Encoder loss: {enc_result['best_loss']:.6f}")

    # 3. CLIP embeddings
    print("\n[3] CLIP encoding...")
    from ai.multimodal.semantic_visual import SemanticVisualEncoder
    clip = SemanticVisualEncoder()
    clip_embs=[]
    for img_arr in images:
        pil = Image.fromarray(img_arr).resize((224, 224), Image.LANCZOS)
        import io
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        emb = clip.encode(buf.getvalue())
        clip_embs.append(emb if emb is not None else np.zeros(512))
    clip_embs = np.array(clip_embs, dtype=np.float32)
    print(f"  CLIP embeddings: {clip_embs.shape}")

    # 4. Train generator
    print("\n[4] Training SequenceGenerator...")
    prim_embs = np.array([encoder.encode(instr) for instr in instructions])
    gen = SequenceGenerator(hidden_dim=64, max_steps=5)
    sequences=[[emb] for emb in prim_embs]
    clip_list=[clip_embs[i] for i in range(len(clip_embs))]
    gen.train(clip_list, sequences, epochs=80, lr=0.003)

    # 5. Generate rough images (A output)
    print("\n[5] Generating rough images (A)...")
    renderer = PrimitiveRenderer((128, 128))
    rough_images=[]
    for i in range(len(images)):
        print(f"  [{i+1}/{len(images)}] {labels[i]}...", end=" ", flush=True)
        primitives = gen.generate_deterministic(clip_embs[i])
        if primitives:
            decoded = encoder.decode(primitives[0])
            rough = renderer.render(decoded)
            rough_images.append(rough)
            print("ok")
        else:
            rough_images.append(Image.fromarray(np.zeros((128, 128, 3), dtype=np.uint8)))
            print("empty")

    # 6. Train PixelRefiner (B)
    print("\n[6] Training PixelRefiner (B)...")
    target_images=[Image.fromarray(img).resize((128, 128), Image.LANCZOS) for img in images]
    refiner = PixelRefiner(hidden_dim=1024, img_size=128)
    refiner_result = refiner.train(rough_images, target_images, epochs=30, lr=0.005, batch_size=8)
    print(f"  Refiner loss: {refiner_result['final_loss']:.6f}")

    # 7. Evaluate
    print("\n[7] Evaluating A vs B...")
    evaluator = GenerationEvaluator()
    save_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "samples_ab")
    os.makedirs(save_dir, exist_ok=True)

    for i in range(min(5, len(images))):
        rough = rough_images[i]
        refined = refiner.refine(rough)
        orig = target_images[i]

        rough_m = evaluator.evaluate(rough)
        refined_m = evaluator.evaluate(refined)
        orig_m = evaluator.evaluate(orig)
        rough_sim = evaluator._clip_image_similarity(rough, orig)
        refined_sim = evaluator._clip_image_similarity(refined, orig)

        # Save comparison: original | rough (A) | refined (B)
        comparison = Image.new("RGB", (384, 128))
        comparison.paste(orig, (0, 0))
        comparison.paste(rough, (128, 0))
        comparison.paste(refined, (256, 0))
        comparison.save(os.path.join(save_dir, f"{i:02d}_{labels[i]}.png"))

        print(f"  [{i}] {labels[i]}: "
              f"A_bright={rough_m['mean_brightness']:.2f} B_bright={refined_m['mean_brightness']:.2f} orig={orig_m['mean_brightness']:.2f} | "
              f"A_sim={rough_sim:.2f} B_sim={refined_sim:.2f}")

    # Save models
    model_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "weights")
    os.makedirs(model_dir, exist_ok=True)
    encoder.save(os.path.join(model_dir, "primitive_encoder.json"))
    gen.save(os.path.join(model_dir, "sequence_generator.json"))
    refiner.save(os.path.join(model_dir, "pixel_refiner.json"))
    print(f"\nModels saved to {model_dir}")
    print(f"Samples saved to {save_dir}")


if __name__ == "__main__":
    main()
