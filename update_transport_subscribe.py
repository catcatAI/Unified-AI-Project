#!/usr/bin/env python3
"""
更新transport.py以使用MQTT订阅管理器
"""

import re

transport_file = '/home/cat/桌面/Unified-AI-Project/apps/backend/src/core/hsp/transport.py'

# 读取文件内容
with open(transport_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 添加导入
old_imports = '''import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from enum import Enum
from multiprocessing import Queue
import asyncio'''

new_imports = '''import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from enum import Enum
from multiprocessing import Queue
import asyncio
from .mqtt_subscription_manager import MQTTSubscriptionManager'''

content = content.replace(old_imports, new_imports)

# 2. 修改MQTTTransport类的__init__方法
old_mqtt_init = '''    def __init__(self, ai_id: str, broker_address: str, broker_port: int):
        """
        MQTT 传输实现
        """
        self.ai_id = ai_id
        self.broker_address = broker_address
        self.broker_port = broker_port
        self._external_connector = None
        
        logger.info(f"MQTTTransport initialized for {ai_id}")'''

new_mqtt_init = '''    def __init__(self, ai_id: str, broker_address: str, broker_port: int):
        """
        MQTT 传输实现
        """
        self.ai_id = ai_id
        self.broker_address = broker_address
        self.broker_port = broker_port
        self._external_connector = None
        self._subscription_manager = None  # MQTT订阅管理器
        
        logger.info(f"MQTTTransport initialized for {ai_id}")'''

content = content.replace(old_mqtt_init, new_mqtt_init)

# 3. 修改connect方法以初始化订阅管理器
old_mqtt_connect = '''    async def connect(self) -> bool:
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
            logger.info(f"MQTT connection {'successful' if result else 'failed'}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False'''

new_mqtt_connect = '''    async def connect(self) -> bool:
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
            return False'''

content = content.replace(old_mqtt_connect, new_mqtt_connect)

# 4. 实现subscribe方法
old_mqtt_subscribe = '''    async def subscribe(self, topic: str, callback: Callable) -> bool:
        """訂閱 MQTT 主題"""
        if not self._external_connector:
            logger.error("Not connected to MQTT broker")
            return False
        
        # TODO: 實現 MQTT 訂閱（需要擴展 ExternalConnector）
        logger.warning("MQTT subscribe not fully implemented yet")
        return True'''

new_mqtt_subscribe = '''    async def subscribe(self, topic: str, callback: Callable, qos: int = 0) -> bool:
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
        
        return self._subscription_manager.get_stats()'''

content = content.replace(old_mqtt_subscribe, new_mqtt_subscribe)

# 5. 修改disconnect方法以清理订阅管理器
old_mqtt_disconnect = '''    async def disconnect(self) -> bool:
        """斷開 MQTT 連接"""
        if self._external_connector:
            result = await self._external_connector.disconnect()
            logger.info("MQTT disconnected")
            return result
        return True'''

new_mqtt_disconnect = '''    async def disconnect(self) -> bool:
        """斷開 MQTT 連接"""
        # 清理订阅管理器
        if self._subscription_manager:
            await self._subscription_manager.destroy()
            self._subscription_manager = None
        
        if self._external_connector:
            result = await self._external_connector.disconnect()
            logger.info("MQTT disconnected")
            return result
        return True'''

content = content.replace(old_mqtt_disconnect, new_mqtt_disconnect)

# 写入文件
with open(transport_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ transport.py 更新完成")
print("修改内容：")
print("1. 添加MQTTSubscriptionManager导入")
print("2. 在MQTTTransport中添加_subscription_manager属性")
print("3. connect方法中初始化订阅管理器")
print("4. 实现完整的subscribe方法")
print("5. 添加unsubscribe、batch_subscribe、list_subscriptions、get_subscription_stats方法")
print("6. disconnect方法中清理订阅管理器")