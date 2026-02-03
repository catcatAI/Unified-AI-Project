"""
HSM Storage Diagnostic Script
檢查 HSM 存儲的實際內容
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def diagnose_hsm_storage():
    """診斷 HSM 存儲問題"""
    
    print("=" * 70)
    print("🔍 HSM 存儲診斷")
    print("=" * 70)
    
    try:
        from apps.backend.src.core.orchestrator import CognitiveOrchestrator
        
        print("🔄 初始化 Orchestrator...")
        angela = CognitiveOrchestrator()
        print("✅ 初始化完成\n")
        
        # 檢查初始狀態
        print(f"📊 初始 HSM 記憶數量: {len(angela.hsm.experiences) if angela.hsm else 0}")
        print()
        
        # 模擬用戶輸入
        test_input = "你好！我是小明"
        print(f"👤 用戶輸入: '{test_input}'")
        print()
        
        # 處理輸入
        result = await angela.process_user_input(test_input)
        print(f"🤖 助手回應: '{result.get('response', '')[:60]}...'")
        print()
        
        # 檢查 HSM 中的所有記憶
        if angela.hsm:
            print(f"📊 處理後 HSM 記憶數量: {len(angela.hsm.experiences)}")
            print()
            print("📝 HSM 中所有記憶內容:")
            print("-" * 70)
            
            for i, exp in enumerate(angela.hsm.experiences):
                print(f"\n記憶 {i+1}:")
                print(f"  內容: '{exp.content}'")
                print(f"  類型: {exp.metadata.get('type', 'unknown')}")
                print(f"  角色: {exp.context.get('role', 'unknown')}")
                print(f"  重要性: {exp.importance}")
            
            print("\n" + "-" * 70)
            print("\n🔍 檢索測試 - 搜尋 '小明':")
            memories = angela.hsm.retrieve_by_association("小明", top_k=5)
            print(f"   找到 {len(memories)} 條記憶")
            
            for i, (exp, score) in enumerate(memories, 1):
                print(f"   {i}. [相似度: {score:.3f}] '{exp.content[:50]}...' (類型: {exp.metadata.get('type', 'unknown')})")
            
            # 驗證問題
            print("\n" + "=" * 70)
            print("⚠️ 問題驗證:")
            
            user_memories = [exp for exp in angela.hsm.experiences if exp.metadata.get('type') == 'user_input']
            assistant_memories = [exp for exp in angela.hsm.experiences if exp.metadata.get('type') == 'assistant_response']
            
            print(f"   用戶輸入記憶數量: {len(user_memories)}")
            print(f"   助手回應記憶數量: {len(assistant_memories)}")
            
            if user_memories:
                print(f"   ✓ 找到用戶輸入記憶: '{user_memories[0].content}'")
            else:
                print(f"   ✗ 未找到用戶輸入記憶！")
            
            if not any(test_input in exp.content for exp in angela.hsm.experiences):
                print(f"   ✗ 警告: HSM 中沒有包含 '{test_input}' 的記憶！")
                print(f"   ✗ 這證實了 bug：用戶輸入未被正確存儲")
        
        print("\n" + "=" * 70)
        print("✅ 診斷完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 診斷失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(diagnose_hsm_storage())
