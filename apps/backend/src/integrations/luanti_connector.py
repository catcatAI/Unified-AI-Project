"""
Luanti Connector - 連接 Luanti (Minetest) 遊戲伺服器

支援：
- WebSocket 連線 (Minetest 5.8+ 支援 WebSocket)
- 畫面抓取 (via CSM 或 server-side mod)
- 動作指令下發
- 狀態同步
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable, Tuple
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class ConnectionState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    READY = "ready"
    ERROR = "error"


@dataclass
class LuantiConfig:
    host: str = "localhost"
    port: int = 30000
    password: str = ""
    protocol_version: int = 39
    auto_reconnect: bool = True
    reconnect_interval: float = 5.0
    ping_interval: float = 10.0
    timeout: float = 30.0


@dataclass
class PlayerState:
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    yaw: float = 0.0
    pitch: float = 0.0
    hp: int = 20
    max_hp: int = 20
    breath: int = 10
    hunger: int = 20
    inventory: Dict[str, int] = field(default_factory=dict)
    wield_index: int = 0
    wielded_item: str = ""
    is_on_ground: bool = True
    is_in_water: bool = False
    is_in_lava: bool = False
    light_level: int = 15
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass
class GameSnapshot:
    tick: int
    timestamp: float
    player: PlayerState
    frame: Optional[np.ndarray] = None  # (H, W, 3) RGB
    nearby_nodes: List[Dict] = field(default_factory=list)
    nearby_entities: List[Dict] = field(default_factory=list)


class LuantiConnector:
    """
    Luanti 遊戲連接器

    設計考量：
    - 非阻塞 async/await
    - 自動重連與心跳
    - 訊息隊列緩衝
    - 狀態快照機制
    """

    def __init__(self, config: Optional[LuantiConfig] = None):
        self.config = config or LuantiConfig()
        self.state = ConnectionState.DISCONNECTED
        self._ws = None
        self._reader_task: Optional[asyncio.Task] = None
        self._ping_task: Optional[asyncio.Task] = None
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._response_futures: Dict[str, asyncio.Future] = {}
        self._handlers: Dict[str, List[Callable]] = {}
        self._player_state = PlayerState()
        self._last_snapshot: Optional[GameSnapshot] = None
        self._tick = 0
        self._connected_event = asyncio.Event()
        self._frame_callback: Optional[Callable[[np.ndarray], None]] = None

    async def connect(self) -> bool:
        """建立 WebSocket 連線"""
        if self.state in (ConnectionState.CONNECTING, ConnectionState.CONNECTED):
            return True

        self.state = ConnectionState.CONNECTING
        url = f"ws://{self.config.host}:{self.config.port}"

        try:
            import websockets

            self._ws = await asyncio.wait_for(
                websockets.connect(url, ping_interval=None), timeout=self.config.timeout
            )
            self.state = ConnectionState.AUTHENTICATING

            # 啟動讀取任務
            self._reader_task = asyncio.create_task(self._reader_loop())
            self._ping_task = asyncio.create_task(self._ping_loop())

            # 發送認證
            await self._send_auth()

            # 等待認證完成
            try:
                await asyncio.wait_for(self._connected_event.wait(), timeout=10.0)
                self.state = ConnectionState.READY
                logger.info(f"Connected to Luanti at {url}")
                return True
            except asyncio.TimeoutError:
                logger.error("Authentication timeout")
                await self.disconnect()
                return False

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.state = ConnectionState.ERROR
            await self._cleanup()
            return False

    async def _send_auth(self):
        """發送認證封包"""
        auth_msg = {
            "type": "auth",
            "protocol_version": self.config.protocol_version,
            "password": self.config.password,
            "client_name": "AngelaAI",
            "client_version": "7.5.0",
        }
        await self._send(auth_msg)

    async def _reader_loop(self):
        """訊息讀取迴圈"""
        try:
            async for message in self._ws:
                await self._handle_message(message)
        except Exception as e:
            logger.error(f"Reader loop error: {e}")
            self.state = ConnectionState.ERROR
            if self.config.auto_reconnect:
                asyncio.create_task(self._reconnect())

    async def _handle_message(self, raw_message: str):
        """處理接收到的訊息"""
        try:
            msg = json.loads(raw_message)
            msg_type = msg.get("type", "")

            # 處理回應 future
            if "request_id" in msg:
                req_id = msg["request_id"]
                if req_id in self._response_futures:
                    fut = self._response_futures.pop(req_id)
                    if not fut.done():
                        fut.set_result(msg)
                    return

            # 分派給註冊處理器
            if msg_type in self._handlers:
                for handler in self._handlers[msg_type]:
                    try:
                        await handler(msg)
                    except Exception as e:
                        logger.error(f"Handler error for {msg_type}: {e}")

            # 特定類型處理
            if msg_type == "auth_success":
                self._connected_event.set()
                self.state = ConnectionState.READY
            elif msg_type == "player_state":
                self._update_player_state(msg)
            elif msg_type == "frame":
                await self._handle_frame(msg)
            elif msg_type == "chat":
                self._dispatch("chat", msg)

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON: {raw_message[:100]}")
        except Exception as e:
            logger.error(f"Message handling error: {e}")

    def _update_player_state(self, msg: Dict):
        """更新玩家狀態"""
        data = msg.get("data", {})
        self._player_state.position = tuple(data.get("position", self._player_state.position))
        self._player_state.yaw = data.get("yaw", self._player_state.yaw)
        self._player_state.pitch = data.get("pitch", self._player_state.pitch)
        self._player_state.hp = data.get("hp", self._player_state.hp)
        self._player_state.hunger = data.get("hunger", self._player_state.hunger)
        self._player_state.breath = data.get("breath", self._player_state.breath)
        self._player_state.inventory = data.get("inventory", self._player_state.inventory)
        self._player_state.wielded_item = data.get("wielded_item", self._player_state.wielded_item)
        self._player_state.is_on_ground = data.get("on_ground", self._player_state.is_on_ground)

    async def _handle_frame(self, msg: Dict):
        """處理畫面資料 (base64 編碼的 PNG/JPG)"""
        import base64
        import io
        from PIL import Image

        try:
            b64_data = msg.get("data", "")
            img_data = base64.b64decode(b64_data)
            img = Image.open(io.BytesIO(img_data)).convert("RGB")
            frame = np.array(img)

            snapshot = GameSnapshot(
                tick=self._tick,
                timestamp=time.time(),
                player=self._player_state,
                frame=frame,
                nearby_nodes=msg.get("nearby_nodes", []),
                nearby_entities=msg.get("nearby_entities", []),
            )
            self._last_snapshot = snapshot
            self._tick += 1

            if self._frame_callback:
                try:
                    self._frame_callback(frame)
                except Exception as e:
                    logger.error(f"Frame callback error: {e}")

        except Exception as e:
            logger.error(f"Frame decode error: {e}")

    async def _ping_loop(self):
        """心跳迴圈"""
        while self.state == ConnectionState.READY:
            await asyncio.sleep(self.config.ping_interval)
            if self.state != ConnectionState.READY:
                break
            await self._send({"type": "ping", "timestamp": time.time()})

    async def _reconnect(self):
        """自動重連"""
        while self.config.auto_reconnect and self.state != ConnectionState.READY:
            logger.info(f"Reconnecting in {self.config.reconnect_interval}s...")
            await asyncio.sleep(self.config.reconnect_interval)
            if await self.connect():
                break

    async def _send(self, msg: Dict):
        """發送訊息"""
        if self._ws and self.state in (
            ConnectionState.CONNECTED,
            ConnectionState.AUTHENTICATING,
            ConnectionState.READY,
        ):
            await self._ws.send(json.dumps(msg))

    async def send_action(self, action: Dict[str, Any]) -> bool:
        """發送動作指令"""
        msg = {"type": "action", "request_id": str(uuid.uuid4()), "data": action}
        await self._send(msg)
        return True

    async def send_action_wait(
        self, action: Dict[str, Any], timeout: float = 5.0
    ) -> Optional[Dict]:
        """發送動作並等待回應"""
        req_id = str(uuid.uuid4())
        msg = {"type": "action", "request_id": req_id, "data": action}

        fut = asyncio.get_event_loop().create_future()
        self._response_futures[req_id] = fut

        await self._send(msg)

        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._response_futures.pop(req_id, None)
            return None

    def on(self, msg_type: str, handler: Callable):
        """註冊訊息處理器"""
        if msg_type not in self._handlers:
            self._handlers[msg_type] = []
        self._handlers[msg_type].append(handler)

    def set_frame_callback(self, callback: Callable[[np.ndarray], None]):
        """設定畫面回調 (同步呼叫，需快速返回)"""
        self._frame_callback = callback

    def get_latest_snapshot(self) -> Optional[GameSnapshot]:
        """取得最新遊戲快照"""
        return self._last_snapshot

    def get_player_state(self) -> PlayerState:
        """取得玩家狀態"""
        return self._player_state

    async def move(
        self,
        forward: float = 0.0,
        strafe: float = 0.0,
        jump: bool = False,
        sprint: bool = False,
        sneak: bool = False,
    ):
        """移動指令"""
        await self.send_action(
            {
                "type": "move",
                "forward": forward,
                "strafe": strafe,
                "jump": jump,
                "sprint": sprint,
                "sneak": sneak,
            }
        )

    async def look(
        self,
        yaw_delta: float = 0.0,
        pitch_delta: float = 0.0,
        absolute_yaw: Optional[float] = None,
        absolute_pitch: Optional[float] = None,
    ):
        """視線控制"""
        await self.send_action(
            {
                "type": "look",
                "yaw_delta": yaw_delta,
                "pitch_delta": pitch_delta,
                "absolute_yaw": absolute_yaw,
                "absolute_pitch": absolute_pitch,
            }
        )

    async def dig(self, hold: bool = True):
        """挖掘/攻擊 (按住 attack)"""
        await self.send_action({"type": "dig", "hold": hold})

    async def place(self, item_name: Optional[str] = None):
        """放置/使用 (按下 use)"""
        await self.send_action({"type": "place", "item": item_name})

    async def craft(self, recipe: str, count: int = 1):
        """合成指令 (需 CSM 支援)"""
        await self.send_action({"type": "craft", "recipe": recipe, "count": count})

    async def inventory_action(self, action: str, **kwargs):
        """背包操作"""
        await self.send_action(
            {"type": "inventory", "action": action, **kwargs}  # open, close, move, drop, craft
        )

    async def chat(self, message: str):
        """發送聊天訊息"""
        await self.send_action({"type": "chat", "message": message})

    async def disconnect(self):
        """斷開連線"""
        self.config.auto_reconnect = False
        await self._cleanup()
        self.state = ConnectionState.DISCONNECTED

    async def _cleanup(self):
        """清理資源"""
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
        if self._ws:
            await self._ws.close()
            self._ws = None
        self._response_futures.clear()


# 同步包裝器 (供非 async 環境使用)
class SyncLuantiConnector:
    """同步介面包裝器"""

    def __init__(self, config: Optional[LuantiConfig] = None):
        self._async = LuantiConnector(config)
        self._loop = asyncio.new_event_loop()

    def connect(self) -> bool:
        return self._loop.run_until_complete(self._async.connect())

    def disconnect(self):
        self._loop.run_until_complete(self._async.disconnect())

    def send_action(self, action: Dict) -> bool:
        return self._loop.run_until_complete(self._async.send_action(action))

    def get_snapshot(self) -> Optional[GameSnapshot]:
        return self._async.get_latest_snapshot()

    def get_player_state(self) -> PlayerState:
        return self._async.get_player_state()

    def move(self, **kwargs):
        self._loop.run_until_complete(self._async.move(**kwargs))

    def look(self, **kwargs):
        self._loop.run_until_complete(self._async.look(**kwargs))

    def dig(self, hold: bool = True):
        self._loop.run_until_complete(self._async.dig(hold))

    def place(self, item: Optional[str] = None):
        self._loop.run_until_complete(self._async.place(item))

    def run_coroutine(self, coro):
        """在事件循環中執行協程"""
        return self._loop.run_until_complete(coro)

    def __del__(self):
        self._loop.close()
