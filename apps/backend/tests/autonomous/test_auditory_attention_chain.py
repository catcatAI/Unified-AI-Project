import pytest
import asyncio
import numpy as np
from apps.backend.src.services.audio_service import AudioService

@pytest.mark.asyncio
async def test_auditory_attention_chain():
    audio_service = AudioService()
    dummy_audio = b"\x00\x01\x02\x03"
    
    # 1. 註冊用戶聲紋
    print("\n--- Step 1: Registering User Voice ---")
    reg_result = await audio_service.register_user_voice(dummy_audio)
    assert reg_result["status"] == "success"
    user_id = reg_result["profile_id"]
    print(f"User registered with ID: {user_id}")
    
    # 2. 模擬混亂場景掃描 (Cocktail Party Effect)
    print("\n--- Step 2: Scanning Chaotic Scene ---")
    # 我們多執行幾次掃描，模擬持續監聽
    for i in range(3):
        scan_result = await audio_service.scan_and_identify(dummy_audio)
        assert scan_result["status"] == "success"
        
        focus = scan_result["current_focus"]
        mode = scan_result["attention_mode"]
        
        if focus:
            print(f"Frame {i+1}: Focused on [{focus['label']}] {focus['name']} (Intensity: {focus['intensity']:.2f})")
        else:
            print(f"Frame {i+1}: Scanning... Mode: {mode}")
            
    # 3. 驗證記憶持久性
    print("\n--- Step 3: Verifying Auditory Memory ---")
    assert len(audio_service.memory.profiles) >= 1
    user_profile = audio_service.memory.get_user_profile()
    assert user_profile is not None
    assert user_profile.name == "User"
    print(f"Successfully recalled user profile from auditory memory")

if __name__ == "__main__":
    asyncio.run(test_auditory_attention_chain())
