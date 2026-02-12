"""
Angela AI v6.0 - Mobile Authentication Demo
行動端身份驗證演示腳本

展示行動端如何使用 Key B 簽署請求以通過後端安全驗證。
"""

import hmac
import hashlib
import json
import time
import requests
import logging
logger = logging.getLogger(__name__)

def sign_request(key_b: str, body: dict) -> str:
    """使用 Key B 對請求內容進行 HMAC-SHA256 簽名"""
    body_str = json.dumps(body, separators=(',', ':'))
    signature = hmac.new(
        key_b.encode(),
        body_str.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

def test_mobile_sync(api_url: str, key_b: str):
    """測試行動端同步接口"""
    endpoint = f"{api_url}/api/v1/mobile/sync"
    
    payload = {
        "device_id": "mobile-phone-001",
        "timestamp": time.time(),
        "action": "status_update",
        "data": {"battery": 85, "status": "active"}
    }
    
    # 1. 生成簽名
    signature = sign_request(key_b, payload)
    
    # 2. 發送請求
    headers = {
        "Content-Type": "application/json",
        "X-Angela-Signature": signature
    }
    
    print(f"🚀 正在發送加密請求到: {endpoint}")
    print(f"🔑 使用簽名: {signature}")
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        if response.status_code == 200:
            print("✅ 驗證成功！服務器回應:")
            print(json.dumps(response.json(), indent=4, ensure_ascii=False))
        else:
            print(f"❌ 驗證失敗: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"💥 請求發生錯誤: {e}")

if __name__ == "__main__":
    # 這裡的 Key B 應該從桌面端的系統匣監控器獲取
    # 模擬測試
    MOCK_KEY_B = "your-key-b-here-from-tray"
    API_BASE = "http://127.0.0.1:8000"
    
    print("--- Angela Mobile Auth Demo ---")
    test_mobile_sync(API_BASE, MOCK_KEY_B)
