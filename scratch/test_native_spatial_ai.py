import asyncio
import os
import sys

# 將專案根目錄加入路徑
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apps.backend.src.core.autonomous.state_matrix import StateMatrix4D
from apps.backend.src.core.autonomous.self_introspector import SelfIntrospector
from apps.backend.src.core.autonomous.digital_life_integrator import DigitalLifeIntegrator
from apps.backend.src.core.autonomous.art_learning_system import ArtLearningSystem
from apps.backend.src.core.autonomous.action_executor import ActionExecutor, Action, ActionCategory, ActionPriority

async def run_tests():
    print("=== 🧪 Testing Native Spatial AI ===")
    
    # 1. 測試美學空間運算
    print("\n--- 1. Testing Art Learning Spatial Colors ---")
    sm = StateMatrix4D()
    sm.update_gamma(happiness=0.9, calm=0.8, sadness=0.1) # 高幸福感、高平靜
    
    art = ArtLearningSystem()
    colors = art.get_color_overrides_spatial(sm)
    print(f"Happy Colors (RGB delta computed): {colors}")
    
    print(f"Initial preferences: {art.aesthetic_preferences}")
    art.learn_from_feedback_spatial(sentiment_score=0.8, state_matrix=sm)
    print(f"Preferences after positive feedback (Gravity Pull): {art.aesthetic_preferences}")
    
    # 2. 測試自我內省趨勢
    print("\n--- 2. Testing Self Introspector Trends ---")
    introspector = SelfIntrospector()
    
    # 模擬持續下降的幸福感
    for w in [0.8, 0.72, 0.65, 0.55]:
        report = await introspector.perform_mental_health_check(
            {"wellbeing": w, "arousal": 0.5, "stress_level": 0.1, "valence": 0.5}, 
            {}
        )
        print(f"Wellbeing {w}: Trend -> {report.get('wellbeing_trend')} | Crisis -> {report.get('crisis_detected', False)}")
        
    print(f"Initial threshold: {introspector._dissonance_threshold}")
    introspector.adapt_dissonance_threshold(post_override_wellbeing=0.8, pre_override_wellbeing=0.5)
    print(f"Adapted threshold (positive outcome): {introspector._dissonance_threshold}")
    
    # 3. 測試 DLI 空間成熟度
    print("\n--- 3. Testing Digital Life Integrator Maturity ---")
    dli = DigitalLifeIntegrator()
    dli.state_matrix.update_alpha(tension=0.1)  # 極低張力
    dli.state_matrix.update_beta(confusion=0.1) # 極低混亂
    dli.state_matrix.update_gamma(calm=0.9)     # 高平靜
    dli.state_matrix.update_delta(trust=0.9)    # 高信任
    maturity = dli._compute_maturity_score()
    print(f"Maturity Score (High stability): {maturity}")
    
    # 4. 測試動作執行器的原生成功率
    print("\n--- 4. Testing Action Executor Success Rate ---")
    dli.state_matrix.update_alpha(energy=0.9, comfort=0.9, tension=0.1)
    
    executor = ActionExecutor()
    executor.set_digital_life_integrator(dli)
    def dummy(): pass
    
    # 高優先級 (體能耗大)
    action1 = Action.create("test", ActionCategory.SYSTEM, ActionPriority.HIGH, dummy)
    success_rate1 = executor._get_action_success_rate_spatial(action1)
    print(f"Success rate (High energy, HIGH priority): {success_rate1:.2%}")
    
    # 後台優先級 (體能耗低)
    action2 = Action.create("test2", ActionCategory.SYSTEM, ActionPriority.BACKGROUND, dummy)
    success_rate2 = executor._get_action_success_rate_spatial(action2)
    print(f"Success rate (High energy, BACKGROUND priority): {success_rate2:.2%}")

if __name__ == "__main__":
    asyncio.run(run_tests())
