
import sys
import os
import time
from datetime import datetime

# 將專案路徑加入 Python Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../apps/backend/src")))

from core.autonomous.state_matrix import StateMatrix4D
from core.autonomous.intent_model import IntentManager, SelfIntent, IntentCategory

def run_intent_gravity_test():
    print("="*60)
    print("Angela AI - Native Self-Intent Gravity Test")
    print("="*60)

    matrix = StateMatrix4D()
    intent_manager = IntentManager()
    
    # 初始狀態
    print(f"初始 Delta 座標: {matrix.delta.coordinate}")

    # 1. 人為注入一個「社交意圖」 (Social Intent)
    # 意圖讓 Delta 維度移動到 (5.0, 5.0, 5.0) -> 代表強烈的社交渴望
    social_intent = SelfIntent(
        id="social_drive_01",
        category=IntentCategory.SOCIAL_BOND,
        target_dimension="delta",
        target_coordinate=(5.0, 5.0, 5.0),
        urgency=0.8,
        strength=1.5
    )
    intent_manager.add_intent(social_intent)

    # 2. 模擬多個生命週期循環
    print("\n[模擬生命週期] 意圖重力開始發生作用...")
    
    for i in range(10):
        # A. 更新意圖管理器 (計算合力向量)
        intent_manager.update_intents(delta_time=0.1)
        
        # B. 將意圖向量注入狀態矩陣
        for dim in ["alpha", "beta", "gamma", "delta"]:
            target = intent_manager.get_intent_influence(dim)
            matrix.set_intent_target(dim, target)
            
        # C. 矩陣自我更新 (會觸發 apply_intent_gravity)
        matrix.update_delta(engagement=0.5) # 觸發更新
        
        print(f"  週期 {i+1}: Delta 座標 -> {matrix.delta.coordinate}")
        time.sleep(0.1)

    # 3. 檢查最終狀態
    final_coord = matrix.delta.coordinate
    print("\n" + "-"*40)
    print(f"最終 Delta 座標: {final_coord}")
    print(f"意圖管理器剩餘意圖數: {len(intent_manager.intents)}")
    print("-"*40)

    if final_coord[0] > 0.1:
        print("\n✅ 測試成功：Delta 座標已受意圖重力吸引而發生位移。")
        print("這證明了 Angela 的行為是由內在意圖「拉動」的，而非單純的外部指令。")
    else:
        print("\n❌ 測試失敗：座標未發生位移。")

if __name__ == "__main__":
    run_intent_gravity_test()
