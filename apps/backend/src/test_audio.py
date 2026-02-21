import asyncio
import logging
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
monorepo_root = project_root.parent.parent
sys.path.append(str(monorepo_root.absolute()))
sys.path.append(str((project_root / "src").absolute()))

from services.audio_service import AudioService, WHISPER_AVAILABLE, EDGE_TTS_AVAILABLE

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

async def test():
    print(f"WHISPER_AVAILABLE: {WHISPER_AVAILABLE}")
    print(f"EDGE_TTS_AVAILABLE: {EDGE_TTS_AVAILABLE}")
    
    a = AudioService()
    
    print("\n--- Testing TTS ---")
    res = await a.text_to_speech('你好，這是 Angela 的音頻測試。', voice='zh-CN-XiaoxiaoNeural')
    if res:
        print(f"TTS generated {len(res)} bytes of audio data.")
        with open("test_output.mp3", "wb") as f:
            f.write(res)
        print("Saved to test_output.mp3")
    else:
        print("TTS returned None")
        
    print("\n--- Testing STT (with the generated audio) ---")
    if res:
        stt_res = await a.speech_to_text(res, language="zh-CN")
        print(f"STT result: {stt_res}")

if __name__ == "__main__":
    asyncio.run(test())
