#!/usr/bin/env python3
"""
Angela AI 系統深入分析腳本
- 測試所有 API 端點
- 測試 WebSocket 連接
- 測試對話功能
- 檢查潛在問題
"""
import asyncio
import aiohttp
import json
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any
import logging
logger = logging.getLogger(__name__)

# 測試配置
BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws"

class SystemAnalyzer:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "api_tests": {},
            "websocket_test": {},
            "dialogue_tests": {},
            "potential_issues": [],
            "summary": {}
        }

    async def test_api_endpoint(self, session: aiohttp.ClientSession, endpoint: str, method: str = "GET", data: dict = None) -> Dict[str, Any]:
        """測試單個 API 端點"""
        url = f"{BASE_URL}{endpoint}"
        start_time = time.time()

        try:
            if method == "GET":
                async with session.get(url) as response:
                    status = response.status
                    response_time = time.time() - start_time
                    try:
                        response_data = await response.json()
                    except Exception as e:
                        logger.error(f'Unexpected error in comprehensive_analysis_test.py: {e}', exc_info=True)
                        response_data = await response.text()


                    return {
                        "status": "success" if 200 <= status < 300 else "error",
                        "status_code": status,
                        "response_time": round(response_time, 3),
                        "response": response_data,
                        "error": None
                    }

            elif method == "POST":
                async with session.post(url, json=data) as response:
                    status = response.status
                    response_time = time.time() - start_time
                    try:
                        response_data = await response.json()
                    except Exception as e:
                        logger.error(f'Unexpected error in comprehensive_analysis_test.py: {e}', exc_info=True)
                        response_data = await response.text()


                    return {
                        "status": "success" if 200 <= status < 300 else "error",
                        "status_code": status,
                        "response_time": round(response_time, 3),
                        "response": response_data,
                        "error": None
                    }

        except Exception as e:
            logger.error(f'Error in comprehensive_analysis_test.py: {e}', exc_info=True)
            return {

                "status": "error",
                "status_code": None,
                "response_time": round(time.time() - start_time, 3),
                "response": None,
                "error": str(e)
            }

    async def test_all_api_endpoints(self):
        """測試所有 API 端點"""
        print("\n" + "="*60)
        print("測試所有 API 端點")
        print("="*60)

        async with aiohttp.ClientSession() as session:
            # 基礎端點
            endpoints = [
                ("/", "GET"),
                ("/health", "GET"),
                ("/api/v1/health", "GET"),
                ("/api/v1/status", "GET"),
                ("/api/v1/agents", "GET"),
                ("/api/v1/agents/1", "GET"),
                ("/api/v1/pet/status", "GET"),
                ("/api/v1/pet/config", "GET"),
                ("/api/v1/pet/interaction", "POST", {"interaction_type": "touch"}),
                ("/api/v1/system/metrics/detailed", "GET"),
                ("/api/v1/system/cluster/status", "GET"),
                ("/api/v1/economy/status", "GET"),
                ("/api/v1/vision/control", "GET"),
                ("/api/v1/tactile/model", "GET"),
                ("/api/v1/audio/control", "GET"),
                ("/api/v1/models", "GET"),
                ("/api/v1/actions/status", "GET"),
                ("/api/v1/ops/dashboard", "GET"),
                ("/api/v1/desktop/state", "GET"),
                ("/api/v1/mobile/status", "GET"),  # 這個預期會失敗
            ]

            for endpoint_info in endpoints:
                if len(endpoint_info) == 2:
                    endpoint, method = endpoint_info
                    data = None
                else:
                    endpoint, method, data = endpoint_info

                print(f"\n測試: {method} {endpoint}")
                result = await self.test_api_endpoint(session, endpoint, method, data)

                self.results["api_tests"][endpoint] = result

                if result["status"] == "success":
                    print(f"  ✅ 成功 ({result['status_code']}) - {result['response_time']}s")
                else:
                    print(f"  ❌ 失敗 ({result['status_code']})")
                    if result["error"]:
                        print(f"     錯誤: {result['error']}")

    async def test_websocket_connection(self):
        """測試 WebSocket 連接"""
        print("\n" + "="*60)
        print("測試 WebSocket 連接")
        print("="*60)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(WS_URL) as ws:
                    print("  ✅ WebSocket 連接成功")

                    # 等待服務器消息
                    try:
                        msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            print(f"  📥 收到消息: {data.get('type', 'unknown')}")

                            self.results["websocket_test"] = {
                                "status": "success",
                                "connected": True,
                                "server_message": data
                            }
                        else:
                            self.results["websocket_test"] = {
                                "status": "success",
                                "connected": True,
                                "server_message": None
                            }
                    except asyncio.TimeoutError:
                        print("  ⚠️  5秒內未收到服務器消息")
                        self.results["websocket_test"] = {
                            "status": "success",
                            "connected": True,
                            "server_message": None,
                            "warning": "No message received within 5 seconds"
                        }

        except Exception as e:
            print(f"  ❌ WebSocket 連接失敗: {e}")
            self.results["websocket_test"] = {
                "status": "error",
                "connected": False,
                "error": str(e)
            }

    async def test_dialogue_functionality(self):
        """測試對話功能"""
        print("\n" + "="*60)
        print("測試對話功能")
        print("="*60)

        async with aiohttp.ClientSession() as session:
            # 測試 /angela/chat 端點
            print("\n測試 /angela/chat 端點")
            result = await self.test_api_endpoint(
                session,
                "/angela/chat",
                "POST",
                {"message": "你好，請問你叫什麼名字？"}
            )
            self.results["dialogue_tests"]["angela_chat"] = result

            if result["status"] == "success":
                print(f"  ✅ 成功 - 響應時間: {result['response_time']}s")
                if isinstance(result["response"], dict):
                    response_text = result['response'].get('response', str(result['response']))
                    if isinstance(response_text, str):
                        print(f"     回應: {response_text[:100]}...")
                    else:
                        print(f"     回應: {str(response_text)[:100]}...")
            else:
                print(f"  ❌ 失敗: {result.get('error', 'Unknown error')}")

            # 測試 /dialogue 端點
            print("\n測試 /dialogue 端點")
            result = await self.test_api_endpoint(
                session,
                "/dialogue",
                "POST",
                {"message": "你好，請問你叫什麼名字？"}
            )
            self.results["dialogue_tests"]["dialogue"] = result

            if result["status"] == "success":
                print(f"  ✅ 成功 - 響應時間: {result['response_time']}s")
                if isinstance(result["response"], dict):
                    response_text = result['response'].get('response', str(result['response']))
                    if isinstance(response_text, str):
                        print(f"     回應: {response_text[:100]}...")
                    else:
                        print(f"     回應: {str(response_text)[:100]}...")
            else:
                print(f"  ❌ 失敗: {result.get('error', 'Unknown error')}")

            # 測試 /api/v1/angela/chat 端點
            print("\n測試 /api/v1/angela/chat 端點")
            result = await self.test_api_endpoint(
                session,
                "/api/v1/angela/chat",
                "POST",
                {"message": "你好，請問你叫什麼名字？"}
            )
            self.results["dialogue_tests"]["api_v1_angela_chat"] = result

            if result["status"] == "success":
                print(f"  ✅ 成功 - 響應時間: {result['response_time']}s")
                if isinstance(result["response"], dict):
                    response_text = result['response'].get('response', str(result['response']))
                    if isinstance(response_text, str):
                        print(f"     回應: {response_text[:100]}...")
                    else:
                        print(f"     回應: {str(response_text)[:100]}...")
            else:
                print(f"  ❌ 失敗: {result.get('error', 'Unknown error')}")

    async def check_potential_issues(self):
        """檢查潛在問題"""
        print("\n" + "="*60)
        print("檢查潛在問題")
        print("="*60)

        issues = []

        # 檢查 API 響應時間
        print("\n檢查 API 響應時間...")
        slow_apis = []
        for endpoint, result in self.results["api_tests"].items():
            if result["status"] == "success" and result["response_time"] > 2.0:
                slow_apis.append({
                    "endpoint": endpoint,
                    "response_time": result["response_time"]
                })

        if slow_apis:
            issues.append({
                "type": "performance",
                "severity": "warning",
                "description": "API 響應時間過慢 (>2秒)",
                "details": slow_apis
            })
            print(f"  ⚠️  發現 {len(slow_apis)} 個響應時間過慢的 API 端點")
        else:
            print("  ✅ 所有 API 響應時間正常")

        # 檢查 API 失敗
        print("\n檢查 API 失敗...")
        failed_apis = []
        for endpoint, result in self.results["api_tests"].items():
            if result["status"] == "error":
                failed_apis.append({
                    "endpoint": endpoint,
                    "error": result.get("error", "Unknown error"),
                    "status_code": result.get("status_code")
                })

        if failed_apis:
            issues.append({
                "type": "functionality",
                "severity": "error",
                "description": "API 端點失敗",
                "details": failed_apis
            })
            print(f"  ❌ 發現 {len(failed_apis)} 個失敗的 API 端點")
        else:
            print("  ✅ 所有 API 端點正常")

        # 檢查對話功能
        print("\n檢查對話功能...")
        failed_dialogues = []
        for endpoint, result in self.results["dialogue_tests"].items():
            if result["status"] == "error":
                failed_dialogues.append({
                    "endpoint": endpoint,
                    "error": result.get("error", "Unknown error")
                })

        if failed_dialogues:
            issues.append({
                "type": "functionality",
                "severity": "error",
                "description": "對話功能失敗",
                "details": failed_dialogues
            })
            print(f"  ❌ 發現 {len(failed_dialogues)} 個失敗的對話端點")
        else:
            print("  ✅ 對話功能正常")

        # 檢查 WebSocket 連接
        print("\n檢查 WebSocket 連接...")
        if self.results["websocket_test"].get("status") != "success":
            issues.append({
                "type": "connectivity",
                "severity": "error",
                "description": "WebSocket 連接失敗",
                "details": [self.results["websocket_test"]]
            })
            print("  ❌ WebSocket 連接失敗")
        else:
            print("  ✅ WebSocket 連接正常")

        self.results["potential_issues"] = issues

    def generate_summary(self):
        """生成摘要"""
        print("\n" + "="*60)
        print("測試摘要")
        print("="*60)

        total_apis = len(self.results["api_tests"])
        successful_apis = sum(1 for r in self.results["api_tests"].values() if r["status"] == "success")
        failed_apis = total_apis - successful_apis

        total_dialogues = len(self.results["dialogue_tests"])
        successful_dialogues = sum(1 for r in self.results["dialogue_tests"].values() if r["status"] == "success")
        failed_dialogues = total_dialogues - successful_dialogues

        websocket_status = self.results["websocket_test"].get("status", "unknown")

        summary = {
            "api_tests": {
                "total": total_apis,
                "successful": successful_apis,
                "failed": failed_apis,
                "success_rate": round(successful_apis / total_apis * 100, 2) if total_apis > 0 else 0
            },
            "dialogue_tests": {
                "total": total_dialogues,
                "successful": successful_dialogues,
                "failed": failed_dialogues,
                "success_rate": round(successful_dialogues / total_dialogues * 100, 2) if total_dialogues > 0 else 0
            },
            "websocket_status": websocket_status,
            "total_issues": len(self.results["potential_issues"]),
            "issues_by_severity": {
                "error": sum(1 for i in self.results["potential_issues"] if i["severity"] == "error"),
                "warning": sum(1 for i in self.results["potential_issues"] if i["severity"] == "warning")
            }
        }

        self.results["summary"] = summary

        print(f"\nAPI 測試: {successful_apis}/{total_apis} 成功 ({summary['api_tests']['success_rate']}%)")
        print(f"對話測試: {successful_dialogues}/{total_dialogues} 成功 ({summary['dialogue_tests']['success_rate']}%)")
        print(f"WebSocket 連接: {'✅ 成功' if websocket_status == 'success' else '❌ 失敗'}")
        print(f"發現問題: {len(self.results['potential_issues'])} 個")
        print(f"  - 錯誤: {summary['issues_by_severity']['error']} 個")
        print(f"  - 警告: {summary['issues_by_severity']['warning']} 個")

    async def run(self):
        """運行所有測試"""
        print("\n" + "="*60)
        print("Angela AI 系統深入分析")
        print("="*60)
        print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            await self.test_all_api_endpoints()
            await self.test_websocket_connection()
            await self.test_dialogue_functionality()
            await self.check_potential_issues()
            self.generate_summary()

            print("\n" + "="*60)
            print(f"完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*60)

            # 保存結果
            with open("/tmp/angela_comprehensive_analysis.json", "w") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)

            print("\n結果已保存到: /tmp/angela_comprehensive_analysis.json")

            return self.results

        except Exception as e:
            print(f"\n❌ 測試過程中發生錯誤: {e}")
            traceback.print_exc()
            return None

async def main():
    analyzer = SystemAnalyzer()
    results = await analyzer.run()

    if results:
        print("\n詳細結果:")
        print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())