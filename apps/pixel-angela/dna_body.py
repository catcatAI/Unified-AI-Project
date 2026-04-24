import numpy as np
from datetime import datetime

class AngelaDNA:
    """
    Angela 的 2.5D 高精度體素軀體 (v3.0 Fascia Integrated).
    解決「像素粘黏」與「深度缺失」問題。
    """
    def __init__(self, width=128, height=384):
        self.width = width
        self.height = height
        # [高, 寬, 深度圖層, 數據通道]
        # Channels: [R, G, B, Stiffness, ID]
        self.voxels = np.zeros((height, width, 6, 5), dtype=np.float32)
        self._build_volumetric_body()

    def _build_body_part(self, z_plane, y_range, x_range, color, stiffness, part_id):
        y_s, y_e = y_range
        x_s, x_e = x_range
        self.voxels[y_s:y_e, x_s:x_e, z_plane, :3] = color
        self.voxels[y_s:y_e, x_s:x_e, z_plane, 3] = stiffness
        self.voxels[y_s:y_e, x_s:x_e, z_plane, 4] = part_id

    def _build_volumetric_body(self):
        # 1. 軀幹 (Z=2) - ID: 101
        self._build_body_part(2, (150, 300), (40, 88), [0.98, 0.98, 1.0], 0.5, 101)
        # 2. 手臂 (Z=4) - ID: 201
        self._build_body_part(4, (140, 220), (30, 98), [0.95, 0.95, 1.0], 0.4, 201)
        # 3. 腿部 (Z=2) - ID: 102
        self._build_body_part(2, (300, 380), (42, 86), [0.98, 0.98, 1.0], 0.6, 102)

    def _apply_fascia_constraints(self, render_matrix):
        """
        [Layer 1.5] 實施肌筋膜防粘黏：在交界處動態生成 1px 陰影
        """
        arm_mask = self.voxels[:, :, 4, 4] == 201
        torso_mask = self.voxels[:, :, 2, 4] == 101
        
        # 尋找重疊邊界 (手臂邊緣且下方是軀幹)
        from scipy.ndimage import binary_dilation
        # 這裡簡化為：將手臂稍微膨脹，交集處塗黑
        dilated_arm = np.zeros_like(arm_mask)
        dilated_arm[1:-1, 1:-1] = arm_mask[1:-1, 1:-1] | arm_mask[0:-2, 1:-1] | arm_mask[2:, 1:-1]
        
        shadow_mask = dilated_arm & torso_mask & (~arm_mask)
        render_matrix[shadow_mask] = [20, 30, 60] # 注入深色陰影像素

    def get_flattened_frame(self):
        """
        [Z-Culling + Fascia Sync] 將體素投影為 2D 影像
        """
        render = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # 由遠及近遍歷
        for z in range(1, 6):
            mask = self.voxels[:, :, z, 4] > 0
            color_data = (self.voxels[:, :, z, :3] * 255).astype(np.uint8)
            render[mask] = color_data[mask]
        
        # --- NEW: ACTIVE NEURAL LINK ---
        # 投影完成後執行肌膜約束 (Layer 1.5)，生成邊緣陰影
        self._apply_fascia_constraints(render)
            
        return render

    def get_render_ready_matrix(self):
        """渲染接口對接"""
        return self.get_flattened_frame()

    def get_stiffness_at(self, x, y):
        for z in range(5, 0, -1):
            if self.voxels[int(y), int(x), z, 4] > 0:
                return self.voxels[int(y), int(x), z, 3]
        return 0.0
