"""
用戶監控系統

檢測用戶在線狀態、活動水平和情緒狀態。
為其他生命循環提供用戶狀態信息。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
import json

logger = logging.getLogger(__name__)


class UserActivityLevel(Enum):
    """用戶活動水平"""
    HIGH = "high"  # 高頻活動
    MEDIUM = "medium"  # 中等活動
    LOW = "low"  # 低活動
    IDLE = "idle"  # 閒置


class UserEmotion(Enum):
    """用戶情緒"""
    HAPPY = "happy"
    SAD = "sad"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    EXCITED = "excited"
    ANXIOUS = "anxious"
    CONFUSED = "confused"
    RELAXED = "relaxed"


@dataclass
class UserState:
    """用戶狀態"""
    user_id: str
    online: bool
    last_activity: datetime
    last_input: str = ""
    emotion: str = UserEmotion.NEUTRAL.value
    emotion_intensity: float = 0.0
    activity_level: str = UserActivityLevel.MEDIUM.value
    session_duration: float = 0.0
    total_interactions: int = 0
    emotion_history: List[Dict[str, Any]] = field(default_factory=list)
    activity_history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'user_id': self.user_id,
            'online': self.online,
            'last_activity': self.last_activity.isoformat(),
            'last_input': self.last_input,
            'emotion': self.emotion,
            'emotion_intensity': self.emotion_intensity,
            'activity_level': self.activity_level,
            'session_duration': self.session_duration,
            'total_interactions': self.total_interactions,
            'emotion_history': self.emotion_history[-10:],  # 只保留最近10條
            'activity_history': self.activity_history[-10:],  # 只保留最近10條
        }


class UserMonitor:
    """
    用戶監控系統

    功能：
    - 檢測用戶在線狀態
    - 監控用戶活動水平
    - 估計用戶情緒
    - 檢測用戶返回和閒置
    """

    def __init__(
        self,
        user_id: str = "default_user",
        check_interval: float = 5.0,
        idle_threshold: float = 300.0,  # 5分鐘
        return_threshold: float = 1800.0  # 30分鐘
    ):
        self.user_id = user_id
        self.check_interval = check_interval
        self.idle_threshold = idle_threshold
        self.return_threshold = return_threshold

        self.user_state = UserState(
            user_id=user_id,
            online=False,
            last_activity=datetime.now()
        )

        self.is_running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._state_change_callbacks: List[Callable] = []

        # 活動追蹤
        self._last_online_time: Optional[datetime] = None
        self._offline_since: Optional[datetime] = None
        self._session_start_time: Optional[datetime] = None

        # 輸入追蹤
        self._recent_inputs: List[Dict[str, Any]] = []
        self._input_rate_window = 60.0  # 計算輸入速率的時間窗口（秒）

        logger.info(f"UserMonitor initialized for user {user_id}")

    def add_state_change_callback(self, callback: Callable):
        """添加狀態變化回調"""
        self._state_change_callbacks.append(callback)

    async def start(self):
        """啟動監控"""
        if self.is_running:
            logger.warning("UserMonitor is already running")
            return

        self.is_running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("UserMonitor started")

    async def stop(self):
        """停止監控"""
        if not self.is_running:
            return

        self.is_running = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("UserMonitor stopped")

    async def _monitor_loop(self):
        """監控循環"""
        logger.info("User monitor loop started")

        while self.is_running:
            try:
                await self._check_user_status()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(1)  # 防止緊密循環

    async def _check_user_status(self):
        """檢查用戶狀態"""
        now = datetime.now()

        # 計算閒置時間
        idle_time = (now - self.user_state.last_activity).total_seconds()

        # 檢測在線狀態
        was_online = self.user_state.online
        self.user_state.online = idle_time < self.idle_threshold

        # 狀態變化檢測
        if was_online and not self.user_state.online:
            # 用戶離線
            self._offline_since = now
            logger.info(f"User {self.user_id} went offline")
            await self._notify_state_change("offline", {"idle_time": idle_time})

        elif not was_online and self.user_state.online:
            # 用戶返回
            self._last_online_time = now
            if self._offline_since:
                offline_duration = (now - self._offline_since).total_seconds()
                if offline_duration > self.return_threshold:
                    logger.info(f"User {self.user_id} returned after {offline_duration:.0f}s")
                    await self._notify_state_change("return", {
                        "offline_duration": offline_duration
                    })
            await self._notify_state_change("online", {})

        # 更新會話持續時間
        if self.user_state.online:
            if self._session_start_time is None:
                self._session_start_time = now
            self.user_state.session_duration = (now - self._session_start_time).total_seconds()
        else:
            self._session_start_time = None
            self.user_state.session_duration = 0.0

        # 更新活動水平
        await self._update_activity_level()

        # 記錄活動歷史
        self.user_state.activity_history.append({
            'timestamp': now.isoformat(),
            'online': self.user_state.online,
            'activity_level': self.user_state.activity_level,
            'idle_time': idle_time
        })

        # 保持歷史記錄在合理範圍
        if len(self.user_state.activity_history) > 100:
            self.user_state.activity_history = self.user_state.activity_history[-100:]

    async def _update_activity_level(self):
        """更新活動水平"""
        now = datetime.now()

        # 清理過期的輸入記錄
        self._recent_inputs = [
            inp for inp in self._recent_inputs
            if (now - datetime.fromisoformat(inp['timestamp'])).total_seconds() < self._input_rate_window
        ]

        # 計算輸入速率
        input_rate = len(self._recent_inputs) / self._input_rate_window

        # 根據輸入速率決定活動水平
        if input_rate > 0.5:  # 每分鐘超過30次輸入
            self.user_state.activity_level = UserActivityLevel.HIGH.value
        elif input_rate > 0.1:  # 每分鐘超過6次輸入
            self.user_state.activity_level = UserActivityLevel.MEDIUM.value
        elif input_rate > 0.02:  # 每分鐘超過1次輸入
            self.user_state.activity_level = UserActivityLevel.LOW.value
        else:
            self.user_state.activity_level = UserActivityLevel.IDLE.value

    async def _notify_state_change(self, event_type: str, data: Dict[str, Any]):
        """通知狀態變化"""
        for callback in self._state_change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, data)
                else:
                    callback(event_type, data)
            except Exception as e:
                logger.error(f"Error in state change callback: {e}")

    def record_input(self, input_text: str, metadata: Optional[Dict[str, Any]] = None):
        """記錄用戶輸入"""
        now = datetime.now()

        # 更新最後活動時間
        self.user_state.last_activity = now
        self.user_state.last_input = input_text
        self.user_state.total_interactions += 1

        # 記錄輸入
        self._recent_inputs.append({
            'timestamp': now.isoformat(),
            'input': input_text,
            'metadata': metadata or {}
        })

        # 估計情緒
        emotion, intensity = self._estimate_emotion_from_text(input_text)
        self.user_state.emotion = emotion
        self.user_state.emotion_intensity = intensity

        # 記錄情緒歷史
        self.user_state.emotion_history.append({
            'timestamp': now.isoformat(),
            'emotion': emotion,
            'intensity': intensity,
            'input': input_text[:100]  # 限制長度
        })

        # 保持歷史記錄在合理範圍
        if len(self.user_state.emotion_history) > 50:
            self.user_state.emotion_history = self.user_state.emotion_history[-50:]

    def _estimate_emotion_from_text(self, text: str) -> tuple[str, float]:
        """
        從文本估計情緒

        返回: (emotion, intensity)
        """
        text_lower = text.lower()

        # 簡單情緒關鍵詞匹配
        emotion_keywords = {
            UserEmotion.HAPPY: [
                '开心', '高兴', '快乐', '棒', '好', '哈哈', '喜欢', '爱',
                'happy', 'great', 'awesome', 'good', 'love', 'like'
            ],
            UserEmotion.SAD: [
                '难过', '悲伤', '难过', '失望', '不好', '哭', '痛苦',
                'sad', 'bad', 'disappointed', 'cry', 'pain'
            ],
            UserEmotion.FRUSTRATED: [
                '烦', '生气', '讨厌', '糟糕', '糟糕', '失败',
                'frustrated', 'annoyed', 'angry', 'hate', 'failed'
            ],
            UserEmotion.EXCITED: [
                '激动', '兴奋', '期待', '哇', '天啊',
                'excited', 'wow', 'amazing', 'amazing'
            ],
            UserEmotion.ANXIOUS: [
                '担心', '害怕', '紧张', '焦虑', '害怕',
                'worried', 'scared', 'nervous', 'anxious', 'afraid'
            ],
            UserEmotion.CONFUSED: [
                '不懂', '不明白', '困惑', '为什么', '怎么回事',
                'confused', 'don\'t understand', 'why', 'how'
            ],
            UserEmotion.RELAXED: [
                '轻松', '舒服', '休息', '平静', '没事',
                'relaxed', 'comfortable', 'rest', 'calm', 'okay'
            ]
        }

        # 計算每種情緒的匹配度
        emotion_scores = {}
        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                emotion_scores[emotion] = score

        # 如果沒有匹配，返回中性
        if not emotion_scores:
            return UserEmotion.NEUTRAL.value, 0.0

        # 返回得分最高的情緒
        best_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        intensity = min(best_emotion[1] / 3.0, 1.0)  # 限制在0-1之間

        return best_emotion[0].value, intensity

    def get_user_state(self) -> UserState:
        """獲取用戶狀態"""
        return self.user_state

    def is_online(self) -> bool:
        """用戶是否在線"""
        return self.user_state.online

    def is_idle(self, threshold: Optional[float] = None) -> bool:
        """用戶是否閒置"""
        if threshold is None:
            threshold = self.idle_threshold

        idle_time = (datetime.now() - self.user_state.last_activity).total_seconds()
        return idle_time > threshold

    def detect_return(self) -> bool:
        """檢測用戶是否剛返回"""
        return (
            self.user_state.online and
            self._last_online_time is not None and
            (datetime.now() - self._last_online_time).total_seconds() < 30
        )

    def get_idle_time(self) -> float:
        """獲取閒置時間（秒）"""
        return (datetime.now() - self.user_state.last_activity).total_seconds()

    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            'user_id': self.user_id,
            'is_running': self.is_running,
            'online': self.user_state.online,
            'activity_level': self.user_state.activity_level,
            'emotion': self.user_state.emotion,
            'emotion_intensity': self.user_state.emotion_intensity,
            'idle_time': self.get_idle_time(),
            'session_duration': self.user_state.session_duration,
            'total_interactions': self.user_state.total_interactions,
            'check_interval': self.check_interval
        }


if __name__ == "__main__":
    # 測試用戶監控系統
    async def test_user_monitor():
        logging.basicConfig(level=logging.INFO)

        monitor = UserMonitor(check_interval=2.0)

        # 添加狀態變化回調
        def on_state_change(event_type, data):
            print(f"[STATE CHANGE] {event_type}: {data}")

        monitor.add_state_change_callback(on_state_change)

        await monitor.start()

        # 模擬用戶輸入
        print("\n=== 模擬用戶交互 ===")
        monitor.record_input("你好！今天心情不错", {"type": "greeting"})
        await asyncio.sleep(3)

        monitor.record_input("我很兴奋！", {"type": "emotion"})
        await asyncio.sleep(3)

        monitor.record_input("这是什么意思？", {"type": "question"})
        await asyncio.sleep(3)

        # 打印狀態
        print(f"\n=== 用戶狀態 ===")
        print(json.dumps(monitor.get_user_state().to_dict(), indent=2, ensure_ascii=False))

        # 停止監控
        await asyncio.sleep(2)
        await monitor.stop()

    asyncio.run(test_user_monitor())