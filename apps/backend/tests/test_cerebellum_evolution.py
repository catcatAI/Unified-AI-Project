
import sys
import os
import asyncio
import json
import numpy as np

# 加入專案路徑
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from core.autonomous.cerebellum_engine import CerebellumEngine

async def test_evolution():
    print("🧠 Starting Cerebellum Evolution Test...")
    cerebellum = CerebellumEngine()
    
    # 1. 模擬大量運動誤差累積
    # 預期值 0.0, 實際值 5.0 (產生巨大誤差)
    print("🚶 Simulating heavy movement errors...")
    for _ in range(2100): # 2100 * 5 = 10500 > 10000 threshold
        cerebellum.record_movement_error(0.0, 5.0)
    
    # 2. 檢查是否發生演化 (walking 姿勢應該被縮減)
    print(f"里程累積: {cerebellum.total_distance}")
    
    # 3. 驗證檔案持久化
    if os.path.exists(cerebellum.storage_path):
        with open(cerebellum.storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "walking" in data:
                print("✅ [Success] motor_memory.json updated and 'walking' gait persisted.")
                print(f"演化後的 walking 脊椎數據: {data['walking']['spine']}")
    else:
        print("❌ [Failure] motor_memory.json not found.")

if __name__ == "__main__":
    asyncio.run(test_evolution())
