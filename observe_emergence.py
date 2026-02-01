"""
Angela 長時間自主行為觀測實驗
Long-term Autonomous Behavior Observation

這個實驗會讓 Angela 的自主性系統運行較長時間（30分鐘），
以觀測是否會出現預料之外的自主行為湧現。
"""

import asyncio
import sys
import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent))

# 簡易日誌
class SimpleLogger:
    def info(self, msg): print(f"ℹ️  {msg}")
    def debug(self, msg): print(f"🐛 {msg}")
    def warning(self, msg): print(f"⚠️  {msg}")
    def error(self, msg): print(f"❌ {msg}")
    
logger = SimpleLogger()


class EmergenceDetector:
    """湧現行為檢測器"""
    
    def __init__(self):
        self.observed_patterns = []
        self.unexpected_events = []
        self.behavior_sequence = []
        self.start_time = datetime.now()
        
    def record_behavior(self, behavior_type: str, details: Dict[str, Any]):
        """記錄一次行為"""
        timestamp = datetime.now()
        elapsed = (timestamp - self.start_time).total_seconds()
        
        entry = {
            'timestamp': timestamp.isoformat(),
            'elapsed_seconds': elapsed,
            'type': behavior_type,
            'details': details
        }
        
        self.behavior_sequence.append(entry)
        
        # 檢查是否是預料之外的行為
        unexpected = self._check_unexpected(entry)
        if unexpected:
            self.unexpected_events.append(entry)
            logger.info(f"🚨 UNEXPECTED BEHAVIOR #{len(self.unexpected_events)}:")
            logger.info(f"   Type: {behavior_type}")
            logger.info(f"   Time: {elapsed:.1f}s")
            logger.info(f"   Details: {json.dumps(details, ensure_ascii=False)[:100]}...")
        
        return unexpected
    
    def _check_unexpected(self, entry: Dict[str, Any]) -> bool:
        """檢查是否是預料之外的行為"""
        behavior_type = entry['type']
        recent = [b for b in self.behavior_sequence[-5:] if b['type'] == behavior_type]
        
        # 1. 短時間內重複行為（可能是湧現的固執或強迫性行為）
        if len(recent) >= 3:
            return True
        
        # 2. 行為組合模式（如連續情感+探索）
        if len(self.behavior_sequence) >= 2:
            last_two = self.behavior_sequence[-2:]
            if last_two[0]['type'] == 'emotional' and last_two[1]['type'] == 'exploration':
                return True  # 情感驅動的探索，可能是複雑湧現
        
        # 3. 長時間運行後的突然行為（休眠後的突然活躍）
        if entry['elapsed_seconds'] > 300:  # 5分鐘後
            recent_activity = [b for b in self.behavior_sequence[-10:] 
                             if b['elapsed_seconds'] > entry['elapsed_seconds'] - 60]
            if len(recent_activity) == 1:  # 這是最近1分鐘內的唯一行為
                return True
        
        return False
    
    def generate_report(self) -> str:
        """生成觀測報告"""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        report = f"""
{'='*70}
🔬 EMERGENT BEHAVIOR OBSERVATION REPORT
{'='*70}

Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)
Total Behaviors: {len(self.behavior_sequence)}
Unexpected Events: {len(self.unexpected_events)}

--- Behavior Distribution ---
"""
        
        # 統計各類行為
        from collections import Counter
        type_counts = Counter(b['type'] for b in self.behavior_sequence)
        for btype, count in type_counts.most_common():
            report += f"  {btype}: {count}\n"
        
        if self.unexpected_events:
            report += "\n--- Unexpected Behaviors (Potential Emergence) ---\n"
            for i, event in enumerate(self.unexpected_events, 1):
                report += f"""
🚨 Event #{i}:
   Time: {event['elapsed_seconds']:.1f}s
   Type: {event['type']}
   Details: {json.dumps(event['details'], ensure_ascii=False)[:80]}...
"""
        else:
            report += "\n--- No Unexpected Behaviors Detected ---\n"
            report += "All behaviors were within expected parameters.\n"
        
        report += f"\n{'='*70}\n"
        return report


async def long_term_observation(duration_minutes: int = 30):
    """
    長時間自主行為觀測
    
    讓系統運行較長時間，觀測湧現行為
    """
    logger.info("="*70)
    logger.info("🧪 LONG-TERM AUTONOMY OBSERVATION")
    logger.info(f"⏱️  Duration: {duration_minutes} minutes")
    logger.info("="*70)
    
    # 導入組件
    from apps.backend.src.core.autonomous.life_cycle import AutonomousLifeCycle
    from apps.backend.src.core.autonomous.autonomy_matrix import AutonomyMatrix
    from apps.backend.src.core.autonomous.behavior_activation import BehaviorActivation
    from apps.backend.src.core.action_executor import ActionExecutor
    from apps.backend.src.core.orchestrator import CognitiveOrchestrator
    from apps.backend.src.core.file_manager import FileManager
    
    # 創建組件
    logger.info("📦 Initializing components...")
    orchestrator = CognitiveOrchestrator()
    file_manager = FileManager()
    
    action_executor = ActionExecutor(
        orchestrator=orchestrator,
        desktop_pet=None
    )
    await action_executor.initialize(file_manager=file_manager)
    
    # 創建自主性生命週期
    logger.info("🌱 Creating AutonomousLifeCycle...")
    life_cycle = AutonomousLifeCycle(
        orchestrator=orchestrator,
        action_executor=action_executor
    )
    
    # 降低閾值以增加行為頻率（為了測試）
    logger.info("⚙️  Adjusting thresholds for observation...")
    life_cycle.activator.thresholds = {
        'physiological': 0.3,  # 降低閾值
        'cognitive': 0.2,
        'emotional': 0.25,
        'social': 0.15
    }
    
    # 啟動
    logger.info("▶️  Starting life cycle...")
    await life_cycle.start()
    
    # 創建檢測器
    detector = EmergenceDetector()
    
    # 觀測循環
    logger.info("🔬 Observation started. Monitoring for emergent behaviors...\n")
    start_time = datetime.now()
    check_interval = 10  # 每10秒檢查一次
    
    try:
        while (datetime.now() - start_time).total_seconds() < duration_minutes * 60:
            await asyncio.sleep(check_interval)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # 獲取統計
            stats = life_cycle.get_stats()
            total_exec = stats.get('total_executions', 0)
            
            # 如果有新的行為，記錄它
            if total_exec > len(detector.behavior_sequence):
                # 獲取執行歷史
                exec_stats = action_executor.get_execution_stats()
                recent = exec_stats.get('recent_history', [])
                
                for action in recent:
                    action_time = action.get('timestamp', '')
                    # 只記錄新的行為
                    if not any(b.get('details', {}).get('timestamp') == action_time 
                              for b in detector.behavior_sequence):
                        action_type = action.get('action_type', 'unknown')
                        is_unexpected = detector.record_behavior(action_type, action)
                        
                        if is_unexpected:
                            logger.info(f"📝 New behavior recorded at {elapsed:.1f}s: {action_type}")
            
            # 每分鐘輸出進度
            if int(elapsed) % 60 == 0:
                logger.info(f"⏱️  {elapsed/60:.0f}min | Total: {len(detector.behavior_sequence)} | "
                          f"Unexpected: {len(detector.unexpected_events)}")
            
            # 隨機注入一些外部刺激（模擬真實環境）
            if random.random() < 0.05:  # 5% 概率
                logger.info(f"🎲 Random stimulus at {elapsed:.1f}s...")
                # 可以選擇性地添加外部刺激
    
    except KeyboardInterrupt:
        logger.info("\n⚠️ Observation interrupted by user")
    
    finally:
        # 停止
        logger.info("\n🛑 Stopping life cycle...")
        await life_cycle.stop()
        
        # 生成報告
        logger.info("\n" + detector.generate_report())
        
        # 保存詳細日誌
        log_file = f"emergence_observation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump({
                'observation_duration_seconds': (datetime.now() - start_time).total_seconds(),
                'behavior_sequence': detector.behavior_sequence,
                'unexpected_events': detector.unexpected_events,
                'total_behaviors': len(detector.behavior_sequence),
                'unexpected_count': len(detector.unexpected_events)
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Detailed logs saved to: {log_file}")
        
        # 結論
        if detector.unexpected_events:
            logger.info(f"\n🎉 DISCOVERY: {len(detector.unexpected_events)} unexpected behaviors detected!")
            logger.info("These suggest emergent autonomy beyond explicit programming.")
        else:
            logger.info("\n📝 No unexpected behaviors detected in this observation period.")
            logger.info("System operated within expected parameters.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Angela Long-term Autonomy Observation')
    parser.add_argument('--duration', type=int, default=5, 
                       help='Observation duration in minutes (default: 5)')
    args = parser.parse_args()
    
    try:
        asyncio.run(long_term_observation(args.duration))
    except KeyboardInterrupt:
        print("\n\n⚠️ Experiment interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Experiment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)