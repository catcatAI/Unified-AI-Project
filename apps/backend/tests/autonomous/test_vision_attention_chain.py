import pytest
import asyncio
from apps.backend.src.services.vision_service import VisionService

@pytest.mark.asyncio
async def test_discover_focus_memory_chain():
    vision_service = VisionService()
    dummy_image = b"\x00\x01\x02\x03"
    
    # 1. 第一幀：發現物體並存入記憶
    print("\n--- Frame 1: Discovering ---")
    result1 = await vision_service.perceive_and_focus(dummy_image)
    
    assert result1["status"] == "success"
    assert result1["perceived_objects_count"] > 0
    assert len(vision_service.memory.objects) > 0
    
    first_focus = result1["next_focus_point"]
    print(f"Discovered objects, next focus set to: {first_focus}")
    
    # 2. 第二幀：模擬聚焦在第一個物體上
    print("\n--- Frame 2: Focusing on Object 1 ---")
    result2 = await vision_service.perceive_and_focus(dummy_image)
    
    # 注意力模式應該變更或維持在物體位置
    assert result2["sampling_results"]["attention_mode"] == "FOCUS"
    print(f"Focused on object at {result2['next_focus_point']}")
    
    # 3. 模擬多次更新，直到注意力切換 (這裡手動模擬超時或興趣衰減)
    print("\n--- Frame 3: Memory Recall and Refocus ---")
    # 手動從記憶中取回一個物體位置並要求回焦
    remembered_objs = list(vision_service.memory.objects.values())
    target_obj = remembered_objs[0]
    
    # 模擬回焦行為
    sampling_refocus = await vision_service.get_sampling_analysis(
        center=target_obj.position,
        distribution="GAUSSIAN",
        scale=0.3 # 更精確的聚焦
    )
    
    assert sampling_refocus["status"] == "success"
    assert vision_service.attention.last_focus_pos == target_obj.position
    print(f"Quickly refocused on remembered object '{target_obj.label}' at {target_obj.position}")

if __name__ == "__main__":
    asyncio.run(test_discover_focus_memory_chain())
