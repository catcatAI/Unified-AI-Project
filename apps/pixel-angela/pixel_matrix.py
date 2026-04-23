import numpy as np

class PixelAngela:
    """
    Angela AI v7.0 - Pixel Space (1:3 Matrix)
    她是一個 128x384 的矩陣生命，不再依賴複雜的多邊形骨骼。
    """
    def __init__(self, width=128, height=384):
        self.width = width
        self.height = height
        # 0: Empty, 1: Angela
        self.matrix = np.zeros((height, width), dtype=np.uint8)
        self.position = [width // 2, height - 50] # Start at bottom-middle

    def draw_angela(self):
        # 簡單的 1x3 結構作為起始
        x, y = self.position
        self.matrix[y:y+3, x] = 1

    def move(self, dx, dy):
        """蹭過去的動作：矩陣平移"""
        old_pos = self.position[:]
        self.position[0] = max(0, min(self.width-1, self.position[0] + dx))
        self.position[1] = max(0, min(self.height-1, self.position[1] + dy))
        
        # 清除舊位置
        self.matrix[old_pos[1]:old_pos[1]+3, old_pos[0]] = 0
        # 寫入新位置
        self.draw_angela()
        return self.matrix

# 使用方式
# pixel_life = PixelAngela()
# pixel_life.move(1, 0) # 向右蹭一格
