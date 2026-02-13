#!/usr/bin/env python3
"""
Angela AI 系統全面 API 測試腳本
"""
import requests
import json
import time
from typing import Dict, List, Tuple

BASE_URL = "http://127.0.0.1:8000"

class APITester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def test_endpoint(self, method: str, endpoint: str, data: dict = None, headers: dict = None) -> Tuple[bool, dict, str]:
        """測試單個 API 端點"""
        url = f"{BASE_URL}{endpoint}"
        self.total_tests += 1

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=5)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=5)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=5)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=5)
            else:
                return False, {}, f"不支援的方法: {method}"

            # 檢查響應
            success = response.status_code < 400
            if success:
                self.passed_tests += 1
                status = "✅ PASS"
            else:
                self.failed_tests += 1
                status = "❌ FAIL"

            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "success": success,
                "response_time": response.elapsed.total_seconds()
            }

            try:
                result["response"] = response.json()
            except:
                result["response"] = response.text[:500]

            self.results.append(result)
            return success, result["response"], status

        except requests.exceptions.Timeout:
            self.failed_tests += 1
            error_msg = "請求超時"
            self.results.append({
                "endpoint": endpoint,
                "method": method,
                "status_code": None,
                "success": False,
                "error": error_msg
            })
            return False, {}, f"❌ FAIL - {error_msg}"
        except requests.exceptions.ConnectionError:
            self.failed_tests += 1
            error_msg = "連接失敗"
            self.results.append({
                "endpoint": endpoint,
                "method": method,
                "status_code": None,
                "success": False,
                "error": error_msg
            })
            return False, {}, f"❌ FAIL - {error_msg}"
        except Exception as e:
            self.failed_tests += 1
            error_msg = str(e)
            self.results.append({
                "endpoint": endpoint,
                "method": method,
                "status_code": None,
                "success": False,
                "error": error_msg
            })
            return False, {}, f"❌ FAIL - {error_msg}"

    def run_all_tests(self):
        """運行所有測試"""
        print("=" * 80)
        print("Angela AI 系統全面 API 測試")
        print("=" * 80)

        # 1. 健康檢查
        print("\n【1/8】健康檢查端點測試")
        print("-" * 80)
        success, response, status = self.test_endpoint("GET", "/health")
        print(f"GET /health: {status} - {json.dumps(response, ensure_ascii=False)}")

        success, response, status = self.test_endpoint("GET", "/api/v1/health")
        print(f"GET /api/v1/health: {status} - {json.dumps(response, ensure_ascii=False)}")

        success, response, status = self.test_endpoint("GET", "/api/v1/status")
        print(f"GET /api/v1/status: {status} - {json.dumps(response, ensure_ascii=False)}")

        # 2. 對話系統
        print("\n【2/8】對話系統測試")
        print("-" * 80)
        success, response, status = self.test_endpoint("POST", "/angela/chat", {"message": "你好"})
        print(f"POST /angela/chat: {status}")

        success, response, status = self.test_endpoint("POST", "/dialogue", {"message": "你好"})
        print(f"POST /dialogue: {status}")

        success, response, status = self.test_endpoint("POST", "/api/v1/angela/chat", {"message": "你好"})
        print(f"POST /api/v1/angela/chat: {status}")

        # 3. 寵物管理
        print("\n【3/8】寵物管理系統測試")
        print("-" * 80)
        success, response, status = self.test_endpoint("GET", "/api/v1/pet/status")
        print(f"GET /api/v1/pet/status: {status}")

        success, response, status = self.test_endpoint("GET", "/api/v1/pet/config")
        print(f"GET /api/v1/pet/config: {status}")

        success, response, status = self.test_endpoint("POST", "/api/v1/pet/interaction", {"type": "touch", "x": 100, "y": 100})
        print(f"POST /api/v1/pet/interaction: {status}")

        # 4. 感官系統
        print("\n【4/8】感官系統測試")
        print("-" * 80)
        success, response, status = self.test_endpoint("GET", "/api/v1/vision/control")
        print(f"GET /api/v1/vision/control: {status}")

        success, response, status = self.test_endpoint("GET", "/api/v1/audio/control")
        print(f"GET /api/v1/audio/control: {status}")

        success, response, status = self.test_endpoint("GET", "/api/v1/tactile/model")
        print(f"GET /api/v1/tactile/model: {status}")

        # 5. 經濟系統
        print("\n【5/8】經濟系統測試")
        print("-" * 80)
        success, response, status = self.test_endpoint("GET", "/api/v1/economy/status")
        print(f"GET /api/v1/economy/status: {status}")

        success, response, status = self.test_endpoint("POST", "/api/v1/economy/transaction", {
            "buyer": "user1",
            "seller": "user2",
            "item_id": "item_1",
            "price": 10.0
        })
        print(f"POST /api/v1/economy/transaction: {status}")

        # 6. 移動端
        print("\n【6/8】移動端測試")
        print("-" * 80)
        success, response, status = self.test_endpoint("GET", "/api/v1/mobile/status")
        print(f"GET /api/v1/mobile/status: {status}")

        success, response, status = self.test_endpoint("POST", "/api/v1/mobile/sync", {"data": "test"})
        print(f"POST /api/v1/mobile/sync: {status}")

        # 7. AI 代理
        print("\n【7/8】AI 代理系統測試")
        print("-" * 80)
        success, response, status = self.test_endpoint("GET", "/api/v1/agents")
        print(f"GET /api/v1/agents: {status}")

        success, response, status = self.test_endpoint("GET", "/api/v1/agents/1")
        print(f"GET /api/v1/agents/1: {status}")

        # 8. 系統指標
        print("\n【8/8】系統指標測試")
        print("-" * 80)
        success, response, status = self.test_endpoint("GET", "/api/v1/system/metrics/detailed")
        print(f"GET /api/v1/system/metrics/detailed: {status}")

        success, response, status = self.test_endpoint("GET", "/api/v1/system/cluster/status")
        print(f"GET /api/v1/system/cluster/status: {status}")

        success, response, status = self.test_endpoint("GET", "/api/v1/ops/dashboard")
        print(f"GET /api/v1/ops/dashboard: {status}")

        success, response, status = self.test_endpoint("GET", "/api/v1/desktop/state")
        print(f"GET /api/v1/desktop/state: {status}")

        success, response, status = self.test_endpoint("GET", "/api/v1/actions/status")
        print(f"GET /api/v1/actions/status: {status}")

        success, response, status = self.test_endpoint("GET", "/api/v1/models")
        print(f"GET /api/v1/models: {status}")

        # 顯示總結
        print("\n" + "=" * 80)
        print("測試總結")
        print("=" * 80)
        print(f"總測試數: {self.total_tests}")
        print(f"通過: {self.passed_tests} ✅")
        print(f"失敗: {self.failed_tests} ❌")
        print(f"成功率: {(self.passed_tests / self.total_tests * 100):.2f}%")

        # 顯示失敗的測試
        if self.failed_tests > 0:
            print("\n失敗的測試:")
            print("-" * 80)
            for result in self.results:
                if not result["success"]:
                    print(f"❌ {result['method']} {result['endpoint']}")
                    if "error" in result:
                        print(f"   錯誤: {result['error']}")
                    if "status_code" in result:
                        print(f"   狀態碼: {result['status_code']}")

        return {
            "total": self.total_tests,
            "passed": self.passed_tests,
            "failed": self.failed_tests,
            "success_rate": self.passed_tests / self.total_tests * 100 if self.total_tests > 0 else 0,
            "results": self.results
        }

if __name__ == "__main__":
    tester = APITester()
    results = tester.run_all_tests()

    # 保存結果到 JSON 文件
    with open("/home/cat/桌面/api_comprehensive_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n詳細結果已保存到: /home/cat/桌面/api_comprehensive_test_results.json")