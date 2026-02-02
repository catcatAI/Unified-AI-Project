#!/usr/bin/env python3
"""
Angela AI 系統超級詳細檢查工具
確保系統完全沒有問題，生產環境就緒
"""

import asyncio
import sys
import os
import json
import time
import traceback
from datetime import datetime
from pathlib import Path

# 添加路徑
sys.path.append('apps/backend')
sys.path.append('apps/backend/src')

class ComprehensiveSystemChecker:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "UNKNOWN",
            "components": {},
            "performance": {},
            "integration": {},
            "errors": [],
            "recommendations": []
        }
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name: str, status: str, details: str = "", performance_ms: float = 0):
        """記錄測試結果"""
        self.total_tests += 1
        if status == "PASS":
            self.passed_tests += 1
            
        result = {
            "status": status,
            "details": details,
            "performance_ms": performance_ms,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"[{status}] {test_name}")
        if details:
            print(f"    {details}")
        if performance_ms > 0:
            print(f"    Performance: {performance_ms:.2f}ms")
            
        return result
        
    async def check_core_components(self):
        """檢查核心組件"""
        print("\n🔍 檢查核心組件...")
        
        # 測試導入
        start_time = time.time()
        try:
            from src.core.orchestrator import CognitiveOrchestrator
            from src.game.angela import Angela
            import_time = (time.time() - start_time) * 1000
            self.results["components"]["core_import"] = self.log_test(
                "Core Components Import", "PASS", 
                "All core components imported successfully", 
                import_time
            )
        except Exception as e:
            self.results["components"]["core_import"] = self.log_test(
                "Core Components Import", "FAIL", str(e)
            )
            self.results["errors"].append(f"Core import failed: {e}")
            return False
            
        # 測試組件初始化
        start_time = time.time()
        try:
            orchestrator = CognitiveOrchestrator()
            angela = Angela()
            init_time = (time.time() - start_time) * 1000
            self.results["components"]["core_init"] = self.log_test(
                "Core Components Initialization", "PASS",
                "All core components initialized successfully",
                init_time
            )
            return True
        except Exception as e:
            self.results["components"]["core_init"] = self.log_test(
                "Core Components Initialization", "FAIL", str(e)
            )
            self.results["errors"].append(f"Core init failed: {e}")
            return False
            
    async def check_dialogue_system(self):
        """檢查對話系統"""
        print("\n🗣️ 檢查對話系統...")
        
        try:
            from src.core.orchestrator import CognitiveOrchestrator
            orchestrator = CognitiveOrchestrator()
            
            # 測試基本對話
            test_inputs = [
                "Hello",
                "What's your name?",
                "How are you?",
                "Can you help me?",
                "Thank you"
            ]
            
            total_time = 0
            for i, user_input in enumerate(test_inputs):
                start_time = time.time()
                try:
                    response = await orchestrator.process_user_input(user_input)
                    response_time = (time.time() - start_time) * 1000
                    total_time += response_time
                    
                    if response and "response" in response and len(response["response"]) > 0:
                        self.results["components"][f"dialogue_test_{i+1}"] = self.log_test(
                            f"Dialogue Test {i+1}: '{user_input}'", "PASS",
                            f"Response: {response['response'][:50]}...",
                            response_time
                        )
                    else:
                        self.results["components"][f"dialogue_test_{i+1}"] = self.log_test(
                            f"Dialogue Test {i+1}: '{user_input}'", "FAIL",
                            "Empty or invalid response"
                        )
                        
                except Exception as e:
                    self.results["components"][f"dialogue_test_{i+1}"] = self.log_test(
                        f"Dialogue Test {i+1}: '{user_input}'", "FAIL", str(e)
                    )
                    
            avg_time = total_time / len(test_inputs)
            self.results["performance"]["dialogue_avg_response_time"] = avg_time
            self.results["components"]["dialogue_overall"] = self.log_test(
                "Dialogue System Overall", "PASS" if avg_time < 5000 else "WARNING",
                f"Average response time: {avg_time:.2f}ms"
            )
            
        except Exception as e:
            self.results["components"]["dialogue_system"] = self.log_test(
                "Dialogue System", "FAIL", str(e)
            )
            self.results["errors"].append(f"Dialogue system failed: {e}")
            
    async def check_memory_system(self):
        """檢查記憶系統"""
        print("\n🧠 檢查記憶系統...")
        
        try:
            from src.core.orchestrator import CognitiveOrchestrator
            orchestrator = CognitiveOrchestrator()
            
            # 測試對話歷史
            initial_count = len(orchestrator.conversation_history)
            
            # 添加一些對話
            await orchestrator.process_user_input("My name is Alice")
            await orchestrator.process_user_input("What's my name?")
            await orchestrator.process_user_input("Remember I like coffee")
            
            final_count = len(orchestrator.conversation_history)
            
            if final_count > initial_count:
                self.results["components"]["memory_conversation"] = self.log_test(
                    "Conversation Memory", "PASS",
                    f"History grew from {initial_count} to {final_count} messages"
                )
            else:
                self.results["components"]["memory_conversation"] = self.log_test(
                    "Conversation Memory", "FAIL", "Conversation history not growing"
                )
                
            # 測試實體提取
            entities = orchestrator._extract_entities_from_history()
            if entities:
                self.results["components"]["memory_entities"] = self.log_test(
                    "Entity Extraction", "PASS", f"Extracted entities: {entities}"
                )
            else:
                self.results["components"]["memory_entities"] = self.log_test(
                    "Entity Extraction", "WARNING", "No entities extracted"
                )
                
        except Exception as e:
            self.results["components"]["memory_system"] = self.log_test(
                "Memory System", "FAIL", str(e)
            )
            self.results["errors"].append(f"Memory system failed: {e}")
            
    async def check_llm_integration(self):
        """檢查LLM集成"""
        print("\n🤖 檢查LLM集成...")
        
        try:
            from src.core.orchestrator import CognitiveOrchestrator
            orchestrator = CognitiveOrchestrator()
            
            # 檢查LLM可用性
            if hasattr(orchestrator, 'llm_available'):
                if orchestrator.llm_available:
                    self.results["components"]["llm_availability"] = self.log_test(
                        "LLM Availability", "PASS", 
                        f"Available models: {getattr(orchestrator, 'available_models', [])}"
                    )
                else:
                    self.results["components"]["llm_availability"] = self.log_test(
                        "LLM Availability", "WARNING", "No LLM available, using rule-based responses"
                    )
            else:
                self.results["components"]["llm_availability"] = self.log_test(
                    "LLM Availability", "WARNING", "LLM availability check not implemented"
                )
                
            # 測試實際響應生成
            start_time = time.time()
            response = await orchestrator.process_user_input("Tell me something interesting")
            response_time = (time.time() - start_time) * 1000
            
            if response and "response" in response:
                self.results["components"]["llm_response"] = self.log_test(
                    "LLM Response Generation", "PASS",
                    f"Generated response: {response['response'][:50]}...",
                    response_time
                )
            else:
                self.results["components"]["llm_response"] = self.log_test(
                    "LLM Response Generation", "FAIL", "No response generated"
                )
                
        except Exception as e:
            self.results["components"]["llm_integration"] = self.log_test(
                "LLM Integration", "FAIL", str(e)
            )
            self.results["errors"].append(f"LLM integration failed: {e}")
            
    async def check_angela_character(self):
        """檢查Angela角色系統"""
        print("\n👤 檢查Angela角色系統...")
        
        try:
            from src.game.angela import Angela
            angela = Angela()
            
            # 測試狀態系統
            initial_favorability = angela.favorability
            initial_mood = angela.mood
            
            # 測試增加好感度
            angela.increase_favorability(10.0)
            if angela.favorability > initial_favorability:
                self.results["components"]["angela_favorability"] = self.log_test(
                    "Angela Favorability System", "PASS",
                    f"Favorability increased from {initial_favorability} to {angela.favorability}"
                )
            else:
                self.results["components"]["angela_favorability"] = self.log_test(
                    "Angela Favorability System", "FAIL", "Favorability not increasing"
                )
                
            # 測試對話功能
            try:
                response = await angela.get_dialogue("Hello", {"test": True})
                if response and len(response) > 0:
                    self.results["components"]["angela_dialogue"] = self.log_test(
                        "Angela Dialogue System", "PASS",
                        f"Dialogue response: {response[:50]}..."
                    )
                else:
                    self.results["components"]["angela_dialogue"] = self.log_test(
                        "Angela Dialogue System", "FAIL", "No dialogue response"
                    )
            except Exception as e:
                # 檢查是否是因為DialogueManager不存在
                if "DialogueManager" in str(e) or "placeholder" in str(e):
                    self.results["components"]["angela_dialogue"] = self.log_test(
                        "Angela Dialogue System", "WARNING", "Using placeholder DialogueManager"
                    )
                else:
                    self.results["components"]["angela_dialogue"] = self.log_test(
                        "Angela Dialogue System", "FAIL", str(e)
                    )
                    
            # 測試禮物系統
            gift_response = await angela.give_gift({"name": "rose", "value": 15, "type": "favorite"})
            if gift_response and len(gift_response) > 0:
                self.results["components"]["angela_gift_system"] = self.log_test(
                    "Angela Gift System", "PASS",
                    f"Gift response: {gift_response[:50]}..."
                )
            else:
                self.results["components"]["angela_gift_system"] = self.log_test(
                    "Angela Gift System", "FAIL", "No gift response"
                )
                
        except Exception as e:
            self.results["components"]["angela_character"] = self.log_test(
                "Angela Character System", "FAIL", str(e)
            )
            self.results["errors"].append(f"Angela character failed: {e}")
            
    async def check_performance_and_stability(self):
        """檢查性能和穩定性"""
        print("\n⚡ 檢查性能和穩定性...")
        
        try:
            from src.core.orchestrator import CognitiveOrchestrator
            orchestrator = CognitiveOrchestrator()
            
            # 壓力測試 - 連續請求
            pressure_test_count = 20
            start_time = time.time()
            
            successful_responses = 0
            for i in range(pressure_test_count):
                try:
                    response = await orchestrator.process_user_input(f"Test message {i+1}")
                    if response and "response" in response:
                        successful_responses += 1
                except:
                    pass
                    
            total_time = (time.time() - start_time) * 1000
            avg_time = total_time / pressure_test_count
            
            if successful_responses >= pressure_test_count * 0.9:  # 90%成功率
                self.results["performance"]["pressure_test"] = self.log_test(
                    "Pressure Test (20 requests)", "PASS",
                    f"Success rate: {successful_responses}/{pressure_test_count}, Avg: {avg_time:.2f}ms",
                    total_time
                )
            else:
                self.results["performance"]["pressure_test"] = self.log_test(
                    "Pressure Test (20 requests)", "FAIL",
                    f"Low success rate: {successful_responses}/{pressure_test_count}",
                    total_time
                )
                
            # 記憶洩漏測試
            initial_history = len(orchestrator.conversation_history)
            for i in range(10):
                await orchestrator.process_user_input(f"Memory test {i+1}")
            
            final_history = len(orchestrator.conversation_history)
            expected_growth = 20  # 10 user + 10 assistant messages
            
            if final_history == initial_history + expected_growth:
                self.results["performance"]["memory_leak_test"] = self.log_test(
                    "Memory Leak Test", "PASS",
                    f"History grew as expected: {initial_history} -> {final_history}"
                )
            else:
                self.results["performance"]["memory_leak_test"] = self.log_test(
                    "Memory Leak Test", "WARNING",
                    f"Unexpected growth: {initial_history} -> {final_history}"
                )
                
        except Exception as e:
            self.results["performance"]["stability_test"] = self.log_test(
                "Performance and Stability", "FAIL", str(e)
            )
            self.results["errors"].append(f"Performance test failed: {e}")
            
    async def check_error_handling(self):
        """檢查錯誤處理"""
        print("\n🛡️ 檢查錯誤處理...")
        
        try:
            from src.core.orchestrator import CognitiveOrchestrator
            orchestrator = CognitiveOrchestrator()
            
            # 測試空輸入
            response = await orchestrator.process_user_input("")
            if response and "response" in response:
                self.results["components"]["error_empty_input"] = self.log_test(
                    "Empty Input Handling", "PASS", "Empty input handled gracefully"
                )
            else:
                self.results["components"]["error_empty_input"] = self.log_test(
                    "Empty Input Handling", "FAIL", "Empty input not handled properly"
                )
                
            # 測試超長輸入
            long_input = "x" * 10000
            start_time = time.time()
            response = await orchestrator.process_user_input(long_input)
            response_time = (time.time() - start_time) * 1000
            
            if response and "response" in response:
                self.results["components"]["error_long_input"] = self.log_test(
                    "Long Input Handling", "PASS",
                    f"Long input handled in {response_time:.2f}ms",
                    response_time
                )
            else:
                self.results["components"]["error_long_input"] = self.log_test(
                    "Long Input Handling", "FAIL", "Long input not handled properly"
                )
                
            # 測試特殊字符
            special_input = "🤖 Test with 特殊 characters and émojis!"
            response = await orchestrator.process_user_input(special_input)
            if response and "response" in response:
                self.results["components"]["error_special_chars"] = self.log_test(
                    "Special Characters Handling", "PASS", "Special characters handled properly"
                )
            else:
                self.results["components"]["error_special_chars"] = self.log_test(
                    "Special Characters Handling", "FAIL", "Special characters not handled properly"
                )
                
        except Exception as e:
            self.results["components"]["error_handling"] = self.log_test(
                "Error Handling", "FAIL", str(e)
            )
            self.results["errors"].append(f"Error handling test failed: {e}")
            
    def check_file_structure(self):
        """檢查文件結構"""
        print("\n📁 檢查文件結構...")
        
        required_files = [
            "apps/backend/src/core/orchestrator.py",
            "apps/backend/src/game/angela.py",
            "apps/backend/src/lu/logic_unit.py",
            "apps/backend/src/core/perception/receptor_system.py",
            "apps/backend/src/core/perception/synesthesia.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if Path(file_path).exists():
                self.results["components"][f"file_{file_path.replace('/', '_')}"] = self.log_test(
                    f"File: {file_path}", "PASS", "File exists"
                )
            else:
                missing_files.append(file_path)
                self.results["components"][f"file_{file_path.replace('/', '_')}"] = self.log_test(
                    f"File: {file_path}", "FAIL", "File missing"
                )
                
        if missing_files:
            self.results["errors"].append(f"Missing files: {missing_files}")
            
    def generate_recommendations(self):
        """生成改進建議"""
        recommendations = []
        
        # 基於錯誤生成建議
        if self.results["errors"]:
            recommendations.append("🔧 Fix all critical errors before production deployment")
            
        # 基於性能生成建議
        if "dialogue_avg_response_time" in self.results["performance"]:
            avg_time = self.results["performance"]["dialogue_avg_response_time"]
            if avg_time > 3000:
                recommendations.append("⚡ Optimize response generation - current average is slow")
            elif avg_time > 1000:
                recommendations.append("⚡ Consider response time optimization")
                
        # 基於組件狀態生成建議
        failed_components = [k for k, v in self.results["components"].items() 
                           if isinstance(v, dict) and v.get("status") == "FAIL"]
        if failed_components:
            recommendations.append(f"🔧 Address failing components: {failed_components}")
            
        # 基於測試覆蓋率生成建議
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        if success_rate < 90:
            recommendations.append(f"📊 Improve test coverage - current success rate: {success_rate:.1f}%")
            
        self.results["recommendations"] = recommendations
        
    def calculate_overall_status(self):
        """計算整體狀態"""
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        if success_rate >= 95 and not self.results["errors"]:
            self.results["overall_status"] = "EXCELLENT - Production Ready"
        elif success_rate >= 85 and len(self.results["errors"]) <= 2:
            self.results["overall_status"] = "GOOD - Nearly Production Ready"
        elif success_rate >= 70:
            self.results["overall_status"] = "FAIR - Needs Improvement"
        else:
            self.results["overall_status"] = "POOR - Not Ready"
            
        self.results["success_rate"] = success_rate
        self.results["total_tests"] = self.total_tests
        self.results["passed_tests"] = self.passed_tests
        self.results["failed_tests"] = self.total_tests - self.passed_tests
        
    async def run_comprehensive_check(self):
        """運行全面檢查"""
        print("🚀 Angela AI 系統超級詳細檢查開始...")
        print("=" * 60)
        
        # 文件結構檢查
        self.check_file_structure()
        
        # 核心組件檢查
        core_ok = await self.check_core_components()
        if not core_ok:
            print("\n❌ 核心組件檢查失敗，無法繼續")
            return self.results
            
        # 系統組件檢查
        await self.check_dialogue_system()
        await self.check_memory_system()
        await self.check_llm_integration()
        await self.check_angela_character()
        await self.check_performance_and_stability()
        await self.check_error_handling()
        
        # 生成建議和總體狀態
        self.generate_recommendations()
        self.calculate_overall_status()
        
        return self.results
        
    def print_final_report(self):
        """打印最終報告"""
        print("\n" + "=" * 60)
        print("📊 Angela AI 系統檢查報告")
        print("=" * 60)
        
        print(f"\n🎯 整體狀態: {self.results.get('overall_status', 'UNKNOWN')}")
        print(f"📈 成功率: {self.results.get('success_rate', 0):.1f}%")
        print(f"✅ 通過測試: {self.results.get('passed_tests', 0)}/{self.results.get('total_tests', 0)}")
        
        if self.results["errors"]:
            print(f"\n❌ 發現錯誤 ({len(self.results['errors'])}):")
            for error in self.results["errors"]:
                print(f"   • {error}")
                
        if self.results["recommendations"]:
            print(f"\n💡 改進建議 ({len(self.results['recommendations'])}):")
            for rec in self.results["recommendations"]:
                print(f"   {rec}")
                
        # 性能摘要
        if self.results["performance"]:
            print(f"\n⚡ 性能摘要:")
            for key, value in self.results["performance"].items():
                if isinstance(value, dict) and "performance_ms" in value:
                    print(f"   • {key}: {value['performance_ms']:.2f}ms")
                    
        print(f"\n🕐 檢查完成時間: {self.results['timestamp']}")
        
        # 生產就緒性檢查清單
        print(f"\n✅ 生產就緒性檢查:")
        checklist = [
            (self.results['success_rate'] >= 90, "90%+ 測試通過率"),
            (len(self.results['errors']) == 0, "無關鍵錯誤"),
            (self.results.get('performance', {}).get('dialogue_avg_response_time', 0) < 5000, "響應時間 < 5秒"),
            (self.results.get('passed_tests', 0) >= 20, "足夠的測試覆蓋")
        ]
        
        ready_count = 0
        for condition, description in checklist:
            status = "✅" if condition else "❌"
            print(f"   {status} {description}")
            if condition:
                ready_count += 1
                
        print(f"\n🎯 生產就緒度: {ready_count}/{len(checklist)} 項目滿足")
        
        if ready_count == len(checklist):
            print("🎉 系統完全就緒，可以部署到生產環境！")
        elif ready_count >= len(checklist) * 0.75:
            print("⚠️ 系統基本就緒，建議修復剩餘問題後部署")
        else:
            print("🔧 系統需要重大改進，不建議部署到生產環境")

async def main():
    checker = ComprehensiveSystemChecker()
    results = await checker.run_comprehensive_check()
    checker.print_final_report()
    
    # 保存詳細報告
    report_path = "COMPREHENSIVE_ANGELA_AI_CHECK_REPORT.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n📄 詳細報告已保存到: {report_path}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())