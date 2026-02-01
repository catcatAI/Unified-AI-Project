#!/usr/bin/env python3
"""
完全修復的對話測試工具
直接調用LLM API，繞過所有複雜性
"""

import asyncio
import requests
import json
import time
from typing import Dict, Any, List

class SimpleLLMTester:
    """簡單的LLM測試器"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.conversation_history = []
        
    def test_llm_conversation(self) -> Dict[str, Any]:
        """測試LLM對話"""
        print("🚀 開始直接LLM對話測試...")
        print("="*60)
        
        test_conversations = [
            {
                "topic": "基礎問候",
                "messages": [
                    "你好，請問你是誰？",
                    "你今天感覺如何？",
                    "謝謝你的回答"
                ]
            },
            {
                "topic": "知識問答",
                "messages": [
                    "什麼是人工智能？",
                    "AI有什麼應用？",
                    "AI的未來發展如何？"
                ]
            },
            {
                "topic": "個人對話",
                "messages": [
                    "我最近感到有些壓力",
                    "你有什麼建議嗎？",
                    "謝謝你的安慰"
                ]
            },
            {
                "topic": "記憶測試",
                "messages": [
                    "我叫王小明，我喜歡編程",
                    "還記得我叫什麼名字嗎？",
                    "我說過我喜歡什麼？"
                ]
            },
            {
                "topic": "複雜推理",
                "messages": [
                    "如果明天下雨，我應該帶傘嗎？",
                    "為什麼帶傘是明智的選擇？",
                    "除了帶傘還有什麼選擇？"
                ]
            }
        ]
        
        results = {
            "total_messages": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "response_times": [],
            "conversation_results": [],
            "issues": []
        }
        
        for topic_test in test_conversations:
            print(f"\n🔍 測試主題: {topic_test['topic']}")
            print("-"*40)
            
            topic_result = self.test_topic_simple(topic_test)
            results["conversation_results"].append(topic_result)
            results["total_messages"] += topic_result["message_count"]
            results["successful_responses"] += topic_result["successful_count"]
            results["failed_responses"] += topic_result["failed_count"]
            results["response_times"].extend(topic_result["response_times"])
            
            if topic_result["issues"]:
                results["issues"].extend(topic_result["issues"])
        
        self.generate_report(results)
        return results
    
    def test_topic_simple(self, topic_test):
        """測試特定主題（簡化版本）"""
        topic = topic_test["topic"]
        messages = topic_test["messages"]
        
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
                
                # 直接調用Ollama API
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": "tinyllama:latest",
                        "prompt": f"User: {message}\\nAssistant: ",
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 80,
                            "top_k": 20,
                            "top_p": 0.9,
                            "repeat_penalty": 1.1
                        }
                    },
                    timeout=20
                )
                
                response_time = time.time() - start_time
                result["response_times"].append(response_time)
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get("response", "").strip()
                    
                    print(f"🤖 AI ({response_time:.1f}s): {ai_response}")
                    
                    # 評估響應質量
                    response_quality = self.evaluate_simple_response(message, ai_response, topic)
                    
                    result["responses"].append({
                        "user_message": message,
                        "ai_response": ai_response,
                        "response_time": response_time,
                        "quality": response_quality
                    })
                    
                    if response_quality["is_acceptable"]:
                        result["successful_count"] += 1
                        print(f"   ✅ {response_quality['assessment']}")
                    else:
                        result["failed_count"] += 1
                        result["issues"].append(f"{topic}-消息{i}: {response_quality['issues']}")
                        print(f"   ❌ {response_quality['issues']}")
                    
                else:
                    print(f"   ❌ HTTP錯誤: {response.status_code}")
                    result["failed_count"] += 1
                    result["issues"].append(f"{topic}-消息{i}: HTTP {response.status_code}")
                
            except requests.exceptions.Timeout:
                print(f"   ❌ 請求超時 (20秒)")
                result["failed_count"] += 1
                result["issues"].append(f"{topic}-消息{i}: 請求超時")
                
            except Exception as e:
                print(f"   ❌ 錯誤: {str(e)}")
                result["failed_count"] += 1
                result["issues"].append(f"{topic}-消息{i}: {str(e)}")
            
            time.sleep(1)  # 短暫延遲
        
        return result
    
    def evaluate_simple_response(self, user_message, ai_response, topic):
        """評估簡單響應質量"""
        evaluation = {
            "is_acceptable": False,
            "assessment": "",
            "issues": [],
            "strengths": []
        }
        
        # 基本檢查
        if len(ai_response.strip()) < 3:
            evaluation["issues"].append("響應過短")
        elif len(ai_response.strip()) > 200:
            evaluation["strengths"].append("響應詳細")
        else:
            evaluation["strengths"].append("響應長度適中")
        
        # 相關性檢查
        user_lower = user_message.lower()
        response_lower = ai_response.lower()
        
        # 根據主題檢查關鍵詞
        topic_keywords = {
            "基礎問候": ["ai", "assistant", "幫助", "hello", "你好"],
            "知識問答": ["人工智能", "ai", "定義", "應用", "發展", "技術"],
            "個人對話": ["壓力", "建議", "休息", "運動", "理解", "支持"],
            "記憶測試": ["記得", "名字", "王小明", "編程", "喜歡"],
            "複雜推理": ["下雨", "傘", "明智", "原因", "選擇", "考慮"]
        }
        
        if topic in topic_keywords:
            keywords = topic_keywords[topic]
            keyword_matches = sum(1 for kw in keywords if kw in response_lower)
            
            if keyword_matches >= 1:
                evaluation["strengths"].append("回應相關")
            else:
                evaluation["issues"].append("回應可能不夠相關")
        
        # 記憶測試特殊檢查
        if "記得" in user_lower or "還記得" in user_lower:
            if any(name in response_lower for name in ["王小明", "小明"]):
                evaluation["strengths"].append("成功回憶用戶姓名")
            else:
                evaluation["issues"].append("未能回憶用戶姓名")
        
        # 語誤檢查
        error_indicators = ["error", "錯誤", "失敗", "無法", "對不起"]
        if any(indicator in response_lower for indicator in error_indicators):
            evaluation["issues"].append("響應包含錯誤指示詞")
        
        # 綜合評估
        if len(evaluation["issues"]) == 0:
            evaluation["is_acceptable"] = True
            evaluation["assessment"] = "優秀響應"
        elif len(evaluation["issues"]) <= 1:
            evaluation["is_acceptable"] = True
            evaluation["assessment"] = "良好響應"
        elif len(evaluation["issues"]) <= 2:
            evaluation["is_acceptable"] = True
            evaluation["assessment"] = "可接受響應"
        else:
            evaluation["assessment"] = "需要改進"
        
        return evaluation
    
    def generate_report(self, results):
        """生成測試報告"""
        print("\n" + "="*80)
        print("🎯 直接LLM對話測試報告")
        print("="*80)
        
        success_rate = results["successful_responses"] / results["total_messages"] * 100 if results["total_messages"] > 0 else 0
        
        print(f"📊 總體統計:")
        print(f"   總消息數: {results['total_messages']}")
        print(f"   成功響應: {results['successful_responses']}")
        print(f"   失敗響應: {results['failed_responses']}")
        print(f"   成功率: {success_rate:.1f}%")
        
        if results["response_times"]:
            avg_time = sum(results["response_times"]) / len(results["response_times"])
            min_time = min(results["response_times"])
            max_time = max(results["response_times"])
            print(f"   平均響應時間: {avg_time:.1f}s")
            print(f"   最快響應: {min_time:.1f}s")
            print(f"   最慢響應: {max_time:.1f}s")
        
        print(f"\n📋 各主題詳情:")
        for topic_result in results["conversation_results"]:
            topic = topic_result["topic"]
            success_rate = topic_result["successful_count"] / topic_result["message_count"] * 100
            print(f"   {topic}:")
            print(f"     成功率: {success_rate:.1f}% ({topic_result['successful_count']}/{topic_result['message_count']})")
            
            if topic_result["issues"]:
                print(f"     問題: {', '.join(topic_result['issues'][:2])}")
        
        if results["issues"]:
            print(f"\n⚠️ 發現的問題:")
            for issue in results["issues"][:5]:
                print(f"   - {issue}")
        
        # 總體評估
        if success_rate >= 80:
            overall = "🎉 LLM系統表現優秀"
        elif success_rate >= 60:
            overall = "✅ LLM系統表現良好"
        elif success_rate >= 40:
            overall = "⚠️ LLM系統基本可用"
        else:
            overall = "❌ LLM系統需要重大改進"
        
        print(f"\n🎯 總體評估: {overall}")
        print(f"   實際LLM功能完成度: {success_rate:.1f}%")
        
        print("="*80)
        
        # 保存報告
        report_data = {
            "test_type": "direct_llm_test",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": results,
            "overall_assessment": overall,
            "real_completion_rate": success_rate
        }
        
        with open("DIRECT_LLM_TEST_REPORT.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 詳細報告已保存到: DIRECT_LLM_TEST_REPORT.json")

def main():
    """主函數"""
    print("🤖 啟動直接LLM對話測試...")
    print("這將直接測試Ollama LLM的對話能力")
    
    tester = SimpleLLMTester()
    
    try:
        results = tester.test_llm_conversation()
    except KeyboardInterrupt:
        print("\n⏹️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()