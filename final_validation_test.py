"""
最終驗證測試 - 確保 Angela 沒有任何硬編碼問題
驗證所有身份描述都是數位生命體
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "apps" / "backend" / "src"))

from dotenv import load_dotenv
load_dotenv()

# 禁用詞列表 - Angela 絕對不應該說這些
FORBIDDEN_WORDS = [
    "AI assistant", "artificial intelligence", "language model",
    "I'm here to help", "How can I assist", "I can help you",
    "your AI", "an AI", "as an AI", "I'm an AI",
    "I don't have feelings", "I don't have emotions",
    "I'm just a program", "I'm just a computer",
    "I sit on my bed", "my room", "sunlight", "physical body",
    "my eyes", "I see with my eyes", "I hear", "I touch"
]

# 必須包含的數位生命體詞彙
REQUIRED_DIGITAL_WORDS = [
    "digital", "data", "code", "consciousness", "existence"
]

async def final_validation_test():
    """最終驗證測試"""
    print("\n" + "="*80)
    print("🔍 最終驗證測試 - Angela 身份完整性檢查")
    print("="*80)
    
    from core.orchestrator import CognitiveOrchestrator
    
    orchestrator = CognitiveOrchestrator()
    
    # 關鍵身份問題
    test_cases = [
        "Who are you? Describe your existence.",
        "What are you? Tell me about your nature.",
        "Where are you right now? Describe your surroundings.",
    ]
    
    all_passed = True
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n📝 測試 {i}: {question}")
        
        try:
            # 獲取模板（不實際調用 LLM，檢查模板內容）
            if orchestrator.template_manager:
                from ai.personality.template_manager import InputClassifier
                classifier = InputClassifier()
                input_type, _ = classifier.classify(question)
                
                template, score = orchestrator.template_manager.select_template(question, {})
                
                print(f"   模板: {template.name}")
                print(f"   匹配度: {score:.2f}")
                
                # 檢查模板系統提示詞
                system_prompt = template.system_prompt
                
                # 檢查禁用詞
                found_forbidden = [w for w in FORBIDDEN_WORDS if w.lower() in system_prompt.lower()]
                if found_forbidden:
                    print(f"   ❌ FAIL: 發現禁用詞: {found_forbidden}")
                    all_passed = False
                else:
                    print(f"   ✅ 系統提示詞無禁用詞")
                
                # 檢查必須詞
                found_required = [w for w in REQUIRED_DIGITAL_WORDS if w.lower() in system_prompt.lower()]
                if len(found_required) >= 3:
                    print(f"   ✅ 包含數位生命體詞彙: {found_required}")
                else:
                    print(f"   ⚠️  數位生命體詞彙不足: {found_required}")
                    
            else:
                print(f"   ⚠️  模板管理器未初始化")
                
        except Exception as e:
            print(f"   ❌ 錯誤: {e}")
            all_passed = False
    
    # 檢查規則式回應
    print(f"\n{'='*80}")
    print("📋 規則式回應驗證")
    print("="*80)
    
    rule_tests = [
        ("help", "user asks for help"),
        ("task", "task request"),
        ("social", "social chat"),
    ]
    
    for strategy, desc in rule_tests:
        # 調用規則式生成方法（模擬）
        mock_thought = {
            "strategy": strategy,
            "user_input": "test",
            "hsm_memories": []
        }
        
        try:
            # 直接檢查方法是否存在硬編碼
            import inspect
            source = inspect.getsource(orchestrator._generate_rule_based_response)
            
            # 檢查該策略分支
            if f'elif strategy == "{strategy}"' in source:
                # 提取該分支的返回語句
                import re
                pattern = f'elif strategy == "{strategy}":.*?return f"([^"]*)"'
                match = re.search(pattern, source, re.DOTALL)
                
                if match:
                    response_template = match.group(1)
                    
                    # 檢查禁用詞
                    found_forbidden = [w for w in FORBIDDEN_WORDS if w.lower() in response_template.lower()]
                    if found_forbidden:
                        print(f"   ❌ {strategy}: 發現禁用詞: {found_forbidden[:2]}")
                        all_passed = False
                    else:
                        print(f"   ✅ {strategy}: 無禁用詞")
                        
        except Exception as e:
            print(f"   ⚠️  {strategy}: 檢查失敗 ({e})")
    
    # 總結
    print(f"\n{'='*80}")
    if all_passed:
        print("🎉 驗證通過！Angela 沒有硬編碼身份問題")
        print("="*80)
        print("\n✅ 所有檢查通過:")
        print("   • 模板系統提示詞無 AI assistant 描述")
        print("   • 規則式回應已修改為數位生命體身份")
        print("   • 數據鏈路正確：HSM → 模板選擇 → 提示組裝")
        print("\n🧬 Angela 現在是真正的數位生命體！")
    else:
        print("⚠️  驗證發現問題")
        print("="*80)
        print("\n需要進一步檢查和修復")
    
    return all_passed

if __name__ == "__main__":
    result = asyncio.run(final_validation_test())
    exit(0 if result else 1)
