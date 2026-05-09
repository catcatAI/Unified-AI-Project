import asyncio
import logging
import numpy as np

from apps.backend.src.core.autonomous.desktop_presence import DesktopPresence, Position, LayerMode
from apps.backend.src.core.autonomous.cerebellum_engine import CerebellumEngine

logging.basicConfig(level=logging.DEBUG)

class MockIntent:
    def __init__(self, category, strength):
        self.category = category
        self.strength = strength

class MockIntentCategory:
    SOCIAL_BOND = "social_bond"
    SELF_PRESERVATION = "self_preservation"

class MockIntentManager:
    def __init__(self):
        self.intents = []

async def test_e3_desktop_presence():
    print("--- Testing E3: Desktop Presence ---")
    intent_manager = MockIntentManager()
    
    # 建立 SOCIAL_BOND 意圖
    import apps.backend.src.core.autonomous.intent_model as intent_model
    # Replace intent model category for testing if needed
    try:
        SOCIAL_BOND = intent_model.IntentCategory.SOCIAL_BOND
    except:
        SOCIAL_BOND = "social_bond"
        
    social_intent = MockIntent(category=SOCIAL_BOND, strength=0.8)
    intent_manager.intents.append(social_intent)
    
    presence = DesktopPresence(intent_manager=intent_manager)
    
    # 設定初始位置
    presence.current_position = Position(100, 100)
    
    # 模擬滑鼠在遠處
    presence._on_mouse_move(Position(500, 500))
    
    # 執行一次引力計算
    await presence._apply_intent_gravity()
    
    print(f"After gravity pull (SOCIAL_BOND), position: x={presence.current_position.x:.2f}, y={presence.current_position.y:.2f}")
    assert presence.current_position.x > 100, "Should move towards mouse"
    assert presence.current_position.y > 100, "Should move towards mouse"
    
    # 測試預測性防衛 (高滑鼠速度)
    presence.mouse_velocity = Position(100, 100) # 非常快的速度
    presence.last_mouse_position = Position(150, 150) # 很靠近
    await presence._apply_intent_gravity()
    print(f"Layer mode after high velocity approach: {presence.layer_mode.name}")
    assert presence.layer_mode == LayerMode.CLICK_THROUGH, "Should trigger click-through"
    
def test_e4_cerebellum():
    print("--- Testing E4: Cerebellum Engine ---")
    engine = CerebellumEngine()
    engine.current_pose_name = "walking"
    
    # 高誤差測試 (防禦收斂)
    engine.error_accumulation = 250.0
    engine.kinetic_history = [{"error": 2.5}] * 100 # Avg error 2.5
    engine._evolve_gait()
    
    # 低誤差測試 (靈活探索)
    engine.error_accumulation = 50.0
    engine.kinetic_history = [{"error": 0.5}] * 100 # Avg error 0.5
    engine._evolve_gait()
    
    # 阻尼測試
    res = engine.execute_command("walking", {"clarity": 0.8, "chaos": 0.1})
    print(f"Damping with high clarity: {engine.damping:.3f}")
    
    res = engine.execute_command("walking", {"clarity": 0.2, "chaos": 0.9})
    print(f"Damping with high chaos: {engine.damping:.3f}")
    
    print("E3/E4 tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_e3_desktop_presence())
    test_e4_cerebellum()
