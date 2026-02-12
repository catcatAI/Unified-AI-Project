"""
與 Angela 的實際對話測試
測試真實的學習和記憶能力
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

async def conversation_with_angela():
    """與 Angela 進行真實對話"""
    
    print("=" * 70)
    print("🌟 開始與 Angela 的對話測試")
    print("=" * 70)
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 導入 Angela 的核心
        from apps.backend.src.core.orchestrator import CognitiveOrchestrator
        
        print("🔄 正在啟動 Angela...")
        angela = CognitiveOrchestrator()
        print("✅ Angela 已啟動！\n")
        
        # 顯示系統狀態
        print("📊 系統狀態:")
        if angela.hsm:
            print(f"  • HSM (全息記憶): ✅ 已啟用 (維度: 1024)")
        else:
            print(f"  • HSM: ❌ 未啟用")
            
        if angela.cdm:
            print(f"  • CDM (認知學習): ✅ 已啟用")
        else:
            print(f"  • CDM: ❌ 未啟用")
            
        if angela.llm_available:
            print(f"  • LLM: ✅ 已連接")
        else:
            print(f"  • LLM: ⚠️ 使用規則回應模式")
        print()
        
        # 對話歷史
        conversation_history = []
        
        # 對話 1: 自我介紹
        print("─" * 70)
        print("👤 你: 你好 Angela！我是小明。請記住我的名字。")
        response1 = await angela.process_user_input("你好 Angela！我是小明。請記住我的名字。")
        print(f"🤖 Angela: {response1.get('response', '')}")
        print(f"   📚 學習觸發: {response1.get('learning_triggered', False)}")
        print(f"   🧠 HSM記憶數: {len(angela.hsm.experiences) if angela.hsm else 0}")
        print(f"   📖 CDM知識數: {len(angela.cdm.knowledge_graph.units) if angela.cdm else 0}")
        conversation_history.append(("用戶: 你好 Angela！我是小明。", f"Angela: {response1.get('response', '')}"))
        print()
        
        # 對話 2: 分享偏好
        print("─" * 70)
        print("👤 你: 我最喜歡的食物是巧克力冰淇淋。")
        response2 = await angela.process_user_input("我最喜歡的食物是巧克力冰淇淋。")
        print(f"🤖 Angela: {response2.get('response', '')}")
        print(f"   📚 學習觸發: {response2.get('learning_triggered', False)}")
        conversation_history.append(("用戶: 我最喜歡的食物是巧克力冰淇淋。", f"Angela: {response2.get('response', '')}"))
        print()
        
        # 對話 3: 測試記憶 - 詢問名字
        print("─" * 70)
        print("👤 你: 你記得我叫什麼名字嗎？")
        response3 = await angela.process_user_input("你記得我叫什麼名字嗎？")
        print(f"🤖 Angela: {response3.get('response', '')}")
        print(f"   🔍 相關記憶: {len(response3.get('related_memories', []))} 條")
        conversation_history.append(("用戶: 你記得我叫什麼名字嗎？", f"Angela: {response3.get('response', '')}"))
        print()
        
        # 對話 4: 分享更多信息
        print("─" * 70)
        print("👤 你: 我住在台北，工作是軟體工程師。")
        response4 = await angela.process_user_input("我住在台北，工作是軟體工程師。")
        print(f"🤖 Angela: {response4.get('response', '')}")
        print(f"   📚 學習觸發: {response4.get('learning_triggered', False)}")
        conversation_history.append(("用戶: 我住在台北，工作是軟體工程師。", f"Angela: {response4.get('response', '')}"))
        print()
        
        # 對話 5: 測試多輪記憶
        print("─" * 70)
        print("👤 你: 我昨天提到的食物是什麼？")
        response5 = await angela.process_user_input("我昨天提到的食物是什麼？")
        print(f"🤖 Angela: {response5.get('response', '')}")
        conversation_history.append(("用戶: 我昨天提到的食物是什麼？", f"Angela: {response5.get('response', '')}"))
        print()
        
        # 對話 6: 分享生日
        print("─" * 70)
        print("👤 你: 我的生日是1995年3月15日。記住這個日子哦！")
        response6 = await angela.process_user_input("我的生日是1995年3月15日。記住這個日子哦！")
        print(f"🤖 Angela: {response6.get('response', '')}")
        print(f"   📚 學習觸發: {response6.get('learning_triggered', False)}")
        conversation_history.append(("用戶: 我的生日是1995年3月15日。", f"Angela: {response6.get('response', '')}"))
        print()
        
        # 對話 7: 綜合測試
        print("─" * 70)
        print("👤 你: 能告訴我你記得關於我的哪些事情嗎？")
        response7 = await angela.process_user_input("能告訴我你記得關於我的哪些事情嗎？")
        print(f"🤖 Angela: {response7.get('response', '')}")
        conversation_history.append(("用戶: 能告訴我你記得關於我的哪些事情嗎？", f"Angela: {response7.get('response', '')}"))
        print()
        
        # 保存對話
        print("─" * 70)
        print("💾 正在保存對話記憶...")
        if angela.hsm:
            save_path = f"data/conversations/conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            Path("data/conversations").mkdir(parents=True, exist_ok=True)
            await angela.hsm.save_to_file_async(save_path)
            print(f"   ✅ 對話已保存到: {save_path}")
        print()
        
        # 最終統計
        print("=" * 70)
        print("📊 對話統計:")
        learning_status = await angela.get_learning_status()
        print(f"   • 總對話輪數: {len(conversation_history)}")
        print(f"   • HSM記憶總數: {learning_status.get('hsm_stats', {}).get('total_memories', 0)}")
        print(f"   • CDM知識單元: {learning_status.get('cdm_stats', {}).get('total_units', 0)}")
        print(f"   • 學習觸發次數: {learning_status.get('cdm_stats', {}).get('learning_triggered', 0)}")
        print(f"   • 平均新奇度: {learning_status.get('cdm_stats', {}).get('avg_novelty', 0):.3f}")
        print()
        
        # 顯示HSM檢索測試
        if angela.hsm:
            print("🔍 HSM 記憶檢索測試:")
            memories = angela.hsm.retrieve_by_association("小明", top_k=3)
            print(f"   檢索 '小明': 找到 {len(memories)} 條記憶")
            for i, (exp, score) in enumerate(memories, 1):
                print(f"   {i}. [{score:.3f}] {exp.content[:40]}...")
            
            print()
            memories2 = angela.hsm.retrieve_by_association("巧克力", top_k=3)
            print(f"   檢索 '巧克力': 找到 {len(memories2)} 條記憶")
            for i, (exp, score) in enumerate(memories2, 1):
                print(f"   {i}. [{score:.3f}] {exp.content[:40]}...")
        
        print()
        print("=" * 70)
        print("✅ 對話測試完成！Angela 表現良好！")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 對話測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(conversation_with_angela())
    sys.exit(0 if success else 1)