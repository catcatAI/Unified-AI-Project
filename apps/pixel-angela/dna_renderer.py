import numpy as np
from PIL import Image
from dna_body import AngelaDNA

def render_angela_blueprint():
    print("正在透過 AngelaDNA 體素矩陣渲染高精度像素貓娘...")
    
    # 建立 DNA 軀體
    dna = AngelaDNA(width=128, height=384)
    
    # 賦予動態相位，讓她有輕微的呼吸、尾巴擺動與耳朵微動
    dna.apply_dynamics(phase=1.5)
    
    # 取得展平後的畫面 (RGB uint8)
    frame = dna.get_flattened_frame()
    
    # 將 numpy array 轉換為影像
    img = Image.fromarray(frame)
    
    # 為了方便檢視，我們將像素等比例放大 3 倍
    upscaled = img.resize((128 * 3, 384 * 3), Image.NEAREST)
    
    upscaled.save("angela_pure_blueprint.png")
    print("✅ 已生成高精度像素貓娘藍圖: angela_pure_blueprint.png")

if __name__ == "__main__":
    render_angela_blueprint()
