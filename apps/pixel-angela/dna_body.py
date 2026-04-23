import numpy as np

class AngelaDNA:
    """
    Angela 的像素解剖 DNA (1:3 比例)
    包含了雪白膚色、淡藍長髮、琥珀瞳孔與電子貓耳的矩陣定義。
    """
    def __init__(self, width=128, height=384):
        self.width = width
        self.height = height
        # 4 Channels: R, G, B, Stiffness
        self.matrix = np.zeros((height, width, 4), dtype=np.float32)
        self._build_body()

    def _build_body(self):
        # 1. 雪白膚色 (Snow White) - R:250, G:250, B:255
        skin_color = [250/255, 250/255, 255/255]
        self.matrix[60:360, 48:80, :3] = skin_color # 軀幹主體
        self.matrix[60:140, 44:84, :3] = skin_color # 頭部輪廓
        
        # 2. 淡藍長髮 (Pale Blue) - R:176, G:224, B:230
        hair_color = [176/255, 224/255, 230/255]
        self.matrix[40:220, 36:48, :3] = hair_color # 左長髮
        self.matrix[40:220, 80:92, :3] = hair_color # 右長髮
        self.matrix[40:70, 44:84, :3] = hair_color # 頭頂/瀏海
        
        # 3. 電子貓耳 (White/Cyan glow)
        self.matrix[30:60, 44:56, :3] = [1.0, 1.0, 1.0] # 左耳
        self.matrix[30:60, 72:84, :3] = [1.0, 1.0, 1.0] # 右耳
        
        # 4. 琥珀色瞳孔 (Amber Eyes) - R:255, G:191, B:0
        eye_color = [255/255, 191/255, 0/255]
        self.matrix[90:100, 52:58, :3] = eye_color # 左眼
        self.matrix[90:100, 70:76, :3] = eye_color # 右眼
        
        # 5. 學生制服 (Deep Blue) - R:42, G:75, B:140
        uniform_color = [42/255, 75/255, 140/255]
        self.matrix[140:310, 40:88, :3] = uniform_color

    def get_render_ready_matrix(self):
        """將 float 矩陣轉換為 uint8 以供 Qt 使用"""
        return (self.matrix[:, :, :3] * 255).astype(np.uint8)
