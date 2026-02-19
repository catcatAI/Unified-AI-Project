#!/usr/bin/env python3
"""
Angela AI WebSocket 全面測試腳本
"""
import asyncio
import websockets
import json
import time
from typing import Dict, List
import logging
logger = logging.getLogger(__name__)

class WebSocketTester:
    def __init__(self, uri: str = "ws://127.0.0.1:8000/ws"):
        self.uri = uri
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    async def test_connection(self) -> bool:
        """測試 WebSocket 連接"""
        self.total_tests += 1
        print(f"\n【1/5】測試 WebSocket 連接")
        print("-" * 80)

        try:
            async with websockets.connect(self.uri, ping_interval=None) as websocket:
                print(f"✅ PASS - WebSocket 連接成功")
                self.passed_tests += 1
                self.results.append({
                    "test": "connection",
                    "status": "pass",
                    "message": "WebSocket 連接成功"
                })
                return True
        except Exception as e:
            print(f"❌ FAIL - WebSocket 連接失敗: {e}")
            self.failed_tests += 1
            self.results.append({
                "test": "connection",
                "status": "fail",
                "message": f"WebSocket 連接失敗: {str(e)}"
            })
            return False

    async def test_message_send_receive(self) -> bool:
        """測試消息發送和接收"""
        self.total_tests += 1
        print(f"\n【2/5】測試消息發送和接收")
        print("-" * 80)

        try:
            async with websockets.connect(self.uri, ping_interval=None) as websocket:
                # 發送測試消息
                test_message = {
                    "type": "test",
                    "data": "hello websocket",
                    "timestamp": time.time()
                }
                await websocket.send(json.dumps(test_message))
                print(f"發送消息: {test_message}")

                # 接收響應
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"收到響應: {response}")

                print(f"✅ PASS - 消息發送和接收成功")
                self.passed_tests += 1
                self.results.append({
                    "test": "message_send_receive",
                    "status": "pass",
                    "message": "消息發送和接收成功"
                })
                return True
        except asyncio.TimeoutError:
            print(f"❌ FAIL - 消息接收超時")
            self.failed_tests += 1
            self.results.append({
                "test": "message_send_receive",
                "status": "fail",
                "message": "消息接收超時"
            })
            return False
        except Exception as e:
            print(f"❌ FAIL - 消息發送和接收失敗: {e}")
            self.failed_tests += 1
            self.results.append({
                "test": "message_send_receive",
                "status": "fail",
                "message": f"消息發送和接收失敗: {str(e)}"
            })
            return False

    async def test_multiple_messages(self) -> bool:
        """測試多條消息連續發送"""
        self.total_tests += 1
        print(f"\n【3/5】測試多條消息連續發送")
        print("-" * 80)

        try:
            async with websockets.connect(self.uri, ping_interval=None) as websocket:
                messages = [
                    {"type": "chat", "message": "第一條消息"},
                    {"type": "status", "query": "health"},
                    {"type": "chat", "message": "第二條消息"},
                    {"type": "action", "command": "test"},
                    {"type": "chat", "message": "第三條消息"}
                ]

                for i, msg in enumerate(messages, 1):
                    await websocket.send(json.dumps(msg))
                    print(f"發送消息 {i}: {msg}")
                    await asyncio.sleep(0.5)

                print(f"✅ PASS - 多條消息連續發送成功")
                self.passed_tests += 1
                self.results.append({
                    "test": "multiple_messages",
                    "status": "pass",
                    "message": "多條消息連續發送成功"
                })
                return True
        except Exception as e:
            print(f"❌ FAIL - 多條消息連續發送失敗: {e}")
            self.failed_tests += 1
            self.results.append({
                "test": "multiple_messages",
                "status": "fail",
                "message": f"多條消息連續發送失敗: {str(e)}"
            })
            return False

    async def test_connection_stability(self) -> bool:
        """測試連接穩定性（保持連接 10 秒）"""
        self.total_tests += 1
        print(f"\n【4/5】測試連接穩定性")
        print("-" * 80)

        try:
            async with websockets.connect(self.uri, ping_interval=None) as websocket:
                print("保持連接 10 秒...")
                start_time = time.time()
                messages_received = 0

                while time.time() - start_time < 10:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        messages_received += 1
                        print(f"收到消息: {response[:100]}")
                    except asyncio.TimeoutError:
                        continue

                print(f"✅ PASS - 連接穩定，在 10 秒內收到 {messages_received} 條消息")
                self.passed_tests += 1
                self.results.append({
                    "test": "connection_stability",
                    "status": "pass",
                    "message": f"連接穩定，在 10 秒內收到 {messages_received} 條消息"
                })
                return True
        except Exception as e:
            print(f"❌ FAIL - 連接穩定性測試失敗: {e}")
            self.failed_tests += 1
            self.results.append({
                "test": "connection_stability",
                "status": "fail",
                "message": f"連接穩定性測試失敗: {str(e)}"
            })
            return False

    async def test_reconnection(self) -> bool:
        """測試重連能力"""
        self.total_tests += 1
        print(f"\n【5/5】測試重連能力")
        print("-" * 80)

        try:
            # 第一次連接
            async with websockets.connect(self.uri, ping_interval=None) as websocket:
                await websocket.send(json.dumps({"type": "test", "message": "first connection"}))
                print("第一次連接成功")

            # 等待 1 秒
            await asyncio.sleep(1)

            # 重新連接
            async with websockets.connect(self.uri, ping_interval=None) as websocket:
                await websocket.send(json.dumps({"type": "test", "message": "reconnection"}))
                print("重新連接成功")

            print(f"✅ PASS - 重連能力測試成功")
            self.passed_tests += 1
            self.results.append({
                "test": "reconnection",
                "status": "pass",
                "message": "重連能力測試成功"
            })
            return True
        except Exception as e:
            print(f"❌ FAIL - 重連能力測試失敗: {e}")
            self.failed_tests += 1
            self.results.append({
                "test": "reconnection",
                "status": "fail",
                "message": f"重連能力測試失敗: {str(e)}"
            })
            return False

    async def run_all_tests(self):
        """運行所有 WebSocket 測試"""
        print("=" * 80)
        print("Angela AI WebSocket 全面測試")
        print("=" * 80)

        await self.test_connection()
        await self.test_message_send_receive()
        await self.test_multiple_messages()
        await self.test_connection_stability()
        await self.test_reconnection()

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
                if result["status"] == "fail":
                    print(f"❌ {result['test']}")
                    print(f"   錯誤: {result['message']}")

        return {
            "total": self.total_tests,
            "passed": self.passed_tests,
            "failed": self.failed_tests,
            "success_rate": self.passed_tests / self.total_tests * 100 if self.total_tests > 0 else 0,
            "results": self.results
        }

async def main():
    tester = WebSocketTester()
    results = await tester.run_all_tests()

    # 保存結果到 JSON 文件
    with open("/home/cat/桌面/websocket_comprehensive_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n詳細結果已保存到: /home/cat/桌面/websocket_comprehensive_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
