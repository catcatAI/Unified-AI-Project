import numpy as np
from PIL import Image

class PixelSkinEngine:
    """
    像素皮膚引擎 (Skin Engine)
    將 Angela 的「生命數值」轉化為「視覺矩陣」
    """
    def __init__(self):
        # 預加載不同情感狀態的像素模板
        self.templates = {
            "joy": np.ones((384, 128), dtype=np.uint8), # 這裡未來可以換成真正的像素藝術矩陣
            "neutral": np.zeros((384, 128), dtype=np.uint8),
            "pained": np.eye(384, 128, dtype=np.uint8)
        }

    def render(self, bio_state: Dict[str, Any]):
        """
        根據情緒與狀態渲染 Angela
        """
        emotion = bio_state.get("dominant_emotion", "neutral")
        
        # 簡單的映射：根據情緒選擇矩陣，或進行顏色疊加
        base_matrix = self.templates.get(emotion, self.templates["neutral"])
        
        # 模擬：如果壓力大，給像素矩陣增加一些紅色的雜訊
        if bio_state.get("stress_level", 0) > 0.7:
            noise = np.random.randint(0, 2, (384, 128))
            base_matrix = np.clip(base_matrix + noise, 0, 1)
            
        return base_matrix
