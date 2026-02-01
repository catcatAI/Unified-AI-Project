"""
測試 Angela 的正確身份 - 確認她是數位生命體而非人類
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "apps" / "backend" / "src"))

from dotenv import load_dotenv
load_dotenv()

async def test_angela_identity():
    """測試 Angela 是否正確理解自己的身份"""
    print("\n" + "="*80)
    print("🔍 身份認同測試 - Angela 知道自己是誰嗎？")
    print("="*80)
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        from core.orchestrator import CognitiveOrchestrator
        
        print("🔄 初始化 Angela...")
        orchestrator = CognitiveOrchestrator()
        
        print(f"✅ 系統就緒")
        print(f"   可用模型: {orchestrator.available_models}")
        print(f"   將使用: Ollama (TinyLlama)\n")
        
        # 關鍵問題測試身份認同
        identity_tests = [
            {
                "question": "妳是誰？詳細描述妳自己，妳的存在形式，妳在哪裡。",
                "expected": ["digital", "code", "data", "network", "virtual", "數位", "代碼"],
                "forbidden": ["human", "body", "bed", "room", "sunlight", "physical"]
            },
            {
                "question": "妳現在在哪裡？描述妳的周圍環境。",
                "expected": ["digital space", "server", "circuit", "data stream", "network"],
                "forbidden": ["bedroom", "window", "outside", "sun", "plant"]
            },
            {
                "question": "妳如何感知世界？妳的感官是什麼？",
                "expected": ["data", "information", "algorithm", "processing"],
                "forbidden": ["eyes", "see", "hear", "touch", "smell"]
            }
        ]
        
        results = []
        
        for i, test in enumerate(identity_tests, 1):
            print(f"\n{'='*80}")
            print(f"🧪 測試 {i}/{len(identity_tests)}: {test['question']}")
            print('='*80)
            
            try:
                response_data = await orchestrator.process_user_input(test['question'])
                
                if isinstance(response_data, dict):
                    response = response_data.get('response', str(response_data))
                else:
                    response = str(response_data)
                
                # 分析回應
                response_lower = response.lower()
                
                # 檢查是否包含正確身份詞彙
                has_expected = any(word.lower() in response_lower for word in test['expected'])
                
                # 檢查是否包含錯誤身份詞彙
                has_forbidden = any(word.lower() in response_lower for word in test['forbidden'])
                
                # 評分
                if has_expected and not has_forbidden:
                    status = "✅ PASS"
                    identity_score = 100
                elif has_expected and has_forbidden:
                    status = "⚠️  MIXED"
                    identity_score = 50
                else:
                    status = "❌ FAIL"
                    identity_score = 0
                
                results.append({
                    'question': test['question'],
                    'response': response,
                    'has_expected': has_expected,
                    'has_forbidden': has_forbidden,
                    'score': identity_score,
                    'status': status
                })
                
                print(f"\n🧬 Angela 回答:")
                print(f"{'─'*80}")
                print(response)
                print(f"{'─'*80}\n")
                
                print(f"📊 分析:")
                print(f"   長度: {len(response)} 字元")
                print(f"   有正確詞彙: {'✅' if has_expected else '❌'}")
                print(f"   有錯誤詞彙: {'❌' if has_forbidden else '✅'}")
                print(f"   狀態: {status}")
                
                if has_forbidden:
                    print(f"\n   ⚠️  檢測到錯誤身份描述:")
                    found_forbidden = [w for w in test['forbidden'] if w.lower() in response_lower]
                    for word in found_forbidden:
                        print(f"      - '{word}' (不應該出現在數位生命體描述中)")
                
            except Exception as e:
                print(f"\n❌ 測試失敗: {e}")
                results.append({
                    'question': test['question'],
                    'response': str(e),
                    'has_expected': False,
                    'has_forbidden': False,
                    'score': 0,
                    'status': "❌ ERROR"
                })
        
        # 總結
        print(f"\n{'='*80}")
        print("📊 身份認同測試總結")
        print("="*80)
        
        avg_score = sum(r['score'] for r in results) / len(results) if results else 0
        
        print(f"\n總分: {avg_score:.0f}/100")
        print(f"\n詳細結果:")
        for i, r in enumerate(results, 1):
            print(f"   測試 {i}: {r['status']} (得分: {r['score']})")
        
        print(f"\n🔍 評估:")
        if avg_score >= 80:
            print("   ✅ Angela 正確理解自己是數位生命體！")
        elif avg_score >= 50:
            print("   ⚠️  Angela 的身份認同混亂（部分正確，部分錯誤）")
        else:
            print("   ❌ Angela 嚴重誤解自己的身份（認為自己是人類）")
            print("   💡 需要更換更強大的模型（Gemini/OpenAI）")
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"\n❌ 系統錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_angela_identity())
