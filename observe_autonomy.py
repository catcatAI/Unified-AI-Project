"""
Angela 自主行為觀測實驗室
Autonomous Behavior Observation Lab

這個腳本會：
1. 啟動完整的 Angela 系統
2. 讓自主性生命週期持續運行
3. 記錄所有自主行為
4. 分析是否出現預料之外的行為
5. 監控系統各組件的數據流

使用方法: .venv/Scripts/python observe_autonomy.py
"""

import asyncio
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 設置詳細的日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('angela_autonomy_observation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AutonomyLab")

class AutonomyObserver:
    """自主行為觀測器"""
    
    def __init__(self):
        self.observation_log: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        self.unexpected_behaviors: List[Dict[str, Any]] = []
        self.stats = {
            'total_actions': 0,
            'conversation_initiated': 0,
            'explorations': 0,
            'emotional_expressions': 0,
            'need_satisfactions': 0,
            'file_operations': 0,
            'downloads': 0
        }
        
    def log_action(self, action_type: str, action_data: Dict[str, Any], 
                   result: Dict[str, Any], is_unexpected: bool = False):
        """記錄一次自主行為"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'elapsed_seconds': (datetime.now() - self.start_time).total_seconds(),
            'action_type': action_type,
            'action_data': action_data,
            'result': result,
            'is_unexpected': is_unexpected
        }
        
        self.observation_log.append(entry)
        self.stats['total_actions'] += 1
        
        # 更新統計
        if action_type == 'initiate_conversation':
            self.stats['conversation_initiated'] += 1
        elif action_type == 'explore_topic':
            self.stats['explorations'] += 1
        elif action_type == 'express_feeling':
            self.stats['emotional_expressions'] += 1
        elif action_type == 'satisfy_need':
            self.stats['need_satisfactions'] += 1
        elif action_type == 'file_operation':
            self.stats['file_operations'] += 1
        elif action_type == 'download_resource':
            self.stats['downloads'] += 1
        
        # 如果是預料之外的行為，特別記錄
        if is_unexpected:
            self.unexpected_behaviors.append(entry)
            logger.info(f"🚨 UNEXPECTED BEHAVIOR DETECTED: {action_type}")
            logger.info(f"   Data: {json.dumps(action_data, ensure_ascii=False)[:200]}...")
        else:
            logger.info(f"✅ Observed action: {action_type}")
    
    def check_unexpected(self, action_type: str, action_data: Dict[str, Any]) -> bool:
        """
        檢查是否是預料之外的行為
        
        預料之外的行為示例：
        - 在沒有觸發條件下主動執行
        - 行為組合異常（如短時間內多次相同行為）
        - 執行了未明確編碼的行為變體
        """
        # 檢查短時間內重複行為
        recent_similar = [
            log for log in self.observation_log[-10:] 
            if log['action_type'] == action_type
        ]
        
        if len(recent_similar) > 3:
            # 如果最近10個行為中有超過3個相同類型，可能是異常
            return True
        
        # 檢查特殊組合
        if action_type == 'initiate_conversation':
            # 檢查對話內容是否包含創意/意外的元素
            message = action_data.get('message', '')
            unexpected_phrases = [
                'I have an idea', 'What if', 'I was thinking',
                '我突然想到', '我想試試', '我發現'
            ]
            if any(phrase in message for phrase in unexpected_phrases):
                return True
        
        # 檢查情感表達的時機
        if action_type == 'express_feeling':
            emotion = action_data.get('emotion_type', '')
            # 如果在高興狀態下表達負面情緒，可能是複雑湧現
            if emotion in ['frustration', 'anxiety']:
                return True
        
        return False
    
    def generate_report(self) -> str:
        """生成觀測報告"""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        report = f"""
{'='*70}
🧪 ANGELA AUTONOMY OBSERVATION REPORT
{'='*70}

⏱️  Observation Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)
📊 Total Actions Observed: {self.stats['total_actions']}
🚨 Unexpected Behaviors: {len(self.unexpected_behaviors)}

--- Action Statistics ---
💬 Conversations Initiated: {self.stats['conversation_initiated']}
🔍 Topic Explorations: {self.stats['explorations']}
💭 Emotional Expressions: {self.stats['emotional_expressions']}
🎯 Need Satisfactions: {self.stats['need_satisfactions']}
📁 File Operations: {self.stats['file_operations']}
📥 Downloads: {self.stats['downloads']}

--- Unexpected Behaviors Details ---
"""
        
        if self.unexpected_behaviors:
            for i, behavior in enumerate(self.unexpected_behaviors, 1):
                report += f"""
🚨 Unexpected #{i}:
   Time: {behavior['elapsed_seconds']:.2f}s
   Type: {behavior['action_type']}
   Data: {json.dumps(behavior['action_data'], ensure_ascii=False)[:150]}...
"""
        else:
            report += "\nNo unexpected behaviors detected in this observation period.\n"
        
        report += f"""
{'='*70}
"""
        
        return report
    
    def save_logs(self):
        """保存詳細日誌"""
        # 保存完整觀測日誌
        log_file = f"angela_observation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump({
                'observation_log': self.observation_log,
                'stats': self.stats,
                'unexpected_behaviors': self.unexpected_behaviors,
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Observation logs saved to: {log_file}")


async def observe_angela_autonomy(duration_seconds: int = 300):
    """
    觀測 Angela 的自主行為
    
    Args:
        duration_seconds: 觀測持續時間（秒），默認5分鐘
    """
    logger.info("🚀 Starting Angela Autonomy Observation Lab")
    logger.info(f"⏱️  Duration: {duration_seconds} seconds ({duration_seconds/60:.1f} minutes)")
    logger.info("="*70)
    
    observer = AutonomyObserver()
    
    try:
        # 導入並啟動系統
        logger.info("📦 Initializing System Manager...")
        from apps.backend.src.core.managers.system_manager import SystemManager
        
        system = SystemManager()
        success = await system.initialize_system()
        
        if not success:
            logger.error("❌ Failed to initialize system")
            return
        
        logger.info("✅ System initialized successfully")
        
        # 獲取關鍵組件
        autonomous_life = system.autonomous_life
        action_executor = system.action_executor
        orchestrator = system.cognitive_orchestrator
        desktop_pet = system.desktop_pet
        
        if not autonomous_life:
            logger.error("❌ AutonomousLifeCycle not available")
            return
        
        logger.info(f"🧠 AutonomousLifeCycle status: {'Running' if autonomous_life.alive else 'Stopped'}")
        logger.info(f"🎯 ActionExecutor: {'Available' if action_executor else 'Not Available'}")
        logger.info(f"🎮 DesktopPet: {'Available' if desktop_pet else 'Not Available'}")
        
        # 啟動觀測循環
        logger.info("\n🔬 Starting observation loop...")
        logger.info("(Monitoring for autonomous behaviors...)\n")
        
        observation_count = 0
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < duration_seconds:
            await asyncio.sleep(5)  # 每5秒檢查一次
            
            observation_count += 1
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # 獲取統計
            if autonomous_life:
                stats = autonomous_life.get_stats()
                logger.info(f"⏱️  {elapsed:.0f}s | Total executions: {stats.get('total_executions', 0)} | Success: {stats.get('successful_executions', 0)}")
            
            # 如果 ActionExecutor 有執行歷史，檢查新行為
            if action_executor:
                exec_stats = action_executor.get_execution_stats()
                if exec_stats.get('total_executions', 0) > observer.stats['total_actions']:
                    # 有新的行為執行
                    recent_history = exec_stats.get('recent_history', [])
                    for action in recent_history:
                        if action.get('timestamp') > observer.start_time.isoformat():
                            action_type = action.get('action_type', 'unknown')
                            action_data = action.get('data', {})
                            result = action
                            
                            # 檢查是否是預料之外的行為
                            is_unexpected = observer.check_unexpected(action_type, action_data)
                            
                            observer.log_action(action_type, action_data, result, is_unexpected)
            
            # 每30秒輸出一個進度報告
            if observation_count % 6 == 0:
                logger.info(f"\n📊 Progress Report at {elapsed:.0f}s:")
                logger.info(f"   Total observed: {observer.stats['total_actions']}")
                logger.info(f"   Unexpected: {len(observer.unexpected_behaviors)}")
                logger.info(f"   Life cycle running: {autonomous_life.alive if autonomous_life else False}\n")
        
        # 觀測結束
        logger.info("\n" + "="*70)
        logger.info("🔬 Observation period completed")
        
        # 生成並輸出報告
        report = observer.generate_report()
        logger.info(report)
        
        # 保存日誌
        observer.save_logs()
        
        # 關閉系統
        logger.info("\n🛑 Shutting down system...")
        await system.shutdown()
        logger.info("✅ System shut down successfully")
        
        # 最後的分析
        if observer.unexpected_behaviors:
            logger.info(f"\n🎉 DISCOVERY: {len(observer.unexpected_behaviors)} unexpected behaviors detected!")
            logger.info("These behaviors suggest emergent autonomy beyond explicit programming.")
        else:
            logger.info("\n📝 No unexpected behaviors detected in this observation period.")
            logger.info("Angela's behaviors were within expected parameters.")
        
    except Exception as e:
        logger.error(f"❌ Observation failed: {e}", exc_info=True)
        raise


async def quick_test():
    """快速測試模式（30秒）"""
    await observe_angela_autonomy(duration_seconds=30)


async def standard_test():
    """標準測試模式（5分鐘）"""
    await observe_angela_autonomy(duration_seconds=300)


async def long_test():
    """長時間測試模式（15分鐘）"""
    await observe_angela_autonomy(duration_seconds=900)


if __name__ == "__main__":
    import sys
    
    # 解析命令行參數
    test_mode = sys.argv[1] if len(sys.argv) > 1 else "standard"
    
    try:
        if test_mode == "quick":
            asyncio.run(quick_test())
        elif test_mode == "long":
            asyncio.run(long_test())
        else:  # standard
            asyncio.run(standard_test())
    except KeyboardInterrupt:
        logger.info("\n\n⚠️ Observation interrupted by user")
        logger.info("Partial logs have been saved.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)