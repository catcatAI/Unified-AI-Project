import numpy as np
from PIL import Image
from dna_body import AngelaDNA

def test_render():
    dna = AngelaDNA()
    matrix = dna.matrix[:, :, 3] # 我們觀察剛性層 (Stiffness)
    
    # 強制將剛性數值映射到灰階 0-255
    # 將 >0 的數值歸一化到 100-255，這樣就不會是黑色了
    render_data = np.zeros(matrix.shape, dtype=np.uint8)
    render_data[matrix > 0] = (matrix[matrix > 0] * 100 + 100).astype(np.uint8)
    
    img = Image.fromarray(render_data)
    img.save("angela_dna_preview.png")
    print("已生成強化渲染圖: angela_dna_preview.png，請檢查身體輪廓。")

if __name__ == "__main__":
    test_render()
