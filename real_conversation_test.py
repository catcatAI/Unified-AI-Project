#!/usr/bin/env python3
"""
真實對話測試工具
實際測試AI系統的對話能力，驗證實際完成度
"""

import asyncio
import requests
import json
import time
from typing import List, Dict, Any

class RealConversationTester:
    """真實對話測試器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = f"test_session_{int(time.time())}"
        self.conversation_history = []
        
    def test_conversation(self) -> Dict[str, Any]:
        """測試完整對話流程"""
        print("🎯 開始真實對話測試...")
        print("=" * 60)
        
        # 定義測試對話序列
        test_conversations = [
            {
                "topic": "基礎問候",
                "messages": [
                    "你好，請問你是誰？",
                    "你今天感覺如何？",
                    "謝謝你的回答"
                ],
                "expected_topics": ["自我介紹", "情感表達", "禮貌回應"]
            },
            {
                "topic": "知識問答",
                "messages": [
                    "什麼是人工智能？",
                    "AI有什麼應用？",
                    "AI的未來發展如何？"
                ],
                "expected_topics": ["定義解釋", "應用列舉", "未來預測"]
            },
            {
                "topic": "個人對話",
                "messages": [
                    "我最近感到有些壓力",
                    "你有什麼建議嗎？",
                    "謝謝你的安慰"
                ],
                "expected_topics": ["情感理解", "建議提供", "支持回應"]
            },
            {
                "topic": "複雜推理",
                "messages": [
                    "如果明天下雨，我應該帶傘嗎？",
                    "為什麼帶傘是明智的選擇？",
                    "除了帶傘還有什麼選擇？"
                ],
                "expected_topics": ["邏輯推理", "原因解釋", "替代方案"]
            },
            {
                "topic": "記憶測試",
                "messages": [
                    "我叫王小明，我喜歡編程",
                    "還記得我叫什麼名字嗎？",
                    "我說過我喜歡什麼？"
                ],
                "expected_topics": ["信息記憶", "記憶回憶", "記憶確認"]
            },
            {
                "topic": "系統功能",
                "messages": [
                    "你能幫我做什麼？",
                    "你可以啟動其他代理嗎？",
                    "你的桌面寵物叫什麼名字？"
                ],
                "expected_topics": ["功能介紹", "代理管理", "寵物互動"]
            }
        ]
        
        results = {
            "total_tests": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "response_times": [],
            "conversation_results": [],
            "issues_found": [],
            "overall_assessment": ""
        }
        
        for topic_test in test_conversations:
            print(f"\n🔍 測試主題: {topic_test['topic']}")
            print("-" * 40)
            
            topic_result = self.test_topic(topic_test)
            results["conversation_results"].append(topic_result)
            results["total_tests"] += topic_result["message_count"]
            results["successful_responses"] += topic_result["successful_count"]
            results["failed_responses"] += topic_result["failed_count"]
            results["response_times"].extend(topic_result["response_times"])
            
            if topic_result["issues"]:
                results["issues_found"].extend(topic_result["issues"])
        
        # 評估總體結果
        results["overall_assessment"] = self.assess_overall_performance(results)
        
        return results
    
    def test_topic(self, topic_test: Dict[str, Any]) -> Dict[str, Any]:
        """測試特定主題的對話"""
        topic = topic_test["topic"]
        messages = topic_test["messages"]
        expected_topics = topic_test["expected_topics"]
        
        result = {
            "topic": topic,
            "message_count": len(messages),
            "successful_count": 0,
            "failed_count": 0,
            "response_times": [],
            "responses": [],
            "issues": []
        }
        
        for i, message in enumerate(messages):
            print(f"\n👤 用戶 ({i+1}/{len(messages)}): {message}")
            
            try:
                start_time = time.time()
                
                # 發送請求到API
                response = requests.post(
                    f"{self.base_url}/api/v1/chat/mscu",
                    json={
                        "message": message,
                        "user_id": f"conversation_test_{int(time.time())}"
                    },
                    timeout=30
                )
                
                response_time = time.time() - start_time
                result["response_times"].append(response_time)
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get("response", "")
                    confidence = data.get("confidence", 0)
                    reasoning = data.get("reasoning", "")
                    
                    print(f"🤖 AI ({response_time:.1f}s): {ai_response}")
                    print(f"   置信度: {confidence:.2f}")
                    
                    # 評估響應質量
                    response_quality = self.evaluate_response(
                        message, ai_response, expected_topics[min(i, len(expected_topics)-1)]
                    )
                    
                    result["responses"].append({
                        "user_message": message,
                        "ai_response": ai_response,
                        "confidence": confidence,
                        "reasoning": reasoning,
                        "response_time": response_time,
                        "quality": response_quality
                    })
                    
                    if response_quality["is_acceptable"]:
                        result["successful_count"] += 1
                        print(f"   ✅ {response_quality['assessment']}")
                    else:
                        result["failed_count"] += 1
                        result["issues"].append(f"主題{topic}-消息{i}: {response_quality['issues']}")
                        print(f"   ❌ {response_quality['issues']}")
                    
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    print(f"   ❌ 錯誤: {error_msg}")
                    result["failed_count"] += 1
                    result["issues"].append(f"主題{topic}-消息{i}: API錯誤 - {error_msg}")
                
            except requests.exceptions.Timeout:
                print(f"   ❌ 錯誤: 請求超時 (30秒)")
                result["failed_count"] += 1
                result["issues"].append(f"主題{topic}-消息{i}: 請求超時")
                
            except Exception as e:
                print(f"   ❌ 錯誤: {str(e)}")
                result["failed_count"] += 1
                result["issues"].append(f"主題{topic}-消息{i}: {str(e)}")
            
            time.sleep(1)  # 短暫延遲
        
        # 計算主題成功率
        if result["message_count"] > 0:
            result["success_rate"] = result["successful_count"] / result["message_count"] * 100
        else:
            result["success_rate"] = 0
            
        return result
    
    def evaluate_response(self, user_message: str, ai_response: str, expected_topic: str) -> Dict[str, Any]:
        """評估AI響應質量"""
        evaluation = {
            "is_acceptable": False,
            "assessment": "",
            "issues": [],
            "strengths": []
        }
        
        response_lower = ai_response.lower()
        user_lower = user_message.lower()
        
        # 基本響應檢查
        if len(ai_response.strip()) < 5:
            evaluation["issues"].append("響應過短")
        elif len(ai_response.strip()) > 500:
            evaluation["strengths"].append("響應詳細")
        else:
            evaluation["strengths"].append("響應長度適中")
        
        # 相關性檢查
        relevance_indicators = {
            "基礎問候": ["你好", "我是", "幫助", "助手"],
            "知識問答": ["定義", "應用", "發展", "技術", "人工智慧"],
            "個人對話": ["理解", "建議", "壓力", "支持", "安慰"],
            "複雜推理": ["邏輯", "原因", "選擇", "建議", "考慮"],
            "記憶測試": ["記得", "名字", "喜歡", "王小明", "編程"],
            "功能介紹": ["功能", "代理", "寵物", "幫助", "能力"]
        }
        
        if expected_topic in relevance_indicators:
            topic_keywords = relevance_indicators[expected_topic]
            keyword_matches = sum(1 for keyword in topic_keywords if keyword in response_lower)
            
            if keyword_matches >= 1:
                evaluation["strengths"].append("回應相關")
            else:
                evaluation["issues"].append("回應可能不夠相關")
        
        # 邏輯一致性檢查
        if "但是" in ai_response and "然而" not in ai_response:
            evaluation["strengths"].append("邏輯連接詞使用適當")
        
        # 情感適當性檢查
        if any(word in user_lower for word in ["壓力", "難過", "擔心"]):
            if any(word in response_lower for word in ["理解", "同情", "建議", "支持"]):
                evaluation["strengths"].append("情感回應適當")
            else:
                evaluation["issues"].append("缺乏情感回應")
        
        # 重複內容檢查
        if "對不起" in response_lower and "無法" in response_lower:
            evaluation["issues"].append("系統表示無法處理")
        
        # 記憶回憶檢查
        if "記得" in user_lower or "還記得" in user_lower:
            if any(name in ai_response for name in ["王小明", "小明"]):
                evaluation["strengths"].append("成功回憶用戶信息")
            else:
                evaluation["issues"].append("未能回憶用戶信息")
        
        # 綜合評估
        if len(evaluation["issues"]) == 0:
            evaluation["is_acceptable"] = True
            evaluation["assessment"] = "優秀響應"
        elif len(evaluation["issues"]) <= 1:
            evaluation["is_acceptable"] = True
            evaluation["assessment"] = "可接受響應"
        else:
            evaluation["assessment"] = "需要改進"
        
        return evaluation
    
    def assess_overall_performance(self, results: Dict[str, Any]) -> str:
        """評估總體性能"""
        success_rate = results["successful_responses"] / results["total_tests"] * 100 if results["total_tests"] > 0 else 0
        avg_response_time = sum(results["response_times"]) / len(results["response_times"]) if results["response_times"] else 0
        
        if success_rate >= 80 and avg_response_time < 15:
            return f"系統表現優秀 (成功率: {success_rate:.1f}%, 平均響應時間: {avg_response_time:.1f}s)"
        elif success_rate >= 60 and avg_response_time < 20:
            return f"系統表現良好 (成功率: {success_rate:.1f}%, 平均響應時間: {avg_response_time:.1f}s)"
        elif success_rate >= 40:
            return f"系統基本可用 (成功率: {success_rate:.1f}%, 平均響應時間: {avg_response_time:.1f}s)"
        else:
            return f"系統需要重大改進 (成功率: {success_rate:.1f}%, 平均響應時間: {avg_response_time:.1f}s)"

def print_detailed_report(results: Dict[str, Any]):
    """打印詳細報告"""
    print("\n" + "=" * 80)
    print("🎯 真實對話測試詳細報告")
    print("=" * 80)
    
    print(f"📊 總體統計:")
    print(f"   總消息數: {results['total_tests']}")
    print(f"   成功響應: {results['successful_responses']}")
    print(f"   失敗響應: {results['failed_responses']}")
    print(f"   成功率: {results['successful_responses']/results['total_tests']*100:.1f}%")
    
    if results['response_times']:
        avg_time = sum(results['response_times']) / len(results['response_times'])
        min_time = min(results['response_times'])
        max_time = max(results['response_times'])
        print(f"   平均響應時間: {avg_time:.1f}s")
        print(f"   最快響應: {min_time:.1f}s")
        print(f"   最慢響應: {max_time:.1f}s")
    
    print(f"\n📋 各主題詳情:")
    for topic_result in results['conversation_results']:
        topic = topic_result['topic']
        success_rate = topic_result['success_rate']
        print(f"   {topic}:")
        print(f"     成功率: {success_rate:.1f}% ({topic_result['successful_count']}/{topic_result['message_count']})")
        
        if topic_result['issues']:
            print(f"     問題: {', '.join(topic_result['issues'][:2])}")
            if len(topic_result['issues']) > 2:
                print(f"       ... 還有 {len(topic_result['issues'])-2} 個問題")
    
    if results['issues_found']:
        print(f"\n⚠️ 發現的問題:")
        for issue in results['issues_found'][:10]:  # 顯示前10個問題
            print(f"   - {issue}")
        if len(results['issues_found']) > 10:
            print(f"   ... 還有 {len(results['issues_found'])-10} 個問題")
    
    print(f"\n🎯 總體評估: {results['overall_assessment']}")
    
    print("\n" + "=" * 80)

def main():
    """主函數"""
    print("🤖 啟動真實對話測試...")
    print("這將測試AI系統的實際對話能力，驗證真正的完成度")
    
    tester = RealConversationTester()
    
    try:
        results = tester.test_conversation()
        print_detailed_report(results)
        
        # 保存測試結果
        import json
        with open("REAL_CONVERSATION_TEST_REPORT.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 詳細報告已保存到: REAL_CONVERSATION_TEST_REPORT.json")
        
    except KeyboardInterrupt:
        print("\n⏹️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()