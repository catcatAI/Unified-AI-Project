import pytest
import os
import sys
import numpy as np
from PIL import Image

pytest.skip("Manual diagnostic script, not a test", allow_module_level=True)

_core_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../packages/biology-core/src"))
if _core_path not in sys.path:
    sys.path.insert(0, _core_path)

from dna_body import AngelaDNA

def test_render():
    dna = AngelaDNA()
    # 簡化矩陣為 0-255 RGB (實際開發中這裡會映射具體顏色)
    # 我們目前 DNA 矩陣是 float32，這裡做簡單歸一化
    data = (dna.matrix[:, :, :3] * 255).astype(np.uint8)
    
    img = Image.fromarray(data)
    img.save("angela_render_test.png")
    print("已生成渲染圖: angela_render_test.png，請檢查是否為 1:3 長方體。")

if __name__ == "__main__":
    test_render()
