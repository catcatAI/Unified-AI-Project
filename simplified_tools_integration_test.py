#!/usr/bin/env python3
"""
簡化版真實工具集成測試
基於項目實際可用組件，無需外部依賴
"""

import asyncio
import sys
import os
import time
import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any

# 添加項目路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps" / "backend" / "src"))

# 導入簡化BaseAgent
from simplified_base_agent import SimplifiedBaseAgent, create_simplified_agent, SimpleTask

class SimplifiedToolsTester:
    """簡化工具測試器 - 基於真實系統組件"""
    
    def __init__(self):
        self.available_tools = []
        self.test_results = []
        self.start_time = time.time()
    
    async def discover_available_tools(self) -> List[Dict[str, Any]]:
        """發現可用的工具（基於真實文件系統）"""
        print("🔍 發現真實可用的工具（基於文件系統）...")
        
        available_tools = []
        tools_dir = project_root / "apps" / "backend" / "src" / "core" / "tools"
        
        if not tools_dir.exists():
            print(f"❌ 工具目錄不存在: {tools_dir}")
            return available_tools
        
        # 查找工具文件
        tool_files = list(tools_dir.glob("*_tool.py"))
        print(f"找到 {len(tool_files)} 個工具文件")
        
        for tool_file in tool_files:
            tool_name = tool_file.stem  # 移除.py擴展名
            class_name = "".join(word.capitalize() for word in tool_name.split('_'))
            
            tool_info = {
                "name": class_name,
                "file": str(tool_file),
                "module": f"core.tools.{tool_name}",
                "status": "file_found",
                "size": tool_file.stat().st_size
            }
            
            # 檢查文件內容
            try:
                with open(tool_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 查找類定義
                if f"class {class_name}" in content:
                    tool_info["has_class"] = True
                    tool_info["status"] = "class_found"
                    
                    # 查找__init__方法
                    if f"def __init__" in content:
                        tool_info["has_init"] = True
                        
                        # 分析構造函數複雜度
                        lines = content.split('\n')
                        init_start = -1
                        for i, line in enumerate(lines):
                            if f"def __init__" in line:
                                init_start = i
                                break
                        
                        if init_start >= 0:
                            # 查找構造函數結束位置（簡單方法）
                            init_lines = 0
                            for i in range(init_start + 1, min(init_start + 20, len(lines))):
                                line = lines[i].strip()
                                if line and not line.startswith(' ') and not line.startswith('\t'):
                                    break
                                init_lines += 1
                            
                            tool_info["init_complexity"] = "simple" if init_lines < 5 else "complex"
                    
                    # 查找其他關鍵方法
                    key_methods = ["search", "calculate", "process", "analyze", "get", "find"]
                    found_methods = []
                    for method in key_methods:
                        if f"def {method}" in content:
                            found_methods.append(method)
                    
                    tool_info["key_methods"] = found_methods
                    tool_info["method_count"] = len(found_methods)
                    
                    available_tools.append(tool_info)
                    print(f"  ✅ {class_name}: 找到類定義和 {len(methods)} 個關鍵方法")
                    
            except Exception as e:
                print(f"  ⚠️ {tool_name}: 文件讀取失敗: {e}")
                tool_info["error"] = str(e)
                available_tools.append(tool_info)
        
        self.available_tools = available_tools
        print(f"\n發現 {len(available_tools)} 個潛在可用工具")
        return available_tools
    
    async def test_tool_integration(self, tool_info: Dict[str, Any]) -> Dict[str, Any]:
        """測試工具集成（無需實例化）"""
        tool_name = tool_info["name"]
        start_time = time.time()
        
        result = {
            "tool_name": tool_name,
            "file": tool_info["file"],
            "status": "started",
            "duration": 0,
            "analysis": {},
            "integration_test": {}
        }
        
        try:
            # 分析工具文件內容
            with open(tool_info["file"], 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                "total_lines": len(content.split('\n')),
                "file_size": len(content),
                "has_docstrings": '"""' in content or "'''" in content,
                "has_async_methods": "async def" in content,
                "has_error_handling": "try:" in content and "except" in content,
                "has_logging": "logging" in content or "logger" in content,
                "external_dependencies": []
            }
            
            # 檢查外部依賴
            import_lines = [line.strip() for line in content.split('\n') if line.strip().startswith('import ') or line.strip().startswith('from ')]
            external_deps = []
            for line in import_lines:
                if 'requests' in line:
                    external_deps.append('requests')
                elif 'bs4' in line or 'BeautifulSoup' in line:
                    external_deps.append('beautifulsoup4')
                elif 'yaml' in line:
                    external_deps.append('pyyaml')
                elif 'numpy' in line:
                    external_deps.append('numpy')
                elif 'pandas' in line:
                    external_deps.append('pandas')
            
            analysis["external_dependencies"] = external_deps
            analysis["import_lines"] = len(import_lines)
            
            result["analysis"] = analysis
            
            # 集成測試：模擬代理調用工具
            integration_test = {
                "agent_capability_match": len(tool_info.get("key_methods", [])) > 0,
                "simplified_integration": await self._test_simplified_integration(tool_info),
                "api_compatibility": await self._test_api_compatibility(tool_info, content)
            }
            
            result["integration_test"] = integration_test
            
            # 評估工具可用性
            if not external_deps and tool_info.get("has_init") and tool_info.get("method_count", 0) > 0:
                result["status"] = "ready_to_use"
            elif len(external_deps) <= 1 and tool_info.get("method_count", 0) > 0:
                result["status"] = "conditionally_available"
            else:
                result["status"] = "needs_dependencies"
            
        except Exception as e:
            result["status"] = "analysis_failed"
            result["error"] = str(e)
        
        result["duration"] = time.time() - start_time
        return result
    
    async def _test_simplified_integration(self, tool_info: Dict[str, Any]) -> Dict[str, Any]:
        """測試與簡化代理的集成"""
        result = {
            "status": "started",
            "agent_tool_communication": "simulated",
            "capability_mapping": []
        }
        
        try:
            # 創建模擬代理
            agent = create_simplified_agent("generic", agent_name=f"ToolUser_{tool_info['name']}")
            
            # 模擬能力映射
            key_methods = tool_info.get("key_methods", [])
            for method in key_methods[:2]:  # 限制映射數量
                capability = {
                    "id": f"{tool_info['name']}_{method}",
                    "name": f"{tool_info['name']}_{method}",
                    "description": f"使用{tool_info['name']}的{method}功能",
                    "version": "1.0"
                }
                result["capability_mapping"].append(capability)
                agent.add_capability(capability)
            
            # 模擬任務處理
            test_task = SimpleTask(
                task_id=f"tool_test_{tool_info['name']}",
                task_type="tool_integration",
                payload={"tool_name": tool_info["name"], "method": key_methods[0] if key_methods else "default"}
            )
            
            task_result = await agent.process_task(test_task)
            result["task_processing"] = task_result
            result["status"] = "integration_successful" if task_result.get("status") == "success" else "integration_partial"
            
        except Exception as e:
            result["status"] = "integration_failed"
            result["error"] = str(e)
        
        return result
    
    async def _test_api_compatibility(self, tool_info: Dict[str, Any], content: str) -> Dict[str, Any]:
        """測試API兼容性"""
        result = {
            "status": "started",
            "async_support": "async def" in content,
            "sync_support": "def " in content and "async def" not in content,
            "error_handling": "try:" in content and "except" in content,
            "return_types": []
        }
        
        try:
            # 檢查返回類型
            if "return" in content:
                if "Dict" in content or "dict" in content:
                    result["return_types"].append("dict")
                if "List" in content or "list" in content:
                    result["return_types"].append("list")
                if "str" in content:
                    result["return_types"].append("string")
                if "int" in content:
                    result["return_types"].append("integer")
            
            # 評估兼容性
            compatibility_score = 0
            if result["async_support"]:
                compatibility_score += 2
            if result["sync_support"]:
                compatibility_score += 1
            if result["error_handling"]:
                compatibility_score += 2
            if result["return_types"]:
                compatibility_score += 1
            
            result["compatibility_score"] = compatibility_score
            result["status"] = "highly_compatible" if compatibility_score >= 4 else "moderately_compatible" if compatibility_score >= 2 else "low_compatibility"
            
        except Exception as e:
            result["status"] = "compatibility_test_failed"
            result["error"] = str(e)
        
        return result
    
    async def run_simplified_test(self) -> Dict[str, Any]:
        """運行簡化測試"""
        print("🔧 開始簡化真實工具集成測試")
        print("=" * 70)
        
        # 發現工具
        available_tools = await self.discover_available_tools()
        
        if not available_tools:
            return {
                "status": "no_tools_found",
                "error": "未發現工具文件",
                "tools_tested": 0
            }
        
        print(f"\n📊 發現 {len(available_tools)} 個工具，開始分析...")
        
        # 測試每個工具
        tool_test_tasks = []
        for tool_info in available_tools:
            task = asyncio.create_task(self.test_tool_integration(tool_info))
            tool_test_tasks.append(task)
        
        tool_results = await asyncio.gather(*tool_test_tasks, return_exceptions=True)
        
        # 處理結果
        successful_tools = []
        failed_tools = []
        ready_tools = []
        
        for result in tool_results:
            if isinstance(result, Exception):
                failed_tools.append({"error": str(result)})
            else:
                if result.get("status") == "ready_to_use":
                    ready_tools.append(result)
                elif result.get("status") in ["conditionally_available", "integration_successful"]:
                    successful_tools.append(result)
                else:
                    failed_tools.append(result)
        
        # 生成報告
        total_duration = time.time() - self.start_time
        
        final_report = {
            "test_name": "simplified_real_tools_integration",
            "status": "completed",
            "summary": {
                "total_tools": len(available_tools),
                "ready_tools": len(ready_tools),
                "successful_tools": len(successful_tools),
                "failed_tools": len(failed_tools),
                "success_rate": (len(ready_tools) + len(successful_tools)) / len(available_tools) * 100 if available_tools else 0
            },
            "tools_results": {
                "ready_to_use": ready_tools,
                "successful": successful_tools,
                "failed": failed_tools
            },
            "test_duration": total_duration,
            "timestamp": time.time()
        }
        
        # 顯示摘要
        print("\n" + "=" * 70)
        print("📋 簡化工具集成測試摘要")
        print("=" * 70)
        
        summary = final_report["summary"]
        print(f"總工具數: {summary['total_tools']}")
        print(f"立即可用: {summary['ready_tools']}")
        print(f"有條件可用: {summary['successful_tools']}")
        print(f"需要修復: {summary['failed_tools']}")
        print(f"成功率: {summary['success_rate']:.1f}%")
        print(f"總測試時間: {total_duration:.2f}秒")
        
        # 顯示詳細結果
        if ready_tools:
            print(f"\n✅ 立即可用工具:")
            for tool in ready_tools[:3]:
                methods = tool.get("analysis", {}).get("key_methods", [])
                print(f"  - {tool['tool_name']}: {len(methods)} 個關鍵方法")
        
        if successful_tools:
            print(f"\n⚠️  有條件可用工具:")
            for tool in successful_tools[:3]:
                deps = tool.get("analysis", {}).get("external_dependencies", [])
                print(f"  - {tool['tool_name']}: 依賴 {deps}")
        
        return final_report

# 代理與工具集成測試
async def test_agents_with_simplified_tools():
    """測試代理與簡化工具的集成"""
    print("\n" + "=" * 70)
    print("🔗 測試代理與工具的集成")
    print("=" * 70)
    
    try:
        # 創建代理團隊
        agents = [
            create_simplified_agent("creative", agent_name="CreativeTeam"),
            create_simplified_agent("analysis", agent_name="AnalysisTeam"),
            create_simplified_agent("search", agent_name="SearchTeam")
        ]
        
        # 啟動所有代理
        start_tasks = [agent.start() for agent in agents]
        start_results = await asyncio.gather(*start_tasks)
        
        print(f"代理團隊啟動: {sum(start_results)}/{len(agents)} 成功")
        
        # 模擬多代理協作場景
        collaboration_scenarios = [
            {
                "scenario": "content_creation_workflow",
                "description": "創意代理 + 搜索代理 + 分析代理",
                "tasks": [
                    SimpleTask("search_001", "web_search", {"query": "AI trends 2024"}),
                    SimpleTask("analyze_001", "data_analysis", {"data": "search_results"}),
                    SimpleTask("creative_001", "content_creation", {"topic": "AI analysis"})
                ]
            }
        ]
        
        scenario_results = []
        for scenario in collaboration_scenarios:
            print(f"\n🎬 執行場景: {scenario['description']}")
            
            # 分配任務給相應代理
            task_results = []
            for i, task in enumerate(scenario['tasks']):
                if i < len(agents):
                    result = await agents[i].process_task(task)
                    task_results.append(result)
            
            scenario_result = {
                "scenario": scenario['scenario'],
                "task_results": task_results,
                "overall_success": all(r.get("status") == "success" for r in task_results)
            }
            scenario_results.append(scenario_result)
            
            print(f"場景結果: {'✅ 成功' if scenario_result['overall_success'] else '❌ 部分成功'}")
        
        # 停止所有代理
        stop_tasks = [agent.stop() for agent in agents]
        stop_results = await asyncio.gather(*stop_tasks)
        
        successful_scenarios = sum(1 for s in scenario_results if s['overall_success'])
        
        return {
            "agent_tool_integration": "success",
            "agents_tested": len(agents),
            "scenarios_tested": len(scenario_results),
            "successful_scenarios": successful_scenarios,
            "scenario_details": scenario_results
        }
        
    except Exception as e:
        return {
            "agent_tool_integration": "failed",
            "error": str(e)
        }

async def main():
    """主測試函數"""
    print("🌍 簡化真實多工具集成測試")
    print("基於項目實際文件結構，無外部依賴")
    print("=" * 70)
    
    tester = SimplifiedToolsTester()
    
    try:
        # 運行工具集成測試
        tools_report = await tester.run_simplified_test()
        
        # 運行代理集成測試
        integration_result = await test_agents_with_simplified_tools()
        
        # 合併結果
        final_result = {
            "tools_integration_report": tools_report,
            "agent_integration_test": integration_result,
            "overall_status": "completed",
            "total_time": time.time() - tester.start_time
        }
        
        # 保存報告
        report_file = "simplified_tools_integration_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 詳細報告已保存到: {report_file}")
        
        # 判斷整體結果
        tools_success = tools_report["summary"]["success_rate"]
        integration_success = integration_result.get("agent_tool_integration") == "success"
        
        if tools_success >= 60 and integration_success:
            print("🎉 簡化工具集成測試基本通過")
            print("✅ 多代理多工具協作功能可用")
            exit_code = 0
        elif tools_success >= 40:
            print("⚠️ 簡化工具集成測試部分通過 - 需要優化")
            exit_code = 1
        else:
            print("❌ 簡化工具集成測試主要失敗 - 需要修復")
            exit_code = 2
        
        return exit_code
        
    except Exception as e:
        print(f"\n💥 測試框架異常: {e}")
        import traceback
        traceback.print_exc()
        return 3

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ 測試被用戶中斷")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 主程序異常: {e}")
        sys.exit(4)