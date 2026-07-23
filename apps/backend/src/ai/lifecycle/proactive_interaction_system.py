"""

主動交互系統

讓 Angela 具備主動觸發用戶交互的能力，
而不僅僅是被動回應。
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from core.system.config.magic_numbers import cache_value, loop_sleep
from core.utils import safe_error
from services.weather_service import WeatherService

from .user_monitor import UserMonitor

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================


logger = logging.getLogger(__name__)


class InteractionOpportunity(Enum):
    """交互機會類型"""

    USER_RETURN = "user_return"  # 用戶返回
    LONG_IDLE = "long_idle"  # 長時間閒置
    EMOTIONAL_CHANGE = "emotional_change"  # 情緒變化
    TIME_BASED = "time_based"  # 基於時間
    MEMORY_TRIGGER = "memory_trigger"  # 記憶觸發
    LEARNING_SHARE = "learning_share"  # 學習分享
    WEATHER_CHANGE = "weather_change"  # 天氣變化
    EVENT_REMINDER = "event_reminder"  # 事件提醒


@dataclass
class InteractionPlan:
    """交互計劃"""

    opportunity: str
    action: str
    message: str
    priority: str
    scheduled_time: datetime
    executed: bool = False
    execution_result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "opportunity": self.opportunity,
            "action": self.action,
            "message": self.message,
            "priority": self.priority,
            "scheduled_time": self.scheduled_time.isoformat(),
            "executed": self.executed,
            "execution_result": self.execution_result,
        }


class ProactiveInteractionSystem:
    """
    主動交互系統

    功能：
    - 檢測用戶狀態
    - 識別交互機會
    - 計劃主動行動
    - 執行主動行動

    這讓 Angela 具備主動性和社交能力。
    """

    def __init__(
        self,
        llm_service: Any,
        state_manager: Any,
        memory_manager: Any,
        user_monitor: UserMonitor,
        check_interval: float = loop_sleep("proactive_check", 15.0),  # 檢查間隔（秒）
        min_check_interval: float = loop_sleep("proactive_min_check", 10.0),
        max_check_interval: float = loop_sleep("proactive_max_check", 30.0),
        broadcast_callback: Optional[callable] = None,
    ):
        self.llm_service = llm_service
        self.state_manager = state_manager
        self.memory_manager = memory_manager
        self.user_monitor = user_monitor
        self.broadcast_callback = broadcast_callback

        self.check_interval = check_interval
        self.min_check_interval = min_check_interval
        self.max_check_interval = max_check_interval

        self.is_running = False
        self._proactive_task: Optional[asyncio.Task] = None

        # 交互計劃隊列
        self.interaction_queue: List[InteractionPlan] = []
        self.max_queue_size = cache_value("proactive_queue", 20)

        # 統計信息
        self.stats = {
            "total_opportunities": 0,
            "planned_actions": 0,
            "executed_actions": 0,
            "opportunity_counts": {},
        }

        # 天氣服務
        self.weather_service = WeatherService()
        self._last_weather_check: Optional[datetime] = None
        self._last_weather_desc: Optional[str] = None

        # 時間相關的配置
        self.last_interaction_time: Optional[datetime] = None
        self.interaction_cooldown = 60.0  # 交互冷卻時間（秒）

        logger.info("ProactiveInteractionSystem initialized")

    async def start(self) -> None:
        """啟動主動交互系統"""
        if self.is_running:
            logger.warning("ProactiveInteractionSystem is already running", exc_info=True)
            return

        self.is_running = True
        self._proactive_task = asyncio.create_task(self._proactive_loop())
        logger.info("ProactiveInteractionSystem started")

    async def stop(self) -> None:
        """停止主動交互系統"""
        if not self.is_running:
            return

        self.is_running = False

        if self._proactive_task:
            self._proactive_task.cancel()
            try:
                await self._proactive_task
            except asyncio.CancelledError:
                pass

        logger.info("ProactiveInteractionSystem stopped")

    async def _proactive_loop(self) -> None:
        """主動交互循環"""
        logger.info("Proactive interaction loop started")

        while self.is_running:
            try:
                # 動態調整檢查間隔
                interval = self._calculate_interval()

                # 執行主動交互流程
                await self._process_proactive_interaction()

                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except (
                Exception
            ) as e:  # broad exception acceptable: loop must be resilient to prevent process termination
                logger.error(f"Error in proactive loop: {e}", exc_info=True)
                await asyncio.sleep(loop_sleep("proactive_tight", 1.0))  # 防止緊密循環

    def _calculate_interval(self) -> float:
        """動態計算檢查間隔"""
        # 根據用戶狀態調整
        user_state = self.user_monitor.get_user_state()

        if user_state.online and user_state.activity_level == "high":
            # 用戶活躍時，減少檢查頻率
            return self.max_check_interval
        elif user_state.online and user_state.activity_level == "low":
            # 用戶不活躍時，增加檢查頻率
            return self.min_check_interval
        else:
            # 默認間隔
            return self.check_interval

    async def _process_proactive_interaction(self) -> None:
        """處理主動交互"""
        try:
            # 1. 檢測用戶狀態
            user_state = await self._detect_user_state()

            # 2. 識別交互機會
            opportunities = await self._identify_opportunities(user_state)

            if not opportunities:
                return

            # 3. 為每個機會計劃行動
            for opportunity in opportunities:
                plan = await self._plan_proactive_action(opportunity, user_state)
                if plan:
                    self.interaction_queue.append(plan)
                    self.stats["planned_actions"] += 1

            # 4. 執行計劃
            await self._execute_planned_actions()

            # 5. 清理隊列
            self._cleanup_queue()

        except (
            Exception
        ) as e:  # broad exception acceptable: proactive processing should not crash the loop
            logger.error(f"Error processing proactive interaction: {e}", exc_info=True)

    async def _detect_user_state(self) -> Dict[str, Any]:
        """檢測用戶狀態"""
        user_state = self.user_monitor.get_user_state()

        return {
            "online": user_state.online,
            "activity_level": user_state.activity_level,
            "emotion": user_state.emotion,
            "emotion_intensity": user_state.emotion_intensity,
            "idle_time": self.user_monitor.get_idle_time(),
            "session_duration": user_state.session_duration,
            "last_activity": user_state.last_activity,
            "user_return": self.user_monitor.detect_return(),
        }

    async def _identify_opportunities(self, user_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """識別交互機會"""
        opportunities = []

        # 1. 用戶返回
        if user_state.get("user_return"):
            opportunities.append(
                {
                    "type": InteractionOpportunity.USER_RETURN.value,
                    "priority": "high",
                    "data": {"offline_duration": user_state.get("session_duration", 0)},
                }
            )
            self.stats["total_opportunities"] += 1

        # 2. 長時間閒置
        if user_state.get("online") and user_state.get("idle_time", 0) > 120:
            opportunities.append(
                {
                    "type": InteractionOpportunity.LONG_IDLE.value,
                    "priority": "medium",
                    "data": {"idle_time": user_state.get("idle_time")},
                }
            )
            self.stats["total_opportunities"] += 1

        # 3. 情緒變化
        emotion = user_state.get("emotion")
        if emotion in ["sad", "frustrated", "anxious"]:
            opportunities.append(
                {
                    "type": InteractionOpportunity.EMOTIONAL_CHANGE.value,
                    "priority": "high",
                    "data": {
                        "emotion": emotion,
                        "intensity": user_state.get("emotion_intensity", 0),
                    },
                }
            )
            self.stats["total_opportunities"] += 1

        # 4. 基於時間的機會
        await self._check_time_based_opportunities(opportunities)

        # 5. 記憶觸發
        await self._check_memory_triggers(opportunities)

        # 6. 天氣變化
        await self._check_weather_opportunities(opportunities)

        # 更新統計
        for opp in opportunities:
            opp_type = opp["type"]
            if opp_type not in self.stats["opportunity_counts"]:
                self.stats["opportunity_counts"][opp_type] = 0
            self.stats["opportunity_counts"][opp_type] += 1

        return opportunities

    async def _check_time_based_opportunities(self, opportunities: List[Dict[str, Any]]) -> None:
        """檢查基於時間的機會"""
        now = datetime.now()

        # 早上問候
        if now.hour == 8 and now.minute < 10:
            opportunities.append(
                {
                    "type": InteractionOpportunity.TIME_BASED.value,
                    "priority": "medium",
                    "data": {"time_type": "morning_greeting", "hour": now.hour},
                }
            )
            self.stats["total_opportunities"] += 1

        # 晚上問候
        elif now.hour == 20 and now.minute < 10:
            opportunities.append(
                {
                    "type": InteractionOpportunity.TIME_BASED.value,
                    "priority": "medium",
                    "data": {"time_type": "evening_greeting", "hour": now.hour},
                }
            )
            self.stats["total_opportunities"] += 1

        # 休息提醒
        elif now.hour >= 23:
            opportunities.append(
                {
                    "type": InteractionOpportunity.TIME_BASED.value,
                    "priority": "low",
                    "data": {"time_type": "sleep_reminder", "hour": now.hour},
                }
            )
            self.stats["total_opportunities"] += 1

    async def _check_memory_triggers(self, opportunities: List[Dict[str, Any]]) -> None:
        """檢查記憶觸發"""
        try:
            # 從記憶中查找重要事件
            if hasattr(self.memory_manager, "get_important_events"):
                events = await self.memory_manager.get_important_events(limit=3)
                if events:
                    opportunities.append(
                        {
                            "type": InteractionOpportunity.MEMORY_TRIGGER.value,
                            "priority": "medium",
                            "data": {"events": events},
                        }
                    )
                    self.stats["total_opportunities"] += 1
        except (
            Exception
        ) as e:  # broad exception acceptable: memory trigger checks should be fault-tolerant
            logger.warning(f"Error checking memory triggers: {e}", exc_info=True)

    async def _check_weather_opportunities(self, opportunities: List[Dict[str, Any]]) -> None:
        """檢查天氣變化機會"""
        if not self.weather_service.is_enabled():
            return
        try:
            weather = await self.weather_service.get_weather()
            desc = weather.get("description", "unknown")
            if desc == "unknown" or desc is None:
                return
            now = datetime.now()
            # First check: log initial weather
            if self._last_weather_desc is None:
                self._last_weather_desc = desc
                self._last_weather_check = now
                return
            # Subsequent checks: detect significant changes
            significant_change = (
                desc != self._last_weather_desc
                and self._last_weather_check is not None
                and (now - self._last_weather_check).total_seconds() > 3600
            )
            if significant_change:
                opportunities.append(
                    {
                        "type": InteractionOpportunity.WEATHER_CHANGE.value,
                        "priority": "low",
                        "data": {
                            "previous": self._last_weather_desc,
                            "current": desc,
                            "temperature": weather.get("temperature_c"),
                            "location": weather.get("location"),
                        },
                    }
                )
                self.stats["total_opportunities"] += 1
                self._last_weather_desc = desc
            self._last_weather_check = now
        except Exception as e:
            logger.warning("Weather check skipped: %s", e, exc_info=True)

    async def _plan_proactive_action(
        self, opportunity: Dict[str, Any], user_state: Dict[str, Any]
    ) -> Optional[InteractionPlan]:
        """計劃主動行動"""
        try:
            # 檢查冷卻時間
            if self.last_interaction_time:
                cooldown_passed = (
                    datetime.now() - self.last_interaction_time
                ).total_seconds() > self.interaction_cooldown
                if not cooldown_passed and opportunity.get("priority") != "high":
                    return None

            # 構建計劃
            opp_type = opportunity["type"]
            priority = opportunity.get("priority", "medium")

            # 根據機會類型生成消息
            if opp_type == InteractionOpportunity.USER_RETURN.value:
                message = await self._generate_return_message(opportunity)
            elif opp_type == InteractionOpportunity.LONG_IDLE.value:
                message = await self._generate_idle_message(opportunity)
            elif opp_type == InteractionOpportunity.EMOTIONAL_CHANGE.value:
                message = await self._generate_emotional_message(opportunity)
            elif opp_type == InteractionOpportunity.TIME_BASED.value:
                message = await self._generate_time_based_message(opportunity)
            elif opp_type == InteractionOpportunity.MEMORY_TRIGGER.value:
                message = await self._generate_memory_message(opportunity)
            elif opp_type == InteractionOpportunity.WEATHER_CHANGE.value:
                message = await self._generate_weather_message(opportunity)
            else:
                engine = self._get_ed3n_engine()
                message = engine.process(
                    "unknown_opportunity", context={"opp_type": opp_type}, depth="reflex"
                )

            plan = InteractionPlan(
                opportunity=opp_type,
                action="proactive_message",
                message=message,
                priority=priority,
                scheduled_time=datetime.now(),
            )

            return plan

        except (
            Exception
        ) as e:  # broad exception acceptable: planning action should not crash the loop
            logger.error(f"Error planning proactive action: {e}", exc_info=True)
            return None

    def _get_ed3n_engine(self) -> Any:
        if not hasattr(self.__class__, "_ed3n_engine"):
            from ai.ed3n.ed3n_engine import ED3NEngine

            self.__class__._ed3n_engine = ED3NEngine.get_shared()
        return self.__class__._ed3n_engine

    async def _generate_return_message(self, opportunity: Dict[str, Any]) -> str:
        """生成返回消息"""
        engine = self._get_ed3n_engine()
        return engine.process("welcome_back", context={"type": "return"}, depth="reflex")

    async def _generate_idle_message(self, opportunity: Dict[str, Any]) -> str:
        """生成閒置消息"""
        idle_time = opportunity.get("data", {}).get("idle_time", 0)
        engine = self._get_ed3n_engine()
        return engine.process("idle_check", context={"idle_time": idle_time}, depth="reflex")

    async def _generate_emotional_message(self, opportunity: Dict[str, Any]) -> str:
        """生成情緒消息"""
        emotion = opportunity.get("data", {}).get("emotion", "neutral")
        engine = self._get_ed3n_engine()
        return engine.process("emotional_response", context={"emotion": emotion}, depth="reflex")

    async def _generate_time_based_message(self, opportunity: Dict[str, Any]) -> str:
        """生成基於時間的消息"""
        time_type = opportunity.get("data", {}).get("time_type", "")
        engine = self._get_ed3n_engine()
        return engine.process("time_greeting", context={"time_type": time_type}, depth="reflex")

    async def _generate_memory_message(self, opportunity: Dict[str, Any]) -> str:
        """生成記憶消息"""
        events = opportunity.get("data", {}).get("events", [])
        engine = self._get_ed3n_engine()
        return engine.process("memory_trigger", context={"events": events}, depth="reflex")

    async def _generate_weather_message(self, opportunity: Dict[str, Any]) -> str:
        """生成天氣消息"""
        data = opportunity.get("data", {})
        desc = data.get("current", "unknown")
        temp = data.get("temperature")
        location = data.get("location", "your area")
        parts = [f"The weather in {location} has changed to {desc}"]
        if temp is not None:
            parts.append(f" ({temp}°C)")
        engine = self._get_ed3n_engine()
        return engine.process("weather_change", context={"message": "".join(parts)}, depth="reflex")

    async def _execute_planned_actions(self) -> None:
        """執行計劃的行動"""
        if not self.interaction_queue:
            return

        # 按優先級排序
        self.interaction_queue.sort(
            key=lambda x: (
                0 if x.priority == "high" else 1 if x.priority == "medium" else 2,
                x.scheduled_time,
            )
        )

        # 執行第一個優先級高的行動
        for plan in self.interaction_queue[:3]:  # 最多執行3個
            if not plan.executed:
                result = await self._execute_proactive_action(plan)
                plan.executed = True
                plan.execution_result = result
                self.stats["executed_actions"] += 1

                # 更新最後交互時間
                self.last_interaction_time = datetime.now()

                logger.info(f"Executed proactive action: {plan.opportunity}")

    async def _execute_proactive_action(self, plan: InteractionPlan) -> Dict[str, Any]:
        """執行主動行動"""
        try:
            # 通過 WebSocket 發送消息給前端
            logger.info(f"[PROACTIVE] {plan.opportunity}: {plan.message}")

            if self.broadcast_callback:
                try:
                    await self.broadcast_callback(
                        {
                            "type": "proactive_action",
                            "opportunity": plan.opportunity,
                            "action": plan.action,
                            "message": plan.message,
                            "priority": plan.priority,
                            "scheduled_time": plan.scheduled_time.isoformat(),
                        }
                    )
                    logger.debug(f"Proactive action sent via WebSocket: {plan.opportunity}")
                except (
                    Exception
                ) as e:  # broad exception acceptable: WebSocket failures should not block action execution
                    logger.warning(
                        f"Failed to send proactive action via WebSocket: {e}", exc_info=True
                    )

            return {"success": True, "sent": True, "message": plan.message}

        except Exception as e:  # broad exception acceptable: action execution should be resilient
            logger.error(f"Error executing proactive action: {e}", exc_info=True)
            return {"success": False, "error": safe_error(e)}

    def _cleanup_queue(self) -> None:
        """清理隊列"""
        # 移除已執行的計劃
        self.interaction_queue = [p for p in self.interaction_queue if not p.executed]

        # 限制隊列大小
        if len(self.interaction_queue) > self.max_queue_size:
            self.interaction_queue = self.interaction_queue[-self.max_queue_size :]

    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            "is_running": self.is_running,
            "check_interval": self.check_interval,
            "total_opportunities": self.stats["total_opportunities"],
            "planned_actions": self.stats["planned_actions"],
            "executed_actions": self.stats["executed_actions"],
            "opportunity_counts": self.stats["opportunity_counts"],
            "queue_size": len(self.interaction_queue),
            "last_interaction_time": (
                self.last_interaction_time.isoformat() if self.last_interaction_time else None
            ),
        }

    def get_queue(self, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取隊列"""
        return [p.to_dict() for p in self.interaction_queue[-limit:]]
