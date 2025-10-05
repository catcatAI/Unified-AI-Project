#!/usr/bin/env python3
"""
修复HSP连接器中的语法错误和问题
"""

import os
import sys
from pathlib import Path

def fix_hsp_connector_syntax_issues():
    """修复HSP连接器中的语法错误"""
    # 使用绝对路径
    connector_path = Path(r"d:\Projects\Unified-AI-Project\apps\backend\src\core\hsp\connector.py")
    
    if not connector_path.exists():
        print(f"错误: 找不到文件 {connector_path}")
        return False
    
    try:
        with open(connector_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复函数定义后缺少冒号的问题
        # 修复 _dispatch_fact_to_callbacks 函数定义
        content = content.replace(
            "async def _dispatch_fact_to_callbacks(self, message: Dict[str, Any])\n    # message here is the full envelope from the internal bus",
            "async def _dispatch_fact_to_callbacks(self, message: Dict[str, Any]):\n    # message here is the full envelope from the internal bus"
        )
        
        # 修复 _dispatch_capability_advertisement_to_callbacks 函数定义
        content = content.replace(
            "async def _dispatch_capability_advertisement_to_callbacks(self, message: Dict[str, Any])\n    payload = message.get(\"payload\")",
            "async def _dispatch_capability_advertisement_to_callbacks(self, message: Dict[str, Any]):\n    payload = message.get(\"payload\")"
        )
        
        # 修复 _dispatch_task_request_to_callbacks 函数定义
        content = content.replace(
            "async def _dispatch_task_request_to_callbacks(self, message: Dict[str, Any])\n    payload = message.get(\"payload\")",
            "async def _dispatch_task_request_to_callbacks(self, message: Dict[str, Any]):\n    payload = message.get(\"payload\")"
        )
        
        # 修复 _dispatch_task_result_to_callbacks 函数定义
        content = content.replace(
            "async def _dispatch_task_result_to_callbacks(self, message: Dict[str, Any])\n    payload = message.get(\"payload\")",
            "async def _dispatch_task_result_to_callbacks(self, message: Dict[str, Any]):\n    payload = message.get(\"payload\")"
        )
        
        # 修复 _dispatch_acknowledgement_to_callbacks 函数定义
        content = content.replace(
            "async def _dispatch_acknowledgement_to_callbacks(self, message: Dict[str, Any])\n    payload = message.get(\"payload\")",
            "async def _dispatch_acknowledgement_to_callbacks(self, message: Dict[str, Any]):\n    payload = message.get(\"payload\")"
        )
        
        # 修复 unsubscribe 函数定义
        content = content.replace(
            "def unsubscribe(self, topic: str, callback: Optional[Callable[..., Any]] = None)\n    if callback is None:",
            "def unsubscribe(self, topic: str, callback: Optional[Callable[..., Any]] = None):\n    if callback is None:"
        )
        
        # 修复 is_connected setter 定义
        content = content.replace(
            "@is_connected.setter\n    def is_connected(self, value: bool)\n    self._is_connected = value",
            "@is_connected.setter\n    def is_connected(self, value: bool):\n        self._is_connected = value"
        )
        
        # 修复 get_communication_status 函数定义
        content = content.replace(
            "def get_communication_status(self) -> Dict[str, Any]:\n    \"\"\"\n    Returns the current communication status.\n    \"\"\"\n    status = {",
            "def get_communication_status(self) -> Dict[str, Any]:\n    \"\"\"\n    Returns the current communication status.\n    \"\"\"\n    status = {"
        )
        
        # 修复 health_check 函数定义
        content = content.replace(
            "async def health_check(self) -> Dict[str, Any]:\n    \"\"\"健康检查\"\"\"\n    health = {",
            "async def health_check(self) -> Dict[str, Any]:\n    \"\"\"健康检查\"\"\"\n    health = {"
        )
        
        # 修复 subscribe 函数定义
        content = content.replace(
            "async def subscribe(self, topic: str, qos: int = 1)\n    \"\"\"\n    Subscribe to a topic.",
            "async def subscribe(self, topic: str, qos: int = 1):\n    \"\"\"\n    Subscribe to a topic."
        )
        
        # 修复 publish_opinion 函数定义
        content = content.replace(
            "async def publish_opinion(self, opinion_payload: HSPOpinionPayload, topic: Optional[str] = None) -> bool:\n    \"\"\"\n    Publishes an opinion to the HSP network.",
            "async def publish_opinion(self, opinion_payload: HSPOpinionPayload, topic: Optional[str] = None) -> bool:\n    \"\"\"\n    Publishes an opinion to the HSP network."
        )
        
        # 修复 subscribe_to_facts 函数定义
        content = content.replace(
            "async def subscribe_to_facts(self, callback: Callable[..., Any])\n    \"\"\"\n    Subscribe to fact messages.",
            "async def subscribe_to_facts(self, callback: Callable[..., Any]):\n    \"\"\"\n    Subscribe to fact messages."
        )
        
        # 修复 subscribe_to_opinions 函数定义
        content = content.replace(
            "async def subscribe_to_opinions(self, callback: Callable[..., Any])\n    \"\"\"\n    Subscribe to opinion messages.",
            "async def subscribe_to_opinions(self, callback: Callable[..., Any]):\n    \"\"\"\n    Subscribe to opinion messages."
        )
        
        # 修复 get_connector_status 函数定义
        content = content.replace(
            "def get_connector_status(self) -> Dict[str, Any]:\n    \"\"\"\n    Get the connector status.",
            "def get_connector_status(self) -> Dict[str, Any]:\n    \"\"\"\n    Get the connector status."
        )
        
        # 修复 _handle_fact_message 函数定义
        content = content.replace(
            "async def _handle_fact_message(self, fact_message: Dict[str, Any])\n    \"\"\"\n    Handle a fact message.",
            "async def _handle_fact_message(self, fact_message: Dict[str, Any]):\n    \"\"\"\n    Handle a fact message."
        )
        
        # 修复 _handle_opinion_message 函数定义
        content = content.replace(
            "async def _handle_opinion_message(self, opinion_message: Dict[str, Any])\n    \"\"\"\n    Handle an opinion message.",
            "async def _handle_opinion_message(self, opinion_message: Dict[str, Any]):\n    \"\"\"\n    Handle an opinion message."
        )
        
        # 修复 _handle_fallback_message 函数定义
        content = content.replace(
            "async def _handle_fallback_message(self, message: FallbackMessage)\n    \"\"\"\n    Handles a message received from a fallback protocol.",
            "async def _handle_fallback_message(self, message: FallbackMessage):\n    \"\"\"\n    Handles a message received from a fallback protocol."
        )
        
        # 修复方法调用中的问题
        # 修复 datetime.now(timezone.utc).isoformat 为 datetime.now(timezone.utc).isoformat()
        content = content.replace("datetime.now(timezone.utc).isoformat", "datetime.now(timezone.utc).isoformat()")
        
        # 修复 uuid.uuid4 为 uuid.uuid4()
        content = content.replace("str(uuid.uuid4)", "str(uuid.uuid4())")
        
        # 修复 fallback_manager.shutdown 为 await self.fallback_manager.shutdown()
        content = content.replace("_ = await self.fallback_manager.shutdown()", "await self.fallback_manager.shutdown()")
        
        # 修复 self.fallback_manager.start 为 await self.fallback_manager.start()
        content = content.replace("_ = await self.fallback_manager.start", "await self.fallback_manager.start()")
        
        # 修复 self.fallback_manager.initialize 为 await self.fallback_manager.initialize()
        content = content.replace("if self.fallback_manager and await self.fallback_manager.initialize:", "if self.fallback_manager and await self.fallback_manager.initialize():")
        
        # 修复 self.fallback_manager.get_status 为 self.fallback_manager.get_status()
        content = content.replace("status[\"fallback_status\"] = self.fallback_manager.get_status", "status[\"fallback_status\"] = self.fallback_manager.get_status()")
        
        # 修复 health check 中的 get_status 调用
        content = content.replace("fallback_status = self.fallback_manager.get_status", "fallback_status = self.fallback_manager.get_status()")
        
        # 修复 topic.decode 为 topic.decode()
        content = content.replace("topic.decode", "topic.decode()")
        
        # 修复 payload.decode 为 payload.decode()
        content = content.replace("payload.decode", "payload.decode()")
        
        # 修复 ExternalConnector.subscribed_topics = set 为 ExternalConnector.subscribed_topics = set()
        content = content.replace("self.external_connector.subscribed_topics = set", "self.external_connector.subscribed_topics = set()")
        
        # 修复 if 语句后缺少冒号的问题
        content = content.replace("if hasattr(self.external_connector, 'subscribe')", "if hasattr(self.external_connector, 'subscribe'):")
        content = content.replace("if topic is None", "if topic is None:")
        content = content.replace("if payload.get(\"envelope\")", "if payload.get(\"envelope\"):")
        
        # 修复双重冒号问题
        content = content.replace("if hasattr(self.external_connector, 'subscribe')::", "if hasattr(self.external_connector, 'subscribe'):")
        
        # 修复 return 语句缩进问题
        content = content.replace("return self.get_communication_status", "return self.get_communication_status()")
        
        # 修复 set()() 问题
        content = content.replace("self.external_connector.subscribed_topics = set()()", "self.external_connector.subscribed_topics = set()")
        
        # 修复更多的双重冒号问题
        content = content.replace(")::", "):")
        
        # 修复四重冒号问题
        content = content.replace("if topic is None::::", "if topic is None:")
        
        # 修复 timestamp_sent 中的多重括号问题
        content = content.replace("datetime.now(timezone.utc).isoformat()()()()()", "datetime.now(timezone.utc).isoformat()")
        content = content.replace("datetime.now(timezone.utc).isoformat()()()()", "datetime.now(timezone.utc).isoformat()")
        content = content.replace("datetime.now(timezone.utc).isoformat()()", "datetime.now(timezone.utc).isoformat()")
        
        # 修复 ack_timestamp 中的多重括号问题
        content = content.replace("datetime.now(timezone.utc).isoformat()()()()", "datetime.now(timezone.utc).isoformat()")
        content = content.replace("datetime.now(timezone.utc).isoformat()()", "datetime.now(timezone.utc).isoformat()")
        
        # 写入修复后的内容
        with open(connector_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"成功修复HSP连接器中的语法错误: {connector_path}")
        return True
        
    except Exception as e:
        print(f"修复HSP连接器时出错: {e}")
        return False

def main():
    """主函数"""
    print("开始修复HSP连接器中的语法错误...")
    
    if fix_hsp_connector_syntax_issues():
        print("HSP连接器语法错误修复完成!")
    else:
        print("HSP连接器语法错误修复失败!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())