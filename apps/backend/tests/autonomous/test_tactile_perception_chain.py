import pytest
import asyncio
from apps.backend.src.services.tactile_service import TactileService

@pytest.mark.asyncio
async def test_tactile_perception_chain():
    tactile_service = TactileService()
    
    # 1. 視覺建模階段 (模擬看到一個金屬杯子)
    print("\n--- Step 1: Visual-to-Tactile Modeling ---")
    visual_data = {
        "object_id": "cup_001",
        "name": "Stainless Steel Cup",
        "texture_complexity": 0.1,    # 很平滑
        "specular_reflection": 0.9,   # 反光強
        "color_warmth": 0.2           # 冷色調
    }
    model_result = await tactile_service.model_object_tactile(visual_data)
    assert "tactile_properties" in model_result
    props = model_result["tactile_properties"]
    print(f"Object {visual_data['object_id']} modeled.")
    print(f"Predicted: Temperature={props['temperature']}°C, Hardness={props['hardness']}")

    # 2. 觸摸模擬階段 (精確到指尖位置)
    print("\n--- Step 2: Precise Touch Interaction ---")
    contact_data = {
        "position": (10.5, 5.0, 0.0),
        "body_part": "right_index_finger_tip",
        "pressure": 0.8,
        "area": 0.5
    }
    touch_result = await tactile_service.simulate_touch("cup_001", contact_data)
    assert touch_result["status"] == "success"
    
    feedback = touch_result["feedback"]
    print(f"Touched with {feedback['body_part']} at {feedback['location']}")
    print(f"Sensation: {feedback['sensations']['texture_feel']}, "
          f"Resistance: {feedback['sensations']['resistance']:.2f}, "
          f"Temp Delta: {feedback['sensations']['temperature_delta']:.1f}°C")

    # 3. 記憶驗證
    print("\n--- Step 3: Tactile Memory Check ---")
    experience = tactile_service.memory.get_object_experience("cup_001")
    assert experience is not None
    assert len(experience["points"]) > 0
    print(f"Successfully retrieved tactile experience for cup_001 from memory")

if __name__ == "__main__":
    asyncio.run(test_tactile_perception_chain())
