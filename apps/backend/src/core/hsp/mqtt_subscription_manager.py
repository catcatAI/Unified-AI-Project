"""
HSP MQTT Subscription Manager

提供完整的MQTT订阅功能，支持：
- 主题订阅和取消订阅
- QoS级别配置
- 消息回调管理
- 订阅状态监控
- 批量订阅操作
"""

import asyncio
import logging
import json
from typing import Callable, Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class SubscriptionStatus(Enum):
    """订阅状态"""
    ACTIVE = "active"
    PENDING = "pending"
    FAILED = "failed"
    UNSUBSCRIBED = "unsubscribed"


@dataclass
class Subscription:
    """订阅信息"""
    topic: str
    qos: int = 0
    callback: Optional[Callable] = None
    status: SubscriptionStatus = SubscriptionStatus.PENDING
    subscribed_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    message_count: int = 0
    error_count: int = 0


class MQTTSubscriptionManager:
    """
    MQTT订阅管理器
    
    管理所有MQTT主题订阅，处理消息回调
    """
    
    def __init__(self, mqtt_client=None):
        """
        初始化订阅管理器
        
        Args:
            mqtt_client: MQTT客户端实例（paho-mqtt或gmqtt）
        """
        self.mqtt_client = mqtt_client
        self._subscriptions: Dict[str, Subscription] = {}
        self._callback_registry: Dict[str, List[Callable]] = {}
        self._pending_subscriptions: Set[str] = set()
        self._lock = asyncio.Lock()
        
        # 统计
        self.stats = {
            "total_subscriptions": 0,
            "active_subscriptions": 0,
            "failed_subscriptions": 0,
            "messages_received": 0,
            "callbacks_executed": 0,
            "callback_errors": 0
        }
        
        logger.info("[MQTTSubManager] Initialized")
    
    async def set_mqtt_client(self, mqtt_client):
        """设置MQTT客户端"""
        self.mqtt_client = mqtt_client
        logger.info("[MQTTSubManager] MQTT client set")
    
    # ================================================================
    # 订阅管理
    # ================================================================
    
    async def subscribe(
        self,
        topic: str,
        callback: Optional[Callable] = None,
        qos: int = 0,
        retry: int = 3
    ) -> bool:
        """
        订阅主题
        
        Args:
            topic: 主题名称（支持通配符 +/#）
            callback: 消息回调函数
            qos: QoS级别（0, 1, 2）
            retry: 失败重试次数
        
        Returns:
            是否订阅成功
        """
        if not self.mqtt_client:
            logger.error("[MQTTSubManager] MQTT client not set")
            return False
        
        async with self._lock:
            # 检查是否已订阅
            if topic in self._subscriptions:
                logger.warning(f"[MQTTSubManager] Already subscribed to: {topic}")
                # 更新回调
                if callback:
                    self._register_callback(topic, callback)
                return True
            
            # 创建订阅记录
            subscription = Subscription(
                topic=topic,
                qos=qos,
                callback=callback,
                status=SubscriptionStatus.PENDING
            )
            self._subscriptions[topic] = subscription
            self._pending_subscriptions.add(topic)
            
            # 注册回调
            if callback:
                self._register_callback(topic, callback)
            
            # 执行订阅
            success = await self._do_subscribe(topic, qos, retry)
            
            # 更新状态
            if success:
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.subscribed_at = datetime.now(timezone.utc)
                self.stats["active_subscriptions"] += 1
            else:
                subscription.status = SubscriptionStatus.FAILED
                self.stats["failed_subscriptions"] += 1
            
            self.stats["total_subscriptions"] = len(self._subscriptions)
            
            return success
    
    async def _do_subscribe(self, topic: str, qos: int, retry: int) -> bool:
        """执行MQTT订阅"""
        last_error = None
        
        for attempt in range(retry):
            try:
                # 检查客户端类型并调用相应方法
                if hasattr(self.mqtt_client, 'subscribe'):
                    # paho-mqtt 或 gmqtt
                    if asyncio.iscoroutinefunction(self.mqtt_client.subscribe):
                        await self.mqtt_client.subscribe(topic, qos)
                    else:
                        self.mqtt_client.subscribe(topic, qos)
                else:
                    logger.error("[MQTTSubManager] MQTT client has no subscribe method")
                    return False
                
                logger.info(f"[MQTTSubManager] Subscribed to: {topic} (QoS: {qos})")
                return True
                
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                last_error = e

                logger.warning(f"[MQTTSubManager] Subscribe attempt {attempt + 1} failed: {e}")
                if attempt < retry - 1:
                    await asyncio.sleep(1 * (attempt + 1))  # 指数退避
        
        logger.error(f"[MQTTSubManager] Subscribe failed after {retry} attempts: {last_error}")
        return False
    
    async def unsubscribe(self, topic: str) -> bool:
        """
        取消订阅
        
        Args:
            topic: 主题名称
        
        Returns:
            是否取消成功
        """
        if not self.mqtt_client:
            return False
        
        async with self._lock:
            if topic not in self._subscriptions:
                logger.warning(f"[MQTTSubManager] Not subscribed to: {topic}")
                return False
            
            subscription = self._subscriptions[topic]
            
            try:
                if hasattr(self.mqtt_client, 'unsubscribe'):
                    if asyncio.iscoroutinefunction(self.mqtt_client.unsubscribe):
                        await self.mqtt_client.unsubscribe(topic)
                    else:
                        self.mqtt_client.unsubscribe(topic)
                
                # 更新状态
                subscription.status = SubscriptionStatus.UNSUBSCRIBED
                del self._subscriptions[topic]
                self._pending_subscriptions.discard(topic)
                self._callback_registry.pop(topic, None)
                
                self.stats["active_subscriptions"] = max(0, self.stats["active_subscriptions"] - 1)
                
                logger.info(f"[MQTTSubManager] Unsubscribed from: {topic}")
                return True
                
            except Exception as e:
                logger.error(f"[MQTTSubManager] Unsubscribe failed: {e}")
                return False
    
    async def unsubscribe_all(self) -> int:
        """
        取消所有订阅
        
        Returns:
            取消成功的数量
        """
        topics = list(self._subscriptions.keys())
        success_count = 0
        
        for topic in topics:
            if await self.unsubscribe(topic):
                success_count += 1
        
        return success_count
    
    # ================================================================
    # 回调管理
    # ================================================================
    
    def _register_callback(self, topic: str, callback: Callable):
        """注册回调函数"""
        if topic not in self._callback_registry:
            self._callback_registry[topic] = []
        self._callback_registry[topic].append(callback)
    
    def add_callback(self, topic: str, callback: Callable):
        """为已订阅的主题添加额外的回调"""
        if topic in self._subscriptions:
            self._register_callback(topic, callback)
            logger.info(f"[MQTTSubManager] Added callback for: {topic}")
        else:
            logger.warning(f"[MQTTSubManager] Cannot add callback: not subscribed to {topic}")
    
    def remove_callback(self, topic: str, callback: Callable):
        """移除回调函数"""
        if topic in self._callback_registry:
            try:
                self._callback_registry[topic].remove(callback)
                logger.info(f"[MQTTSubManager] Removed callback for: {topic}")
            except ValueError:
                logger.warning(f"[MQTTSubManager] Callback not found for: {topic}")
    
    # ================================================================
    # 消息处理
    # ================================================================
    
    async def on_message(self, topic: str, payload: bytes, qos: int, retain: bool = False):
        """
        处理收到的MQTT消息
        
        Args:
            topic: 主题
            payload: 消息内容
            qos: QoS级别
            retain: 是否为保留消息
        """
        self.stats["messages_received"] += 1
        
        # 解析消息
        try:
            if isinstance(payload, (bytes, bytearray)):
                message = json.loads(payload.decode('utf-8'))
            else:
                message = json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"[MQTTSubManager] Failed to parse message: {e}")
            return
        
        # 查找匹配的订阅
        matched_topics = self._find_matching_topics(topic)
        
        if not matched_topics:
            logger.debug(f"[MQTTSubManager] No subscription matches topic: {topic}")
            return
        
        # 执行回调
        for matched_topic in matched_topics:
            subscription = self._subscriptions[matched_topic]
            subscription.last_message_at = datetime.now(timezone.utc)
            subscription.message_count += 1
            
            callbacks = self._callback_registry.get(matched_topic, [])
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(topic, message, qos, retain)
                    else:
                        callback(topic, message, qos, retain)
                    
                    self.stats["callbacks_executed"] += 1
                    
                except Exception as e:
                    logger.error(f'Error in {__name__}: {e}', exc_info=True)
                    self.stats["callback_errors"] += 1

                    subscription.error_count += 1
                    logger.error(f"[MQTTSubManager] Callback error for {matched_topic}: {e}")
    
    def _find_matching_topics(self, received_topic: str) -> List[str]:
        """
        查找与接收主题匹配的订阅主题
        
        支持通配符：
        - +: 单级通配符
        - #: 多级通配符
        """
        matched = []
        
        for subscription_topic in self._subscriptions:
            if self._topic_matches(subscription_topic, received_topic):
                matched.append(subscription_topic)
        
        return matched
    
    def _topic_matches(self, subscription: str, received: str) -> bool:
        """
        检查主题是否匹配（支持通配符）
        """
        sub_parts = subscription.split('/')
        recv_parts = received.split('/')
        
        # # 通配符匹配所有
        if subscription == '#':
            return True
        
        # 长度检查（# 可以匹配剩余所有层级）
        if len(sub_parts) > len(recv_parts):
            # 除非最后一个部分是 # 且订阅主题更短
            if '#' not in sub_parts or len(sub_parts) > len(recv_parts) + 1:
                return False
        
        for i, sub_part in enumerate(sub_parts):
            if i >= len(recv_parts):
                return False
            
            # # 匹配剩余所有
            if sub_part == '#':
                return True
            
            # + 匹配单级
            if sub_part == '+':
                continue
            
            # 精确匹配
            if sub_part != recv_parts[i]:
                return False
        
        # 如果有 #，它应该在末尾并匹配所有剩余
        if '#' in sub_parts:
            return sub_parts[-1] == '#'
        
        # 长度必须相等（无通配符）
        return len(sub_parts) == len(recv_parts)
    
    # ================================================================
    # 批量操作
    # ================================================================
    
    async def batch_subscribe(
        self,
        topics: List[str],
        callback: Optional[Callable] = None,
        qos: int = 0
    ) -> Dict[str, bool]:
        """
        批量订阅
        
        Args:
            topics: 主题列表
            callback: 回调函数（所有主题共享）
            qos: QoS级别
        
        Returns:
            {topic: success} 字典
        """
        results = {}
        
        for topic in topics:
            results[topic] = await self.subscribe(topic, callback, qos)
        
        return results
    
    # ================================================================
    # 状态查询
    # ================================================================
    
    def get_subscription_info(self, topic: str) -> Optional[Dict[str, Any]]:
        """获取订阅信息"""
        if topic not in self._subscriptions:
            return None
        
        sub = self._subscriptions[topic]
        
        return {
            "topic": sub.topic,
            "qos": sub.qos,
            "status": sub.status.value,
            "subscribed_at": sub.subscribed_at.isoformat() if sub.subscribed_at else None,
            "last_message_at": sub.last_message_at.isoformat() if sub.last_message_at else None,
            "message_count": sub.message_count,
            "error_count": sub.error_count,
            "callback_count": len(self._callback_registry.get(topic, []))
        }
    
    def list_subscriptions(self) -> List[Dict[str, Any]]:
        """列出所有订阅"""
        return [
            self.get_subscription_info(topic)
            for topic in self._subscriptions
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "subscriptions": [
                {"topic": topic, "status": sub.status.value}
                for topic, sub in self._subscriptions.items()
            ]
        }
    
    # ================================================================
    # 工具方法
    # ================================================================
    
    def is_subscribed(self, topic: str) -> bool:
        """检查是否已订阅"""
        return topic in self._subscriptions
    
    def get_active_topics(self) -> List[str]:
        """获取所有活跃的主题"""
        return [
            topic
            for topic, sub in self._subscriptions.items()
            if sub.status == SubscriptionStatus.ACTIVE
        ]
    
    # ================================================================
    # 销毁
    # ================================================================
    
    async def destroy(self):
        """销毁管理器"""
        await self.unsubscribe_all()
        self._subscriptions.clear()
        self._callback_registry.clear()
        self._pending_subscriptions.clear()
        logger.info("[MQTTSubManager] Destroyed")


# 导出
__all__ = [
    'MQTTSubscriptionManager',
    'Subscription',
    'SubscriptionStatus'
]