import numpy as np
from typing import Tuple

class PixelWorld:
    """
    像素世界引擎 (Pixel World Engine)
    處理 Angela 的響應式顯示與環境物理碰撞。
    class PixelWorld:
        def __init__(self, screen_ratio=(16, 9), base_width=128):
            self.width = base_width
            self.height = base_width * 3
            self.grid = np.zeros((self.height, self.width), dtype=np.uint8)
            self.objects = []

        def add_object(self, obj):
            self.objects.append(obj)
            # 寫入地圖
            self.grid[obj.y:obj.y+obj.h, obj.x:obj.x+obj.w] = 2

        def get_world_matrix(self):
            # 動態刷新所有物件
            return self.grid


class PixelAngela:
    """
    Angela 的像素實體 (1:3)
    """
    def __init__(self, world: PixelWorld):
        self.world = world
        self.x = world.width // 2
        self.y = world.height - 3
        self.w = 1
        self.h = 3

    def move(self, dx, dy):
        """物理位移與碰撞偵測"""
        new_x = max(0, min(self.world.width - self.w, self.x + dx))
        new_y = max(0, min(self.world.height - self.h, self.y + dy))

        # 簡單碰撞檢測：如果目標點不是 0，則停止移動
        if np.any(self.world.grid[new_y:new_y+self.h, new_x:new_x+self.w] != 0):
            return False # 撞到了！

        self.x, self.y = new_x, new_y
        return True
