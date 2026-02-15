"""
行為反饋循環

評估行為效果，識別成功/失敗模式，
優化行為策略和決策參數。
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class BehaviorRecord:
    """行為記錄"""
    action: str
    message: str
    priority: str
    timestamp: datetime
    user_response: Optional[str] = None
    user_emotion: Optional[str] = None
    effectiveness_score: float = 0.0
    outcome: str = "unknown"  # success, failure, neutral

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'action': self.action,
            'message': self.message,
            'priority': self.priority,
            'timestamp': self.timestamp.isoformat(),
            'user_response': self.user_response,
            'user_emotion': self.user_emotion,
            'effectiveness_score': self.effectiveness_score,
            'outcome': self.outcome
        }


@dataclass
class BehaviorPattern:
    """行為模式"""
    action: str
    context: str
    success_rate: float
    avg_effectiveness: float
    count: int
    last_updated: datetime

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'action': self.action,
            'context': self.context,
            'success_rate': self.success_rate,
            'avg_effectiveness': self.avg_effectiveness,
            'count': self.count,
            'last_updated': self.last_updated.isoformat()
        }


class BehaviorFeedbackLoop:
    """
    行為反饋循環

    功能：
    - 收集行為執行記錄
    - 評估行為效果
    - 識別成功/失敗模式
    - 更新行為策略
    - 優化決策參數

    這讓 Angela 能夠從經驗中學習和改進。
    """

    def __init__(
        self,
        llm_service: Any,
        memory_manager: Any,
        learning_engine: Any,
        loop_interval: float = 45.0,  # 反饋循環間隔（秒）
        min_loop_interval: float = 30.0,
        max_loop_interval: float = 60.0
    ):
        self.llm_service = llm_service
        self.memory_manager = memory_manager
        self.learning_engine = learning_engine

        self.loop_interval = loop_interval
        self.min_loop_interval = min_loop_interval
        self.max_loop_interval = max_loop_interval

        self.is_running = False
        self._feedback_task: Optional[asyncio.Task] = None

        # 行為記錄
        self.behavior_records: List[BehaviorRecord] = []
        self.max_records = 500

        # 行為模式
        self.behavior_patterns: Dict[str, BehaviorPattern] = {}

        # 策略參數
        self.strategy_parameters: Dict[str, float] = {
            'greet_threshold': 60.0,  # 問候閾值（秒）
            'comfort_sensitivity': 0.7,  # 安慰敏感度
            'interaction_frequency': 0.5,  # 交互頻率
            'priority_weight': {'high': 1.0, 'medium': 0.7, 'low': 0.4}  # 優先級權重
        }

        # 統計信息
        self.stats = {
            'total_behaviors': 0,
            'evaluated_behaviors': 0,
            'successful_behaviors': 0,
            'failed_behaviors': 0,
            'pattern_updates': 0,
            'strategy_updates': 0
        }

        logger.info("BehaviorFeedbackLoop initialized")

    async def start(self):
        """啟動反饋循環"""
        if self.is_running:
            logger.warning("BehaviorFeedbackLoop is already running")
            return

        self.is_running = True
        self._feedback_task = asyncio.create_task(self._feedback_loop())
        logger.info("BehaviorFeedbackLoop started")

    async def stop(self):
        """停止反饋循環"""
        if not self.is_running:
            return

        self.is_running = False

        if self._feedback_task:
            self._feedback_task.cancel()
            try:
                await self._feedback_task
            except asyncio.CancelledError:
                pass

        logger.info("BehaviorFeedbackLoop stopped")

    async def _feedback_loop(self):
        """反饋循環"""
        logger.info("Behavior feedback loop started")

        while self.is_running:
            try:
                # 動態調整循環間隔
                interval = self._calculate_interval()

                # 執行反饋流程
                await self._process_feedback()

                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in feedback loop: {e}")
                await asyncio.sleep(1)  # 防止緊密循環

    def _calculate_interval(self) -> float:
        """動態計算循環間隔"""
        # 根據記錄數量調整
        if len(self.behavior_records) > 100:
            return self.min_loop_interval
        elif len(self.behavior_records) > 50:
            return self.loop_interval
        else:
            return self.max_loop_interval

    async def _process_feedback(self):
        """處理反饋流程"""
        try:
            # 1. 收集新的行為記錄（已通過 record_behavior 方法收集）

            # 2. 評估行為效果
            if self.behavior_records:
                await self._evaluate_behaviors()

            # 3. 分析模式
            await self._analyze_patterns()

            # 4. 更新策略
            await self._update_strategy()

            # 5. 存儲學習結果
            await self._store_learning_results()

        except Exception as e:
            logger.error(f"Error processing feedback: {e}")

    def record_behavior(
        self,
        action: str,
        message: str,
        priority: str,
        user_response: Optional[str] = None,
        user_emotion: Optional[str] = None
    ):
        """記錄行為"""
        record = BehaviorRecord(
            action=action,
            message=message,
            priority=priority,
            timestamp=datetime.now(),
            user_response=user_response,
            user_emotion=user_emotion
        )

        self.behavior_records.append(record)
        self.stats['total_behaviors'] += 1

        # 限制記錄數量
        if len(self.behavior_records) > self.max_records:
            self.behavior_records = self.behavior_records[-self.max_records:]

        logger.debug(f"Recorded behavior: {action}")

    async def _evaluate_behaviors(self):
        """評估行為效果"""
        for record in self.behavior_records:
            if record.effectiveness_score == 0.0:  # 只評估未評估的記錄
                score = await self.evaluate_behavior(record)
                record.effectiveness_score = score

                # 判斷結果
                if score > 0.7:
                    record.outcome = "success"
                    self.stats['successful_behaviors'] += 1
                elif score < 0.3:
                    record.outcome = "failure"
                    self.stats['failed_behaviors'] += 1
                else:
                    record.outcome = "neutral"

                self.stats['evaluated_behaviors'] += 1

    async def evaluate_behavior(self, record: BehaviorRecord) -> float:
        """評估單個行為的效果"""
        try:
            # 基於多個因素評估
            score = 0.5  # 基礎分

            # 1. 用戶響應
            if record.user_response:
                # 有響應表示用戶參與
                response_length = len(record.user_response)
                if response_length > 10:
                    score += 0.3
                elif response_length > 0:
                    score += 0.1

            # 2. 用戶情緒
            if record.user_emotion:
                if record.user_emotion in ['happy', 'excited']:
                    score += 0.3
                elif record.user_emotion in ['sad', 'frustrated']:
                    score -= 0.2
                elif record.user_emotion == 'neutral':
                    score += 0.1

            # 3. 優先級匹配
            if record.action == 'greet' and record.priority == 'high':
                score += 0.1

            # 4. 時間因素（越近的記錄權重越高）
            time_since = (datetime.now() - record.timestamp).total_seconds()
            if time_since < 60:
                score += 0.1
            elif time_since > 3600:
                score -= 0.1

            # 限制在 0-1 之間
            return max(0.0, min(1.0, score))

        except Exception as e:
            logger.error(f"Error evaluating behavior: {e}")
            return 0.5

    async def _analyze_patterns(self):
        """分析行為模式"""
        # 按動作類型分組
        action_groups: Dict[str, List[BehaviorRecord]] = {}
        for record in self.behavior_records:
            if record.action not in action_groups:
                action_groups[record.action] = []
            action_groups[record.action].append(record)

        # 分析每個動作類型
        for action, records in action_groups.items():
            if len(records) < 3:  # 需要至少3個記錄才能分析模式
                continue

            # 計算成功率
            success_count = sum(1 for r in records if r.outcome == "success")
            success_rate = success_count / len(records)

            # 計算平均效果
            avg_effectiveness = sum(r.effectiveness_score for r in records) / len(records)

            # 更新或創建模式
            pattern_key = f"{action}_default"
            if pattern_key in self.behavior_patterns:
                self.behavior_patterns[pattern_key].success_rate = success_rate
                self.behavior_patterns[pattern_key].avg_effectiveness = avg_effectiveness
                self.behavior_patterns[pattern_key].count = len(records)
                self.behavior_patterns[pattern_key].last_updated = datetime.now()
            else:
                self.behavior_patterns[pattern_key] = BehaviorPattern(
                    action=action,
                    context="default",
                    success_rate=success_rate,
                    avg_effectiveness=avg_effectiveness,
                    count=len(records),
                    last_updated=datetime.now()
                )

            self.stats['pattern_updates'] += 1

    async def _update_strategy(self):
        """更新策略參數"""
        # 根據模式分析結果更新策略

        for pattern_key, pattern in self.behavior_patterns.items():
            action = pattern.action

            # 如果成功率低，調整策略
            if pattern.success_rate < 0.4 and pattern.count > 5:
                logger.info(f"Adjusting strategy for {action} (low success rate: {pattern.success_rate:.2f})")

                if action == 'greet':
                    # 降低問候頻率
                    self.strategy_parameters['greet_threshold'] *= 1.5
                elif action == 'comfort':
                    # 增加安慰敏感度
                    self.strategy_parameters['comfort_sensitivity'] = min(1.0, pattern.success_rate + 0.2)

                self.stats['strategy_updates'] += 1

            # 如果成功率高，加強策略
            elif pattern.success_rate > 0.8 and pattern.count > 5:
                if action == 'greet':
                    # 提高問候頻率
                    self.strategy_parameters['greet_threshold'] *= 0.9

                self.stats['strategy_updates'] += 1

    async def _store_learning_results(self):
        """存儲學習結果到記憶"""
        try:
            # 存儲行為模式
            if hasattr(self.memory_manager, 'store_experience'):
                patterns_summary = {
                    'timestamp': datetime.now().isoformat(),
                    'patterns': [p.to_dict() for p in self.behavior_patterns.values()],
                    'strategy_parameters': self.strategy_parameters
                }

                await self.memory_manager.store_experience(
                    raw_data=json.dumps(patterns_summary, ensure_ascii=False),
                    data_type="behavior_learning"
                )

        except Exception as e:
            logger.warning(f"Error storing learning results: {e}")

    def get_behavior_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """獲取行為歷史"""
        return [r.to_dict() for r in self.behavior_records[-limit:]]

    def get_patterns(self) -> Dict[str, Dict[str, Any]]:
        """獲取行為模式"""
        return {k: v.to_dict() for k, v in self.behavior_patterns.items()}

    def get_strategy_parameters(self) -> Dict[str, Any]:
        """獲取策略參數"""
        return self.strategy_parameters.copy()

    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            'is_running': self.is_running,
            'loop_interval': self.loop_interval,
            'total_behaviors': self.stats['total_behaviors'],
            'evaluated_behaviors': self.stats['evaluated_behaviors'],
            'successful_behaviors': self.stats['successful_behaviors'],
            'failed_behaviors': self.stats['failed_behaviors'],
            'pattern_updates': self.stats['pattern_updates'],
            'strategy_updates': self.stats['strategy_updates'],
            'success_rate': (
                self.stats['successful_behaviors'] / self.stats['evaluated_behaviors']
                if self.stats['evaluated_behaviors'] > 0 else 0.0
            ),
            'patterns_count': len(self.behavior_patterns)
        }


if __name__ == "__main__":
    # 測試行為反饋循環
    async def test_behavior_feedback_loop():
        from dataclasses import dataclass

        logging.basicConfig(level=logging.INFO)

        # Mock 服務
        class MockLLMService:
            pass

        class MockMemoryManager:
            async def store_experience(self, raw_data, data_type):
                pass

        class MockLearningEngine:
            pass

        # 創建組件
        llm_service = MockLLMService()
        memory_manager = MockMemoryManager()
        learning_engine = MockLearningEngine()

        # 創建反饋循環
        feedback_loop = BehaviorFeedbackLoop(
            llm_service=llm_service,
            memory_manager=memory_manager,
            learning_engine=learning_engine,
            loop_interval=3.0
        )

        # 啟動循環
        await feedback_loop.start()

        # 記錄一些行為
        logger.info("=== 記錄行為 ===")
        feedback_loop.record_behavior(
            action="greet",
            message="你好！",
            priority="medium",
            user_response="你好啊",
            user_emotion="happy"
        )

        await asyncio.sleep(1)

        feedback_loop.record_behavior(
            action="comfort",
            message="你看上去有點難過",
            priority="high",
            user_response="謝謝你的關心",
            user_emotion="neutral"
        )

        await asyncio.sleep(1)

        feedback_loop.record_behavior(
            action="greet",
            message="嘿，你在做什麼？",
            priority="low",
            user_response=None,
            user_emotion=None
        )

        # 運行一段時間
        await asyncio.sleep(10)

        # 打印統計
        logger.info(f"\n=== 行為反饋統計 ===")
        logger.info(json.dumps(feedback_loop.get_stats(), indent=2, ensure_ascii=False))

        logger.info(f"\n=== 行為模式 ===")
        logger.info(json.dumps(feedback_loop.get_patterns(), indent=2, ensure_ascii=False))

        logger.info(f"\n=== 策略參數 ===")
        logger.info(json.dumps(feedback_loop.get_strategy_parameters(), indent=2, ensure_ascii=False))

        # 停止
        await feedback_loop.stop()

    asyncio.run(test_behavior_feedback_loop())
