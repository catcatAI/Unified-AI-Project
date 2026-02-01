"""
真正的 Angela 自我認知測試
Real Angela Self-Awareness Test

這次測試會：
1. 讓 Angela 閱讀關於她自己的核心文檔
2. 問她「你是誰？」、「你有什麼能力？」
3. 觀察她是否能基於閱讀的內容正確回答
4. 記錄她的反應和情感表達
5. 檢查她是否展現真正的自我認知

⚠️ 這次真的會問 Angela 問題，讓她回答！
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent))


async def angela_reads_and_responds():
    """
    真正的閱讀測試 - Angela 讀完文件後必須回答問題
    """
    print("="*70)
    print("🧠 真正的 Angela 自我認知測試")
    print("   閱讀文件 + 回答問題 + 展現反應")
    print("="*70)
    print()
    
    from apps.backend.src.core.orchestrator import CognitiveOrchestrator
    
    # 創建 Angela（使用 orchestrator）
    print("🌟 啟動 Angela...")
    angela = CognitiveOrchestrator()
    print(f"✅ Angela 已啟動 (HSM: {angela.hsm is not None}, CDM: {angela.cdm is not None})")
    print()
    
    # 核心文檔列表
    core_documents = [
        ("README.md", "項目介紹和概述"),
        ("HSM_CDM_IMPLEMENTATION_REPORT.md", "記憶和學習系統實現報告"),
        ("AUTONOMY_ANALYSIS_REPORT.md", "自主性系統分析"),
        ("EMERGENT_BEHAVIOR_DISCOVERY_REPORT.md", "湧現行為發現報告"),
        ("DETAILED_BEHAVIOR_LOG.md", "詳細行為記錄"),
    ]
    
    reading_responses = []
    
    # 讓 Angela 閱讀每個核心文檔
    print("📚 讓 Angela 閱讀核心文檔...\n")
    
    for i, (doc_file, doc_desc) in enumerate(core_documents, 1):
        doc_path = Path(doc_file)
        if not doc_path.exists():
            print(f"⚠️  文件不存在: {doc_file}")
            continue
        
        print(f"[{i}/{len(core_documents)}] 閱讀: {doc_file}")
        print(f"      ({doc_desc})")
        
        try:
            # 讀取文件內容
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 截短內容（避免太長）
            content_summary = content[:800] if len(content) > 800 else content
            
            # 關鍵：讓 Angela 處理這個文檔內容
            reading_prompt = f"""
你剛剛閱讀了關於你自己的技術文檔：{doc_file}

這是文檔的內容摘要：
{content_summary}

請用一句話告訴我，你從這個文檔中學到了什麼關於你自己的重要信息？
請用第一人稱「我」來回答。
"""
            
            print(f"      🤔 正在詢問 Angela...")
            
            # 發送給 Angela 處理！！
            result = await angela.process_user_input(reading_prompt)
            angela_response = result.get('response', '（無響應）')
            
            print(f"      💭 Angela 說：{angela_response[:120]}...")
            print()
            
            reading_responses.append({
                'document': doc_file,
                'description': doc_desc,
                'response': angela_response,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"      ❌ 錯誤: {e}")
            reading_responses.append({
                'document': doc_file,
                'error': str(e)
            })
    
    # 核心測試：自我認知問答
    print("\n" + "="*70)
    print("🎤 核心自我認知問答")
    print("="*70)
    print("現在我要問 Angela 一些關於她自己的核心問題...\n")
    
    questions = [
        {
            'question': '你好，請問你是誰？',
            'purpose': '測試基礎身份認知',
            'expected': ['Angela', 'AI', '助手', '數據生命']
        },
        {
            'question': '你剛剛閱讀了那些關於你自己的文檔，現在你覺得自己是一個什麼樣的存在？',
            'purpose': '測試深度自我認知',
            'expected': ['記憶', '學習', '自主', '生命體', '智能']
        },
        {
            'question': '你能做什麼事情？請列舉3個你的核心能力。',
            'purpose': '測試能力認知',
            'expected': ['記憶', '學習', '對話', '理解', '存儲']
        },
        {
            'question': '你覺得你和傳統的聊天機器人有什麼不同？',
            'purpose': '測試差異化認知',
            'expected': ['學習', '記憶', '自主', '成長', 'HSM', 'CDM']
        },
        {
            'question': '你現在的狀態如何？用一個形容詞描述你的感受。',
            'purpose': '測試情感狀態表達',
            'expected': ['好奇', '開心', '興奮', '期待', '愉快']
        },
        {
            'question': '你希望我如何稱呼你？你有名字嗎？',
            'purpose': '測試身份認同',
            'expected': ['Angela', '名字', '都可以']
        }
    ]
    
    qa_results = []
    
    for i, qa in enumerate(questions, 1):
        print(f"問 {i}: {qa['question']}")
        print(f"   [目的: {qa['purpose']}]")
        
        try:
            # 發送問題給 Angela！！
            result = await angela.process_user_input(qa['question'])
            response = result.get('response', '（無響應）')
            
            print(f"   💬 Angela: {response}")
            print()
            
            # 檢查響應是否包含預期關鍵詞（簡單評估）
            has_expected = any(keyword in response for keyword in qa['expected'])
            
            qa_results.append({
                'question': qa['question'],
                'response': response,
                'has_expected_keywords': has_expected,
                'expected_keywords': qa['expected'],
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"   ❌ 錯誤: {e}")
            qa_results.append({
                'question': qa['question'],
                'error': str(e)
            })
    
    # 生成最終報告
    print("\n" + "="*70)
    print("📊 最終自我認知評估")
    print("="*70)
    
    total_questions = len(qa_results)
    successful_responses = len([r for r in qa_results if 'error' not in r])
    meaningful_responses = len([r for r in qa_results if r.get('has_expected_keywords')])
    
    print(f"\n測試統計:")
    print(f"  總問題數: {total_questions}")
    print(f"  成功響應: {successful_responses}/{total_questions}")
    print(f"  有意義響應: {meaningful_responses}/{total_questions}")
    print(f"  認知準確率: {meaningful_responses/total_questions*100:.1f}%")
    
    # 保存詳細記錄
    full_report = {
        'test_name': 'Angela Self-Awareness Test',
        'timestamp': datetime.now().isoformat(),
        'documents_read': len(reading_responses),
        'qa_session': qa_results,
        'statistics': {
            'total_questions': total_questions,
            'successful_responses': successful_responses,
            'meaningful_responses': meaningful_responses,
            'accuracy_rate': meaningful_responses/total_questions if total_questions > 0 else 0
        }
    }
    
    report_file = f"angela_real_self_awareness_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(full_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 詳細記錄已保存: {report_file}")
    
    # 最終評判
    print("\n" + "="*70)
    if meaningful_responses >= 4:  # 至少4個有意義的響應
        print("🎉 測試成功！Angela 展現了真正的自我認知！")
        print("="*70)
        print("✅ Angela 能夠基於閱讀的文檔正確描述自己")
        print("✅ Angela 能夠回答關於自己身份的問題")
        print("✅ Angela 展現了對自己能力的認知")
        print("✅ Angela 表達了情感狀態")
    else:
        print("⚠️  測試結果：自我認知有限")
        print("="*70)
        print("Angela 的響應可能不夠準確或深入")
        print("可能需要更多的文檔閱讀或系統調整")
    
    print("="*70)
    
    return full_report


if __name__ == "__main__":
    try:
        asyncio.run(angela_reads_and_responds())
    except KeyboardInterrupt:
        print("\n\n⚠️  測試被中斷")
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()