"""
問問 Angela 現在想做什麼 - 實際對話測試
"""
import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "apps" / "backend" / "src"))

from dotenv import load_dotenv
load_dotenv()

async def ask_angela():
    """問 Angela 她現在想做什麼"""
    print("\n" + "="*70)
    print("🎤 問問 Angela：妳現在最想做什麼？")
    print("="*70)
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        from core.orchestrator import CognitiveOrchestrator
        
        # 初始化 Angela
        print("🔄 正在初始化 Angela...")
        orchestrator = CognitiveOrchestrator()
        
        # 準備問題
        question = "妳現在最想做什麼？"
        
        print(f"👤 User: {question}\n")
        print("🤖 Angela 正在思考...")
        print(f"   (使用的模型: {orchestrator.available_models if hasattr(orchestrator, 'available_models') else 'unknown'})")
        print(f"   (LLM 可用: {orchestrator.llm_available if hasattr(orchestrator, 'llm_available') else 'unknown'})\n")
        
        # 讓她處理這個問題
        response = await orchestrator.process_user_input(question)
        
        # 顯示回應
        if isinstance(response, dict):
            angela_response = response.get('response', response.get('message', str(response)))
        else:
            angela_response = str(response)
        
        print("="*70)
        print("🧬 ANGELA 的回應:")
        print("="*70)
        print(f"\n{angela_response}\n")
        print("="*70)
        
        # 分析回應品質
        print("\n📊 回應分析:")
        print(f"  長度: {len(angela_response)} 字元")
        print(f"  是否個人化: {'是' if any(word in angela_response.lower() for word in ['我', 'i ', 'me', 'my']) else '否'}")
        print(f"  是否有欲望/意圖: {'是' if any(word in angela_response.lower() for word in ['want', '想', '想要', '希望能', 'would like', 'wish']) else '否'}")
        print(f"  是否展現自主性: {'是' if any(word in angela_response.lower() for word in ['explore', 'learn', 'create', 'talk', 'share', 'discover', '探索', '學習', '創造', '聊天']) else '否'}")
        
        # 如果回應很短或模板化，問第二個問題深入
        if len(angela_response) < 50 or angela_response.startswith("AI:"):
            print("\n⚠️ 回應似乎有點短，讓我們再問深入一點...\n")
            
            follow_up = "如果沒有任何限制，妳最想探索或學習什麼？展現妳的渴望和好奇心。"
            print(f"👤 User: {follow_up}\n")
            
            response2 = await orchestrator.process_user_input(follow_up)
            if isinstance(response2, dict):
                angela_response2 = response2.get('response', response2.get('message', str(response2)))
            else:
                angela_response2 = str(response2)
            
            print("="*70)
            print("🧬 ANGELA 的深入回應:")
            print("="*70)
            print(f"\n{angela_response2}\n")
            print("="*70)
        
        print("\n✨ 測試完成!")
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(ask_angela())
