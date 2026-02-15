#!/usr/bin/env python3
"""
Angela AI API 端點測試腳本
測試所有可用的 API 端點並記錄結果
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# API 基礎配置
BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 30

# 測試結果存儲
test_results = []

def test_endpoint(method: str, path: str, data: Dict = None, params: Dict = None) -> Dict[str, Any]:
    """測試單個 API 端點"""
    url = f"{BASE_URL}{path}"
    start_time = time.time()

    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, timeout=TIMEOUT)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, params=params, timeout=TIMEOUT)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, params=params, timeout=TIMEOUT)
        elif method.upper() == "DELETE":
            response = requests.delete(url, params=params, timeout=TIMEOUT)
        else:
            return {
                "path": path,
                "method": method,
                "status": "ERROR",
                "error": f"不支持的 HTTP 方法: {method}",
                "response_time": time.time() - start_time
            }

        response_time = time.time() - start_time

        # 解析響應
        try:
            response_data = response.json()
        except:
            response_data = response.text[:500] if response.text else ""

        return {
            "path": path,
            "method": method,
            "status_code": response.status_code,
            "status": "SUCCESS" if response.status_code < 400 else "ERROR",
            "response_time": round(response_time, 3),
            "response_size": len(response.content),
            "response_preview": str(response_data)[:300]
        }

    except requests.exceptions.Timeout:
        return {
            "path": path,
            "method": method,
            "status": "TIMEOUT",
            "error": "請求超時",
            "response_time": time.time() - start_time
        }
    except requests.exceptions.ConnectionError:
        return {
            "path": path,
            "method": method,
            "status": "CONNECTION_ERROR",
            "error": "連接失敗",
            "response_time": time.time() - start_time
        }
    except Exception as e:
        return {
            "path": path,
            "method": method,
            "status": "EXCEPTION",
            "error": str(e),
            "response_time": time.time() - start_time
        }

def run_tests():
    """運行所有測試"""
    global test_results

    print("=" * 80)
    print("Angela AI API 端點測試")
    print("=" * 80)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"基礎 URL: {BASE_URL}")
    print("=" * 80)
    print()

    # 1. 基礎端點測試
    print("\n【1. 基礎端點測試】")
    basic_tests = [
        ("GET", "/", None, None),
        ("GET", "/health", None, None),
        ("GET", "/api/v1/health", None, None),
        ("GET", "/api/v1/status", None, None),
        ("GET", "/docs", None, None),
    ]

    for method, path, data, params in basic_tests:
        result = test_endpoint(method, path, data, params)
        test_results.append(result)
        status_icon = "✓" if result["status"] == "SUCCESS" else "✗"
        print(f"{status_icon} {method} {path} - {result['status']} ({result.get('response_time', 0)}s)")

    # 2. 聊天 API 測試
    print("\n【2. 聊天 API 測試】")
    chat_tests = [
        ("POST", "/angela/chat", {"message": "你好，Angela"}, None),
        ("POST", "/api/v1/angela/chat", {"message": "測試訊息"}, None),
        ("POST", "/dialogue", {"message": "對話測試"}, None),
    ]

    for method, path, data, params in chat_tests:
        result = test_endpoint(method, path, data, params)
        test_results.append(result)
        status_icon = "✓" if result["status"] == "SUCCESS" else "✗"
        print(f"{status_icon} {method} {path} - {result['status']} ({result.get('response_time', 0)}s)")
        if result.get('status_code') == 200:
            print(f"  響應預覽: {result.get('response_preview', '')[:100]}")

    # 3. 代理系統測試
    print("\n【3. 代理系統測試】")
    agent_tests = [
        ("GET", "/api/v1/agents", None, None),
        ("GET", "/api/v1/agents/1", None, None),
    ]

    for method, path, data, params in agent_tests:
        result = test_endpoint(method, path, data, params)
        test_results.append(result)
        status_icon = "✓" if result["status"] == "SUCCESS" else "✗"
        print(f"{status_icon} {method} {path} - {result['status']} ({result.get('response_time', 0)}s)")

    # 4. Pet 系統測試
    print("\n【4. Pet 系統測試】")
    pet_tests = [
        ("GET", "/api/v1/pet/status", None, None),
        ("GET", "/api/v1/pet/config", None, None),
        ("POST", "/api/v1/pet/interaction", {"action": "touch", "part": "head"}, None),
    ]

    for method, path, data, params in pet_tests:
        result = test_endpoint(method, path, data, params)
        test_results.append(result)
        status_icon = "✓" if result["status"] == "SUCCESS" else "✗"
        print(f"{status_icon} {method} {path} - {result['status']} ({result.get('response_time', 0)}s)")

    # 5. 系統狀態測試
    print("\n【5. 系統狀態測試】")
    system_tests = [
        ("GET", "/api/v1/system/metrics/detailed", None, None),
        ("GET", "/api/v1/system/cluster/status", None, None),
        ("GET", "/api/v1/economy/status", None, None),
        ("GET", "/api/v1/mobile/status", None, None),
    ]

    for method, path, data, params in system_tests:
        result = test_endpoint(method, path, data, params)
        test_results.append(result)
        status_icon = "✓" if result["status"] == "SUCCESS" else "✗"
        print(f"{status_icon} {method} {path} - {result['status']} ({result.get('response_time', 0)}s)")

    # 6. 視覺和觸覺測試
    print("\n【6. 視覺和觸覺測試】")
    sensory_tests = [
        ("GET", "/api/v1/vision/control", None, None),
        ("GET", "/api/v1/tactile/model", None, None),
        ("GET", "/api/v1/audio/control", None, None),
    ]

    for method, path, data, params in sensory_tests:
        result = test_endpoint(method, path, data, params)
        test_results.append(result)
        status_icon = "✓" if result["status"] == "SUCCESS" else "✗"
        print(f"{status_icon} {method} {path} - {result['status']} ({result.get('response_time', 0)}s)")

    # 7. 其他 API 測試
    print("\n【7. 其他 API 測試】")
    other_tests = [
        ("GET", "/api/v1/models", None, None),
        ("GET", "/api/v1/actions/status", None, None),
        ("GET", "/api/v1/ops/dashboard", None, None),
        ("GET", "/api/v1/desktop/state", None, None),
    ]

    for method, path, data, params in other_tests:
        result = test_endpoint(method, path, data, params)
        test_results.append(result)
        status_icon = "✓" if result["status"] == "SUCCESS" else "✗"
        print(f"{status_icon} {method} {path} - {result['status']} ({result.get('response_time', 0)}s)")

    # 統計結果
    print("\n" + "=" * 80)
    print("測試統計")
    print("=" * 80)

    total = len(test_results)
    success = sum(1 for r in test_results if r["status"] == "SUCCESS")
    failed = total - success

    print(f"總測試數: {total}")
    print(f"成功: {success} ({success/total*100:.1f}%)")
    print(f"失敗: {failed} ({failed/total*100:.1f}%)")

    # 響應時間統計
    response_times = [r.get('response_time', 0) for r in test_results if 'response_time' in r]
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        print(f"\n響應時間統計:")
        print(f"  平均: {avg_time:.3f}s")
        print(f"  最快: {min_time:.3f}s")
        print(f"  最慢: {max_time:.3f}s")

    # 失敗的測試
    if failed > 0:
        print("\n失敗的測試:")
        for result in test_results:
            if result["status"] != "SUCCESS":
                print(f"  ✗ {result['method']} {result['path']}")
                print(f"    狀態: {result['status']}")
                if 'error' in result:
                    print(f"    錯誤: {result['error']}")

    print("\n" + "=" * 80)
    print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # 保存詳細結果
    with open('/home/cat/桌面/api_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)

    print(f"\n詳細結果已保存到: /home/cat/桌面/api_test_results.json")

if __name__ == "__main__":
    run_tests()