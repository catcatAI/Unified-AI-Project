"""Quick A-B test: 3 images, no generator, direct encode-decode.
DEPRECATED: This script uses the OLD architecture (rule-based decomposer).
For GVV architecture, see test_gvv_quick.py
"""
import sys, os, json
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join("apps", "backend", "src"))
print("Loading modules...", flush=True)

from ai.multimodal.primitives.decomposer import decompose_spatial as decompose_enhanced
from ai.multimodal.primitives.primitive_encoder import PrimitiveEncoder
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer
try:
    from ai.multimodal.primitives.pixel_refiner import PixelRefiner
except ImportError:
    PixelRefiner = None
from ai.multimodal.evaluation.generation_evaluator import GenerationEvaluator

print("Loading data...", flush=True)
data_dir = os.path.join("data", "multimodal", "cifar10")
idx = json.load(open(os.path.join(data_dir, "index.json")))
images, labels = [], []
for cls in idx["classes"][:3]:
    cls_dir = os.path.join(data_dir, cls)
    f = sorted(os.listdir(cls_dir))[0]
    images.append(np.load(os.path.join(cls_dir, f)))
    labels.append(cls)
print(f"{len(images)} images: {labels}", flush=True)

# Decompose
instructions = [decompose_enhanced(img) for img in images]
print("Decomposed", flush=True)

# Train encoder
encoder = PrimitiveEncoder()
encoder.train(instructions, epochs=100, lr=0.002)
print("Encoder trained", flush=True)

# Generate rough images
renderer = PrimitiveRenderer((128, 128))
rough_images = []
for i in range(len(images)):
    enc = encoder.encode(instructions[i])
    decoded = encoder.decode(enc)
    rough_images.append(renderer.render(decoded))
    print(f"  Rough [{i}] ok", flush=True)

# Train PixelRefiner
target_images = [Image.fromarray(img).resize((128, 128), Image.LANCZOS) for img in images]
refiner = PixelRefiner(hidden_dim=256, img_size=128)
result = refiner.train(rough_images, target_images, epochs=30, lr=0.005, batch_size=2)
loss_val = result["final_loss"]
print("Refiner loss: %.6f" % loss_val, flush=True)

# Evaluate and save
evaluator = GenerationEvaluator()
save_dir = os.path.join("data", "multimodal", "samples_ab")
os.makedirs(save_dir, exist_ok=True)

for i in range(len(images)):
    refined = refiner.refine(rough_images[i])
    rough_sim = evaluator._clip_image_similarity(rough_images[i], target_images[i])
    refined_sim = evaluator._clip_image_similarity(refined, target_images[i])
    print("  [%d] %s: A_sim=%.2f B_sim=%.2f" % (i, labels[i], rough_sim, refined_sim), flush=True)

    comp = Image.new("RGB", (384, 128))
    comp.paste(target_images[i], (0, 0))
    comp.paste(rough_images[i], (128, 0))
    comp.paste(refined, (256, 0))
    comp.save(os.path.join(save_dir, "%02d_%s.png" % (i, labels[i])))

print("Done! Saved to %s" % save_dir, flush=True)
