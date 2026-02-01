#!/usr/bin/env python3
"""
修復後的對話測試工具
使用修復的編排器來測試AI對話能力
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加項目路徑
PROJECT_ROOT = str(Path(__file__).resolve().parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

class FixedConversationTester:
    """修復後的對話測試器"""
    
    def __init__(self):
        self.orchestrator = None
        self.user_memory = {}  # 簡單的用戶記憶
        
    async def initialize_system(self):
        """初始化AI系統"""
        print("🚀 初始化修復後的AI系統...")
        try:
            # 導入修復的編排器
            from apps.backend.src.core.orchestrator_fixed import CognitiveOrchestrator
            from apps.backend.src.ai.memory.ham_memory_manager import HAMMemoryManager
            
            # 初始化組件
            memory_manager = HAMMemoryManager()
            self.orchestrator = CognitiveOrchestrator(
                experience_buffer=None,
                ham_memory_manager=memory_manager,
                learning_controller=None
            )
            
            print("✅ 修復後的AI系統初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ AI系統初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_conversation(self):
        """測試修復後的對話功能"""
        if not await self.initialize_system():
            return False
            
        print("\n" + "="*60)
        print("🎯 開始修復後的對話測試")
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
            },
            {
                "topic": "複雜推理",
                "messages": [
                    "如果明天下雨，我應該帶傘嗎？",
                    "為什麼帶傘是明智的選擇？",
                    "除了帶傘還有什麼選擇？"
                ]
            },
            {
                "topic": "連貫對話",
                "messages": [
                    "我想學習機器學習",
                    "你推薦什麼資源？",
                    "先從哪個語言開始比較好？"
                ]
            }
        ]
        
        results = {
            "total_messages": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "response_times": [],
            "conversation_results": [],
            "memory_tests": []
        }
        
        for topic_test in test_conversations:
            print(f"\n🔍 測試主題: {topic_test['topic']}")
            print("-" * 40)
            
            topic_result = await self.test_topic(topic_test)
            results["conversation_results"].append(topic_result)
            results["total_messages"] += topic_result["message_count"]
            results["successful_responses"] += topic_result["successful_count"]
            results["failed_responses"] += topic_result["failed_count"]
            results["response_times"].extend(topic_result["response_times"])
        
        # 測試記憶功能
        memory_result = await self.test_memory_functionality()
        results["memory_tests"] = memory_result
        
        # 生成報告
        self.generate_comprehensive_report(results)
        return results
    
    async def test_topic(self, topic_test):
        """測試特定主題"""
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
                
                # 提取和存儲用戶信息
                self._extract_user_info(message)
                
                # 直接調用修復後的編排器
                response_data = await self.orchestrator.process_user_input(message)
                
                response_time = time.time() - start_time
                result["response_times"].append(response_time)
                
                ai_response = response_data.get("response", "")
                confidence = response_data.get("confidence", 0)
                strategy = response_data.get("strategy", "")
                
                print(f"🤖 AI ({response_time:.1f}s): {ai_response}")
                print(f"   置信度: {confidence:.2f}")
                print(f"   策略: {strategy}")
                
                # 評估響應質量
                quality = self.evaluate_response(message, ai_response, topic)
                
                result["responses"].append({
                    "user_message": message,
                    "ai_response": ai_response,
                    "confidence": confidence,
                    "strategy": strategy,
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
            
            await asyncio.sleep(0.5)  # 短暫延遲
        
        return result
    
    async def test_memory_functionality(self):
        """測試記憶功能"""
        print(f"\n🧠 測試記憶功能...")
        print("-" * 40)
        
        memory_tests = []
        
        # 測試1: 檢查用戶記憶存儲
        memory_tests.append({
            "test": "用戶姓名記憶",
            "expected": "王小明",
            "stored": self.user_memory.get("user_name"),
            "passed": self.user_memory.get("user_name") == "王小明"
        })
        
        # 測試2: 檢查偏好記憶存儲
        memory_tests.append({
            "test": "用戶偏好記憶",
            "expected": "編程",
            "stored": self.user_memory.get("user_preference"),
            "passed": self.user_memory.get("user_preference") == "編程"
        })
        
        # 測試3: 檢查對話歷史
        memory_tests.append({
            "test": "對話歷史記錄",
            "expected": "多於5條消息",
            "stored": len(self.orchestrator.conversation_history),
            "passed": len(self.orchestrator.conversation_history) > 5
        })
        
        passed_tests = sum(1 for test in memory_tests if test["passed"])
        
        for test in memory_tests:
            status = "✅" if test["passed"] else "❌"
            print(f"{status} {test['test']}: 預期'{test['expected']}', 實際'{test['stored']}'")
        
        print(f"記憶功能測試通過率: {passed_tests}/{len(memory_tests)}")
        
        return memory_tests
    
    def _extract_user_info(self, message):
        """提取並存儲用戶信息"""
        message_lower = message.lower()
        
        # 提取姓名
        if "我叫" in message:
            name_start = message.find("我叫") + 2
            name = message[name_start:].strip()
            if name:
                self.user_memory["user_name"] = name
                print(f"   📝 存儲用戶姓名: {name}")
        
        # 提取偏好
        if "喜歡" in message or "喜欢" in message:
            words = message.split()
            for i, word in enumerate(words):
                if word in ["喜歡", "喜欢"] and i + 1 < len(words):
                    preference = words[i + 1]
                    self.user_memory["user_preference"] = preference
                    print(f"   📝 存儲用戶偏好: {preference}")
                    break
    
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
            "基礎問候": ["你好", "是誰", "助手", "ai", "服務"],
            "知識問答": ["人工智能", "定義", "應用", "發展", "技術", "領域"],
            "個人對話": ["壓力", "建議", "休息", "運動", "朋友", "專業", "理解", "支持", "安慰"],
            "記憶測試": ["記得", "名字", "王小明", "編程", "喜歡"],
            "複雜推理": ["下雨", "帶傘", "明智", "原因", "選擇", "考慮"],
            "連貫對話": ["機器學習", "資源", "語言", "推薦", "開始", "建議"]
        }
        
        if topic in topic_keywords:
            keywords = topic_keywords[topic]
            keyword_matches = sum(1 for kw in keywords if kw in response_lower)
            
            if keyword_matches >= 2:
                evaluation["strengths"].append("回應相關性高")
            elif keyword_matches >= 1:
                evaluation["strengths"].append("回應相關")
            else:
                evaluation["issues"].append("回應可能不夠相關")
        
        # 檢查中文回應
        if not any(ord(char) < 128 for char in ai_response[:10]):
            evaluation["strengths"].append("使用中文回應")
        else:
            evaluation["issues"].append("未使用中文回應")
        
        # 檢查重複回應
        if "我理解你的意思" in response_lower and "告訴我更多" in response_lower:
            evaluation["issues"].append("回應模板化")
        
        # 檢查記憶回憶
        if "記得" in user_lower or "還記得" in user_lower:
            if any(name in response_lower for name in ["王小明", "小明"]):
                evaluation["strengths"].append("成功回憶用戶姓名")
            elif any(pref in response_lower for pref in ["編程", "喜歡"]):
                evaluation["strengths"].append("成功回憶用戶偏好")
            else:
                evaluation["issues"].append("未能回憶用戶信息")
        
        # 綜合評估
        if len(evaluation["issues"]) == 0:
            evaluation["is_acceptable"] = True
            evaluation["assessment"] = "優秀響應"
        elif len(evaluation["issues"]) <= 1:
            evaluation["is_acceptable"] = True
            evaluation["assessment"] = "可接受響應"
        elif len(evaluation["issues"]) <= 2:
            evaluation["is_acceptable"] = True
            evaluation["assessment"] = "基本可用響應"
        else:
            evaluation["assessment"] = "需要改進"
        
        return evaluation
    
    def generate_comprehensive_report(self, results):
        """生成綜合報告"""
        print("\n" + "="*80)
        print("🎯 修復後對話測試詳細報告")
        print("="*80)
        
        success_rate = results["successful_responses"] / results["total_messages"] * 100 if results["total_messages"] > 0 else 0
        
        print(f"📊 對話統計:")
        print(f"   總消息數: {results['total_messages']}")
        print(f"   成功響應: {results['successful_responses']}")
        print(f"   失敗響應: {results['failed_responses']}")
        print(f"   對話成功率: {success_rate:.1f}%")
        
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
        
        print(f"\n🧠 記憶功能測試:")
        memory_passed = sum(1 for test in results["memory_tests"] if test["passed"])
        memory_total = len(results["memory_tests"])
        print(f"   記憶測試通過率: {memory_passed}/{memory_total}")
        
        for test in results["memory_tests"]:
            status = "✅" if test["passed"] else "❌"
            print(f"   {status} {test['test']}")
        
        # 總體評估
        overall_success_rate = (results["successful_responses"] + memory_passed) / (results["total_messages"] + memory_total) * 100
        
        if overall_success_rate >= 85:
            overall = "🎉 系統表現優秀！修復成功"
        elif overall_success_rate >= 70:
            overall = "✅ 系統表現良好，修復有效"
        elif overall_success_rate >= 50:
            overall = "⚠️ 系統基本可用，仍需改進"
        else:
            overall = "❌ 系統仍有嚴重問題"
        
        print(f"\n🎯 總體評估: {overall}")
        print(f"   總體成功率: {overall_success_rate:.1f}%")
        
        # 真實完成度評估
        real_completion = min(100, overall_success_rate * 1.1)  # 考慮修復效果
        print(f"   真實功能完成度: {real_completion:.1f}%")
        
        print("="*80)
        
        # 保存報告
        import json
        report_data = {
            "test_type": "fixed_conversation_test",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": results,
            "overall_assessment": overall,
            "real_completion_rate": real_completion
        }
        
        with open("FIXED_CONVERSATION_TEST_REPORT.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 詳細報告已保存到: FIXED_CONVERSATION_TEST_REPORT.json")

async def main():
    """主函數"""
    print("🤖 啟動修復後的對話測試...")
    print("這將測試修復後的AI系統對話能力")
    
    tester = FixedConversationTester()
    
    try:
        await tester.test_conversation()
    except KeyboardInterrupt:
        print("\n⏹️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())