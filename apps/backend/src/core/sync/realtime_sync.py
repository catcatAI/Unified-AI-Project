"""
實時同步系統
實現系統間的實時數據同步和狀態同步
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import websockets
import redis.asyncio as redis
from contextlib import asynccontextmanager

# 設置日誌
logging.basicConfig(level=logging.INFO())
logger = logging.getLogger(__name__)

class SyncEventType(Enum):
    """同步事件類型"""
    DATA_UPDATE = "data_update"
    STATUS_CHANGE = "status_change"
    MODEL_UPDATE = "model_update"
    AGENT_ACTION = "agent_action"
    SYSTEM_ALERT = "system_alert"
    USER_ACTION = "user_action"
    TRAINING_PROGRESS = "training_progress"

@dataclass
class SyncEvent,
    """同步事件"""
    id, str
    type, SyncEventType
    source, str
    target, Optional[str]
    data, Dict[str, Any]
    timestamp, datetime
    priority, int = 1  # 1=低, 2=中, 3=高
    
    def to_dict(self) -> Dict[str, Any]
        """轉換為字典"""
        return {
            **asdict(self),
            'type': self.type.value(),
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
def from_dict(cls, data, Dict[str, Any]) -> 'SyncEvent':
        """從字典創建事件"""
        data['type'] = SyncEventType(data['type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

class RealtimeSyncManager,
    """實時同步管理器"""
    
    def __init__(self, redis_url, str == "redis,//localhost,6379"):
        self.redis_url = redis_url
        self.redis_client, Optional[redis.Redis] = None
        self.websocket_connections, Dict[str, websockets.WebSocketServerProtocol] = {}
        self.event_handlers, Dict[SyncEventType, List[Callable]] = {}
        self.subscribers, Dict[str, List[Callable]] = {}
        self.sync_stats = {
            'events_sent': 0,
            'events_received': 0,
            'connections': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    async def initialize(self):
        """初始化同步管理器"""
        try,
            # 連接到 Redis
            self.redis_client = redis.from_url(self.redis_url())
            await self.redis_client.ping()
            logger.info("Redis 連接成功")
            
            # 啟動事件監聽
            asyncio.create_task(self._listen_for_events())
            
            logger.info("實時同步管理器初始化完成")
        except Exception as e,::
            logger.error(f"初始化實時同步管理器失敗, {e}")
            # 如果 Redis 不可用,使用內存替代
            self._use_memory_fallback()
    
    def _use_memory_fallback(self):
        """使用內存作為後備"""
        logger.warning("Redis 不可用,使用內存存儲作為後備")
        self.memory_store = {}
        self.redis_client == None
    
    async def register_websocket(self, websocket, websockets.WebSocketServerProtocol(), client_id, str):
        """註冊 WebSocket 連接"""
        self.websocket_connections[client_id] = websocket
        self.sync_stats['connections'] += 1
        logger.info(f"WebSocket 連接已註冊, {client_id}")
        
        # 發送歡迎消息
        await self._send_to_client(client_id, {
            'type': 'connection_established',
            'client_id': client_id,
            'timestamp': datetime.now().isoformat()
        })
    
    async def unregister_websocket(self, client_id, str):
        """註銷 WebSocket 連接"""
        if client_id in self.websocket_connections,::
            del self.websocket_connections[client_id]
            self.sync_stats['connections'] -= 1
            logger.info(f"WebSocket 連接已註銷, {client_id}")
    
    async def _send_to_client(self, client_id, str, message, Dict[str, Any]):
        """發送消息到特定客戶端"""
        if client_id in self.websocket_connections,::
            try,
                await self.websocket_connections[client_id].send(json.dumps(message))
            except Exception as e,::
                logger.error(f"發送消息到客戶端 {client_id} 失敗, {e}")
                # 移除失效的連接
                await self.unregister_websocket(client_id)
    
    async def broadcast(self, event, SyncEvent, exclude_client, Optional[str] = None):
        """廣播事件到所有連接的客戶端"""
        message = event.to_dict()
        
        # 發送到 WebSocket 客戶端
        for client_id in self.websocket_connections,::
            if client_id != exclude_client,::
                await self._send_to_client(client_id, message)
        
        # 發送到 Redis(如果可用)
        if self.redis_client,::
            try,
                await self.redis_client.publish('sync_events', json.dumps(message))
                self.sync_stats['events_sent'] += 1
            except Exception as e,::
                logger.error(f"發布事件到 Redis 失敗, {e}")
                self.sync_stats['errors'] += 1
        else,
            # 使用內存存儲
            if 'events' not in self.memory_store,::
                self.memory_store['events'] = []
            self.memory_store['events'].append(message)
    
    async def send_event(self, event_type, SyncEventType, source, str, data, Dict[str, Any] ,
    target, Optional[str] = None, priority, int == 1):
        """發送同步事件"""
        event == SyncEvent(,
    id=str(uuid.uuid4()),
            type=event_type,
            source=source,
            target=target,
            data=data,
            timestamp=datetime.now(),
            priority=priority
        )
        
        # 調用註冊的事件處理器
        if event_type in self.event_handlers,::
            for handler in self.event_handlers[event_type]::
                try,
                    await handler(event)
                except Exception as e,::
                    logger.error(f"事件處理器執行失敗, {e}")
        
        # 廣播事件
        await self.broadcast(event)
        
        logger.info(f"事件已發送, {event_type.value} from {source}")
    
    def register_handler(self, event_type, SyncEventType, handler, Callable):
        """註冊事件處理器"""
        if event_type not in self.event_handlers,::
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"已註冊 {event_type.value} 事件處理器")
    
    def subscribe(self, pattern, str, callback, Callable):
        """訂閱特定模式的事件"""
        if pattern not in self.subscribers,::
            self.subscribers[pattern] = []
        self.subscribers[pattern].append(callback)
        logger.info(f"已訂閱模式, {pattern}")
    
    async def _listen_for_events(self):
        """監聽 Redis 事件"""
        if not self.redis_client,::
            return
        
        try,
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe('sync_events')
            
            async for message in pubsub.listen():::
                if message['type'] == 'message':::
                    try,
                        event_data = json.loads(message['data'])
                        event == SyncEvent.from_dict(event_data)
                        await self._process_received_event(event)
                    except Exception as e,::
                        logger.error(f"處理接收的事件失敗, {e}")
                        self.sync_stats['errors'] += 1
        except Exception as e,::
            logger.error(f"監聽 Redis 事件失敗, {e}")
    
    async def _process_received_event(self, event, SyncEvent):
        """處理接收到的事件"""
        self.sync_stats['events_received'] += 1
        
        # 檢查訂閱者
        for pattern, callbacks in self.subscribers.items():::
            if pattern in event.source or pattern in event.type.value,::
                for callback in callbacks,::
                    try,
                        await callback(event)
                    except Exception as e,::
                        logger.error(f"訂閱者回調執行失敗, {e}")
    
    async def sync_data_between_systems(self, from_system, str, to_system, str, ,
    data, Dict[str, Any] sync_type, str == "full"):
        """在系統間同步數據"""
        await self.send_event(,
    SyncEventType.DATA_UPDATE(),
            from_system,
            {
                'to_system': to_system,
                'data': data,
                'sync_type': sync_type
            }
        )
        
        logger.info(f"數據同步請求已發送, {from_system} -> {to_system}")
    
    async def sync_system_status(self, system, str, status, Dict[str, Any]):
        """同步系統狀態"""
        await self.send_event(,
    SyncEventType.STATUS_CHANGE(),
            system,
            status
        )
    
    async def sync_model_update(self, model_id, str, update_data, Dict[str, Any]):
        """同步模型更新"""
        await self.send_event(,
    SyncEventType.MODEL_UPDATE(),
            "model_manager",
            {
                'model_id': model_id,
                'update_data': update_data
            }
        )
    
    async def sync_agent_action(self, agent_id, str, action, str, result, Dict[str, Any]):
        """同步代理動作"""
        await self.send_event(,
    SyncEventType.AGENT_ACTION(),
            "agent_manager",
            {
                'agent_id': agent_id,
                'action': action,
                'result': result
            }
        )
    
    async def sync_training_progress(self, training_id, str, progress, Dict[str, Any]):
        """同步訓練進度"""
        await self.send_event(,
    SyncEventType.TRAINING_PROGRESS(),
            "training_manager",
            {
                'training_id': training_id,
                'progress': progress
            }
        )
    
    async def create_sync_group(self, group_name, str, members, List[str]):
        """創建同步組"""
        await self.send_event(,
    SyncEventType.SYSTEM_ALERT(),
            "sync_manager",
            {
                'action': 'create_group',
                'group_name': group_name,
                'members': members
            }
        )
    
    async def handle_data_conflict(self, conflict_info, Dict[str, Any]):
        """處理數據衝突"""
        await self.send_event(,
    SyncEventType.SYSTEM_ALERT(),
            "conflict_resolver",
            conflict_info,
            priority=3
        )
    
    async def get_sync_stats(self) -> Dict[str, Any]
        """獲取同步統計信息"""
        uptime = datetime.now() - self.sync_stats['start_time']
        return {
            **self.sync_stats(),
            'uptime_seconds': uptime.total_seconds(),
            'active_connections': len(self.websocket_connections()),
            'registered_handlers': sum(len(handlers) for handlers in self.event_handlers.values()),:::
            'subscriptions': sum(len(callbacks) for callbacks in self.subscribers.values())::
        }

    async def cleanup(self):
        """清理資源"""
        # 關閉所有 WebSocket 連接
        for websocket in self.websocket_connections.values():::
            try,
                await websocket.close()
            except,::
                pass
        
        # 關閉 Redis 連接
        if self.redis_client,::
            await self.redis_client.close()
        
        logger.info("實時同步管理器已清理")

# 創建全局實例
sync_manager == RealtimeSyncManager()

# 預定義的事件處理器
async def default_data_update_handler(event, SyncEvent):
    """默認數據更新處理器"""
    logger.info(f"處理數據更新, {event.source} -> {event.data.get('to_system')}")

async def default_status_change_handler(event, SyncEvent):
    """默認狀態變更處理器"""
    logger.info(f"系統狀態變更, {event.source} - {event.data}")

async def default_model_update_handler(event, SyncEvent):
    """默認模型更新處理器"""
    logger.info(f"模型更新, {event.data.get('model_id')}")

# 註冊默認處理器
sync_manager.register_handler(SyncEventType.DATA_UPDATE(), default_data_update_handler)
sync_manager.register_handler(SyncEventType.STATUS_CHANGE(), default_status_change_handler)
sync_manager.register_handler(SyncEventType.MODEL_UPDATE(), default_model_update_handler)