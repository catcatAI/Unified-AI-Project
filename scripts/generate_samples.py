"""Generate and save sample images for visual inspection."""
import sys
import os
import json
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.multimodal.primitives.primitive_types import DrawingInstructions, Point, Line, Plane
from ai.multimodal.primitives.primitive_encoder import PrimitiveEncoder
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer
from ai.multimodal.generator.sequence_generator import SequenceGenerator
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
    for cls in idx["classes"][:4]:
        cls_dir = os.path.join(data_dir, cls)
        for f in sorted(os.listdir(cls_dir))[:2]:
            if f.endswith(".npy"):
                images.append(np.load(os.path.join(cls_dir, f)))
                labels.append(cls)

    print(f"Loaded {len(images)} images: {set(labels)}")

    # 1. Train encoder
    instructions=[decompose(img) for img in images]
    encoder = PrimitiveEncoder()
    encoder.train(instructions, epochs=150, lr=0.002)

    # 2. CLIP embeddings
    from ai.multimodal.semantic_visual import SemanticVisualEncoder
    clip = SemanticVisualEncoder()
    clip_embs=[]
    for idx_img, img_arr in enumerate(images):
        pil = Image.fromarray(img_arr).resize((224, 224), Image.LANCZOS)
        import io
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        print(f"  CLIP encoding [{idx_img+1}/{len(images)}]...", end=" ", flush=True)
        emb = clip.encode(buf.getvalue())
        clip_embs.append(emb if emb is not None else np.zeros(512))
        print("ok")
    clip_embs = np.array(clip_embs, dtype=np.float32)

    # 3. Train generator
    prim_embs = np.array([encoder.encode(instr) for instr in instructions])
    gen = SequenceGenerator(hidden_dim=64, max_steps=5)
    sequences=[[emb] for emb in prim_embs]
    clip_list=[clip_embs[i] for i in range(len(clip_embs))]
    gen.train(clip_list, sequences, epochs=80, lr=0.003)

    # 4. Generate and save comparison
    renderer = PrimitiveRenderer((128, 128))
    evaluator = GenerationEvaluator()
    save_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "samples")
    os.makedirs(save_dir, exist_ok=True)

    print(f"\nSaving to {save_dir}/")
    for i in range(min(8, len(images))):
        primitives = gen.generate_deterministic(clip_embs[i])
        if primitives:
            decoded = encoder.decode(primitives[0])
            gen_img = renderer.render(decoded)
            orig_img = Image.fromarray(images[i]).resize((128, 128), Image.LANCZOS)

            # Side-by-side: original | generated
            comparison = Image.new("RGB", (256, 128))
            comparison.paste(orig_img, (0, 0))
            comparison.paste(gen_img, (128, 0))

            fname = f"{i:02d}_{labels[i]}.png"
            comparison.save(os.path.join(save_dir, fname))

            gen_m = evaluator.evaluate(gen_img)
            orig_m = evaluator.evaluate(orig_img)
            print(f"  {fname}: orig_bright={orig_m['mean_brightness']:.2f} gen_bright={gen_m['mean_brightness']:.2f}")

    print(f"\nDone! {len(images)} comparisons saved to {save_dir}/")


if __name__ == "__main__":
    main()
