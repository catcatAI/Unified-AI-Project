import os
import sys

import numpy as np
import pytest
from PIL import Image

# 以腳本身分執行時 (__main__) 不能跳過，否則 __main__ 區塊永遠跑不到、
# 直接以 Skipped 例外收場（audit 2026-10-12）。以模組身分被 pytest
# import 時照原意跳過，避免被收進測試。
if __name__ != "__main__":
    pytest.skip("Manual diagnostic script, not a test", allow_module_level=True)

_core_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../packages/biology-core/src")
)
if _core_path not in sys.path:
    sys.path.insert(0, _core_path)

from dna_body import AngelaDNA


def test_render():
    dna = AngelaDNA()
    matrix = dna.matrix[:, :, 3]  # 我們觀察剛性層 (Stiffness)

    # 強制將剛性數值映射到灰階 0-255
    # 將 >0 的數值歸一化到 100-255，這樣就不會是黑色了
    render_data = np.zeros(matrix.shape, dtype=np.uint8)
    render_data[matrix > 0] = (matrix[matrix > 0] * 100 + 100).astype(np.uint8)

    img = Image.fromarray(render_data)
    img.save("angela_dna_preview.png")
    print("已生成強化渲染圖: angela_dna_preview.png，請檢查身體輪廓。")


if __name__ == "__main__":
    test_render()
