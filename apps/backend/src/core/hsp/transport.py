#!/usr/bin/env python3
"""
HSP Transport Abstraction Layer
支持本地 IPC (multiprocessing.Queue) 和遠程 MQTT 的統一接口
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from enum import Enum
from multiprocessing import Queue
import asyncio
from .mqtt_subscription_manager import MQTTSubscriptionManager

logger = logging.getLogger(__name__)


class HSPTransportMode(Enum):
    """HSP 傳輸模式"""
    LOCAL_IPC = "local_ipc"      # 本地進程間通信（multiprocessing.Queue）
    MQTT_BROKER = "mqtt_broker"  # MQTT 代理（現有實現）


class HSPTransport(ABC):
    """HSP 傳輸層抽象基類"""
    
    @abstractmethod
    async def connect(self) -> bool:
        """建立連接"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """斷開連接"""
        pass
    
    @abstractmethod
    async def publish(self, topic: str, payload: Dict[str, Any]) -> bool:
        """發布消息"""
        pass
    
    @abstractmethod
    async def subscribe(self, topic: str, callback: Callable) -> bool:
        """訂閱主題"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """檢查連接狀態"""
        pass


class LocalIPCTransport(HSPTransport):
    """
    本地 IPC 傳輸實現
    使用 multiprocessing.Queue 進行進程間通信
    """
    
    def __init__(self, send_queue: Optional[Queue] = None, 
                 recv_queue: Optional[Queue] = None):
        """
        初始化本地 IPC 傳輸
        
        Args:
            send_queue: 發送隊列（向其他進程發送消息）
            recv_queue: 接收隊列（從其他進程接收消息）
        """
        self.send_queue = send_queue
        self.recv_queue = recv_queue
        self._connected = False
        self._subscriptions: Dict[str, Callable] = {}
        self._listener_task: Optional[asyncio.Task] = None
        
        logger.info("LocalIPCTransport initialized")
    
    async def connect(self) -> bool:
        """建立連接（對於本地 IPC，主要是啟動監聽器）"""
        if self._connected:
            logger.warning("Already connected")
            return True
        
        self._connected = True
        
        # 啟動消息監聽器
        if self.recv_queue:
            self._listener_task = asyncio.create_task(self._message_listener())
        
        logger.info("LocalIPCTransport connected")
        return True
    
    async def disconnect(self) -> bool:
        """斷開連接"""
        if not self._connected:
            return True
        
        self._connected = False
        
        # 停止監聽器
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        
        logger.info("LocalIPCTransport disconnected")
        return True
    
    async def publish(self, topic: str, payload: Dict[str, Any]) -> bool:
        """
        發布消息到隊列
        
        Args:
            topic: 主題（用於路由）
            payload: 消息負載
        """
        if not self._connected or not self.send_queue:
            logger.error("Not connected or send_queue not available")
            return False
        
        message = {
            "topic": topic,
            "payload": payload
        }
        
        try:
            # 使用 run_in_executor 避免阻塞
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.send_queue.put, message)
            logger.debug(f"Published message to topic: {topic}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False
    
    async def subscribe(self, topic: str, callback: Callable) -> bool:
        """
        訂閱主題
        
        Args:
            topic: 主題名稱
            callback: 回調函數（接收 payload）
        """
        self._subscriptions[topic] = callback
        logger.info(f"Subscribed to topic: {topic}")
        return True
    
    def is_connected(self) -> bool:
        """檢查連接狀態"""
        return self._connected
    
    async def _message_listener(self):
        """消息監聽器（在後台運行）"""
        logger.info("Message listener started")
        
        while self._connected:
            try:
                # 非阻塞獲取消息
                loop = asyncio.get_event_loop()
                message = await loop.run_in_executor(
                    None, 
                    lambda: self.recv_queue.get(timeout=0.5) if self.recv_queue else None
                )
                
                if message:
                    topic = message.get("topic")
                    payload = message.get("payload")
                    
                    # 調用訂閱的回調
                    if topic in self._subscriptions:
                        callback = self._subscriptions[topic]
                        if asyncio.iscoroutinefunction(callback):
                            await callback(payload)
                        else:
                            callback(payload)
                    else:
                        logger.debug(f"No subscription for topic: {topic}")
                        
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                if self._connected:
# 只在連接時記錄錯誤
                    logger.debug(f"Listener error (may be timeout): {e}")
                await asyncio.sleep(0.1)
        
        logger.info("Message listener stopped")


class MQTTTransport(HSPTransport):
    """
    MQTT 傳輸實現（包裝現有的 ExternalConnector）
    保持與現有代碼的兼容性
    """
    
    def __init__(self, ai_id: str, broker_address: str = "localhost", 
                 broker_port: int = 1883):
        """
        初始化 MQTT 傳輸
        
        Args:
            ai_id: AI 標識符
            broker_address: MQTT 代理地址
            broker_port: MQTT 代理端口
        """
        self.ai_id = ai_id
        self.broker_address = broker_address
        self.broker_port = broker_port
        self._external_connector = None
        
        logger.info(f"MQTTTransport initialized for {ai_id}")
    
    async def connect(self) -> bool:
        """建立 MQTT 連接"""
        try:
            # 延遲導入以避免循環依賴
            from src.core.hsp.external.external_connector import ExternalConnector
            
            self._external_connector = ExternalConnector(
                ai_id=self.ai_id,
                broker_address=self.broker_address,
                broker_port=self.broker_port
            )
            
            result = await self._external_connector.connect()
            
            if result:
                # 初始化订阅管理器
                self._subscription_manager = MQTTSubscriptionManager()
                if hasattr(self._external_connector, 'mqtt_client'):
                    await self._subscription_manager.set_mqtt_client(
                        self._external_connector.mqtt_client
                    )
                logger.info("MQTT subscription manager initialized")
            
            logger.info(f"MQTT connection {'successful' if result else 'failed'}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """斷開 MQTT 連接"""
        # 清理订阅管理器
        if self._subscription_manager:
            await self._subscription_manager.destroy()
            self._subscription_manager = None
        
        if self._external_connector:
            result = await self._external_connector.disconnect()
            logger.info("MQTT disconnected")
            return result
        return True
    
    async def publish(self, topic: str, payload: Dict[str, Any]) -> bool:
        """發布 MQTT 消息"""
        if not self._external_connector:
            logger.error("Not connected to MQTT broker")
            return False
        
        return await self._external_connector.publish(topic, payload)
    
    async def subscribe(self, topic: str, callback: Callable, qos: int = 0) -> bool:
        """訂閱 MQTT 主題"""
        if not self._external_connector or not self._subscription_manager:
            logger.error("Not connected to MQTT broker or subscription manager not initialized")
            return False
        
        try:
            result = await self._subscription_manager.subscribe(topic, callback, qos)
            if result:
                logger.info(f"Successfully subscribed to topic: {topic}")
            else:
                logger.error(f"Failed to subscribe to topic: {topic}")
            return result
        except Exception as e:
            logger.error(f"Error subscribing to topic {topic}: {e}")
            return False
    
    async def unsubscribe(self, topic: str) -> bool:
        """取消訂閱 MQTT 主題"""
        if not self._subscription_manager:
            logger.error("Subscription manager not initialized")
            return False
        
        try:
            result = await self._subscription_manager.unsubscribe(topic)
            return result
        except Exception as e:
            logger.error(f"Error unsubscribing from topic {topic}: {e}")
            return False
    
    async def batch_subscribe(self, topics: list, callback: Callable, qos: int = 0) -> dict:
        """批量訂閱 MQTT 主題"""
        if not self._subscription_manager:
            logger.error("Subscription manager not initialized")
            return {}
        
        try:
            results = await self._subscription_manager.batch_subscribe(topics, callback, qos)
            return results
        except Exception as e:
            logger.error(f"Error in batch subscribe: {e}")
            return {}
    
    def list_subscriptions(self) -> list:
        """列出所有訂閱"""
        if not self._subscription_manager:
            return []
        
        return self._subscription_manager.list_subscriptions()
    
    def get_subscription_stats(self) -> dict:
        """獲取訂閱統計"""
        if not self._subscription_manager:
            return {}
        
        return self._subscription_manager.get_stats()
    
    def is_connected(self) -> bool:
        """檢查 MQTT 連接狀態"""
        return self._external_connector is not None


class HSPTransportFactory:
    """HSP 傳輸工廠"""
    
    @staticmethod
    def create_transport(mode: HSPTransportMode, **kwargs) -> HSPTransport:
        """
        創建 HSP 傳輸實例
        
        Args:
            mode: 傳輸模式
            **kwargs: 傳輸特定參數
        
        Returns:
            HSPTransport 實例
        """
        if mode == HSPTransportMode.LOCAL_IPC:
            return LocalIPCTransport(
                send_queue=kwargs.get("send_queue"),
                recv_queue=kwargs.get("recv_queue")
            )
        elif mode == HSPTransportMode.MQTT_BROKER:
            return MQTTTransport(
                ai_id=kwargs.get("ai_id", "default_ai"),
                broker_address=kwargs.get("broker_address", "localhost"),
                broker_port=kwargs.get("broker_port", 1883)
            )
        else:
            raise ValueError(f"Unknown transport mode: {mode}")


# 測試代碼
if __name__ == "__main__":
    import multiprocessing as mp
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def test_local_ipc():
        """測試本地 IPC 傳輸"""
        print("=== Testing Local IPC Transport ===\n")
        
        # 創建隊列
        queue_a_to_b = mp.Queue()
        queue_b_to_a = mp.Queue()
        
        # 創建兩個傳輸實例（模擬兩個進程）
        transport_a = LocalIPCTransport(send_queue=queue_a_to_b, recv_queue=queue_b_to_a)
        transport_b = LocalIPCTransport(send_queue=queue_b_to_a, recv_queue=queue_a_to_b)
        
        # 連接
        await transport_a.connect()
        await transport_b.connect()
        
        # 訂閱
        received_messages = []
        
        async def on_message(payload):
            received_messages.append(payload)
            print(f"Received: {payload}")
        
        await transport_b.subscribe("test_topic", on_message)
        
        # 發送消息
        await transport_a.publish("test_topic", {"message": "Hello from A"})
        
        # 等待消息處理
        await asyncio.sleep(1)
        
        # 斷開連接
        await transport_a.disconnect()
        await transport_b.disconnect()
        
        print(f"\nReceived {len(received_messages)} messages")
        print("=== Test Complete ===")
    
    # 運行測試
    asyncio.run(test_local_ipc())
