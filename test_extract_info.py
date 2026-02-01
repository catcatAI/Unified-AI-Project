"""
簡單測試 - 驗證 HSM 記憶提取
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from apps.backend.src.core.orchestrator import CognitiveOrchestrator

# 創建實例
orch = CognitiveOrchestrator()

# 測試 _extract_info_from_hsm_memories
print("=== 測試 HSM 記憶提取 ===\n")

# 模擬 HSM 記憶
hsm_memories = [
    {"content": "你好！我是小明，請記住我的名字。", "score": 0.95},
    {"content": "我最喜歡吃巧克力冰淇淋", "score": 0.85},
    {"content": "我住在台北", "score": 0.75}
]

print("輸入記憶:")
for i, mem in enumerate(hsm_memories, 1):
    print(f"  {i}. {mem['content']}")

# 調用提取函數
info = orch._extract_info_from_hsm_memories(hsm_memories)

print(f"\n提取結果:")
print(f"  • 用戶姓名: {info.get('user_name')}")
print(f"  • 偏好: {info.get('preferences', [])}")
print(f"  • 話題: {info.get('topics', [])}")
print(f"  • 事實: {info.get('facts', [])}")

# 驗證
if info.get('user_name') == '小明':
    print("\n✅ 成功提取用戶姓名！")
else:
    print(f"\n❌ 未能提取用戶姓名 (得到: {info.get('user_name')})")