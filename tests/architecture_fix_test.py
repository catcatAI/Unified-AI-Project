#!/usr/bin/env python3
"""
Angela AI 架構修復測試腳本

測試內容：
1. P0-1: 4D 狀態矩陣同步機制
2. P0-2: 生物層與執行層反饋路徑
3. P0-3: AI 代理系統與狀態矩陣影響機制
4. P0-4: 記憶系統與情感系統整合
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

# 添加項目路徑
project_root = "/home/cat/桌面/Unified-AI-Project"
backend_root = os.path.join(project_root, "apps", "backend")
sys.path.insert(0, project_root)
sys.path.insert(0, backend_root)
sys.path.insert(0, os.path.join(backend_root, "src"))

# 導入測試模塊
try:
    # 嘗試直接導入
    BiologicalIntegrator = None
    BiologicalEvent = None
    BiologicalEventPublisher = None
    AgentManager = None
    AgentResult = None
    StateImpact = None
    DefaultAgentResultEvaluator = None
    HAMMemoryManager = None

    # 導入生物整合器
    from core.autonomous.biological_integrator import (
        BiologicalIntegrator,
        BiologicalEvent,
        BiologicalEventPublisher
    )
    print("✅ 成功導入 BiologicalIntegrator")

    # 導入代理管理器
    from ai.agents.agent_manager import (
        AgentManager,
        AgentResult,
        StateImpact,
        DefaultAgentResultEvaluator
    )
    print("✅ 成功導入 AgentManager")

    # 導入記憶管理器
    from ai.memory.ham_memory.ham_manager import HAMMemoryManager
    print("✅ 成功導入 HAMMemoryManager")

except ImportError as e:
    print(f"⚠️ 部分模塊導入失敗: {e}")
    print("將使用文件檢查模式進行測試")


class ArchitectureFixTest:
    """架構修復測試類"""

    def __init__(self):
        self.test_results = []
        self.test_start_time = datetime.now()

    def log_test(self, test_name: str, status: str, message: str = ""):
        """記錄測試結果"""
        result = {
            "test_name": test_name,
            "status": status,  # "pass", "fail", "skip"
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_icon = "✅" if status == "pass" else "❌" if status == "fail" else "⚠️"
        print(f"{status_icon} {test_name}: {status.upper()}")
        if message:
            print(f"   {message}")

    # P0-1 測試
    async def test_p0_1_state_matrix_sync(self):
        """測試 4D 狀態矩陣同步機制"""
        print("\n=== P0-1: 4D 狀態矩陣同步機制 ===")

        # 檢查前端文件是否包含必要的功能
        frontend_files = [
            "/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/js/backend-websocket.js",
            "/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/js/state-matrix.js"
        ]

        for file_path in frontend_files:
            if not os.path.exists(file_path):
                self.log_test("P0-1 文件檢查", "fail", f"文件不存在: {file_path}")
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 檢查關鍵功能
            if "messageSequence" in content:
                self.log_test("P0-1 消息序列號", "pass", "消息序列號機制已實現")
            else:
                self.log_test("P0-1 消息序列號", "fail", "缺少消息序列號機制")

            if "mergeStateData" in content or "_mergeStateData" in content:
                self.log_test("P0-1 狀態合併", "pass", "狀態合併機制已實現")
            else:
                self.log_test("P0-1 狀態合併", "fail", "缺少狀態合併機制")

            if "pendingUpdates" in content:
                self.log_test("P0-1 待處理消息緩存", "pass", "待處理消息緩存已實現")
            else:
                self.log_test("P0-1 待處理消息緩存", "fail", "缺少待處理消息緩存")

    # P0-2 測試
    async def test_p0_2_biological_feedback(self):
        """測試生物層與執行層反饋路徑"""
        print("\n=== P0-2: 生物層與執行層反饋路徑 ===")

        # 測試生物事件定義
        try:
            events = [
                BiologicalEvent.EMOTION_CHANGED,
                BiologicalEvent.STRESS_CHANGED,
                BiologicalEvent.ENERGY_CHANGED,
                BiologicalEvent.MOOD_CHANGED,
                BiologicalEvent.AROUSAL_CHANGED
            ]
            self.log_test("P0-2 生物事件定義", "pass", f"定義了 {len(events)} 種生物事件")
        except Exception as e:
            self.log_test("P0-2 生物事件定義", "fail", str(e))

        # 測試生物事件發布器
        try:
            publisher = BiologicalEventPublisher()

            # 測試訂閱和發布
            event_received = []
            async def callback(event, data):
                event_received.append((event, data))

            publisher.subscribe(BiologicalEvent.EMOTION_CHANGED, callback)
            await publisher.publish(BiologicalEvent.EMOTION_CHANGED, {"test": "data"})

            if len(event_received) > 0:
                self.log_test("P0-2 事件發布器", "pass", "事件發布器正常工作")
            else:
                self.log_test("P0-2 事件發布器", "fail", "事件發布器無法發布事件")
        except Exception as e:
            self.log_test("P0-2 事件發布器", "fail", str(e))

        # 檢查前端生物事件監聽
        frontend_file = "/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/js/app.js"
        if os.path.exists(frontend_file):
            with open(frontend_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if "biological_event" in content:
                self.log_test("P0-2 前端生物事件監聽", "pass", "前端已實現生物事件監聽")
            else:
                self.log_test("P0-2 前端生物事件監聽", "fail", "前端缺少生物事件監聽")
        else:
            self.log_test("P0-2 前端生物事件監聽", "fail", "前端文件不存在")

    # P0-3 測試
    async def test_p0_3_agent_state_impact(self):
        """測試 AI 代理系統與狀態矩陣影響機制"""
        print("\n=== P0-3: AI 代理系統與狀態矩陣影響機制 ===")

        # 測試代理結果評估器
        try:
            evaluator = DefaultAgentResultEvaluator()

            # 測試成功結果
            success_result = AgentResult(
                agent_type="CreativeWritingAgent",
                agent_id="test_agent",
                success=True,
                result_data={"output": "test"},
                execution_time=1.0
            )

            impact = await evaluator.evaluate(success_result)

            if impact.gamma.get('creativity', 0) > 0:
                self.log_test("P0-3 成功結果評估", "pass", "成功結果正確評估創造力影響")
            else:
                self.log_test("P0-3 成功結果評估", "fail", "成功結果未評估創造力影響")

            # 測試失敗結果
            failure_result = AgentResult(
                agent_type="CreativeWritingAgent",
                agent_id="test_agent",
                success=False,
                result_data=None,
                execution_time=1.0,
                error="Test error"
            )

            impact = await evaluator.evaluate(failure_result)

            if impact.alpha.get('tension', 0) > 0:
                self.log_test("P0-3 失敗結果評估", "pass", "失敗結果正確評估緊張影響")
            else:
                self.log_test("P0-3 失敗結果評估", "fail", "失敗結果未評估緊張影響")

        except Exception as e:
            self.log_test("P0-3 代理結果評估器", "fail", str(e))

        # 檢查 AgentManager 是否集成了評估器
        agent_manager_file = "/home/cat/桌面/Unified-AI-Project/apps/backend/src/ai/agents/agent_manager.py"
        if os.path.exists(agent_manager_file):
            with open(agent_manager_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if "execute_agent" in content:
                self.log_test("P0-3 AgentManager 集成", "pass", "AgentManager 已集成執行和評估功能")
            else:
                self.log_test("P0-3 AgentManager 集成", "fail", "AgentManager 缺少執行和評估功能")
        else:
            self.log_test("P0-3 AgentManager 集成", "fail", "AgentManager 文件不存在")

    # P0-4 測試
    async def test_p0_4_emotional_memory(self):
        """測試記憶系統與情感系統整合"""
        print("\n=== P0-4: 記憶系統與情感系統整合 ===")

        # 測試情感記憶存儲
        try:
            # 使用臨時目錄
            temp_dir = "/tmp/test_ham"
            os.makedirs(temp_dir, exist_ok=True)

            ham_manager = HAMMemoryManager(storage_dir=temp_dir, core_storage_filename="test_ham.json")

            # 存儲情感記憶
            memory_id = await ham_manager.store_emotional_memory(
                content="這是一個測試情感記憶",
                emotion="happy",
                intensity=0.8,
                context={"reason": "test"}
            )

            if memory_id:
                self.log_test("P0-4 情感記憶存儲", "pass", f"成功存儲情感記憶: {memory_id}")
            else:
                self.log_test("P0-4 情感記憶存儲", "fail", "情感記憶存儲失敗")

            # 檢索情感記憶
            memories = await ham_manager.retrieve_emotional_memories(
                emotion="happy",
                min_intensity=0.5,
                limit=5
            )

            if len(memories) > 0:
                self.log_test("P0-4 情感記憶檢索", "pass", f"成功檢索 {len(memories)} 條情感記憶")
            else:
                self.log_test("P0-4 情感記憶檢索", "fail", "情感記憶檢索失敗")

        except Exception as e:
            self.log_test("P0-4 情感記憶功能", "fail", str(e))

        # 檢查決策循環是否集成了情感記憶
        llm_file = "/home/cat/桌面/Unified-AI-Project/apps/backend/src/ai/lifecycle/llm_decision_loop.py"
        if os.path.exists(llm_file):
            with open(llm_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if "retrieve_emotional_memories" in content:
                self.log_test("P0-4 決策循環集成", "pass", "決策循環已集成情感記憶")
            else:
                self.log_test("P0-4 決策循環集成", "fail", "決策循環未集成情感記憶")
        else:
            self.log_test("P0-4 決策循環集成", "fail", "決策循環文件不存在")

    # 生成測試報告
    def generate_report(self) -> Dict[str, Any]:
        """生成測試報告"""
        test_end_time = datetime.now()
        duration = (test_end_time - self.test_start_time).total_seconds()

        pass_count = sum(1 for r in self.test_results if r["status"] == "pass")
        fail_count = sum(1 for r in self.test_results if r["status"] == "fail")
        skip_count = sum(1 for r in self.test_results if r["status"] == "skip")
        total_count = len(self.test_results)

        report = {
            "summary": {
                "total_tests": total_count,
                "passed": pass_count,
                "failed": fail_count,
                "skipped": skip_count,
                "success_rate": f"{(pass_count / total_count * 100):.1f}%" if total_count > 0 else "0%",
                "duration_seconds": duration,
                "start_time": self.test_start_time.isoformat(),
                "end_time": test_end_time.isoformat()
            },
            "results": self.test_results
        }

        return report

    async def run_all_tests(self):
        """運行所有測試"""
        print("=" * 80)
        print("Angela AI 架構修復測試")
        print("=" * 80)
        print(f"開始時間: {self.test_start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 運行所有測試
        await self.test_p0_1_state_matrix_sync()
        await self.test_p0_2_biological_feedback()
        await self.test_p0_3_agent_state_impact()
        await self.test_p0_4_emotional_memory()

        # 生成報告
        report = self.generate_report()

        # 打印摘要
        print("\n" + "=" * 80)
        print("測試摘要")
        print("=" * 80)
        print(f"總測試數: {report['summary']['total_tests']}")
        print(f"通過: {report['summary']['passed']} ✅")
        print(f"失敗: {report['summary']['failed']} ❌")
        print(f"跳過: {report['summary']['skipped']} ⚠️")
        print(f"成功率: {report['summary']['success_rate']}")
        print(f"耗時: {report['summary']['duration_seconds']:.2f} 秒")

        # 保存報告
        report_file = "/home/cat/桌面/architecture_fix_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n測試報告已保存到: {report_file}")

        return report


async def main():
    """主函數"""
    tester = ArchitectureFixTest()
    report = await tester.run_all_tests()

    # 返回退出代碼
    if report['summary']['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
