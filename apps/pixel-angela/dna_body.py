import numpy as np
from datetime import datetime
from scipy.ndimage import binary_dilation

class AngelaDNA:
    """
    Angela 的 2.5D 高精度體素軀體 (Definitive Anatomical Matrix).
    嚴格遵循 [N+N] 協議，保全所有已開發器官：髮絲、脊椎、五指、雙腳、服飾與分泌物。
    """
    def __init__(self, width=128, height=384):
        self.width = width
        self.height = height
        # Layers: 1:後髮, 2:軀幹/腳, 3:制服, 4:手臂/手, 5:臉部/前髮
        self.voxels = np.zeros((height, width, 6, 5), dtype=np.float32)
        self._build_volumetric_body()

    def _build_part(self, z, y, x, color, stiff, pid):
        self.voxels[y[0]:y[1], x[0]:x[1], z, :3] = color
        self.voxels[y[0]:y[1], x[0]:x[1], z, 3] = stiff
        self.voxels[y[0]:y[1], x[0]:x[1], z, 4] = pid

    def _build_volumetric_body(self, hair_offset=0.0, breath_phase=0.0):
        """
        [ASI Standard] 全器官建構。
        """
        import math
        self.voxels.fill(0)
        
        # 1. 動態與物理參數
        breathing_w = int(math.sin(breath_phase) * 1.0)
        uniform_swing = math.sin(breath_phase - 0.2) * 1.6
        s_mid, s_tip = hair_offset * 1.5, hair_offset * 3.0
        bx = int(64 + hair_offset * 0.5) # 軀幹位移
        hx = int(64 + hair_offset * 0.2) # 頭部位移

        # --- Z=1: 後髮 (3段式) ---
        self._build_part(1, (100, 150), (20, 108), [0.8, 0.9, 1.0], 0.1, 10) # Root
        self._build_part(1, (150, 300), (int(15+s_mid), int(113+s_mid)), [0.75, 0.85, 1.0], 0.1, 11) # Mid
        self._build_part(1, (300, 380), (int(10+s_tip), int(118+s_tip)), [0.7, 0.8, 0.95], 0.1, 12) # Tip
        
        # --- Z=2: 脊椎、軀幹與精密雙腳 ---
        # 頸椎、胸椎、腰椎、骨盆
        self._build_part(2, (142, 150), (bx-6, bx+6), [0.99, 0.98, 1.0], 0.4, 105) 
        tw = 26 + breathing_w
        self._build_part(2, (150, 190), (bx-tw//2, bx+tw//2), [0.98, 0.98, 1.0], 0.5, 101) 
        self._build_part(2, (190, 226), (bx-11, bx+11), [0.98, 0.98, 1.0], 0.5, 106) 
        self._build_part(2, (226, 360), (bx-16, bx+16), [0.98, 0.98, 1.0], 0.6, 107) 
        
        # 雙腳 (IDs 601-613)
        for side in [-1, 1]:
            ax = bx + side * 15
            fid = 601 if side == -1 else 611
            self._build_part(2, (360, 366), (ax-5, ax+5), [0.98, 0.98, 1.0], 0.7, fid) # Heel
            self._build_part(2, (366, 376), (ax-4, ax+5), [0.98, 0.98, 1.0], 0.6, fid+1) # Midfoot
            self._build_part(2, (376, 382), (ax-(side*2), ax-(side*2)+3), [0.97, 0.97, 1.0], 0.4, fid+2) # Big Toe

        # --- Z=3: 制服 (Fabric Lag) ---
        ux = int(64 + uniform_swing)
        uw = tw + 2
        self._build_part(3, (160, 230), (ux-uw//2, ux+uw//2), [0.9, 0.9, 0.95], 0.8, 401)
        
        # --- Z=4: 手臂與精密五指 ---
        self._build_part(4, (145, 220), (bx-30, bx-10), [0.98, 0.98, 1.0], 0.4, 201) # L_Palm
        self._build_part(4, (145, 220), (bx+10, bx+30), [0.98, 0.98, 1.0], 0.4, 202) # R_Palm
        # 10 根指節 (IDs 301-315)
        for i, (name, length, width) in enumerate([
            ("Thumb", 18, 4), ("Index", 18, 3), ("Middle", 20, 3), ("Ring", 18, 3), ("Pinky", 14, 2)
        ]):
            lx = bx - 30 + i*4
            self._build_part(4, (220, 220 + length), (lx, lx + width), [0.97, 0.97, 1.0], 0.3, 301 + i)
            rx = bx + 30 - i*4 - width
            self._build_part(4, (220, 220 + length), (rx, rx + width), [0.97, 0.97, 1.0], 0.3, 311 + i)
        
        # --- Z=5: 頭部、五官與前髮 ---
        self._build_part(5, (70, 142), (hx-24, hx+24), [0.99, 0.99, 1.0], 0.3, 501) # Face
        self._build_part(5, (100, 115), (hx-14, hx-4), [1.0, 0.7, 0.2], 0.2, 502) # L_Eye
        self._build_part(5, (100, 115), (hx+4, hx+14), [1.0, 0.7, 0.2], 0.2, 503) # R_Eye
        self._build_part(5, (130, 133), (hx-6, hx+6), [0.9, 0.4, 0.4], 0.1, 504) # Mouth
        # 前髮 (2段式)
        self._build_part(5, (65, 100), (hx-29+int(s_mid), hx+29+int(s_mid)), [0.85, 0.95, 1.0], 0.1, 20)
        self._build_part(5, (100, 115), (hx-26+int(s_tip), hx+26+int(s_tip)), [0.8, 0.9, 1.0], 0.05, 21)

    def apply_dynamics(self, phase):
        import math
        current_swing = math.sin(phase) * 2.0
        self._build_volumetric_body(hair_offset=current_swing, breath_phase=phase)

    def _apply_fascia_shadows(self, render_matrix):
        """實施 AO 陰影 (Layer 1.5)"""
        for arm_id in [201, 202]:
            arm_mask = np.any(self.voxels[:, :, :, 4] == arm_id, axis=2)
            torso_mask = np.any(self.voxels[:, :, :, 4] == 101, axis=2)
            dilated = binary_dilation(arm_mask, iterations=2)
            shadow_mask = dilated & torso_mask & (~arm_mask)
            render_matrix[shadow_mask] = (render_matrix[shadow_mask] * 0.7).astype(np.uint8)
        # 大腿縫陰影
        leg_l, leg_r = np.any(self.voxels[:, :, :, 4] == 601, axis=2), np.any(self.voxels[:, :, :, 4] == 611, axis=2)
        gap = binary_dilation(leg_l, iterations=2) & binary_dilation(leg_r, iterations=2)
        render_matrix[gap & ~(leg_l | leg_r)] = [15, 20, 40]

    def _apply_secretions(self, render_matrix, bio_state):
        stress = bio_state.get("stress", 0.0) if bio_state else 0.0
        if stress > 0.4:
            alpha = min(0.6, (stress - 0.4) * 1.0)
            for y, x in [(110, 58), (110, 75)]:
                render_matrix[y:y+3, x:x+6] = (render_matrix[y:y+3, x:x+6] * (1-alpha) + np.array([255, 150, 150]) * alpha).astype(np.uint8)
        if stress > 0.7:
            drop_y, drop_x = 75 + int(datetime.now().microsecond % 20), 60 + int(datetime.now().second % 10)
            render_matrix[drop_y:drop_y+2, drop_x] = [200, 230, 255]

    def get_flattened_frame(self, bio_state=None):
        render = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        for z in range(1, 6):
            mask = self.voxels[:, :, z, 4] > 0
            color_data = (self.voxels[:, :, z, :3] * 255).astype(np.uint8)
            render[mask] = color_data[mask]
        self._apply_fascia_shadows(render)
        if bio_state: self._apply_secretions(render, bio_state)
        return render

    def get_render_ready_matrix(self):
        return self.get_flattened_frame()

    def get_stiffness_at(self, x, y):
        for z in range(5, 0, -1):
            if self.voxels[int(y), int(x), z, 4] > 0:
                return self.voxels[int(y), int(x), z, 3]
        return 0.0
