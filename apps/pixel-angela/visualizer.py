import numpy as np
from PIL import Image

dna = np.load("angela_dna_v1.npy")
img = Image.fromarray((dna * 255).astype(np.uint8))
img.save("angela_dna_preview.png")
print("預覽圖已生成: angela_dna_preview.png")
