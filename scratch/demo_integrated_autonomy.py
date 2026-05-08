
import sys
import os
import time

# 將專案路徑加入 Python Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../apps/backend/src")))

from core.autonomous.state_matrix import StateMatrix4D, CognitiveOp
from core.autonomous.intent_model import IntentManager, SelfIntent, IntentCategory
from core.autonomous.memory_neuroplasticity_bridge import MemoryNeuroplasticityBridge
from core.autonomous.self_introspector import SelfIntrospector
from core.autonomous.digital_life_integrator import ModalityGateway, ModalityType
from core.autonomous.digital_life_constants import ActionGeometricMapping

def run_integrated_demo():
    print("="*80)
    print("Angela AI - Integrated Autonomy Demo: The Conflict of Drive & Duty")
    print("="*80)

    # 1. 系統初始化
    matrix = StateMatrix4D()
    intents = IntentManager()
    memory = MemoryNeuroplasticityBridge()
    introspector = SelfIntrospector()
    gateway = ModalityGateway()

    # 2. 設定初始情境：極度疲勞 + 空間記憶
    matrix.alpha.values["energy"] = 0.15 # 15% 能量
    print(f"[Initial] 狀態: 能量={matrix.alpha.values['energy']:.2f}, 座標={matrix.alpha.coordinate}")

    # 在座標 (10, 10, 10) 儲存一個「工作記憶」
    task_id = memory.register_memory(
        memory_id="task_001",
        content="Finalize coordinate system implementation",
        category="task",
        coordinate=(10.0, 10.0, 10.0)
    )

    print(f"[Memory] 記憶已錨定: ID={task_id} @ (10, 10, 10)")

    # 3. 意圖生成 (Self-Drive)
    intents.generate_homeostatic_intents(matrix.get_state())
    # 人為加入一個對「記憶點」的吸引意圖 (Duty Drive)
    intents.add_intent(SelfIntent(
        id="duty_task",
        category=IntentCategory.EXPLORATION,
        target_dimension="gamma",
        target_coordinate=(10.0, 10.0, 10.0),
        urgency=0.5,
        strength=1.0
    ))
    
    print(f"[Intents] 當前意圖池: {[i.category.name for i in intents.intents]}")

    # 4. 模擬 10 步時空演化 (展現連動與回憶)
    print("\n[Evolution] 系統進入演化循環 (展現連動與自動回憶)...")
    for i in range(10):
        # A. 意圖同步到矩陣
        intents.update_intents(delta_time=1.0)
        
        # B. 空間記憶自動掃描 (Task N.21.6)
        intents.scan_memory_proximity(memory, matrix.get_state())
        
        for dim in ["alpha", "beta", "gamma", "delta"]:
            matrix.set_intent_target(dim, intents.get_intent_influence(dim))
        
        # C. 矩陣更新
        matrix.update_alpha(energy=0.15)
        # 注意：我們不主動更新 Gamma，觀察它是否會因為「維度連動 (Drag)」而被拉動
        
        active_intents = [i.id for i in intents.intents]
        print(f"  Step {i+1}: Alpha={matrix.alpha.coordinate[1]:.2f}, Gamma={matrix.gamma.coordinate[0]:.2f} | 意圖數: {len(active_intents)}")
        if any("recall" in id for id in active_intents):
            print(f"    ✨ [System] 偵測到空間記憶接近，自動觸發「聯想意圖」!")

    # 5. 用戶請求 (Complex Math Task)
    expr = "(10 + 5) * 2"
    print(f"\n[User Input] 用戶請求運算: {expr}")
    
    # 使用標準動作向量：COGNITIVE_HEAVY
    action_vector = ActionGeometricMapping.COGNITIVE_HEAVY
    
    # 意圖檢查 (System 1 vs System 2)
    alignment = introspector.check_intent_alignment(
        action_name="Math_Task",
        action_vector=action_vector,
        current_coord=matrix.alpha.coordinate,
        intent_target=intents.get_intent_influence("alpha")
    )
    
    print(f"[Introspection] 衝突檢查: Alignment={alignment['alignment']:.2f}, Dissonance={alignment['dissonance_score']:.2f}")

    # 6. 模態閘控決策 (基於衝突報告)
    gateway.update_gates(arousal=25.0, introspection_report=alignment)
    
    if not gateway.is_active(ModalityType.AUDIO):
        print("\n[Output Gating] ⚡ 偵測到嚴重衝突：Angela 關閉了語音模態，僅以簡短文字回應...")
    
    # 即使疲憊，仍執行運算 (幾何邏輯)
    result = matrix.evaluate_math_spatially(expr)
    print(f"[Result] 運算結果: {result}")

    print("\n" + "="*80)

if __name__ == "__main__":
    run_integrated_demo()
