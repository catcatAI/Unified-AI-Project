#!/usr/bin/env python3
"""
HSP Fallback協議使用示例

這個示例展示了如何使用增強的HSP連接器，包括：
1. 配置fallback協議
2. 處理HSP連接失敗
3. 自動切換到備用協議
4. 監控通訊狀態
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime, timezone

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.hsp.connector import HSPConnector
from src.hsp.types import HSPFactPayload, HSPCapabilityAdvertisementPayload, HSPTaskRequestPayload
from src.hsp.utils.fallback_config_loader import get_config_loader

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HSPFallbackDemo:
    """HSP Fallback協議演示類"""
    
    def __init__(self):
        self.connector = None
        self.received_messages = []
    
    async def setup_connector(self, ai_id: str = "demo_ai"):
        """設置HSP連接器"""
        logger.info("=== 設置HSP連接器 ===")
        
        # 加載配置
        config_loader = get_config_loader()
        hsp_config = config_loader.get_hsp_config()
        mqtt_config = hsp_config.get("mqtt", {})
        
        # 創建連接器（啟用fallback）
        self.connector = HSPConnector(
            ai_id=ai_id,
            broker_address=mqtt_config.get("broker_address", "127.0.0.1"),
            broker_port=mqtt_config.get("broker_port", 1883),
            mock_mode=False,  # 使用真實模式來測試fallback
            enable_fallback=True
        )
        
        # 註冊消息處理器
        self.connector.register_on_fact_callback(self._handle_fact)
        self.connector.register_on_capability_advertisement_callback(self._handle_capability)
        self.connector.register_on_task_request_callback(self._handle_task_request)
        
        logger.info(f"HSP連接器已創建，AI ID: {ai_id}")
        
        # 等待fallback協議初始化
        await asyncio.sleep(2)
        
        return self.connector
    
    async def _handle_fact(self, fact_payload: HSPFactPayload, sender_id: str, envelope: dict):
        """處理接收到的事實"""
        logger.info(f"收到事實 from {sender_id}: {fact_payload.get('statement_nl', 'No statement')}")
        self.received_messages.append(("fact", fact_payload, sender_id))
    
    async def _handle_capability(self, cap_payload: HSPCapabilityAdvertisementPayload, sender_id: str, envelope: dict):
        """處理接收到的能力廣告"""
        logger.info(f"收到能力廣告 from {sender_id}: {cap_payload.get('name', 'No name')}")
        self.received_messages.append(("capability", cap_payload, sender_id))
    
    async def _handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_id: str, envelope: dict):
        """處理接收到的任務請求"""
        logger.info(f"收到任務請求 from {sender_id}: {task_payload.get('request_id', 'No ID')}")
        self.received_messages.append(("task_request", task_payload, sender_id))
    
    async def demonstrate_connection_and_fallback(self):
        """演示連接和fallback機制"""
        logger.info("=== 演示連接和Fallback機制 ===")
        
        # 嘗試連接HSP
        logger.info("1. 嘗試連接HSP...")
        try:
            await self.connector.connect()
            logger.info("HSP連接嘗試完成")
        except Exception as e:
            logger.warning(f"HSP連接異常: {e}")
        
        # 檢查通訊狀態
        status = self.connector.get_communication_status()
        logger.info("2. 通訊狀態檢查:")
        logger.info(f"   - HSP可用: {status.get('hsp_available', False)}")
        logger.info(f"   - 已連接: {status.get('is_connected', False)}")
        logger.info(f"   - Fallback啟用: {status.get('fallback_enabled', False)}")
        logger.info(f"   - Fallback初始化: {status.get('fallback_initialized', False)}")
        
        if status.get('fallback_status'):
            fallback_status = status['fallback_status']
            logger.info(f"   - 活動協議: {fallback_status.get('active_protocol', 'None')}")
            
            protocols = fallback_status.get('protocols', [])
            for protocol in protocols:
                logger.info(f"   - {protocol['name']}: {protocol['status']} (優先級: {protocol['priority']})")
        
        # 健康檢查
        logger.info("3. 進行健康檢查...")
        health = await self.connector.health_check()
        logger.info(f"   - HSP健康: {health.get('hsp_healthy', False)}")
        logger.info(f"   - Fallback健康: {health.get('fallback_healthy', False)}")
        logger.info(f"   - 整體健康: {health.get('overall_healthy', False)}")
        
        return health.get('overall_healthy', False)
    
    async def demonstrate_message_sending(self):
        """演示消息發送"""
        logger.info("=== 演示消息發送 ===")
        
        # 發送事實
        logger.info("1. 發送事實消息...")
        fact_payload: HSPFactPayload = {
            "id": f"demo_fact_{int(datetime.now().timestamp())}",
            "statement_type": "natural_language",
            "statement_nl": "這是通過fallback協議發送的演示事實",
            "source_ai_id": self.connector.ai_id,
            "timestamp_created": datetime.now(timezone.utc).isoformat(),
            "confidence_score": 0.95
        }
        
        success = await self.connector.publish_fact(fact_payload, "hsp/knowledge/facts/demo")
        logger.info(f"   事實發送結果: {'成功' if success else '失敗'}")
        
        # 發送能力廣告
        logger.info("2. 發送能力廣告...")
        capability_payload: HSPCapabilityAdvertisementPayload = {
            "capability_id": f"demo_capability_{int(datetime.now().timestamp())}",
            "ai_id": self.connector.ai_id,
            "name": "演示能力",
            "description": "這是一個演示能力，展示fallback協議的使用",
            "version": "1.0",
            "availability_status": "online"
        }
        
        success = await self.connector.publish_capability_advertisement(capability_payload)
        logger.info(f"   能力廣告發送結果: {'成功' if success else '失敗'}")
        
        # 發送任務請求
        logger.info("3. 發送任務請求...")
        task_payload: HSPTaskRequestPayload = {
            "request_id": f"demo_request_{int(datetime.now().timestamp())}",
            "requester_ai_id": self.connector.ai_id,
            "target_ai_id": "demo_target_ai",
            "parameters": {
                "task_type": "demo_task",
                "description": "這是一個演示任務請求",
                "priority": "normal"
            }
        }
        
        correlation_id = await self.connector.send_task_request(task_payload, "demo_target_ai")
        logger.info(f"   任務請求發送結果: {'成功' if correlation_id else '失敗'}")
        if correlation_id:
            logger.info(f"   關聯ID: {correlation_id}")
        
        return True
    
    async def demonstrate_protocol_switching(self):
        """演示協議切換"""
        logger.info("=== 演示協議切換 ===")
        
        if not self.connector.fallback_manager:
            logger.warning("Fallback管理器未初始化，跳過協議切換演示")
            return
        
        # 獲取當前狀態
        status = self.connector.fallback_manager.get_status()
        current_protocol = status.get('active_protocol')
        logger.info(f"當前活動協議: {current_protocol}")
        
        # 模擬協議故障（這裡只是演示，實際中協議會自動切換）
        logger.info("模擬協議故障和自動切換...")
        
        # 強制重新選擇協議
        await self.connector.fallback_manager._select_active_protocol()
        
        # 檢查新狀態
        new_status = self.connector.fallback_manager.get_status()
        new_protocol = new_status.get('active_protocol')
        logger.info(f"切換後協議: {new_protocol}")
        
        # 測試切換後的消息發送
        test_fact: HSPFactPayload = {
            "id": f"switch_test_fact_{int(datetime.now().timestamp())}",
            "statement_type": "natural_language",
            "statement_nl": "協議切換測試消息",
            "source_ai_id": self.connector.ai_id,
            "timestamp_created": datetime.now(timezone.utc).isoformat(),
            "confidence_score": 0.9
        }
        
        success = await self.connector.publish_fact(test_fact, "hsp/knowledge/facts/switch_test")
        logger.info(f"協議切換後消息發送: {'成功' if success else '失敗'}")
        
        return True
    
    async def show_statistics(self):
        """顯示統計信息"""
        logger.info("=== 統計信息 ===")
        
        if self.connector.fallback_manager:
            status = self.connector.fallback_manager.get_status()
            protocols = status.get('protocols', [])
            
            for protocol in protocols:
                stats = protocol.get('stats', {})
                logger.info(f"{protocol['name']} 協議統計:")
                logger.info(f"   - 狀態: {protocol['status']}")
                logger.info(f"   - 發送消息: {stats.get('messages_sent', 0)}")
                logger.info(f"   - 接收消息: {stats.get('messages_received', 0)}")
                logger.info(f"   - 錯誤數: {stats.get('errors', 0)}")
                logger.info(f"   - 最後活動: {stats.get('last_activity', 'Never')}")
        
        logger.info(f"本地接收到的消息數: {len(self.received_messages)}")
        for i, (msg_type, payload, sender) in enumerate(self.received_messages):
            logger.info(f"   {i+1}. {msg_type} from {sender}")
    
    async def cleanup(self):
        """清理資源"""
        logger.info("=== 清理資源 ===")
        
        if self.connector:
            try:
                await self.connector.disconnect()
            except:
                pass
            
            if self.connector.fallback_manager:
                try:
                    await self.connector.fallback_manager.stop()
                except:
                    pass
        
        logger.info("資源清理完成")

async def main():
    """主演示函數"""
    demo = HSPFallbackDemo()
    
    try:
        # 設置連接器
        await demo.setup_connector("fallback_demo_ai")
        
        # 演示連接和fallback
        healthy = await demo.demonstrate_connection_and_fallback()
        
        if healthy:
            # 演示消息發送
            await demo.demonstrate_message_sending()
            
            # 等待消息處理
            await asyncio.sleep(2)
            
            # 演示協議切換
            await demo.demonstrate_protocol_switching()
            
            # 等待更多處理
            await asyncio.sleep(2)
        
        # 顯示統計信息
        await demo.show_statistics()
        
    except Exception as e:
        logger.error(f"演示過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理
        await demo.cleanup()

if __name__ == "__main__":
    print("HSP Fallback協議演示")
    print("=" * 50)
    asyncio.run(main())