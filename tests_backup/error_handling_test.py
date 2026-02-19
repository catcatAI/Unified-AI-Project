#!/usr/bin/env python3
"""
錯誤處理測試腳本
測試 API 的錯誤處理能力
"""

import requests
import json
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 10

print("=" * 80)
print("錯誤處理測試")
print("=" * 80)
print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 測試 1: 無效的 JSON
print("【測試 1: 無效的 JSON】")
try:
    response = requests.post(
        f"{BASE_URL}/angela/chat",
        data="invalid json",
        headers={"Content-Type": "application/json"},
        timeout=TIMEOUT
    )
    print(f"狀態碼: {response.status_code}")
    print(f"響應: {response.text[:200]}")
except Exception as e:
    print(f"錯誤: {e}")
print()

# 測試 2: 缺少必需字段
print("【測試 2: 缺少必需字段】")
try:
    response = requests.post(
        f"{BASE_URL}/angela/chat",
        json={},
        timeout=TIMEOUT
    )
    print(f"狀態碼: {response.status_code}")
    print(f"響應: {response.text[:200]}")
except Exception as e:
    print(f"錯誤: {e}")
print()

# 測試 3: 空消息
print("【測試 3: 空消息】")
try:
    response = requests.post(
        f"{BASE_URL}/angela/chat",
        json={"message": ""},
        timeout=TIMEOUT
    )
    print(f"狀態碼: {response.status_code}")
    print(f"響應: {response.text[:200]}")
except Exception as e:
    print(f"錯誤: {e}")
print()

# 測試 4: 超長消息
print("【測試 4: 超長消息】")
try:
    long_message = "測試" * 10000
    response = requests.post(
        f"{BASE_URL}/angela/chat",
        json={"message": long_message},
        timeout=TIMEOUT
    )
    print(f"狀態碼: {response.status_code}")
    print(f"響應: {response.text[:200]}")
except Exception as e:
    print(f"錯誤: {e}")
print()

# 測試 5: 特殊字符
print("【測試 5: 特殊字符】")
try:
    special_chars = "測試 <script>alert('xss')</script> &test; 'quote' \"double\""
    response = requests.post(
        f"{BASE_URL}/angela/chat",
        json={"message": special_chars},
        timeout=TIMEOUT
    )
    print(f"狀態碼: {response.status_code}")
    print(f"響應: {response.text[:200]}")
except Exception as e:
    print(f"錯誤: {e}")
print()

# 測試 6: 不存在的端點
print("【測試 6: 不存在的端點】")
try:
    response = requests.get(f"{BASE_URL}/api/v1/nonexistent", timeout=TIMEOUT)
    print(f"狀態碼: {response.status_code}")
    print(f"響應: {response.text[:200]}")
except Exception as e:
    print(f"錯誤: {e}")
print()

# 測試 7: 錯誤的 HTTP 方法
print("【測試 7: 錯誤的 HTTP 方法】")
try:
    response = requests.delete(f"{BASE_URL}/angela/chat", timeout=TIMEOUT)
    print(f"狀態碼: {response.status_code}")
    print(f"響應: {response.text[:200]}")
except Exception as e:
    print(f"錯誤: {e}")
print()

# 測試 8: SQL 注入嘗試
print("【測試 8: SQL 注入嘗試】")
try:
    sql_injection = "'; DROP TABLE users; --"
    response = requests.post(
        f"{BASE_URL}/angela/chat",
        json={"message": sql_injection},
        timeout=TIMEOUT
    )
    print(f"狀態碼: {response.status_code}")
    print(f"響應: {response.text[:200]}")
except Exception as e:
    print(f"錯誤: {e}")
print()

print("=" * 80)
print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)