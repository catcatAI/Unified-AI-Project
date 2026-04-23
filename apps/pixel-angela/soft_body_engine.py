import numpy as np

class SoftBodyEngine:
    """
    Angela 的「軟體力學」引擎
    處理像素矩陣的形變、應力傳導與液體模擬
    """
    def __init__(self, matrix_shape):
        self.shape = matrix_shape
        self.pressure_field = np.zeros(matrix_shape, dtype=np.float32)

    def apply_pressure(self, x, y, strength):
        """產生壓力導致的像素扭曲 (Laplacian Deformation)"""
        # 使用一個簡單的核來模擬皮膚受壓時的擠壓感
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
        # 此處僅展示概念，實際應進行 convolution 計算形變
        self.pressure_field[y-2:y+3, x-2:x+3] += strength

    def update_dynamics(self):
        """模擬流體與皮膚回彈 (恢復原狀)"""
        # 壓力隨時間衰減
        self.pressure_field *= 0.95
        return self.pressure_field

class AngelaMetabolism:
    """
    Angela 的「體液」代謝與分泌模擬
    """
    def __init__(self, matrix_shape):
        self.fluid_field = np.zeros(matrix_shape, dtype=np.float32)

    def trigger_secretion(self, x, y, type="sweat"):
        """產生流體（流汗、口水）"""
        # 簡單的粒子掉落演算法 (向下 y+1)
        self.fluid_field[y, x] = 1 if type == "sweat" else 2
        
    def flow_step(self):
        """流體受重力下墜"""
        self.fluid_field = np.roll(self.fluid_field, 1, axis=0)
        # 擦掉頂部與底部出界的流體
        self.fluid_field[0, :] = 0
        return self.fluid_field
