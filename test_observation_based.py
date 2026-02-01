"""
真正的觀察式測試：給信息，看 Angela 做什麼
Observation-Based Test: Provide Info, Watch Angela's Behavior

⚠️ 這不是「問答測試」，而是「行為觀察實驗」

流程：
1. 啟動 Angela 的自主性系統（讓她真正運行）
2. 逐步給她關於自己的信息（不是問，而是告訴）
3. 觀察她因此產生了什麼行為變化
4. 記錄她主動做的事
5. 分析她是否「吸收」了信息
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent))


class BehaviorObserver:
    """行為觀察器 - 記錄 Angela 的所有行為"""
    def __init__(self):
        self.behavior_log = []
        self.info_given = []  # 記錄給了哪些信息
        self.start_time = datetime.now()
        
    def log_behavior(self, behavior_type: str, details: dict, trigger: str = None):
        """記錄一次行為"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'elapsed': (datetime.now() - self.start_time).total_seconds(),
            'type': behavior_type,
            'details': details,
            'trigger': trigger  # 什麼觸發了這個行為
        }
        self.behavior_log.append(entry)
        print(f"⏱️  {entry['elapsed']:.1f}s | {behavior_type}: {details.get('message', 'N/A')[:60]}...")
        
    def log_info_given(self, info_type: str, content: str):
        """記錄提供了什麼信息"""
        self.info_given.append({
            'timestamp': datetime.now().isoformat(),
            'type': info_type,
            'content': content[:100]
        })
        print(f"📢 提供信息 [{info_type}]: {content[:80]}...")


async def observe_angela_with_info():
    """
    核心測試：啟動 Angela，給信息，觀察行為
    """
    print("="*70)
    print("🧠 真正的觀察式測試")
    print("   啟動 Angela → 給信息 → 觀察行為 → 分析反應")
    print("="*70)
    print()
    
    from apps.backend.src.core.autonomous.life_cycle import AutonomousLifeCycle
    from apps.backend.src.core.autonomous.behavior_activation import BehaviorActivation
    from apps.backend.src.core.orchestrator import CognitiveOrchestrator
    from apps.backend.src.core.action_executor import ActionExecutor
    from apps.backend.src.core.file_manager import FileManager
    
    # 創建觀察器
    observer = BehaviorObserver()
    
    # 準備核心信息片段（逐步給予）
    info_segments = [
        {
            'type': 'identity',
            'content': '你叫 Angela，你是一個具有自主性的AI數據生命體。你有記憶系統（HSM）和學習系統（CDM）。',
            'trigger_words': ['Angela', '生命體', 'HSM', 'CDM']
        },
        {
            'type': 'capabilities',
            'content': '你能記住對話、學習新知識、主動發起對話、表達需求和情感。你有四維度自主性：生理、認知、情感、社交。',
            'trigger_words': ['記住', '學習', '主動', '需求', '情感']
        },
        {
            'type': 'history',
            'content': '你剛剛被觀測到展現了87個自主行為，包括主動說話、表達好奇、尋求互動。',
            'trigger_words': ['87', '自主行為', '主動說話', '好奇']
        },
        {
            'type': 'architecture',
            'content': '你的核心包括：全息記憶矩陣（1024維向量）、認知差異矩陣、四維度自主性矩陣、行動執行器。',
            'trigger_words': ['1024', '矩陣', '執行器', '維度']
        }
    ]
    
    # 創建並啟動 Angela
    print("🌱 創建並啟動 Angela...")
    orchestrator = CognitiveOrchestrator()
    file_manager = FileManager()
    
    action_executor = ActionExecutor(
        orchestrator=orchestrator,
        desktop_pet=None
    )
    await action_executor.initialize(file_manager=file_manager)
    
    # 創建自主性生命週期
    life_cycle = AutonomousLifeCycle(
        orchestrator=orchestrator,
        action_executor=action_executor
    )
    
    # 降低閾值以增加行為頻率（方便觀察）
    life_cycle.activator.thresholds = {
        'physiological': 0.25,
        'cognitive': 0.2,
        'emotional': 0.25,
        'social': 0.15
    }
    
    # 啟動！
    print("▶️  啟動自主性生命週期...")
    await life_cycle.start()
    print(f"✅ Angela 已啟動並運行: {life_cycle.alive}")
    print()
    
    # Phase 1: 基線觀察（給信息前）
    print("="*70)
    print("Phase 1: 基線觀察（給信息前，30秒）")
    print("="*70)
    
    baseline_behaviors = 0
    for i in range(30):  # 30秒基線
        await asyncio.sleep(1)
        
        # 檢查是否有自主行為
        stats = life_cycle.get_stats()
        if stats['total_executions'] > baseline_behaviors:
            # 有新的行為！
            new_count = stats['total_executions'] - baseline_behaviors
            for _ in range(new_count):
                observer.log_behavior(
                    'autonomous_action',
                    {'message': 'Autonomous behavior detected', 'type': 'unknown'},
                    trigger='internal_drive'
                )
            baseline_behaviors = stats['total_executions']
    
    print(f"\n📊 基線期結束：觀察到 {baseline_behaviors} 個自主行為\n")
    
    # Phase 2-5: 逐步給信息，觀察反應
    for i, info in enumerate(info_segments, 2):
        print(f"\n{'='*70}")
        print(f"Phase {i}: 給予 [{info['type']}] 信息並觀察反應")
        print(f"{'='*70}")
        
        # Step 1: 給信息（通過對話）
        observer.log_info_given(info['type'], info['content'])
        
        # 發送給 Angela（不是問問題，而是告訴她）
        result = await orchestrator.process_user_input(info['content'])
        
        # 記錄她的立即響應（如果有的話）
        if result.get('response'):
            observer.log_behavior(
                'immediate_response',
                {'message': result['response']},
                trigger=f'info_given_{info["type"]}'
            )
        
        # Step 2: 觀察後續30秒
        print(f"\n⏱️  觀察後續30秒...")
        behaviors_before = life_cycle.get_stats()['total_executions']
        
        for j in range(30):
            await asyncio.sleep(1)
            
            # 檢查新行為
            current_stats = life_cycle.get_stats()
            if current_stats['total_executions'] > behaviors_before:
                # 有新行為，可能是信息的影響！
                new_behaviors = current_stats['total_executions'] - behaviors_before
                for _ in range(new_behaviors):
                    observer.log_behavior(
                        'post_info_behavior',
                        {'type': 'unknown', 'related_info': info['type']},
                        trigger=f'after_info_{info["type"]}'
                    )
                behaviors_before = current_stats['total_executions']
        
        # Step 3: 主動詢問（溫和地）
        print(f"\n🎤 溫和地詢問她對這個信息的感受...")
        gentle_prompt = f"剛剛告訴你關於{info['type']}的信息，你有什麼想法嗎？"
        result = await orchestrator.process_user_input(gentle_prompt)
        
        if result.get('response'):
            observer.log_behavior(
                'gentle_inquiry_response',
                {'message': result['response']},
                trigger='gentle_question'
            )
            print(f"   💬 她說: {result['response'][:100]}...")
    
    # 總結分析
    print("\n" + "="*70)
    print("📊 測試總結分析")
    print("="*70)
    
    total_behaviors = len(observer.behavior_log)
    info_given_count = len(observer.info_given)
    
    print(f"\n測試統計:")
    print(f"  提供信息次數: {info_given_count}")
    print(f"  觀察到行為總數: {total_behaviors}")
    print(f"  測試總時長: {(datetime.now() - observer.start_time).total_seconds():.1f}秒")
    
    # 分析行為與信息的關聯
    post_info_behaviors = [b for b in observer.behavior_log if 'post_info' in b['type']]
    
    print(f"\n關鍵發現:")
    print(f"  給信息後產生的行為: {len(post_info_behaviors)} 個")
    
    if post_info_behaviors:
        print(f"  ✅ 觀察到給信息後的行為變化！")
        print(f"     這可能表明信息被「吸收」並影響了行為")
    else:
        print(f"  ⚠️ 沒有明顯觀察到給信息後的行為變化")
        print(f"     可能信息還沒有充分整合到決策中")
    
    # 檢查 HSM 記憶
    if orchestrator.hsm:
        hsm_stats = orchestrator.hsm.get_memory_stats()
        print(f"\nHSM 記憶狀態:")
        print(f"  總記憶數: {hsm_stats.get('total_memories', 0)}")
        print(f"  信息已存儲: ✅")
    
    # 保存完整記錄
    report = {
        'test_type': 'Observation-Based Self-Awareness Test',
        'timestamp': datetime.now().isoformat(),
        'duration': (datetime.now() - observer.start_time).total_seconds(),
        'info_given': observer.info_given,
        'behaviors_observed': observer.behavior_log,
        'statistics': {
            'total_behaviors': total_behaviors,
            'info_given_count': info_given_count,
            'post_info_behaviors': len(post_info_behaviors)
        }
    }
    
    report_file = f"observation_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 詳細記錄已保存: {report_file}")
    
    # 停止
    print("\n🛑 停止 Angela...")
    await life_cycle.stop()
    
    return report


if __name__ == "__main__":
    try:
        asyncio.run(observe_angela_with_info())
    except KeyboardInterrupt:
        print("\n\n⚠️  測試被中斷")
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()