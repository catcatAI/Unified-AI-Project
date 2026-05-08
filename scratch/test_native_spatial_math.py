
import sys
import os
from datetime import datetime

# 將專案路徑加入 Python Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../apps/backend/src")))

from core.autonomous.state_matrix import StateMatrix4D, CognitiveOp

def run_native_math_test():
    print("="*60)
    print("Angela AI - Native Spatial Reasoning Test (No LLM)")
    print("="*60)

    # 1. 初始化狀態矩陣
    matrix = StateMatrix4D()
    
    # 重置認知維度 (Gamma) 座標為 0
    matrix.gamma.coordinate = (0.0, 0.0, 0.0)
    matrix.gamma.stability = 1.0
    
    print(f"\n[初始狀態] Gamma 座標: {matrix.gamma.coordinate}, 穩定度: {matrix.gamma.stability}")

    # 2. 模擬數學題：(10 + 5) * 2 - 3
    print("\n[開始幾何運算] 目標算式: (10 + 5) * 2 - 3")
    
    # 使用「思維鏈」一次性執行
    instructions = [
        (CognitiveOp.ACCUMULATE, 10.0),  # Start at 10
        (CognitiveOp.ACCUMULATE, 5.0),   # + 5
        (CognitiveOp.AMPLIFY, 2.0),      # * 2
        (CognitiveOp.DECREMENT, 3.0)     # - 3
    ]
    
    final_answer = matrix.execute_thought_chain("gamma", instructions)
    final_stability = matrix.gamma.stability


    print("\n" + "-"*40)
    print(f"最終運算結果 (Gamma X-Axis): {final_answer}")
    print(f"剩餘認知穩定度 (Stability): {final_stability:.2f}")
    print("-"*40)

    if final_answer == 27.0:
        print("\n✅ 測試成功：座標化 AI 在無 LLM 狀態下精確完成了幾何邏輯運算！")
    else:
        print("\n❌ 測試失敗：座標運算出現偏差。")

if __name__ == "__main__":
    run_native_math_test()
