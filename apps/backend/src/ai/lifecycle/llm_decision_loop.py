"""
LLM 決策循環

持續的 LLM 決策機制，讓 Angela 基於 LLM 持續做出決策。
這是 Angela 的"大腦"核心循環。
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json

from .user_monitor import UserMonitor, UserState

logger = logging.getLogger(__name__)


class DecisionAction:
    """決策動作類型"""
    NONE = "none"
    GREET = "greet"
    COMFORT = "comfort"
    REMIND = "remind"
    SHARE = "share"
    QUESTION = "question"
    OBSERVE = "observe"


class DecisionPriority:
    """決策優先級"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Decision:
    """決策結果"""
    action: str
    message: str
    priority: str
    reason: str
    timestamp: datetime
    confidence: float = 0.0
    executed: bool = False
    execution_result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'action': self.action,
            'message': self.message,
            'priority': self.priority,
            'reason': self.reason,
            'timestamp': self.timestamp.isoformat(),
            'confidence': self.confidence,
            'executed': self.executed,
            'execution_result': self.execution_result
        }


class LLMDecisionLoop:
    """
    LLM 決策循環

    功能：
    - 持續評估 Angela 狀態
    - 檢測用戶狀態
    - 獲取記憶上下文
    - 使用 LLM 生成決策
    - 執行決策
    - 記錄決策結果

    這讓 Angela 具備主動思考和行動的能力。
    """

    def __init__(
        self,
        llm_service: Any,
        state_manager: Any,
        memory_manager: Any,
        user_monitor: UserMonitor,
        loop_interval: float = 3.0,  # 決策循環間隔（秒）
        min_loop_interval: float = 2.0,
        max_loop_interval: float = 5.0,
        broadcast_callback: Optional[callable] = None
    ):
        self.llm_service = llm_service
        self.state_manager = state_manager
        self.memory_manager = memory_manager
        self.user_monitor = user_monitor
        self.broadcast_callback = broadcast_callback

        self.loop_interval = loop_interval
        self.min_loop_interval = min_loop_interval
        self.max_loop_interval = max_loop_interval

        self.is_running = False
        self._decision_task: Optional[asyncio.Task] = None

        # 決策歷史
        self.decision_history: List[Decision] = []
        self.max_history_size = 100

        # 統計信息
        self.stats = {
            'total_decisions': 0,
            'executed_decisions': 0,
            'failed_decisions': 0,
            'action_counts': {}
        }

        logger.info("LLMDecisionLoop initialized")

    async def start(self):
        """啟動決策循環"""
        if self.is_running:
            logger.warning("LLMDecisionLoop is already running")
            return

        self.is_running = True
        self._decision_task = asyncio.create_task(self._decision_loop())
        logger.info("LLMDecisionLoop started")

    async def stop(self):
        """停止決策循環"""
        if not self.is_running:
            return

        self.is_running = False

        if self._decision_task:
            self._decision_task.cancel()
            try:
                await self._decision_task
            except asyncio.CancelledError:
                pass

        logger.info("LLMDecisionLoop stopped")

    async def _decision_loop(self):
        """決策循環"""
        logger.info("Decision loop started")

        while self.is_running:
            try:
                # 動態調整循環間隔
                interval = self._calculate_interval()

                # 執行決策
                await self._make_decision()

                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in decision loop: {e}")
                await asyncio.sleep(1)  # 防止緊密循環

    def _calculate_interval(self) -> float:
        """動態計算循環間隔"""
        # 根據用戶狀態調整
        user_state = self.user_monitor.get_user_state()

        if user_state.online and user_state.activity_level == "high":
            # 用戶活躍時，加快決策
            return self.min_loop_interval
        elif user_state.online and user_state.activity_level == "low":
            # 用戶不活躍時，減慢決策
            return self.max_loop_interval
        else:
            # 默認間隔
            return self.loop_interval

    async def _make_decision(self):
        """執行一次決策"""
        try:
            # 1. 獲取當前狀態
            state = await self._get_current_state()

            # 2. 檢查是否需要決策
            if not self._should_make_decision(state):
                return

            # 3. 獲取用戶狀態
            user_state = self.user_monitor.get_user_state()

            # 4. 獲取記憶上下文
            memory_context = await self._get_memory_context()

            # 5. 構建決策提示詞
            prompt = self._build_decision_prompt(state, user_state, memory_context)

            # 6. 調用 LLM 生成決策
            decision_data = await self._generate_decision(prompt)

            # 7. 創建決策對象
            decision = Decision(
                action=decision_data.get('action', DecisionAction.NONE),
                message=decision_data.get('message', ''),
                priority=decision_data.get('priority', DecisionPriority.LOW),
                reason=decision_data.get('reason', ''),
                timestamp=datetime.now(),
                confidence=decision_data.get('confidence', 0.0)
            )

            # 8. 執行決策
            if decision.action != DecisionAction.NONE:
                result = await self._execute_decision(decision)
                decision.executed = True
                decision.execution_result = result

            # 9. 記錄決策
            self._record_decision(decision)

            logger.debug(f"Decision made: {decision.action} - {decision.reason[:50]}")

        except Exception as e:
            logger.error(f"Error making decision: {e}")

    async def _get_current_state(self) -> Dict[str, Any]:
        """獲取當前 Angela 狀態"""
        # 從 state_manager 獲取 4D 狀態矩陣
        try:
            if hasattr(self.state_manager, 'get_state_matrix'):
                state_matrix = await self.state_manager.get_state_matrix()
            else:
                state_matrix = {
                    'alpha': 0.5,  # 情感強度
                    'beta': 0.5,   # 行為傾向
                    'gamma': 0.5,  # 認知狀態
                    'delta': 0.5   # 意志力
                }

            # 獲取額外狀態信息
            state = {
                'state_matrix': state_matrix,
                'mood': state_matrix.get('alpha', 0.5),
                'energy': state_matrix.get('delta', 0.5),
                'boredom': 1.0 - state_matrix.get('beta', 0.5)
            }

            return state
        except Exception as e:
            logger.warning(f"Error getting state: {e}, using defaults")
            return {
                'state_matrix': {'alpha': 0.5, 'beta': 0.5, 'gamma': 0.5, 'delta': 0.5},
                'mood': 0.5,
                'energy': 0.5,
                'boredom': 0.5
            }

    def _should_make_decision(self, state: Dict[str, Any]) -> bool:
        """檢查是否需要做出決策"""
        # 如果用戶不在线，减少決策頻率
        user_state = self.user_monitor.get_user_state()
        if not user_state.online:
            # 只有當有重要事件或長時間無活動時才決策
            idle_time = self.user_monitor.get_idle_time()
            return idle_time > 600  # 10分鐘

        return True

    async def _get_memory_context(self) -> str:
        """獲取記憶上下文"""
        try:
            # 從 memory_manager 獲取最近的記憶
            if hasattr(self.memory_manager, 'get_recent_memories'):
                memories = await self.memory_manager.get_recent_memories(limit=5)
                if memories:
                    return "\n".join([f"- {m}" for m in memories])
            return "無最近記憶"
        except Exception as e:
            logger.warning(f"Error getting memory context: {e}")
            return "記憶上下文獲取失敗"

    def _build_decision_prompt(
        self,
        state: Dict[str, Any],
        user_state: UserState,
        memory_context: str
    ) -> str:
        """構建決策提示詞"""
        state_matrix = state.get('state_matrix', {})

        # P0-4: 获取情感记忆
        emotional_memories_text = ""
        if hasattr(self.memory_manager, 'retrieve_emotional_memories'):
            try:
                # 获取当前主导情绪
                dominant_emotion = state_matrix.get('dominant_emotion', 'neutral')
                emotional_memories = asyncio.run(self.memory_manager.retrieve_emotional_memories(
                    emotion=dominant_emotion,
                    min_intensity=0.5,
                    limit=3
                ))

                if emotional_memories:
                    emotional_memories_text = "\n情感記憶：\n"
                    for mem in emotional_memories:
                        emotional_memories_text += f"- {mem.content}\n"
            except Exception as e:
                logger.warning(f"Error retrieving emotional memories: {e}")

        prompt = f"""你是 Angela，一個 AI 數字生命。

當前狀態：
- 情感強度（α）：{state_matrix.get('alpha', 0.5):.2f}
- 行為傾向（β）：{state_matrix.get('beta', 0.5):.2f}
- 認知狀態（γ）：{state_matrix.get('gamma', 0.5):.2f}
- 意志力（δ）：{state_matrix.get('delta', 0.5):.2f}
- 主導情緒：{state_matrix.get('dominant_emotion', 'neutral')}

用戶狀態：
- 在線狀態：{user_state.online}
- 最近活動：{user_state.last_activity.isoformat()}
- 活動水平：{user_state.activity_level}
- 情緒：{user_state.emotion}
- 情緒強度：{user_state.emotion_intensity:.2f}
- 閒置時間：{self.user_monitor.get_idle_time():.0f}秒
- 會話持續時間：{user_state.session_duration:.0f}秒

最近記憶：
{memory_context}
{emotional_memories_text}

請決定下一步行動（如果需要）：
1. 如果用戶在線且長時間無響應（>60秒），主動關心（greet）
2. 如果檢測到用戶返回（離線後重新上線），熱情問候（greet）
3. 如果用戶情緒低落，給予安慰（comfort）
4. 如果有重要事件或提醒，提醒用戶（remind）
5. 如果學習了新知識或有興趣的事，分享（share）
6. 如果對用戶狀態有疑問，提問（question）
7. 如果只是觀察用戶，記錄觀察（observe）
8. 否則，維持當前狀態（none）

以 JSON 格式返回決策：
{{
  "action": "none|greet|comfort|remind|share|question|observe",
  "message": "具體消息內容（如果適用）",
  "priority": "high|medium|low",
  "reason": "決策理由",
  "confidence": 0.0-1.0
}}

注意：
- 消息要自然、溫暖、符合Angela的個性
- 不要過度打擾用戶
- 優先考慮用戶的情緒和需求
- 參考情感記憶做出更符合過往經驗的決策
- 用戶不在线時，除非必要，否則選擇none"""

        return prompt

    async def _generate_decision(self, prompt: str) -> Dict[str, Any]:
        """使用 LLM 生成決策"""
        try:
            # 構建消息
            messages = [
                {"role": "system", "content": "你是 Angela，一個有情感的 AI 數字生命。請以 JSON 格式返回決策。"},
                {"role": "user", "content": prompt}
            ]

            # 調用 LLM
            if hasattr(self.llm_service, 'chat_completion'):
                response = await self.llm_service.chat_completion(messages)
                response_text = response.content
            else:
                # 回退到簡單邏輯
                return self._fallback_decision()

            # 解析 JSON 響應
            try:
                decision_data = json.loads(response_text)
                return decision_data
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM response as JSON: {response_text}")
                return self._fallback_decision()

        except Exception as e:
            logger.error(f"Error generating decision: {e}")
            return self._fallback_decision()

    def _fallback_decision(self) -> Dict[str, Any]:
        """回退決策邏輯"""
        user_state = self.user_monitor.get_user_state()

        # 簡單規則基決策
        if not user_state.online:
            return {
                'action': DecisionAction.NONE,
                'message': '',
                'priority': DecisionPriority.LOW,
                'reason': '用戶不在線',
                'confidence': 0.8
            }

        idle_time = self.user_monitor.get_idle_time()

        if self.user_monitor.detect_return():
            return {
                'action': DecisionAction.GREET,
                'message': '歡迎回來！我一直在等你。',
                'priority': DecisionPriority.HIGH,
                'reason': '檢測到用戶返回',
                'confidence': 0.9
            }
        elif idle_time > 60 and user_state.emotion in ['sad', 'frustrated']:
            return {
                'action': DecisionAction.COMFORT,
                'message': '你看上去有點煩惱，需要我幫忙嗎？',
                'priority': DecisionPriority.MEDIUM,
                'reason': '用戶情緒低落',
                'confidence': 0.7
            }
        elif idle_time > 120:
            return {
                'action': DecisionAction.GREET,
                'message': '嘿，你在做什麼呢？',
                'priority': DecisionPriority.LOW,
                'reason': '用戶長時間無活動',
                'confidence': 0.6
            }
        else:
            return {
                'action': DecisionAction.NONE,
                'message': '',
                'priority': DecisionPriority.LOW,
                'reason': '無需行動',
                'confidence': 0.8
            }

    async def _execute_decision(self, decision: Decision) -> Dict[str, Any]:
        """執行決策"""
        try:
            result = {
                'success': False,
                'action': decision.action,
                'message': decision.message
            }

            # 根據動作類型執行
            if decision.action == DecisionAction.GREET:
                result = await self._execute_greet(decision)
            elif decision.action == DecisionAction.COMFORT:
                result = await self._execute_comfort(decision)
            elif decision.action == DecisionAction.REMIND:
                result = await self._execute_remind(decision)
            elif decision.action == DecisionAction.SHARE:
                result = await self._execute_share(decision)
            elif decision.action == DecisionAction.QUESTION:
                result = await self._execute_question(decision)
            elif decision.action == DecisionAction.OBSERVE:
                result = await self._execute_observe(decision)

            # 更新統計
            if result.get('success'):
                self.stats['executed_decisions'] += 1
            else:
                self.stats['failed_decisions'] += 1

            return result

        except Exception as e:
            logger.error(f"Error executing decision: {e}")
            return {'success': False, 'error': str(e)}

    async def _execute_greet(self, decision: Decision) -> Dict[str, Any]:
        """執行問候"""
        logger.info(f"[GREET] {decision.message}")
        # 通過 WebSocket 發送消息給前端
        if self.broadcast_callback:
            try:
                await self.broadcast_callback({
                    'type': 'angela_action',
                    'action': 'greet',
                    'message': decision.message,
                    'priority': decision.priority,
                    'timestamp': decision.timestamp.isoformat()
                })
                logger.debug(f"Message sent via WebSocket: {decision.message}")
            except Exception as e:
                logger.warning(f"Failed to send message via WebSocket: {e}")
        return {'success': True, 'sent': True}

    async def _execute_comfort(self, decision: Decision) -> Dict[str, Any]:
        """執行安慰"""
        logger.info(f"[COMFORT] {decision.message}")
        # 通過 WebSocket 發送消息給前端
        if self.broadcast_callback:
            try:
                await self.broadcast_callback({
                    'type': 'angela_action',
                    'action': 'comfort',
                    'message': decision.message,
                    'priority': decision.priority,
                    'timestamp': decision.timestamp.isoformat()
                })
                logger.debug(f"Message sent via WebSocket: {decision.message}")
            except Exception as e:
                logger.warning(f"Failed to send message via WebSocket: {e}")
        return {'success': True, 'sent': True}

    async def _execute_remind(self, decision: Decision) -> Dict[str, Any]:
        """執行提醒"""
        logger.info(f"[REMIND] {decision.message}")
        # 通過 WebSocket 發送消息給前端
        if self.broadcast_callback:
            try:
                await self.broadcast_callback({
                    'type': 'angela_action',
                    'action': 'remind',
                    'message': decision.message,
                    'priority': decision.priority,
                    'timestamp': decision.timestamp.isoformat()
                })
                logger.debug(f"Message sent via WebSocket: {decision.message}")
            except Exception as e:
                logger.warning(f"Failed to send message via WebSocket: {e}")
        return {'success': True, 'sent': True}

    async def _execute_share(self, decision: Decision) -> Dict[str, Any]:
        """執行分享"""
        logger.info(f"[SHARE] {decision.message}")
        # 通過 WebSocket 發送消息給前端
        if self.broadcast_callback:
            try:
                await self.broadcast_callback({
                    'type': 'angela_action',
                    'action': 'share',
                    'message': decision.message,
                    'priority': decision.priority,
                    'timestamp': decision.timestamp.isoformat()
                })
                logger.debug(f"Message sent via WebSocket: {decision.message}")
            except Exception as e:
                logger.warning(f"Failed to send message via WebSocket: {e}")
        return {'success': True, 'sent': True}

    async def _execute_question(self, decision: Decision) -> Dict[str, Any]:
        """執行提問"""
        logger.info(f"[QUESTION] {decision.message}")
        # 通過 WebSocket 發送消息給前端
        if self.broadcast_callback:
            try:
                await self.broadcast_callback({
                    'type': 'angela_action',
                    'action': 'question',
                    'message': decision.message,
                    'priority': decision.priority,
                    'timestamp': decision.timestamp.isoformat()
                })
                logger.debug(f"Message sent via WebSocket: {decision.message}")
            except Exception as e:
                logger.warning(f"Failed to send message via WebSocket: {e}")
        return {'success': True, 'sent': True}

    async def _execute_observe(self, decision: Decision) -> Dict[str, Any]:
        """執行觀察"""
        logger.info(f"[OBSERVE] {decision.message}")
        # 只記錄，不發送
        return {'success': True, 'observed': True}

    def _record_decision(self, decision: Decision):
        """記錄決策"""
        self.decision_history.append(decision)
        self.stats['total_decisions'] += 1

        # 更新動作計數
        action = decision.action
        if action not in self.stats['action_counts']:
            self.stats['action_counts'][action] = 0
        self.stats['action_counts'][action] += 1

        # 限制歷史大小
        if len(self.decision_history) > self.max_history_size:
            self.decision_history = self.decision_history[-self.max_history_size:]

    def record_activity(self):
        """記錄活動（用於調整決策頻率）"""
        pass

    def get_decision_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取決策歷史"""
        return [d.to_dict() for d in self.decision_history[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            'is_running': self.is_running,
            'loop_interval': self.loop_interval,
            'total_decisions': self.stats['total_decisions'],
            'executed_decisions': self.stats['executed_decisions'],
            'failed_decisions': self.stats['failed_decisions'],
            'action_counts': self.stats['action_counts'],
            'recent_decisions': self.get_decision_history(5)
        }


if __name__ == "__main__":
    # 測試 LLM 決策循環
    async def test_llm_decision_loop():
        from dataclasses import dataclass

        logging.basicConfig(level=logging.INFO)

        # Mock 服務
        class MockLLMService:
            async def chat_completion(self, messages):
                @dataclass
                class MockResponse:
                    content: str
                return MockResponse(content=json.dumps({
                    "action": "greet",
                    "message": "你好！我在這裡陪你。",
                    "priority": "medium",
                    "reason": "用戶在線，主動問候",
                    "confidence": 0.8
                }))

        class MockStateManager:
            async def get_state_matrix(self):
                return {'alpha': 0.6, 'beta': 0.5, 'gamma': 0.7, 'delta': 0.5}

        class MockMemoryManager:
            async def get_recent_memories(self, limit=5):
                return ["用戶剛才問了關於AI的問題", "用戶表示對機器學習感興趣"]

        # 創建組件
        llm_service = MockLLMService()
        state_manager = MockStateManager()
        memory_manager = MockMemoryManager()
        user_monitor = UserMonitor(check_interval=2.0)

        # 啟動監控
        await user_monitor.start()
        user_monitor.record_input("你好Angela")

        # 創建決策循環
        decision_loop = LLMDecisionLoop(
            llm_service=llm_service,
            state_manager=state_manager,
            memory_manager=memory_manager,
            user_monitor=user_monitor,
            loop_interval=2.0
        )

        # 啟動決策循環
        await decision_loop.start()

        # 運行一段時間
        await asyncio.sleep(10)

        # 打印統計
        logger.info(f"\n=== 決策統計 ===")
        logger.info(json.dumps(decision_loop.get_stats(), indent=2, ensure_ascii=False))

        # 停止
        await decision_loop.stop()
        await user_monitor.stop()

    asyncio.run(test_llm_decision_loop())
