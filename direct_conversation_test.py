#!/usr/bin/env python3
"""
直接對話測試工具
通過直接調用系統組件來測試AI對話能力
繞過API服務器問題，直接測試核心功能
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加項目路徑
PROJECT_ROOT = str(Path(__file__).resolve().parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

class DirectConversationTester:
    """直接對話測試器"""
    
    def __init__(self):
        self.orchestrator = None
        self.memory_manager = None
        
    async def initialize_system(self):
        """初始化AI系統"""
        print("🚀 初始化AI系統...")
        try:
            # 直接初始化組件
            from apps.backend.src.ai.memory.ham_memory_manager import HAMMemoryManager
            from apps.backend.src.core.orchestrator import CognitiveOrchestrator
            
            self.memory_manager = HAMMemoryManager()
            self.orchestrator = CognitiveOrchestrator(
                experience_buffer=None,
                ham_memory_manager=self.memory_manager,
                learning_controller=None
            )
            
            print("✅ AI系統初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ AI系統初始化失敗: {e}")
            return False
    
    async def test_direct_conversation(self):
        """測試直接對話功能"""
        if not await self.initialize_system():
            return False
            
        print("\n" + "="*60)
        print("🎯 開始直接對話測試")
        print("="*60)
        
        # 測試對話序列
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
            }
        ]
        
        results = {
            "total_messages": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "response_times": [],
            "conversation_details": [],
            "issues": []
        }
        
        for topic_test in test_conversations:
            topic_result = await self.test_topic(topic_test)
            results["conversation_details"].append(topic_result)
            results["total_messages"] += topic_result["message_count"]
            results["successful_responses"] += topic_result["successful_count"]
            results["failed_responses"] += topic_result["failed_count"]
            results["response_times"].extend(topic_result["response_times"])
            
            if topic_result["issues"]:
                results["issues"].extend(topic_result["issues"])
        
        # 生成報告
        self.generate_report(results)
        return results
    
    async def test_topic(self, topic_test):
        """測試特定主題"""
        topic = topic_test["topic"]
        messages = topic_test["messages"]
        
        print(f"\n🔍 測試主題: {topic}")
        print("-" * 40)
        
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
                
                # 直接調用編排器處理消息
                response_data = await self.orchestrator.process_user_input(message)
                
                response_time = time.time() - start_time
                result["response_times"].append(response_time)
                
                ai_response = response_data.get("response", "")
                confidence = response_data.get("confidence", 0)
                reasoning = response_data.get("reasoning", "")
                
                print(f"🤖 AI ({response_time:.1f}s): {ai_response}")
                print(f"   置信度: {confidence:.2f}")
                print(f"   推理: {reasoning}")
                
                # 評估響應質量
                quality = self.evaluate_response(message, ai_response, topic)
                
                result["responses"].append({
                    "user_message": message,
                    "ai_response": ai_response,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "response_time": response_time,
                    "quality": quality
                })
                
                if quality["is_acceptable"]:
                    result["successful_count"] += 1
                    print(f"   ✅ {quality['assessment']}")
                else:
                    result["failed_count"] += 1
                    result["issues"].append(f"{topic}-消息{i}: {quality['issues']}")
                    print(f"   ❌ {quality['issues']}")
                
            except Exception as e:
                print(f"   ❌ 錯誤: {str(e)}")
                result["failed_count"] += 1
                result["issues"].append(f"{topic}-消息{i}: {str(e)}")
            
            await asyncio.sleep(1)  # 短暫延遲
        
        return result
    
    def evaluate_response(self, user_message, ai_response, topic):
        """評估AI響應質量"""
        evaluation = {
            "is_acceptable": False,
            "assessment": "",
            "issues": [],
            "strengths": []
        }
        
        # 基本檢查
        if len(ai_response.strip()) < 5:
            evaluation["issues"].append("響應過短")
        elif len(ai_response.strip()) > 500:
            evaluation["strengths"].append("響應詳細")
        else:
            evaluation["strengths"].append("響應長度適中")
        
        # 相關性檢查
        response_lower = ai_response.lower()
        user_lower = user_message.lower()
        
        # 根據主題檢查關鍵詞
        topic_keywords = {
            "基礎問候": ["你好", "我是", "助手", "幫助", "ai"],
            "知識問答": ["定義", "人工智能", "應用", "發展", "技術"],
            "個人對話": ["理解", "建議", "壓力", "支持", "安慰"],
            "記憶測試": ["記得", "名字", "王小明", "編程", "喜歡"]
        }
        
        if topic in topic_keywords:
            keywords = topic_keywords[topic]
            keyword_matches = sum(1 for kw in keywords if kw in response_lower)
            
            if keyword_matches >= 1:
                evaluation["strengths"].append("回應相關")
            else:
                evaluation["issues"].append("回應可能不夠相關")
        
        # 錯誤檢查
        error_indicators = ["錯誤", "失敗", "無法", "抱歉", "對不起"]
        if any(indicator in response_lower for indicator in error_indicators):
            if "無法" in response_lower:
                evaluation["issues"].append("系統表示無法處理")
            else:
                evaluation["issues"].append("響應包含錯誤指示詞")
        
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
    
    def generate_report(self, results):
        """生成測試報告"""
        print("\n" + "="*80)
        print("🎯 直接對話測試報告")
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
        for topic_result in results["conversation_details"]:
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
            overall = "系統表現優秀"
        elif success_rate >= 60:
            overall = "系統表現良好"
        elif success_rate >= 40:
            overall = "系統基本可用"
        else:
            overall = "系統需要重大改進"
        
        print(f"\n🎯 總體評估: {overall}")
        
        print("="*80)
        
        # 保存報告
        import json
        report_data = {
            "test_type": "direct_conversation",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": results,
            "overall_assessment": overall
        }
        
        with open("DIRECT_CONVERSATION_TEST_REPORT.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 詳細報告已保存到: DIRECT_CONVERSATION_TEST_REPORT.json")

async def main():
    """主函數"""
    print("🤖 啟動直接對話測試...")
    print("這將通過直接調用系統組件來測試AI的實際對話能力")
    
    tester = DirectConversationTester()
    
    try:
        await tester.test_direct_conversation()
    except KeyboardInterrupt:
        print("\n⏹️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(main())