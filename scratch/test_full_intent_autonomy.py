
import sys
import os
import numpy as np

# 將專案路徑加入 Python Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../apps/backend/src")))

from core.autonomous.state_matrix import StateMatrix4D
from core.autonomous.intent_model import IntentManager
from core.autonomous.self_introspector import SelfIntrospector

def run_autonomy_test():
    print("="*70)
    print("Angela AI - Full Intent Autonomy & Consistency Test")
    print("="*70)

    matrix = StateMatrix4D()
    intent_manager = IntentManager()
    introspector = SelfIntrospector()

    # 1. 設定低能量狀態 (Alpha Energy = 0.1)
    matrix.alpha.values["energy"] = 0.1
    summary = matrix.get_state()
    print(f"[狀態] 當前能量: {matrix.alpha.values['energy']:.2f} (極度疲勞)")

    # 2. 自動生成意圖 (Self-Drive Generation)
    intent_manager.generate_homeostatic_intents(summary)
    print(f"[意圖] 已自動生成意圖: {[i.category.name for i in intent_manager.intents]}")

    # 3. 執行幾次生命週期，讓重力發生作用
    for _ in range(5):
        intent_manager.update_intents(delta_time=1.0)
        for dim in ["alpha", "beta", "gamma", "delta"]:
            matrix.set_intent_target(dim, intent_manager.get_intent_influence(dim))
        matrix.update_alpha(energy=0.1) # 驅動更新
    
    print(f"[演化] Alpha 座標向意圖點移動至: {matrix.alpha.coordinate}")

    # 4. 意圖一致性測試 (Conflict Detection)
    # 假設 LLM 想要 Angela 執行 "激烈跳舞"
    # 跳舞是一個需要大量能量的動作，向量指離原點 (1, 1, 1)
    action_name = "Dance_Intense"
    action_vector = (1.0, 1.0, 1.0) 
    
    # 獲取當前維度意圖
    intent_target = intent_manager.get_intent_influence("alpha")
    current_coord = matrix.alpha.coordinate
    
    print(f"\n[動作提案] LLM 請求執行: {action_name}")
    print(f"  -> 動作向量: {action_vector}")
    print(f"  -> 當前生理狀態: {current_coord}")
    print(f"  -> 內生意圖目標: {intent_target} (休息點)")
    
    alignment_report = introspector.check_intent_alignment(
        action_name=action_name,
        action_vector=action_vector,
        current_coord=current_coord,
        intent_target=intent_target
    )

    
    print(f"  -> 相似度 (Alignment): {alignment_report['alignment']:.4f}")
    print(f"  -> 認知失調得分 (Dissonance): {alignment_report['dissonance_score']:.4f}")
    
    if alignment_report["is_conflicting"]:
        print(f"\n⚠️ 警告：偵測到嚴重認知失調！(Conflict Detected)")
        print(f"建議決策: {alignment_report['decision_override']} (節流/拒絕)")
        print("原因: Angela 的原生生理意圖是「休息」，與高能量動作衝突。")
    else:
        print("\n✅ 動作與意圖一致，准予執行。")

    print("\n" + "="*70)

if __name__ == "__main__":
    run_autonomy_test()
