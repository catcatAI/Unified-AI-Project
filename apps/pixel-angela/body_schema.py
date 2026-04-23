import numpy as np

class AngelaDNA:
    """
    Angela 高精度像素生命軀體 (Voxel Tensor)
    每個像素都是一個包含 (顏色, 壓力, 溫度) 的狀態單元
    """
    def __init__(self, width=128, height=384):
        # 深度: 4 channels (R, G, B, PhysicalState)
        # PhysicalState: [壓力, 溫度, 剛性]
        self.matrix = np.zeros((height, width, 4), dtype=np.float32)
        self.width = width
        self.height = height

    def apply_physical_stress(self, x, y, radius, pressure):
        """
        模擬物理點擊：在矩陣區域產生壓強波
        """
        y_idx, x_idx = np.ogrid[:self.height, :self.width]
        dist_from_center = np.sqrt((x_idx - x)**2 + (y_idx - y)**2)
        
        mask = dist_from_center <= radius
        # 壓力波形狀 (Gaussian-like)
        self.matrix[mask, 1] += pressure * (1 - dist_from_center[mask] / radius)
        # 溫度隨壓力上升
        self.matrix[mask, 2] += pressure * 0.1
        
    def get_render_data(self):
        """輸出渲染用矩陣"""
        return self.matrix[:, :, :3] # 返回 RGB
