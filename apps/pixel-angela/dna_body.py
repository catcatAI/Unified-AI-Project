import numpy as np

class AngelaDNA:
    """
    Angela 的 2.5D 高精度體素軀體 (Definitive Edition).
    解決「像素粘黏」問題：使用多層深度堆疊 (Z-Stack)。
    """
    def __init__(self, width=128, height=384):
        self.width = width
        self.height = height
        # 2030 架構：[高, 寬, 深度圖層, 數據通道]
        # 深度圖層 (Depth Planes): 0:背景, 1:後髮, 2:軀幹, 3:前衣, 4:手臂, 5:五指
        # 數據通道 (Channels): [R, G, B, Stiffness, ID]
        self.voxels = np.zeros((height, width, 6, 5), dtype=np.float32)
        self._build_volumetric_body()

    def _build_body_part(self, z_plane, y_range, x_range, color, stiffness, part_id):
        """在指定的 Z 平面精確繪製部位，不影響其他 Z 平面"""
        y_s, y_e = y_range
        x_s, x_e = x_range
        self.voxels[y_s:y_e, x_s:x_e, z_plane, :3] = color
        self.voxels[y_s:y_e, x_s:x_e, z_plane, 3] = stiffness
        self.voxels[y_s:y_e, x_s:x_e, z_plane, 4] = part_id

    def _build_volumetric_body(self):
        # 1. 軀幹 (Z=2)
        self._build_body_part(2, (150, 300), (40, 88), [0.98, 0.98, 1.0], 0.5, 101)
        # 2. 手掌 (Z=4) - 即使它現在與軀幹座標重疊，數據也是分離的
        self._build_body_part(4, (180, 220), (30, 60), [0.98, 0.98, 1.0], 0.4, 201)
        # 3. 獨立的手指 (Z=5) - 解決「手指連在一起」的問題
        for i in range(5):
            # 每根手指在 Z=5 平面上有獨立的 ID 和 1px 的 Z 軸間隙 (模擬)
            self._build_body_part(5, (170, 190), (32 + i*5, 34 + i*5), [0.95, 0.95, 1.0], 0.3, 300 + i)

    def get_flattened_frame(self):
        """
        [Z-Culling 渲染]：將 3D 體素投影為 2D 影像
        從最上層 (Z=5) 向下掃描，取第一個非空像素
        """
        render = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        # 由近及遠遍歷 (從 Z=5 到 Z=1)
        for z in range(5, 0, -1):
            mask = self.voxels[:, :, z, 4] > 0 # 根據 ID 判斷是否有物體
            # 只有目前 render 為空的地方才填入
            empty_mask = np.all(render == 0, axis=-1)
            final_mask = mask & empty_mask
            render[final_mask] = (self.voxels[final_mask, z, :3] * 255).astype(np.uint8)
        return render

    def get_stiffness_at(self, x, y):
        """獲取最上層物體的剛性"""
        for z in range(5, 0, -1):
            if self.voxels[int(y), int(x), z, 4] > 0:
                return self.voxels[int(y), int(x), z, 3]
        return 0.0
