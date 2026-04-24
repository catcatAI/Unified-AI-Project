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

    def _build_volumetric_body(self, hair_offset=0.0, breath_phase=0.0):
        """
        [Anatomical Realization] 基於 TXT 矩陣重構 Angela 的解剖結構。
        實施精密脊椎與呼吸聯動 (v1.1 Spine Matrix).
        """
        import math
        self.voxels.fill(0)
        
        # 呼吸縮放係數 (±1px)
        breathing_w = int(math.sin(breath_phase) * 1.0)

        # --- Z=1: 後髮 3 區 ---
        s_mid, s_tip = hair_offset * 1.5, hair_offset * 3.0
        self._build_part(1, (100, 150), (20, 108), [0.8, 0.9, 1.0], 0.1, 10)
        self._build_part(1, (150, 300), (int(15+s_mid), int(113+s_mid)), [0.75, 0.85, 1.0], 0.1, 11)
        self._build_part(1, (300, 380), (int(10+s_tip), int(118+s_tip)), [0.7, 0.8, 0.95], 0.1, 12)
        
        # --- Z=2: 精密脊椎與軀幹系統 (The 9-Node Backbone) ---
        # A. 頸椎 (C1-C7): 長度 8px, 寬度 12px
        self._build_part(2, (142, 150), (58, 70), [0.99, 0.98, 1.0], 0.4, 105)
        
        # B. 胸椎 (T1-T12): 總長 40px, 基礎寬度 26px + 呼吸補償
        tw = 26 + breathing_w
        self._build_part(2, (150, 190), (64 - tw//2, 64 + tw//2), [0.98, 0.98, 1.0], 0.5, 101)
        
        # C. 腰椎 (L1-L5): 總長 36px, 寬度 22px (腰線)
        self._build_part(2, (190, 226), (53, 75), [0.98, 0.98, 1.0], 0.5, 106)
        
        # D. 薦骨與骨盆 (Pelvis): 長度 20px, 寬度 32px (Rigid)
        self._build_part(2, (226, 246), (48, 80), [0.98, 0.98, 1.0], 0.6, 107)

        # --- Z=2: 精密下肢與雙腳 (Legs & Feet) ---
        # 102: 骨盆/下半身基座
        self._build_part(2, (246, 360), (44, 84), [0.98, 0.98, 1.0], 0.6, 102)
        
        # 實體化雙腳 (左腳 ID: 601-605, 右腳 ID: 611-615)
        for i, side in enumerate([-1, 1]): # -1 為左, 1 為右
            base_x = 64 + side * 15 # 腳踝起始中軸
            offset = 10 if side == 1 else 0
            fid = 601 if side == -1 else 611
            
            # 腳踝與腳跟 (Ankle & Heel, L:6, Px_W:10)
            self._build_part(2, (360, 366), (base_x - 5, base_x + 5), [0.98, 0.98, 1.0], 0.7, fid)
            # 腳掌中段 (Midfoot, L:10, Px_W:9)
            self._build_part(2, (366, 376), (base_x - 4, base_x + 5), [0.98, 0.98, 1.0], 0.6, fid + 1)
            # 大腳趾 (Big Toe, L:6, Px_W:3)
            self._build_part(2, (376, 382), (base_x - (side*2), base_x - (side*2) + 3), [0.97, 0.97, 1.0], 0.4, fid + 2)
            # 小腳趾群組 (Small Toes Group, L:5, Px_W:7)
            self._build_part(2, (376, 381), (base_x + (side*1), base_x + (side*1) + 7*side if side==1 else base_x-6), [0.97, 0.97, 1.0], 0.4, fid + 3)
        
        # --- Z=3: 制服 (隨胸腔縮放) ---
        uw = tw + 2
        self._build_part(3, (160, 230), (64 - uw//2, 64 + uw//2), [0.9, 0.9, 0.95], 0.8, 401)
        
        # --- Z=4: 手臂與雙手 (Arms & Hands) ---
        # 201: 左手腕/掌心, 202: 右手腕/掌心
        self._build_part(4, (145, 220), (25, 45), [0.98, 0.98, 1.0], 0.4, 201)
        self._build_part(4, (145, 220), (83, 103), [0.98, 0.98, 1.0], 0.4, 202)
        
        # 實體化手指 (左手 ID: 301-305, 右手 ID: 311-315)
        # 根據矩陣 Px_W 與 L 設定座標
        for i, (name, length, width) in enumerate([
            ("Thumb", 18, 4), ("Index", 18, 3), ("Middle", 20, 3), ("Ring", 18, 3), ("Pinky", 14, 2)
        ]):
            # 左手手指 (向左下方伸展)
            lx = 25 + i*4
            self._build_part(4, (220, 220 + length), (lx, lx + width), [0.97, 0.97, 1.0], 0.3, 301 + i)
            # 右手手指 (鏡像)
            rx = 103 - i*4 - width
            self._build_part(4, (220, 220 + length), (rx, rx + width), [0.97, 0.97, 1.0], 0.3, 311 + i)
        
        # --- Z=5: 頭部五官與前髮 ---
        self._build_part(5, (70, 142), (40, 88), [0.99, 0.99, 1.0], 0.3, 501)
        self._build_part(5, (100, 115), (50, 60), [1.0, 0.7, 0.2], 0.2, 502)
        self._build_part(5, (100, 115), (68, 78), [1.0, 0.7, 0.2], 0.2, 503)
        self._build_part(5, (130, 133), (58, 70), [0.9, 0.4, 0.4], 0.1, 504)
        self._build_part(5, (65, 100), (int(35+s_mid), int(93+s_mid)), [0.85, 0.95, 1.0], 0.1, 20)
        self._build_part(5, (100, 115), (int(38+s_tip), int(90+s_tip)), [0.8, 0.9, 1.0], 0.05, 21)

    def apply_dynamics(self, phase):
        """
        [N.12.8] 同步驅動肢體、髮絲與胸腔呼吸。
        """
        import math
        current_swing = math.sin(phase) * 2.0
        # 將相位傳遞給軀體重構，觸發呼吸擴張
        self._build_volumetric_body(hair_offset=current_swing, breath_phase=phase)

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

    def _apply_secretions(self, render_matrix, bio_state):
        """
        [N.12.11] 實施電子分泌物渲染：紅暈、汗水、淚水。
        """
        stress = bio_state.get("stress", 0.0)
        emotion = bio_state.get("emotion", "neutral")
        
        # 1. 紅暈 (Blush) - 基於 Arousal / Stress
        if stress > 0.4:
            # 臉部頰部座標 (L110-120, L55-65/L75-85)
            alpha = min(0.6, (stress - 0.4) * 1.0)
            for y, x in [(110, 58), (110, 75)]: # 頰點
                render_matrix[y:y+3, x:x+6] = (render_matrix[y:y+3, x:x+6] * (1-alpha) + 
                                              np.array([255, 150, 150]) * alpha).astype(np.uint8)

        # 2. 汗水 (Sweat) - 基於 Stress
        if stress > 0.7:
            # 隨機產生汗珠像素在頸部或額頭
            drop_y = 75 + int(datetime.now().microsecond % 20)
            drop_x = 60 + int(datetime.now().second % 10)
            render_matrix[drop_y:drop_y+2, drop_x] = [200, 230, 255] # 淡藍色汗滴
            
        # 3. 淚水 (Tears) - 極端壓力
        if stress > 0.9:
            render_matrix[115:125, 52:54] = [220, 240, 255]
            render_matrix[115:125, 76:78] = [220, 240, 255]

    def get_flattened_frame(self, bio_state=None):
        render = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        for z in range(1, 6):
            mask = self.voxels[:, :, z, 4] > 0
            color_data = (self.voxels[:, :, z, :3] * 255).astype(np.uint8)
            render[mask] = color_data[mask]
        
        self._apply_fascia_shadows(render)
        
        # --- NEW: ACTIVE SECRETIONS ---
        if bio_state:
            self._apply_secretions(render, bio_state)
            
        return render

    def get_render_ready_matrix(self):
        return self.get_flattened_frame()

    def get_stiffness_at(self, x, y):
        for z in range(5, 0, -1):
            if self.voxels[int(y), int(x), z, 4] > 0:
                return self.voxels[int(y), int(x), z, 3]
        return 0.0
