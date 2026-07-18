import sys, os, numpy as np
sys.path.insert(0, os.path.join("apps", "backend", "src"))
from ai.multimodal.primitives.differentiable_renderer import DifferentiableRenderer
from PIL import Image

renderer = DifferentiableRenderer((128, 128))

vec = np.zeros(263, dtype=np.float32)
vec[0:3] = [0.5, 0.5, 0.5]

# Red point
vec[5] = 0.3
vec[6] = 0.3
vec[7] = 1.0
vec[8] = 0.0
vec[9] = 0.0

# Green plane
off = 5 + 15*5 + 10*8
vec[off] = 0.5
vec[off+1] = 0.5
vec[off+2] = 0.3
vec[off+3] = 0.3
vec[off+4] = 0.0
vec[off+5] = 0.5
vec[off+6] = 0.0

# Red circle
off2 = off + 5*9
vec[off2] = 0.5
vec[off2+1] = 0.5
vec[off2+2] = 0.2
vec[off2+3] = 1.0
vec[off2+4] = 0.0
vec[off2+5] = 0.0

img_arr = renderer.render(vec)
print("Shape:", img_arr.shape, "Range:", img_arr.min(), "-", img_arr.max())
img = Image.fromarray((img_arr * 255).astype(np.uint8))
os.makedirs("data/multimodal", exist_ok=True)
img.save("data/multimodal/test_diff_render.png")
print("Saved")
