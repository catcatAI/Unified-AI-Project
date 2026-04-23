import numpy as np
from PIL import Image

def render_angela_blueprint():
    # 建立 128x384 的畫布
    canvas = np.zeros((384, 128, 3), dtype=np.uint8)
    
    # 定義 Angela: 藍色長方體 (1:3 比例)
    # 這裡我們不讀取圖片，我們直接用數值在矩陣中寫入顏色
    # Angela 的身體區域: 寬度 64, 高度 192 (1:3)
    # 顏色: 深藍 (R:42, G:75, B:140)
    canvas[96:288, 32:96] = [42, 75, 140]
    
    img = Image.fromarray(canvas)
    img.save("angela_pure_blueprint.png")
    print("已生成純代碼藍圖: angela_pure_blueprint.png")

if __name__ == "__main__":
    render_angela_blueprint()
