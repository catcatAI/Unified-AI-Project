import numpy as np
from datetime import datetime
from scipy.ndimage import binary_dilation

class AngelaDNA:
    """
    Angela 的 2.5D 高精度體素軀體 (v3.0 Fascia & Shadow Integrated).
    實施「鄰域排斥演算法」以產生真實的邊緣陰影。
    """
    def __init__(self, width=128, height=384):
        self.width = width
        self.height = height
        # [高, 寬, 深度圖層, 數據通道] 
        # Layers: 1:後髮, 2:軀幹, 3:前衣, 4:手臂, 5:細節
        # Channels: [R, G, B, Stiffness, PartID]
        self.voxels = np.zeros((height, width, 6, 5), dtype=np.float32)
        self._build_volumetric_body()

    def _build_part(self, z, y, x, color, stiff, pid):
        self.voxels[y[0]:y[1], x[0]:x[1], z, :3] = color
        self.voxels[y[0]:y[1], x[0]:x[1], z, 3] = stiff
        self.voxels[y[0]:y[1], x[0]:x[1], z, 4] = pid

    def _build_volumetric_body(self, hair_offset=0.0):
        """
        [Anatomical Realization] 基於 TXT 矩陣重構 Angela 的解剖結構。
        支援動態偏移 (hair_offset) 用於物理擺動。
        """
        # 清空畫布 (增量重繪動態層)
        self.voxels.fill(0)

        # --- Z=1: 後髮 3 區 (Back Hair) ---
        # 髮梢 (ID 12) 擺幅最大，髮根 (ID 10) 幾乎不動
        s_mid = hair_offset * 1.5
        s_tip = hair_offset * 3.0
        
        self._build_part(1, (100, 150), (20, 108), [0.8, 0.9, 1.0], 0.1, 10) # Root
        self._build_part(1, (150, 300), (int(15+s_mid), int(113+s_mid)), [0.75, 0.85, 1.0], 0.1, 11) # Mid
        self._build_part(1, (300, 380), (int(10+s_tip), int(118+s_tip)), [0.7, 0.8, 0.95], 0.1, 12) # Tip
        
        # --- Z=2: 頸部與軀幹 (固定層) ---
        self._build_part(2, (142, 150), (58, 70), [0.99, 0.98, 1.0], 0.4, 105)
        self._build_part(2, (150, 310), (45, 83), [0.98, 0.98, 1.0], 0.5, 101)
        self._build_part(2, (310, 384), (40, 88), [0.98, 0.98, 1.0], 0.6, 102)
        
        # --- Z=3: 制服與外殼 ---
        self._build_part(3, (160, 300), (44, 84), [0.9, 0.9, 0.95], 0.8, 401)
        
        # --- Z=4: 手臂 ---
        self._build_part(4, (140, 240), (25, 45), [0.98, 0.98, 1.0], 0.4, 201)
        self._build_part(4, (140, 240), (83, 103), [0.98, 0.98, 1.0], 0.4, 202)
        
        # --- Z=5: 頭部五官與前髮 ---
        self._build_part(5, (70, 142), (40, 88), [0.99, 0.99, 1.0], 0.3, 501)
        self._build_part(5, (100, 115), (50, 60), [1.0, 0.7, 0.2], 0.2, 502)
        self._build_part(5, (100, 115), (68, 78), [1.0, 0.7, 0.2], 0.2, 503)
        self._build_part(5, (130, 133), (58, 70), [0.9, 0.4, 0.4], 0.1, 504)
        
        # 前髮擺動 (s_mid 係數)
        self._build_part(5, (65, 100), (int(35+s_mid), int(93+s_mid)), [0.85, 0.95, 1.0], 0.1, 20)
        self._build_part(5, (100, 115), (int(38+s_tip), int(90+s_tip)), [0.8, 0.9, 1.0], 0.05, 21)

    def apply_dynamics(self, phase):
        """
        [N.12.7.b] 實施分段慣性擺動公式。
        """
        import math
        # 核心公式：Swing = sin(Phase)
        # 我們根據呼吸相位來驅動頭髮微擺
        current_swing = math.sin(phase) * 2.0
        self._build_volumetric_body(hair_offset=current_swing)

    def _apply_fascia_shadows(self, render_matrix):
        """
        [Layer 1.5] 實施環境光遮蔽 (Ambient Occlusion) 像素模擬
        """
        # A. 腋下/手臂陰影 (ID 201/202 與 ID 101 交叉處)
        for arm_id in [201, 202]:
            arm_mask = np.any(self.voxels[:, :, :, 4] == arm_id, axis=2)
            torso_mask = np.any(self.voxels[:, :, :, 4] == 101, axis=2)
            
            # 手臂膨脹 2px 尋找邊界
            dilated = binary_dilation(arm_mask, iterations=2)
            shadow_mask = dilated & torso_mask & (~arm_mask)
            render_matrix[shadow_mask] = (render_matrix[shadow_mask] * 0.7).astype(np.uint8)

        # B. 大腿縫陰影 (ID 103 與 ID 104 鄰域)
        leg_l = np.any(self.voxels[:, :, :, 4] == 103, axis=2)
        leg_r = np.any(self.voxels[:, :, :, 4] == 104, axis=2)
        gap_shadow = binary_dilation(leg_l, iterations=2) & binary_dilation(leg_r, iterations=2)
        # 排除腿部本體，僅在空隙中填入深色
        empty_space = ~ (leg_l | leg_r)
        render_matrix[gap_shadow & empty_space] = [15, 20, 40]

    def get_flattened_frame(self):
        render = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        # Z-Buffer 投影 (Z=1 到 Z=5)
        for z in range(1, 6):
            mask = self.voxels[:, :, z, 4] > 0
            color_data = (self.voxels[:, :, z, :3] * 255).astype(np.uint8)
            render[mask] = color_data[mask]
        
        # 注入動態陰影
        self._apply_fascia_shadows(render)
        return render

    def get_render_ready_matrix(self):
        return self.get_flattened_frame()

    def get_stiffness_at(self, x, y):
        for z in range(5, 0, -1):
            if self.voxels[int(y), int(x), z, 4] > 0:
                return self.voxels[int(y), int(x), z, 3]
        return 0.0
