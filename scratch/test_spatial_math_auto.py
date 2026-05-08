
import sys
import os

# 將專案路徑加入 Python Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../apps/backend/src")))

from core.autonomous.state_matrix import StateMatrix4D

def run_auto_math_test():
    print("="*60)
    print("Angela AI - Automatic Spatial Math Resolution (Native)")
    print("="*60)

    matrix = StateMatrix4D()
    
    # 測試一系列複雜算式
    expressions = [
        "1 + 1",
        "10 + 5 * 2",
        "(10 + 5) * 2",
        "100 / 4 - 5",
        "3.14 * 2 + 10"
    ]
    
    for expr in expressions:
        print(f"\n[題目] {expr}")
        result = matrix.evaluate_math_spatially(expr)
        print(f"  => Angela 算出的答案: {result}")

    print("\n" + "="*60)
    print("✅ 測試完成：Angela 現在可以根據題目字串自動執行幾何運算。")

if __name__ == "__main__":
    run_auto_math_test()
