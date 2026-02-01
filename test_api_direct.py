#!/usr/bin/env python3
"""
簡化的API測試工具
直接測試FastAPI端點而不依賴外部連接
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加項目路徑
PROJECT_ROOT = str(Path(__file__).resolve().parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_api_endpoints():
    """測試API端點功能"""
    
    logger.info("🧪 開始API端點測試...")
    
    try:
        # 直接導入測試API端點
        from apps.backend.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # 測試健康檢查端點
        logger.info("測試健康檢查端點...")
        response = client.get("/")
        if response.status_code == 200:
            logger.info("✅ 健康檢查端點正常")
        else:
            logger.error(f"❌ 健康檢查失敗: {response.status_code}")
        
        # 測試聊天端點
        logger.info("測試聊天端點...")
        response = client.post(
            "/api/v1/chat/mscu",
            json={"message": "Hello", "user_id": "test_user"}
        )
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ 聊天端點正常")
            logger.info(f"   響應: {data}")
        else:
            logger.error(f"❌ 聊天端點失敗: {response.status_code}")
            logger.error(f"   錯誤: {response.text}")
        
        # 測試記憶存儲端點
        logger.info("測試記憶存儲端點...")
        response = client.post(
            "/api/v1/memory/store",
            json={
                "experience": {
                    "content": "Test memory",
                    "user_id": "test_user",
                    "type": "conversation"
                }
            }
        )
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ 記憶存儲端點正常")
            logger.info(f"   響應: {data}")
        else:
            logger.error(f"❌ 記憶存儲端點失敗: {response.status_code}")
            logger.error(f"   錯誤: {response.text}")
        
        # 測試代理端點
        logger.info("測試代理端點...")
        response = client.post(
            "/api/v1/agents/launch",
            json={"agent_type": "conversational", "config": {}}
        )
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ 代理端點正常")
            logger.info(f"   代理數量: {len(data.get('agents', []))}")
        else:
            logger.error(f"❌ 代理端點失敗: {response.status_code}")
            logger.error(f"   錯誤: {response.text}")
        
        # 測試寵物狀態端點
        logger.info("測試寵物狀態端點...")
        response = client.get("/api/v1/pet/status")
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ 寵物狀態端點正常")
            logger.info(f"   寵物名稱: {data.get('pet_name', 'Unknown')}")
        else:
            logger.error(f"❌ 寵物狀態端點失敗: {response.status_code}")
            logger.error(f"   錯誤: {response.text}")
        
        # 測試系統狀態端點
        logger.info("測試系統狀態端點...")
        response = client.get("/api/v1/system/status")
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ 系統狀態端點正常")
            logger.info(f"   狀態: {data.get('status', 'unknown')}")
        else:
            logger.error(f"❌ 系統狀態端點失敗: {response.status_code}")
            logger.error(f"   錯誤: {response.text}")
        
        logger.info("🎉 API端點測試完成！")
        
    except ImportError as e:
        logger.error(f"無法導入必要的模塊: {e}")
        logger.error("請確保FastAPI和testclient已安裝")
        
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_endpoints())