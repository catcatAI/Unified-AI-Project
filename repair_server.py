import os
import re

path = r'D:\Projects\Unified-AI-Project\apps\backend\src\services\main_api_server.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. 修正廣播頻率: 5s -> 0.2s
text = text.replace('await asyncio.sleep(5)', 'await asyncio.sleep(0.2)')

# 2. 注入空間數據到 state_data
# 找到 state_data 的定義並加入 spatial
old_state_data = '''            # Map the GSI-4 / Bio status to UI dimensions (alpha, beta, gamma, delta)
            state_data = {
                "alpha": {
                    "energy": (100.0 - bio_state.get("fatigue", 0.0)) / 100.0,
                    "stress": bio_state.get("stress_level", 0.0),
                    "hormones": bio_state.get("hormones", {}),
                },
                "beta": {
                    "learning_rate": 0.01,
                    "cognitive_load": 0.0,
                },
                "gamma": {
                    "happiness": bio_state.get("mood", 0.5),
                    "emotion": bio_state.get("dominant_emotion", "calm"),
                },
                "delta": {
                    "intensity": bio_state.get("arousal", 50.0) / 100.0,
                },
                "timestamp": datetime.now().isoformat(),
            }'''

new_state_data = '''            # Map the GSI-4 / Bio status to UI dimensions
            state_data = {
                "alpha": {
                    "energy": (100.0 - bio_state.get("fatigue", 0.0)) / 100.0,
                    "stress": bio_state.get("stress_level", 0.0),
                    "hormones": bio_state.get("hormones", {}),
                },
                "beta": {
                    "learning_rate": 0.01,
                    "cognitive_load": 0.0,
                },
                "gamma": {
                    "happiness": bio_state.get("mood", 0.5),
                    "emotion": bio_state.get("dominant_emotion", "calm"),
                },
                "delta": {
                    "intensity": bio_state.get("arousal", 50.0) / 100.0,
                },
                "spatial": {
                    "x": heartbeat.x,
                    "y": heartbeat.y,
                },
                "timestamp": datetime.now().isoformat(),
            }'''

text = text.replace(old_state_data, new_state_data)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Successfully performed surgical repair on main_api_server.py")
