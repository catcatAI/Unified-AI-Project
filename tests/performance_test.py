#!/usr/bin/env python3
"""
性能測試腳本
測試 API 的響應時間和並發處理能力
"""

import requests
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import logging
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 30

print("=" * 80)
print("性能測試")
print("=" * 80)
print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 測試 1: 單個請求響應時間
print("【測試 1: 單個請求響應時間】")
endpoints = [
    ("GET", "/"),
    ("GET", "/health"),
    ("GET", "/api/v1/pet/status"),
    ("GET", "/api/v1/agents"),
]

for method, path in endpoints:
    start_time = time.time()
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{path}", timeout=TIMEOUT)
        response_time = time.time() - start_time
        print(f"  {method} {path}: {response_time:.3f}s (狀態: {response.status_code})")
    except Exception as e:
        logger.error(f'Error in performance_test.py: {e}', exc_info=True)
        response_time = time.time() - start_time

        print(f"  {method} {path}: {response_time:.3f}s (錯誤: {e})")
print()

# 測試 2: 連續請求響應時間變化
print("【測試 2: 連續請求響應時間變化】")
response_times = []
for i in range(10):
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=TIMEOUT)
        response_time = time.time() - start_time
        response_times.append(response_time)
        print(f"  請求 {i+1}: {response_time:.3f}s")
    except Exception as e:
        print(f"  請求 {i+1}: 錯誤 - {e}")

if response_times:
    avg = sum(response_times) / len(response_times)
    min_time = min(response_times)
    max_time = max(response_times)
    print(f"  平均: {avg:.3f}s, 最快: {min_time:.3f}s, 最慢: {max_time:.3f}s")
print()

# 測試 3: 並發請求
print("【測試 3: 並發請求】")
def make_request(request_id):
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=TIMEOUT)
        response_time = time.time() - start_time
        return request_id, response_time, response.status_code, None
    except Exception as e:
        logger.error(f'Error in performance_test.py: {e}', exc_info=True)
        response_time = time.time() - start_time

        return request_id, response_time, None, str(e)

concurrent_levels = [1, 5, 10, 20]
for concurrent in concurrent_levels:
    print(f"  並發級別: {concurrent}")
    start_time = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=concurrent) as executor:
        futures = [executor.submit(make_request, i) for i in range(concurrent)]
        for future in futures:
            results.append(future.result())

    total_time = time.time() - start_time
    successful = sum(1 for r in results if r[3] is None)
    failed = concurrent - successful
    avg_response = sum(r[1] for r in results) / len(results)

    print(f"    總時間: {total_time:.3f}s")
    print(f"    成功: {successful}, 失敗: {failed}")
    print(f"    平均響應時間: {avg_response:.3f}s")
    print(f"    吞吐量: {concurrent/total_time:.2f} 請求/秒")
print()

# 測試 4: 資源使用監控
print("【測試 4: 資源使用監控】")
import psutil
cpu_before = psutil.cpu_percent(interval=1)
memory_before = psutil.virtual_memory().percent

print(f"  測試前 CPU: {cpu_before}%, 內存: {memory_before}%")

# 執行一些請求
for _ in range(20):
    requests.get(f"{BASE_URL}/api/v1/health", timeout=TIMEOUT)

cpu_after = psutil.cpu_percent(interval=1)
memory_after = psutil.virtual_memory().percent

print(f"  測試後 CPU: {cpu_after}%, 內存: {memory_after}%")
print(f"  CPU 變化: {cpu_after - cpu_before:+.1f}%")
print(f"  內存變化: {memory_after - memory_before:+.1f}%")
print()

print("=" * 80)
print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)