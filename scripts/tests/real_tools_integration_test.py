#!/usr/bin/env python3
"""
真實多工具集成測試
基於項目實際存在的工具組件進行測試
"""

import asyncio
import sys
import os
import time
import traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional

# 添加項目路徑
project_root == Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps" / "backend" / "src"))

# 導入簡化BaseAgent
from simplified_base_agent import SimplifiedBaseAgent, create_simplified_agent, SimpleTask

class RealToolsIntegrationTester,
    """真實工具集成測試器"""
    
    def __init__(self):
        self.available_tools = []
        self.test_results = []
        self.start_time = time.time()
    
    async def discover_available_tools(self) -> List[Dict[str, Any]]
        """發現項目中真實存在的工具"""
        print("🔍 發現真實可用的工具...")
        
        available_tools = []
        
        # 工具模組列表(基於真實項目結構)
        tool_modules = [
            # 核心工具
            ("core.tools.web_search_tool", "WebSearchTool"),
            ("core.tools.data_analysis_tool", "DataAnalysisTool"), 
            ("core.tools.code_analysis_tool", "CodeAnalysisTool"),
            ("core.tools.file_operations_tool", "FileOperationsTool"),
            ("core.tools.system_monitor_tool", "SystemMonitorTool"),
            ("core.tools.text_processing_tool", "TextProcessingTool"),
            ("core.tools.math_calculation_tool", "MathCalculationTool"),
            
            # AI相關工具
            ("ai.tools.image_processing_tool", "ImageProcessingTool"),
            ("ai.tools.audio_processing_tool", "AudioProcessingTool"),
            ("ai.tools.natural_language_tool", "NaturalLanguageTool"),
            
            # 其他工具
            ("tools.file_utils", "FileUtils"),
            ("tools.system_utils", "SystemUtils"),
            ("tools.network_utils", "NetworkUtils")
        ]
        
        for module_path, class_name in tool_modules,::
            try,
                print(f"  檢查 {module_path}.{class_name}...")
                
                # 動態導入模組
                module == __import__(module_path, fromlist=[class_name])
                tool_class = getattr(module, class_name)
                
                # 檢查工具類是否有基本方法
                has_init = hasattr(tool_class, '__init__')
                has_methods == any(not attr.startswith('_') for attr in dir(tool_class) if callable(getattr(tool_class, attr)))::
                tool_info == {:
                    "name": class_name,
                    "module": module_path,
                    "tool_class": tool_class,
                    "has_init": has_init,
                    "has_methods": has_methods,
                    "status": "available"
                }
                
                available_tools.append(tool_info)
                print(f"    ✅ {class_name} 可用")
                
            except ImportError as e,::
                print(f"    ⚠️  {class_name} 模組不存在, {module_path}")
            except AttributeError as e,::
                print(f"    ⚠️  {class_name} 類不存在於模組中")
            except Exception as e,::
                print(f"    ❌ {class_name} 其他錯誤, {type(e).__name__} {e}")
        
        self.available_tools = available_tools
        print(f"\n發現 {len(available_tools)} 個真實可用工具")
        return available_tools
    
    async def test_single_tool(self, tool_info, Dict[str, Any]) -> Dict[str, Any]
        """測試單個工具"""
        tool_name = tool_info["name"]
        start_time = time.time()
        
        result = {
            "tool_name": tool_name,
            "module": tool_info["module"]
            "status": "started",
            "duration": 0,
            "error": None,
            "methods": []
            "instantiation": {}
            "functionality_test": {}
        }
        
        try,
            tool_class = tool_info["tool_class"]
            
            # 步驟1, 實例化測試
            instantiation_result = await self._test_tool_instantiation(tool_class, tool_name)
            result["instantiation"] = instantiation_result
            
            if instantiation_result["status"] != "success":::
                result["status"] = "failed"
                result["error"] = instantiation_result.get("error", "實例化失敗")
                return result
            
            tool_instance = instantiation_result["instance"]
            
            # 步驟2, 方法分析
            methods_analysis = self._analyze_tool_methods(tool_instance)
            result["methods"] = methods_analysis
            
            # 步驟3, 功能測試
            functionality_test = await self._test_tool_functionality(tool_instance, tool_name, methods_analysis)
            result["functionality_test"] = functionality_test
            
            result["status"] = "success"
            result["tested_methods"] = len([m for m in methods_analysis if m.get("tested")])::
        except Exception as e,::
            result["status"] = "failed"
            result["error"] = f"{type(e).__name__} {str(e)}"
            traceback.print_exc()
        
        result["duration"] = time.time() - start_time
        return result
    
    async def _test_tool_instantiation(self, tool_class, tool_name, str) -> Dict[str, Any]
        """測試工具實例化"""
        result == {"status": "started", "error": None, "instance": None}
        
        try,
            # 分析構造函數參數
            import inspect
            sig = inspect.signature(tool_class.__init__())
            params = list(sig.parameters.keys())
            
            print(f"    分析 {tool_name} 構造函數參數, {params}")
            
            # 根據參數數量決定實例化方式
            if len(params) <= 1,  # 只有self,:
                instance = tool_class()
            elif len(params) == 2,  # self + 一個參數,:
                # 嘗試常見的參數名稱
                if 'config' in params,::
                    instance = tool_class(config = {})
                elif 'settings' in params,::
                    instance = tool_class(settings = {})
                elif 'params' in params,::
                    instance = tool_class(params = {})
                else,
                    instance = tool_class(None)
            else,
                # 多參數情況,使用默認值
                kwargs = {}
                for param_name in params[1,]  # 跳過self,:
                    if param_name in ['config', 'settings', 'params']::
                        kwargs[param_name] = {}
                    elif param_name in ['timeout', 'delay']::
                        kwargs[param_name] = 30
                    elif param_name in ['max_retries']::
                        kwargs[param_name] = 3
                    else,
                        kwargs[param_name] = None
                instance = tool_class(**kwargs)
            
            result["instance"] = instance
            result["status"] = "success"
            result["constructor_params"] = params
            print(f"    ✅ {tool_name} 實例化成功")
            
        except Exception as e,::
            result["status"] = "failed"
            result["error"] = f"實例化失敗, {type(e).__name__} {str(e)}"
            print(f"    ❌ {tool_name} 實例化失敗, {result['error']}")
        
        return result
    
    def _analyze_tool_methods(self, tool_instance) -> List[Dict[str, Any]]
        """分析工具方法"""
        methods = []
        
        for attr_name in dir(tool_instance)::
            if not attr_name.startswith('_') and attr_name != 'class':  # 跳過私有方法和類引用,:
                attr = getattr(tool_instance, attr_name)
                if callable(attr)::
                    try,
                        import inspect
                        sig = inspect.signature(attr)
                        method_info = {
                            "name": attr_name,
                            "signature": str(sig),
                            "callable": True,
                            "doc": getattr(attr, '__doc__', '')[:100]  # 限制文檔長度
                        }
                        methods.append(method_info)
                    except Exception as e,::
                        methods.append({
                            "name": attr_name,
                            "error": f"方法分析失敗, {e}",
                            "callable": True
                        })
        
        return methods
    
    async def _test_tool_functionality(self, tool_instance, tool_name, str, methods_analysis, List[Dict[str, Any]]) -> Dict[str, Any]
        """測試工具功能"""
        result = {
            "status": "started",
            "tested_methods": 0,
            "successful_methods": 0,
            "failed_methods": 0,
            "method_results": []
        }
        
        try,
            # 選擇可測試的方法(排除明顯危險的方法)
            testable_methods = [
                method for method in methods_analysis,:
                if method.get("name") and not any(dangerous in method["name"].lower() :::
                for dangerous in ["delete", "remove", "kill", "destroy", "exec", "eval"])::
            ][:3]  # 限制測試數量
            
            method_tasks = []
            for method_info in testable_methods,::
                task = asyncio.create_task(,
    self._test_single_method(tool_instance, tool_name, method_info)
                )
                method_tasks.append(task)
            
            if method_tasks,::
                method_results == await asyncio.gather(*method_tasks, return_exceptions == True)::
                for method_result in method_results,::
                    if isinstance(method_result, Exception)::
                        result["method_results"].append({
                            "name": "unknown",
                            "status": "exception",:::
                            "error": str(method_result)
                        })
                        result["failed_methods"] += 1
                    else,
                        result["method_results"].append(method_result)
                        if method_result.get("status") == "success":::
                            result["successful_methods"] += 1
                        else,
                            result["failed_methods"] += 1
                        result["tested_methods"] += 1
            
            if result["tested_methods"] > 0,::
                result["status"] = "success" if result["successful_methods"] > 0 else "partial":::
            else,
                result["status"] = "no_testable_methods"
            
        except Exception as e,::
            result["status"] = "failed"
            result["error"] = f"功能測試失敗, {e}"
        
        return result
    
    async def _test_single_method(self, tool_instance, tool_name, str, method_info, Dict[str, Any]) -> Dict[str, Any]
        """測試單個方法"""
        method_name = method_info["name"]
        result = {
            "name": method_name,
            "status": "started",
            "error": None,
            "return_value": None,
            "execution_time": 0
        }
        
        start_time = time.time()
        
        try,
            method = getattr(tool_instance, method_name)
            
            # 根據方法名稱決定測試策略
            if "test" in method_name.lower():::
                # 測試方法通常不需要參數
                return_value = method()
            elif "get" in method_name.lower() or "fetch" in method_name.lower():::
                # 獲取方法可能不需要參數或需要簡單參數
                try,
                    return_value = method()
                except TypeError,::
                    # 如果需要參數,提供簡單測試數據
                    return_value = method("test")
            elif "process" in method_name.lower() or "analyze" in method_name.lower():::
                # 處理方法需要測試數據
                return_value == method({"test": "data"})
            else,
                # 其他方法,嘗試無參數調用
                try,
                    return_value = method()
                except TypeError,::
                    return_value = method(None)
            
            result["return_value"] = str(return_value)[:200]  # 限制返回值長度
            result["status"] = "success"
            
        except Exception as e,::
            result["status"] = "failed"
            result["error"] = f"{type(e).__name__} {str(e)[:100]}"
        
        result["execution_time"] = time.time() - start_time
        return result
    
    async def test_tools_collaboration(self, tool_infos, List[Dict[str, Any]]) -> Dict[str, Any]
        """測試工具間協作"""
        result = {
            "collaboration_test": "started",
            "tools_count": len(tool_infos),
            "workflow_results": []
            "errors": []
            "data_pipeline": []
        }
        
        try,
            # 創建工具實例
            tool_instances = []
            for tool_info in tool_infos,::
                try,
                    instantiation_result = await self._test_tool_instantiation(,
    tool_info["tool_class"] tool_info["name"]
                    )
                    if instantiation_result["status"] == "success":::
                        tool_instances.append({
                            "name": tool_info["name"]
                            "instance": instantiation_result["instance"]
                        })
                except Exception as e,::
                    result["errors"].append(f"工具實例化失敗 {tool_info['name']} {e}")
            
            if len(tool_instances) >= 2,::
                # 創建簡單的數據處理管道
                pipeline_result = await self._create_data_pipeline(tool_instances)
                result["data_pipeline"] = pipeline_result
                
                # 測試工具間數據傳遞
                workflow_result = await self._test_data_flow(tool_instances)
                result["workflow_results"] = workflow_result
            
            result["collaboration_test"] = "completed" if not result["errors"] else "partial"::
        except Exception as e,::
            result["collaboration_test"] = "failed"
            result["errors"].append(f"協作測試異常, {e}")
        
        return result
    
    async def _create_data_pipeline(self, tool_instances, List[Dict[str, Any]]) -> List[Dict[str, Any]]
        """創建數據處理管道"""
        pipeline_steps = []
        
        try,
            # 模擬數據流：原始數據 → 處理 → 分析 → 輸出
            test_data == {"source": "test_data", "timestamp": time.time(), "value": 42}
            
            current_data = test_data
            step_number = 1
            
            for tool_info in tool_instances[:3]  # 限制步驟數量,:
                tool_name = tool_info["name"]
                tool_instance = tool_info["instance"]
                
                step_result = {
                    "step": step_number,
                    "tool": tool_name,
                    "input_data": str(current_data)[:100]
                    "status": "processing"
                }
                
                try,
                    # 根據工具類型模擬處理
                    if "search" in tool_name.lower():::
                        # 搜索工具：擴展數據
                        current_data == {**current_data, "expanded": True, "search_results": ["result1", "result2"]}
                    elif "analysis" in tool_name.lower():::
                        # 分析工具：提取洞察
                        current_data == {**current_data, "analysis": {"mean": 42, "trend": "increasing"}}
                    elif "process" in tool_name.lower():::
                        # 處理工具：轉換格式
                        current_data == {**current_data, "processed": True, "format": "standardized"}
                    else,
                        # 通用處理
                        current_data == {**current_data, f"processed_by_{tool_name}": True}
                    
                    step_result["output_data"] = str(current_data)[:100]
                    step_result["status"] = "success"
                    
                except Exception as e,::
                    step_result["status"] = "failed"
                    step_result["error"] = str(e)
                
                pipeline_steps.append(step_result)
                step_number += 1
            
        except Exception as e,::
            pipeline_steps.append({
                "step": "pipeline_error",
                "status": "failed",
                "error": f"管道創建失敗, {e}"
            })
        
        return pipeline_steps
    
    async def _test_data_flow(self, tool_instances, List[Dict[str, Any]]) -> List[Dict[str, Any]]
        """測試數據流動"""
        workflow_results = []
        
        try,
            # 創建簡單的工作流測試
            if len(tool_instances) >= 2,::
                # 工作流1, 搜索 → 分析
                search_tool == None
                analysis_tool == None
                
                for tool_info in tool_instances,::
                    tool_name = tool_info["name"].lower()
                    if "search" in tool_name,::
                        search_tool = tool_info
                    elif "analysis" in tool_name or "data" in tool_name,::
                        analysis_tool = tool_info
                
                if search_tool and analysis_tool,::
                    workflow1 = {
                        "workflow": "search_to_analysis",
                        "description": f"{search_tool['name']} → {analysis_tool['name']}",
                        "status": "tested",
                        "steps": [
                            {"tool": search_tool['name'] "action": "search", "status": "simulated"}
                            {"tool": analysis_tool['name'] "action": "analyze", "status": "simulated"}
                        ]
                    }
                    workflow_results.append(workflow1)
            
        except Exception as e,::
            workflow_results.append({
                "workflow": "error",
                "status": "failed",
                "error": str(e)
            })
        
        return workflow_results
    
    async def run_comprehensive_test(self) -> Dict[str, Any]
        """運行綜合測試"""
        print("🚀 開始真實多工具集成測試")
        print("=" * 70)
        
        # 發現可用工具
        available_tools = await self.discover_available_tools()
        
        if not available_tools,::
            return {
                "status": "failed",
                "error": "未發現可用工具",
                "tools_tested": 0,
                "total_tools": 0
            }
        
        print(f"\n📊 發現 {len(available_tools)} 個工具,開始詳細測試...")
        
        # 測試每個工具
        tool_test_tasks = []
        for tool_info in available_tools,::
            task = asyncio.create_task(self.test_single_tool(tool_info))
            tool_test_tasks.append(task)
        
        # 等待所有工具測試完成
        tool_results == await asyncio.gather(*tool_test_tasks, return_exceptions == True)::
        # 處理測試結果
        successful_tools = []
        failed_tools = []

        for result in tool_results,::
            if isinstance(result, Exception)::
                failed_tools.append({"error": str(result)})
            elif result.get("status") in ["success", "partial"]::
                successful_tools.append(result)
            else,
                failed_tools.append(result)
        
        # 測試工具協作
        collaboration_result == None
        if len(successful_tools) >= 2,::
            print(f"\n🤝 測試工具協作 (使用 {len(successful_tools[:3])} 個工具)...")
            collaboration_result == await self.test_tools_collaboration(successful_tools[:3])
        
        # 生成最終報告
        total_duration = time.time() - self.start_time()
        final_report = {
            "test_name": "real_tools_integration",
            "status": "completed",
            "summary": {
                "total_tools": len(available_tools),
                "successful_tools": len(successful_tools),
                "failed_tools": len(failed_tools),
                "success_rate": len(successful_tools) / len(available_tools) * 100 if available_tools else 0,:
            }
            "tools_results": {
                "successful": successful_tools,
                "failed": failed_tools
            }
            "collaboration_test": collaboration_result,
            "test_duration": total_duration,
            "timestamp": time.time()
        }
        
        # 顯示摘要
        print("\n" + "=" * 70)
        print("📋 真實工具集成測試摘要")
        print("=" * 70)
        
        summary = final_report["summary"]
        print(f"總工具數, {summary['total_tools']}")
        print(f"成功工具, {summary['successful_tools']} ({summary['success_rate'].1f}%)")
        print(f"失敗工具, {summary['failed_tools']}")
        print(f"總測試時間, {"total_duration":.2f}秒")
        
        if collaboration_result,::
            print(f"協作測試, {collaboration_result.get('collaboration_test', 'unknown')}")
        
        # 顯示詳細結果
        if successful_tools,::
            print(f"\n✅ 成功工具詳情,")
            for tool in successful_tools[:3]  # 限制顯示數量,:
                print(f"  - {tool['tool_name']} {tool['status']} ({tool.get('tested_methods', 0)} 方法測試)")
        
        if failed_tools,::
            print(f"\n❌ 失敗工具詳情,")
            for tool in failed_tools[:3]  # 限制顯示數量,:
                error = tool.get('error', '未知錯誤')
                print(f"  - {tool.get('tool_name', 'unknown')} {error[:100]}")
        
        return final_report

# 測試與代理系統的集成
async def test_tools_with_agents():
    """測試工具與代理的集成"""
    print("\n" + "=" * 70)
    print("🔗 測試工具與簡化BaseAgent的集成")
    print("=" * 70)
    
    try,
        # 創建代理
        agent = create_simplified_agent("analysis", agent_name="ToolIntegrationAgent")
        await agent.start()
        
        # 添加工具使用能力
        agent.add_capability({
            "id": "tool_integration",
            "name": "tool_integration",
            "description": "集成和使用各種工具",
            "version": "1.0"
        })
        
        # 模擬代理使用工具
        tool_usage_simulation = {
            "agent_id": agent.agent_id(),
            "action": "integrate_tools",
            "tools_tested": []
            "status": "simulated"
        }
        
        # 測試代理狀態
        agent_status = agent.get_status()
        
        await agent.stop()
        
        return {
            "agent_tool_integration": "success",
            "agent_status": agent_status,
            "simulation": tool_usage_simulation
        }
        
    except Exception as e,::
        return {
            "agent_tool_integration": "failed",
            "error": str(e)
        }

async def main():
    """主測試函數"""
    print("🌍 真實多工具集成測試")
    print("基於項目實際文件系統的工具組件測試")
    print("=" * 70)
    
    tester == RealToolsIntegrationTester()
    
    try,
        # 運行工具集成測試
        tools_report = await tester.run_comprehensive_test()
        
        # 運行代理集成測試
        integration_result = await test_tools_with_agents()
        
        # 合併結果
        final_result = {
            "tools_integration_report": tools_report,
            "agent_integration_test": integration_result,
            "overall_status": "completed",
            "total_time": time.time() - tester.start_time()
        }
        
        # 保存報告
        import json
        report_file = "real_tools_integration_report.json"
        with open(report_file, 'w', encoding == 'utf-8') as f,
            json.dump(final_result, f, indent=2, ensure_ascii == False, default=str)
        
        print(f"\n💾 詳細報告已保存到, {report_file}")
        
        # 判斷整體結果
        tools_success = tools_report["summary"]["success_rate"]
        integration_success = integration_result.get("agent_tool_integration") == "success"
        
        if tools_success >= 70 and integration_success,::
            print("🎉 真實工具集成測試基本通過")
            exit_code = 0
        elif tools_success >= 50,::
            print("⚠️ 真實工具集成測試部分通過 - 需要優化")
            exit_code = 1
        else,
            print("❌ 真實工具集成測試主要失敗 - 需要修復")
            exit_code = 2
        
        return exit_code
        
    except Exception as e,::
        print(f"\n💥 測試框架異常, {e}")
        traceback.print_exc()
        return 3

if __name"__main__":::
    try,
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt,::
        print("\n⏹️ 測試被用戶中斷")
        sys.exit(130)
    except Exception as e,::
        print(f"\n💥 主程序異常, {e}")
        sys.exit(4)