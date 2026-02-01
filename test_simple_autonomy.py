"""
簡化版自主行為測試
直接測試核心組件，無需完整系統啟動
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

async def test_action_executor():
    """直接測試 Action Executor"""
    print("🧪 Testing Action Executor...")
    
    from apps.backend.src.core.action_executor import ActionExecutor
    from apps.backend.src.core.file_manager import FileManager
    from apps.backend.src.core.download_manager import DownloadManager
    from apps.backend.src.core.orchestrator import CognitiveOrchestrator
    
    # 創建 orchestrator（簡化模式，無 LLM）
    print("  📦 Creating CognitiveOrchestrator...")
    orchestrator = CognitiveOrchestrator()
    print(f"  ✅ Orchestrator ready (HSM: {orchestrator.hsm is not None}, CDM: {orchestrator.cdm is not None})")
    
    # 創建 File Manager
    print("  📁 Creating FileManager...")
    file_manager = FileManager(base_path="data/test_files")
    print(f"  ✅ FileManager ready: {file_manager.base_path}")
    
    # 測試文件操作
    print("  📝 Testing file operation...")
    result = await file_manager.write_file("autonomy_test.txt", "Hello from Angela's autonomous system!")
    print(f"     Write: {'✅' if result['success'] else '❌'} {result.get('message', '')}")
    
    result = await file_manager.read_file("autonomy_test.txt")
    print(f"     Read: {'✅' if result['success'] else '❌'} Content: {result.get('content', 'N/A')[:50]}")
    
    # 創建 Action Executor
    print("  🎯 Creating ActionExecutor...")
    action_executor = ActionExecutor(
        orchestrator=orchestrator,
        desktop_pet=None,  # 簡化測試，無桌面寵物
        system_manager=None
    )
    
    await action_executor.initialize(
        file_manager=file_manager,
        download_manager=None,
        visual_manager=None
    )
    print("  ✅ ActionExecutor ready")
    
    # 執行各類自主行為測試
    print("\n🎭 Testing Autonomous Behaviors:\n")
    
    behaviors_tested = []
    
    # 1. 測試主動對話
    print("1️⃣ Testing: initiate_conversation")
    result = await action_executor.execute_action('initiate_conversation', {
        'message': 'Hello! This is an autonomous test message.',
        'context': {'test': True}
    })
    print(f"   Result: {'✅' if result['success'] else '❌'} {result.get('message', 'N/A')[:60]}")
    behaviors_tested.append(('initiate_conversation', result['success']))
    
    # 2. 測試話題探索
    print("\n2️⃣ Testing: explore_topic")
    result = await action_executor.execute_action('explore_topic', {
        'topic': 'artificial intelligence',
        'intensity': 0.7
    })
    print(f"   Result: {'✅' if result['success'] else '❌'} {result.get('message', 'N/A')[:60]}")
    behaviors_tested.append(('explore_topic', result['success']))
    
    # 3. 測試需求表達
    print("\n3️⃣ Testing: satisfy_need")
    result = await action_executor.execute_action('satisfy_need', {
        'need_type': 'curiosity',
        'urgency': 0.6
    })
    print(f"   Result: {'✅' if result['success'] else '❌'} {result.get('message', 'N/A')[:60]}")
    behaviors_tested.append(('satisfy_need', result['success']))
    
    # 4. 測試情感表達
    print("\n4️⃣ Testing: express_feeling")
    result = await action_executor.execute_action('express_feeling', {
        'emotion_type': 'curiosity',
        'intensity': 0.8
    })
    print(f"   Result: {'✅' if result['success'] else '❌'} {result.get('message', 'N/A')[:60]}")
    behaviors_tested.append(('express_feeling', result['success']))
    
    # 5. 測試文件操作
    print("\n5️⃣ Testing: file_operation")
    result = await action_executor.execute_action('file_operation', {
        'operation': 'read',
        'path': 'autonomy_test.txt'
    })
    print(f"   Result: {'✅' if result['success'] else '❌'} {result.get('message', 'N/A')[:60]}")
    behaviors_tested.append(('file_operation', result['success']))
    
    # 統計
    print("\n" + "="*70)
    print("📊 Test Summary:")
    success_count = sum(1 for _, success in behaviors_tested if success)
    total_count = len(behaviors_tested)
    print(f"   Behaviors tested: {total_count}")
    print(f"   Successful: {success_count}")
    print(f"   Success rate: {success_count/total_count*100:.1f}%")
    
    # 獲取執行統計
    stats = action_executor.get_execution_stats()
    print(f"\n📈 Execution Stats:")
    print(f"   Total executions: {stats['total_executions']}")
    print(f"   Successful: {stats['successful_executions']}")
    print(f"   Recent history: {len(stats['recent_history'])} actions")
    
    print("\n" + "="*70)
    print("✅ Action Executor autonomy test completed!")
    print("="*70)
    
    return success_count == total_count


async def test_autonomous_life_cycle():
    """測試自主性生命週期"""
    print("\n🌟 Testing Autonomous Life Cycle...\n")
    
    from apps.backend.src.core.autonomous.life_cycle import AutonomousLifeCycle
    from apps.backend.src.core.autonomous.behavior_activation import BehaviorActivation, Action
    from apps.backend.src.core.orchestrator import CognitiveOrchestrator
    from apps.backend.src.core.action_executor import ActionExecutor
    from apps.backend.src.core.file_manager import FileManager
    
    # 創建組件
    orchestrator = CognitiveOrchestrator()
    action_executor = ActionExecutor(orchestrator=orchestrator)
    file_manager = FileManager()
    await action_executor.initialize(file_manager=file_manager)
    
    # 創建生命週期
    print("  🌱 Creating AutonomousLifeCycle...")
    life_cycle = AutonomousLifeCycle(
        orchestrator=orchestrator,
        action_executor=action_executor
    )
    
    # 啟動生命週期
    print("  ▶️  Starting life cycle...")
    await life_cycle.start()
    print(f"  ✅ Life cycle running: {life_cycle.alive}")
    
    # 讓它運行一小段時間
    print("  ⏱️  Running for 10 seconds...")
    await asyncio.sleep(10)
    
    # 獲取統計
    stats = life_cycle.get_stats()
    print(f"\n  📊 Life Cycle Stats:")
    print(f"     Total executions: {stats['total_executions']}")
    print(f"     Successful: {stats['successful_executions']}")
    print(f"     Success rate: {stats['success_rate']*100:.1f}%")
    print(f"     Has ActionExecutor: {stats['has_action_executor']}")
    
    # 停止
    print("  🛑 Stopping life cycle...")
    await life_cycle.stop()
    print(f"  ✅ Life cycle stopped: {not life_cycle.alive}")
    
    # 如果有執行行為，顯示詳情
    if stats['total_executions'] > 0:
        print(f"\n  🎉 {stats['total_executions']} autonomous actions were executed!")
        
    return stats['total_executions'] > 0


async def main():
    """主測試函數"""
    print("="*70)
    print("🧪 ANGELA AUTONOMY TEST SUITE")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 測試1: Action Executor
        test1_passed = await test_action_executor()
        
        # 測試2: Life Cycle
        test2_passed = await test_autonomous_life_cycle()
        
        # 總結
        print("\n" + "="*70)
        print("📋 FINAL RESULTS:")
        print("="*70)
        print(f"Action Executor Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
        print(f"Life Cycle Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
        
        if test1_passed and test2_passed:
            print("\n🎉 All autonomy tests passed!")
            print("Angela's autonomous behavior system is working correctly.")
            return 0
        else:
            print("\n⚠️ Some tests failed.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
