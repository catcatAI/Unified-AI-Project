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
        import math
        self.voxels.fill(0)
        
        # 1. 動態與物理參數
        breathing_w = int(math.sin(breath_phase) * 1.5)
        tail_swing = math.sin(breath_phase - 0.5) * 14.0
        ear_twitch = math.sin(breath_phase * 2) * 2.0
        s_mid, s_tip = hair_offset * 1.5, hair_offset * 3.0
        bx = int(64 + hair_offset * 0.5) # 軀幹位移
        hx = int(64 + hair_offset * 0.2) # 頭部位移

        # 顏色定義 (RGB float 0~1)
        C_SKIN = [1.0, 0.88, 0.80]
        C_HAIR = [0.96, 0.65, 0.75] # 亮粉色貓娘
        C_HAIR_DARK = [0.85, 0.45, 0.60]
        C_EAR_INNER = [1.0, 0.80, 0.85]
        C_EYE = [0.15, 0.65, 0.95] # 碧藍瞳孔
        C_EYE_HL = [1.0, 1.0, 1.0] # 高光
        C_SHIRT = [0.98, 0.98, 1.0] # 白襯衫
        C_SKIRT = [0.15, 0.18, 0.28] # 深藍百褶裙
        C_RIBBON = [0.9, 0.25, 0.35] # 紅色緞帶
        C_SOCK = [0.12, 0.12, 0.15] # 黑絲長襪
        C_SHOE = [0.35, 0.25, 0.25] # 小皮鞋

        # --- Z=0: 後髮 (最深層) ---
        self._build_part(0, (90, 160), (hx-35, hx+35), C_HAIR_DARK, 0.1, 10)
        self._build_part(0, (160, 240), (hx-40+int(s_mid), hx+40+int(s_mid)), C_HAIR_DARK, 0.1, 11)
        self._build_part(0, (240, 280), (hx-45+int(s_tip), hx+45+int(s_tip)), C_HAIR_DARK, 0.1, 12)

        # --- Z=1: 貓尾 (在後髮之前) ---
        # 貓尾巴 (精修版: 兩階段渲染以消除接縫)
        C_TAIL_EDGE = [0.4, 0.2, 0.3] 
        tx = bx
        # 第一階段: 繪製完整的深色邊緣背景
        for i in range(30):
            ty = 190 + i * 6 
            tw = max(2, 7 - int(i * 0.2)) 
            offset = int(math.sin(i * 0.4) * tail_swing)
            # 寬度多2, 高度多4，確保背景完全連通
            self._build_part(1, (ty-2, ty+12), (tx+offset-tw-2, tx+offset+tw+2), C_TAIL_EDGE, 0.2, 15+i)
        
        # 第二階段: 繪製主體 (有4px重疊，絕對無接縫)
        for i in range(30):
            ty = 190 + i * 6 
            tw = max(2, 7 - int(i * 0.2)) 
            offset = int(math.sin(i * 0.4) * tail_swing)
            self._build_part(1, (ty, ty+10), (tx+offset-tw, tx+offset+tw), C_HAIR_DARK, 0.2, 15+i)

        # --- Z=2: 軀幹與腿部 (IDs 100-199, 600-699) ---
        # 脖頸
        self._build_part(2, (115, 128), (hx-6, hx+6), C_SKIN, 0.4, 105) 
        
        # 身體 (制服打底)
        tw = 22 + breathing_w
        self._build_part(2, (128, 165), (bx-tw//2, bx+tw//2), C_SHIRT, 0.5, 101) # 胸腹
        self._build_part(2, (165, 185), (bx-10, bx+10), C_SKIN, 0.6, 106) # 腰部 (絕對領域)

        # 雙腿 (大腿 -> 小腿 -> 鞋子)
        for side in [-1, 1]:
            ax = bx + side * 14
            fid = 601 if side == -1 else 611
            # 大腿 (透氣膚色)
            self._build_part(2, (180, 230), (ax-8, ax+8), C_SKIN, 0.7, fid)
            # 膝蓋以下長襪 (Zettai Ryouiki)
            self._build_part(2, (230, 350), (ax-7, ax+7), C_SOCK, 0.7, fid+1)
            # 皮鞋本體
            self._build_part(2, (350, 370), (ax-9, ax+9), C_SHOE, 0.7, fid+2)
            # 皮鞋尖端
            self._build_part(2, (370, 376), (ax-(side*4)-6, ax-(side*4)+6), C_SHOE, 0.7, fid+3)

        # --- Z=3: 服飾配件 (裙子、緞帶) ---
        ux = int(bx + math.sin(breath_phase)*1.0)
        # 百褶裙 (分層次增加立體感)
        self._build_part(3, (160, 195), (ux-22, ux+22), C_SKIRT, 0.8, 401)
        self._build_part(3, (185, 205), (ux-28, ux+28), C_SKIRT, 0.8, 402)
        
        # 水手服領結
        self._build_part(3, (130, 142), (ux-8, ux+8), C_RIBBON, 0.5, 403)
        self._build_part(3, (135, 155), (ux-14, ux-4), C_RIBBON, 0.6, 404)
        self._build_part(3, (135, 155), (ux+4, ux+14), C_RIBBON, 0.6, 405)

        # --- Z=4: 手臂 (IDs 200-399) ---
        # 左手
        self._build_part(4, (130, 150), (bx-26, bx-12), C_SHIRT, 0.4, 201) # 短袖
        self._build_part(4, (150, 200), (bx-24, bx-16), C_SKIN, 0.4, 203) # 手臂
        self._build_part(4, (200, 215), (bx-22, bx-14), C_SKIN, 0.4, 205) # 手掌
        
        # 右手
        self._build_part(4, (130, 150), (bx+12, bx+26), C_SHIRT, 0.4, 202) # 短袖
        self._build_part(4, (150, 200), (bx+16, bx+24), C_SKIN, 0.4, 204) # 手臂
        self._build_part(4, (200, 215), (bx+14, bx+22), C_SKIN, 0.4, 206) # 手掌

        # --- Z=5: 頭部、貓耳與五官 ---
        # 臉部輪廓
        self._build_part(5, (65, 120), (hx-24, hx+24), C_SKIN, 0.3, 501)
        
        # 動態貓耳 (左右)
        ew = int(ear_twitch)
        for side in [-1, 1]:
            ex = hx + side * 18
            # 建立三角形貓耳
            for i in range(22):
                w = 14 - int(i * 0.6)
                if w < 1: continue
                base_y = 58 # 修正：將耳根下降到與頭部相接的位置，解決浮空問題
                # 外耳廓 (毛髮色)
                self._build_part(5, (base_y-i, base_y-i+1), (ex-w+ew*side, ex+w+ew*side), C_HAIR, 0.1, 510)
                # 內耳 (粉嫩色)
                if w > 3:
                    self._build_part(5, (base_y-i+1, base_y-i+2), (ex-w+3+ew*side, ex+w-3+ew*side), C_EAR_INNER, 0.1, 511)

        # 閃亮大眼 (新增深色眼線描邊)
        self._build_part(5, (83, 99), (hx-19, hx-5), [0.15, 0.1, 0.15], 0.2, 502) # 左眼框
        self._build_part(5, (84, 98), (hx-18, hx-6), C_EYE, 0.2, 502) # 左眼
        self._build_part(5, (86, 92), (hx-16, hx-10), C_EYE_HL, 0.2, 502) # 左眼高光
        
        self._build_part(5, (83, 99), (hx+5, hx+19), [0.15, 0.1, 0.15], 0.2, 503) # 右眼框
        self._build_part(5, (84, 98), (hx+6, hx+18), C_EYE, 0.2, 503) # 右眼
        self._build_part(5, (86, 92), (hx+10, hx+16), C_EYE_HL, 0.2, 503) # 右眼高光
        
        # 貓嘴 \w/
        self._build_part(5, (106, 108), (hx-4, hx-1), C_HAIR_DARK, 0.1, 504) 
        self._build_part(5, (106, 108), (hx+1, hx+4), C_HAIR_DARK, 0.1, 504) 
        self._build_part(5, (108, 111), (hx-2, hx+2), C_EAR_INNER, 0.1, 504) # 舌頭

        # 微紅雙頰
        self._build_part(5, (96, 100), (hx-22, hx-14), C_EAR_INNER, 0.2, 505)
        self._build_part(5, (96, 100), (hx+14, hx+22), C_EAR_INNER, 0.2, 506)

        # 前髮 / 瀏海 / 呆毛
        self._build_part(5, (55, 75), (hx-26, hx+26), C_HAIR, 0.1, 20) # 頂部瀏海
        self._build_part(5, (75, 85), (hx-26, hx-14), C_HAIR, 0.1, 21) # 左鬢角
        self._build_part(5, (75, 85), (hx+14, hx+26), C_HAIR, 0.1, 22) # 右鬢角
        # 靈魂呆毛 (Ahoge)
        self._build_part(5, (40, 55), (hx-2, hx+2), C_HAIR, 0.05, 23)

    def apply_dynamics(self, phase):
        import math
        current_swing = math.sin(phase) * 2.0
        self._build_volumetric_body(hair_offset=current_swing, breath_phase=phase)

    def _apply_fascia_shadows(self, render_matrix):
        """實施 AO 陰影 (Layer 1.5)"""
        # 擴充手臂 ID 陣列以對應新的設計
        for arm_id in [201, 202, 203, 204]:
            arm_mask = np.any(self.voxels[:, :, :, 4] == arm_id, axis=2)
            torso_mask = np.any(self.voxels[:, :, :, 4] == 101, axis=2)
            dilated = binary_dilation(arm_mask, iterations=2)
            shadow_mask = dilated & torso_mask & (~arm_mask)
            # 僅修改 RGB 通道，避免破壞 Alpha
            render_matrix[shadow_mask, :3] = (render_matrix[shadow_mask, :3] * 0.7).astype(np.uint8)
        # 大腿縫陰影
        leg_l, leg_r = np.any(self.voxels[:, :, :, 4] == 601, axis=2), np.any(self.voxels[:, :, :, 4] == 611, axis=2)
        gap = binary_dilation(leg_l, iterations=2) & binary_dilation(leg_r, iterations=2)
        render_matrix[gap & ~(leg_l | leg_r)] = [15, 20, 40, 255]

    def _apply_secretions(self, render_matrix, bio_state):
        stress = bio_state.get("stress", 0.0) if bio_state else 0.0
        if stress > 0.4:
            alpha = min(0.6, (stress - 0.4) * 1.0)
            for y, x in [(110, 58), (110, 75)]:
                render_matrix[y:y+3, x:x+6, :3] = (render_matrix[y:y+3, x:x+6, :3] * (1-alpha) + np.array([255, 150, 150]) * alpha).astype(np.uint8)
        if stress > 0.7:
            drop_y, drop_x = 75 + int(datetime.now().microsecond % 20), 60 + int(datetime.now().second % 10)
            render_matrix[drop_y:drop_y+2, drop_x] = [200, 230, 255, 255]

    def get_flattened_frame(self, bio_state=None):
        # 使用 RGBA 畫布，支援透明背景與圖層外框描邊
        render = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        OUTLINE_COLOR = np.array([45, 35, 55, 255], dtype=np.uint8) # 深紫色描邊

        for z in range(0, 6):
            mask = self.voxels[:, :, z, 4] > 0
            color_data = (self.voxels[:, :, z, :3] * 255).astype(np.uint8)
            
            # 建立當前層的 RGBA 影像
            rgba_data = np.zeros((self.height, self.width, 4), dtype=np.uint8)
            rgba_data[mask, :3] = color_data[mask]
            rgba_data[mask, 3] = 255
            
            # 取得描邊遮罩 (擴展 1 pixel 但不包含原圖形)
            outline_mask = binary_dilation(mask) & (~mask)
            
            # 繪製描邊 (這會自動產生前後景色的立體遮蔽效果)
            render[outline_mask] = OUTLINE_COLOR
            # 繪製本體
            render[mask] = rgba_data[mask]

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
