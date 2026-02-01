"""
修復後的 Angela 對話測試
驗證 HSM 和 CDM 知識是否真正被使用
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

async def test_fixed_conversation():
    """測試修復後的對話"""
    
    print("=" * 70)
    print("🧪 修復後的 Angela 對話測試")
    print("=" * 70)
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        from apps.backend.src.core.orchestrator import CognitiveOrchestrator
        
        print("🔄 初始化 Angela...")
        angela = CognitiveOrchestrator()
        print("✅ Angela 已啟動\n")
        
        # 對話 1: 自我介紹
        print("─" * 70)
        print("👤 用戶: 你好！我是小明，請記住我的名字。")
        result1 = await angela.process_user_input("你好！我是小明，請記住我的名字。")
        print(f"🤖 Angela: {result1.get('response', '')}")
        print(f"   📝 HSM記憶: {len(angela.hsm.experiences) if angela.hsm else 0}")
        print(f"   📚 CDM知識: {len(angela.cdm.knowledge_graph.units) if angela.cdm else 0}")
        print()
        
        # 對話 2: 分享偏好
        print("─" * 70)
        print("👤 用戶: 我最喜歡吃巧克力冰淇淋。")
        result2 = await angela.process_user_input("我最喜歡吃巧克力冰淇淋。")
        print(f"🤖 Angela: {result2.get('response', '')}")
        print()
        
        # 對話 3: 測試記憶（關鍵測試）
        print("─" * 70)
        print("👤 用戶: 你記得我叫什麼名字嗎？（關鍵測試）")
        result3 = await angela.process_user_input("你記得我叫什麼名字嗎？")
        print(f"🤖 Angela: {result3.get('response', '')}")
        
        # 檢查回應中是否包含"小明"
        if "小明" in result3.get('response', ''):
            print("   ✅ 成功！Angela 記得用戶姓名")
        else:
            print("   ❌ 問題：Angela 沒有在回應中使用記憶的姓名")
            print(f"   🔍 HSM記憶: {result3.get('hsm_memories', [])}")
        print()
        
        # 對話 4: 更多測試
        print("─" * 70)
        print("👤 用戶: 你知道關於我的哪些事情？")
        result4 = await angela.process_user_input("你知道關於我的哪些事情？")
        print(f"🤖 Angela: {result4.get('response', '')}")
        print()
        
        # 顯示學習狀態
        print("=" * 70)
        print("📊 最終學習狀態:")
        learning_status = await angela.get_learning_status()
        print(f"   • HSM記憶總數: {learning_status.get('hsm_stats', {}).get('total_memories', 0)}")
        print(f"   • CDM知識單元: {learning_status.get('cdm_stats', {}).get('total_units', 0)}")
        print(f"   • 對話歷史: {learning_status.get('conversation_count', 0)}")
        
        # HSM 檢索測試
        if angela.hsm:
            print("\n🔍 HSM 記憶檢索測試:")
            memories = angela.hsm.retrieve_by_association("小明", top_k=3)
            print(f"   檢索 '小明': 找到 {len(memories)} 條記憶")
            for i, (exp, score) in enumerate(memories, 1):
                print(f"   {i}. [{score:.3f}] {exp.content[:40]}...")
        
        print("\n" + "=" * 70)
        print("✅ 修復測試完成")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_fixed_conversation())
    sys.exit(0 if success else 1)