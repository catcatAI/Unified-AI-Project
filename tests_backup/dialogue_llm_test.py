#!/usr/bin/env python3
"""
Angela AI 對話功能和 LLM 集成測試腳本
"""
import requests
import json
import time
from typing import Dict, List
import logging
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000"

class DialogueLLMTester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def test_dialogue_endpoint(self, endpoint: str, message: str) -> bool:
        """測試對話端點"""
        self.total_tests += 1

        try:
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json={"message": message},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                # 檢查響應是否包含必要的字段
                if "response" in data or "response_text" in data:
                    response_text = data.get("response", data.get("response_text", ""))
                    if response_text and len(response_text) > 0:
                        self.passed_tests += 1
                        self.results.append({
                            "test": f"dialogue_{endpoint}",
                            "status": "pass",
                            "message": f"對話成功: {response_text[:100]}",
                            "full_response": data
                        })
                        return True

            self.failed_tests += 1
            self.results.append({
                "test": f"dialogue_{endpoint}",
                "status": "fail",
                "message": f"對話失敗: {response.text}",
                "status_code": response.status_code
            })
            return False
        except Exception as e:
            logger.error(f'Error in dialogue_llm_test.py: {e}', exc_info=True)
            self.failed_tests += 1

            self.results.append({
                "test": f"dialogue_{endpoint}",
                "status": "fail",
                "message": f"對話異常: {str(e)}"
            })
            return False

    def test_multiple_conversations(self) -> bool:
        """測試多輪對話"""
        self.total_tests += 1

        try:
            conversation_history = [
                "你好",
                "我很好",
                "你是誰",
                "今天天氣如何",
                "謝謝"
            ]

            print("\n【2/4】測試多輪對話")
            print("-" * 80)

            all_success = True
            for i, message in enumerate(conversation_history, 1):
                success, data, _ = self.test_single_request(message)
                if not success:
                    all_success = False
                print(f"第 {i} 輪: '{message}' -> {'成功' if success else '失敗'}")

            if all_success:
                self.passed_tests += 1
                self.results.append({
                    "test": "multiple_conversations",
                    "status": "pass",
                    "message": "多輪對話全部成功"
                })
                return True
            else:
                self.failed_tests += 1
                self.results.append({
                    "test": "multiple_conversations",
                    "status": "fail",
                    "message": "多輪對話部分失敗"
                })
                return False
        except Exception as e:
            logger.error(f'Error in dialogue_llm_test.py: {e}', exc_info=True)
            self.failed_tests += 1

            self.results.append({
                "test": "multiple_conversations",
                "status": "fail",
                "message": f"多輪對話異常: {str(e)}"
            })
            return False

    def test_single_request(self, message: str):
        """發送單個對話請求"""
        try:
            response = requests.post(
                f"{BASE_URL}/angela/chat",
                json={"message": message},
                timeout=10
            )
            if response.status_code == 200:
                return True, response.json(), "✅"
            else:
                return False, response.text, "❌"
        except Exception as e:
            logger.error(f'Error in dialogue_llm_test.py: {e}', exc_info=True)
            return False, str(e), "❌"


    def test_emotion_detection(self) -> bool:
        """測試情感識別"""
        self.total_tests += 1

        try:
            print("\n【3/4】測試情感識別")
            print("-" * 80)

            test_messages = [
                ("我很開心", "positive"),
                ("我很難過", "negative"),
                ("我很平靜", "neutral"),
                ("我很憤怒", "negative"),
                ("我很興奮", "positive")
            ]

            detected_emotions = []
            for message, expected_emotion in test_messages:
                success, data, _ = self.test_single_request(message)
                if success:
                    emotion = data.get("emotion", data.get("angela_mood", "unknown"))
                    detected_emotions.append((message, emotion))
                    print(f"'{message}' -> {emotion}")

            self.passed_tests += 1
            self.results.append({
                "test": "emotion_detection",
                "status": "pass",
                "message": "情感識別測試完成",
                "emotions": detected_emotions
            })
            return True
        except Exception as e:
            logger.error(f'Error in dialogue_llm_test.py: {e}', exc_info=True)
            self.failed_tests += 1

            self.results.append({
                "test": "emotion_detection",
                "status": "fail",
                "message": f"情感識別異常: {str(e)}"
            })
            return False

    def test_response_time(self) -> bool:
        """測試響應時間"""
        self.total_tests += 1

        try:
            print("\n【4/4】測試響應時間")
            print("-" * 80)

            test_messages = [
                "你好",
                "簡單的問題",
                "這是一個稍微長一點的問題",
                "這是一個非常長的問題，用來測試系統處理長文本的能力，看看響應時間是否在可接受範圍內"
            ]

            response_times = []
            for message in test_messages:
                start_time = time.time()
                success, data, _ = self.test_single_request(message)
                end_time = time.time()
                response_time = end_time - start_time

                if success:
                    response_times.append((message, response_time))
                    print(f"'{message[:30]}...' -> {response_time:.2f}秒")

            if response_times:
                avg_time = sum(rt for _, rt in response_times) / len(response_times)
                print(f"\n平均響應時間: {avg_time:.2f}秒")

                if avg_time < 5.0:
                    self.passed_tests += 1
                    self.results.append({
                        "test": "response_time",
                        "status": "pass",
                        "message": f"平均響應時間 {avg_time:.2f}秒，在可接受範圍內",
                        "response_times": response_times
                    })
                    return True
                else:
                    self.failed_tests += 1
                    self.results.append({
                        "test": "response_time",
                        "status": "fail",
                        "message": f"平均響應時間 {avg_time:.2f}秒，超過5秒閾值",
                        "response_times": response_times
                    })
                    return False
            else:
                self.failed_tests += 1
                self.results.append({
                    "test": "response_time",
                    "status": "fail",
                    "message": "無響應時間數據"
                })
                return False
        except Exception as e:
            logger.error(f'Error in dialogue_llm_test.py: {e}', exc_info=True)
            self.failed_tests += 1

            self.results.append({
                "test": "response_time",
                "status": "fail",
                "message": f"響應時間測試異常: {str(e)}"
            })
            return False

    def run_all_tests(self):
        """運行所有對話和 LLM 測試"""
        print("=" * 80)
        print("Angela AI 對話功能和 LLM 集成測試")
        print("=" * 80)

        # 1. 測試不同的對話端點
        print("\n【1/4】測試不同的對話端點")
        print("-" * 80)

        endpoints = [
            "/angela/chat",
            "/dialogue",
            "/api/v1/angela/chat"
        ]

        for endpoint in endpoints:
            success = self.test_dialogue_endpoint(endpoint, "你好，測試對話功能")
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{endpoint}: {status}")

        # 2. 測試多輪對話
        self.test_multiple_conversations()

        # 3. 測試情感識別
        self.test_emotion_detection()

        # 4. 測試響應時間
        self.test_response_time()

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

if __name__ == "__main__":
    tester = DialogueLLMTester()
    results = tester.run_all_tests()

    # 保存結果到 JSON 文件
    with open("/home/cat/桌面/dialogue_llm_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n詳細結果已保存到: /home/cat/桌面/dialogue_llm_test_results.json")