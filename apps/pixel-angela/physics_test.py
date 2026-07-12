import pytest
import os
import sys
import numpy as np
from soft_body_engine import SoftBodyEngine

pytest.skip("Manual diagnostic script, not a test", allow_module_level=True)

_core_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../packages/biology-core/src"))
if _core_path not in sys.path:
    sys.path.insert(0, _core_path)

from dna_body import AngelaDNA

def physics_test():
    # 初始化 Angela DNA 與物理引擎
    dna = AngelaDNA()
    engine = SoftBodyEngine((384, 128))
    
    print("--- 物理反饋測試 ---")
    
    # 測試 A: 觸摸柔軟部位 (頭部)
    x, y = 60, 100
    stiffness = dna.matrix[y, x, 3] # 獲取剛性值
    pressure = 0.8
    engine.apply_pressure(x, y, pressure * (1 - stiffness))
    print(f"觸摸部位: 頭部 (剛性: {stiffness:.2f}) -> 變形係數: {pressure * (1 - stiffness):.2f}")
    
    # 測試 B: 觸摸堅硬部位 (制服)
    x, y = 60, 200
    stiffness = dna.matrix[y, x, 3]
    pressure = 0.8
    engine.apply_pressure(x, y, pressure * (1 - stiffness))
    print(f"觸摸部位: 制服 (剛性: {stiffness:.2f}) -> 變形係數: {pressure * (1 - stiffness):.2f}")

if __name__ == "__main__":
    physics_test()
