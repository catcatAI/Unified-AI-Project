#!/usr/bin/env python3
"""
统一自动修复工具 - 支持四种操作模式和范围执行
支持: 單純測試、測試後自動修復、單純自動修復、自動修復後自動測試
"""

import os
import sys
import json
import traceback
import argparse
import time
from pathlib import Path
from typing import List, Tuple, Dict, Set, Optional
from enum import Enum

# 导入新架构模块
from core.fix_engine import FixEngine, FixType, FixStatus
from core.test_runner import TestRunner, TestType, TestScope
from core.environment_checker import EnvironmentChecker, EnvironmentComponent
from core.report_generator import ReportGenerator, ReportType, ReportFormat
from core.config_manager import ConfigManager, ConfigType
from modules.import_fixer import ImportFixer
from modules.dependency_fixer import DependencyFixer
from modules.syntax_fixer import SyntaxFixer
from modules.cleanup_module import CleanupModule
from utils.file_utils import FileUtils
from utils.process_utils import ProcessUtils, ExecutionMode

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_ROOT = PROJECT_ROOT / "apps" / "backend"
SRC_DIR = BACKEND_ROOT / "src"

class OperationMode(Enum):
    """操作模式枚举"""
    PURE_TEST = "pure_test"              # 單純測試
    TEST_THEN_FIX = "test_then_fix"      # 測試後自動修復
    PURE_FIX = "pure_fix"                # 單純自動修復
    FIX_THEN_TEST = "fix_then_test"      # 自動修復後自動測試

class ExecutionScope(Enum):
    """执行范围枚举"""
    PROJECT_WIDE = "project_wide"        # 整个项目
    BACKEND_ONLY = "backend_only"        # 仅后端
    FRONTEND_ONLY = "frontend_only"      # 仅前端
    SPECIFIC_MODULE = "specific_module"  # 特定模块
    SPECIFIC_TEST = "specific_test"      # 特定测试

class UnifiedAutoFix:
    """统一自动修复系统 - 使用新架构"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_root = project_root / "apps" / "backend"
        self.src_dir = self.backend_root / "src"
        self.frontend_root = project_root / "apps" / "frontend-dashboard"
        self.desktop_root = project_root / "apps" / "desktop-app"
        
        # 初始化新架构组件
        self.fix_engine = FixEngine(project_root)
        self.test_runner = TestRunner(project_root)
        self.environment_checker = EnvironmentChecker(project_root)
        self.report_generator = ReportGenerator(project_root)
        self.config_manager = ConfigManager(project_root)
        self.file_utils = FileUtils(project_root)
        self.process_utils = ProcessUtils(project_root)
        
        # 初始化修复模块
        self.import_fixer = ImportFixer(project_root)
        self.dependency_fixer = DependencyFixer(project_root)
        self.syntax_fixer = SyntaxFixer(project_root)
        self.cleanup_module = CleanupModule(project_root)
        
        # 注册修复模块到修复引擎
        self.fix_engine.register_fix_module("import_fixer", self.import_fixer)
        self.fix_engine.register_fix_module("dependency_fixer", self.dependency_fixer)
        self.fix_engine.register_fix_module("syntax_fixer", self.syntax_fixer)
        self.fix_engine.register_fix_module("cleanup_module", self.cleanup_module)
        
        # 设置默认启用的修复类型
        self.fix_engine.enable_fix_type(FixType.IMPORT)
        self.fix_engine.enable_fix_type(FixType.DEPENDENCY)
        self.fix_engine.enable_fix_type(FixType.SYNTAX)
        self.fix_engine.enable_fix_type(FixType.CLEANUP)
        
        self.operation_mode = OperationMode.PURE_TEST
        self.execution_scope = ExecutionScope.PROJECT_WIDE
        self.specific_target = None
        
        self.report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "operation_mode": None,
            "execution_scope": None,
            "specific_target": None,
            "test_results": {},
            "fix_results": {},
            "environment_results": {},
            "errors": [],
            "warnings": [],
            "summary": {}
        }
        
    def set_operation_mode(self, mode: OperationMode):
        """设置操作模式"""
        self.operation_mode = mode
        self.report["operation_mode"] = mode.value
        
    def set_execution_scope(self, scope: ExecutionScope, target: Optional[str] = None):
        """设置执行范围"""
        self.execution_scope = scope
        self.specific_target = target
        self.report["execution_scope"] = scope.value
        self.report["specific_target"] = target
        
    def run_tests(self) -> bool:
        """运行测试 - 使用新架构"""
        print(f"\n=== 运行测试 ({self.operation_mode.value}) ===")
        
        try:
            # 映射执行范围到测试范围
            test_scope = self._map_to_test_scope()
            test_type = TestType.UNIT  # 默认使用单元测试
            
            # 构建测试配置
            test_config = {
                "type": test_type.value,
                "scope": test_scope.value,
                "target": self.specific_target,
                "verbose": True
            }
            
            # 运行测试
            test_result = self.test_runner.run_test(
                test_type, 
                test_scope, 
                self.specific_target, 
                verbose=True
            )
            
            # 记录测试结果
            self.report["test_results"] = {
                "command": test_result.command,
                "return_code": test_result.return_code,
                "duration": test_result.duration,
                "tests_collected": test_result.tests_collected,
                "tests_passed": test_result.tests_passed,
                "tests_failed": test_result.tests_failed,
                "tests_skipped": test_result.tests_skipped,
                "stdout": test_result.stdout,
                "stderr": test_result.stderr,
                "success": test_result.success
            }
            
            return test_result.success
                
        except Exception as e:
            error_msg = f"运行测试时出错: {str(e)}"
            print(f"✗ {error_msg}")
            self.report["errors"].append(error_msg)
            return False
                
    def run_auto_fix(self) -> bool:
        """运行自动修复 - 使用新架构"""
        print(f"\n=== 运行自动修复 ({self.operation_mode.value}) ===")
        
        try:
            # 运行修复引擎
            fix_results = self.fix_engine.run_fixes()
            
            # 记录修复结果
            self.report["fix_results"] = {
                "total_fixes": len(fix_results),
                "successful_fixes": sum(1 for r in fix_results if r.status == FixStatus.SUCCESS),
                "failed_fixes": sum(1 for r in fix_results if r.status == FixStatus.FAILED),
                "fixes_details": [
                    {
                        "type": r.fix_type.value,
                        "target": r.target,
                        "status": r.status.value,
                        "message": r.message,
                        "duration": r.duration
                    }
                    for r in fix_results
                ],
                "success": all(r.status == FixStatus.SUCCESS for r in fix_results)
            }
            
            # 输出修复摘要
            total = len(fix_results)
            successful = self.report["fix_results"]["successful_fixes"]
            failed = self.report["fix_results"]["failed_fixes"]
            
            print(f"修复完成: {successful}/{total} 成功, {failed} 失败")
            
            return self.report["fix_results"]["success"]
                
        except Exception as e:
            error_msg = f"运行自动修复时出错: {str(e)}"
            print(f"✗ {error_msg}")
            self.report["errors"].append(error_msg)
            return False
                
    def execute(self) -> bool:
        """执行选定的操作模式 - 使用新架构"""
        print(f"\n=== 开始执行 {self.operation_mode.value} 模式 ===")
        print(f"执行范围: {self.execution_scope.value}")
        if self.specific_target:
            print(f"特定目标: {self.specific_target}")
        
        # 首先检查环境
        print("检查执行环境...")
        env_success = self.check_environment()
        
        success = False
        
        if self.operation_mode == OperationMode.PURE_TEST:
            # 單純測試
            if env_success:
                success = self.run_tests()
            else:
                print("环境检查失败，跳过测试")
                success = False
            
        elif self.operation_mode == OperationMode.TEST_THEN_FIX:
            # 測試後自動修復
            if env_success:
                test_success = self.run_tests()
                if not test_success:
                    print("测试失败，开始自动修复...")
                    success = self.run_auto_fix()
                else:
                    print("测试通过，跳过修复")
                    success = True
            else:
                print("环境检查失败，跳过测试和修复")
                success = False
                
        elif self.operation_mode == OperationMode.PURE_FIX:
            # 單純自動修復
            if env_success:
                success = self.run_auto_fix()
            else:
                print("环境检查失败，跳过修复")
                success = False
            
        elif self.operation_mode == OperationMode.FIX_THEN_TEST:
            # 自動修復後自動測試
            if env_success:
                fix_success = self.run_auto_fix()
                if fix_success:
                    print("修复完成，开始测试...")
                    success = self.run_tests()
                else:
                    print("修复失败，跳过测试")
                    success = False
            else:
                print("环境检查失败，跳过修复和测试")
                success = False
                
        # 生成总结报告
        self._generate_summary(success)
        
        # 保存详细报告
        self._save_detailed_reports()
        
        return success
        
    def _map_to_test_scope(self) -> TestScope:
        """映射执行范围到测试范围"""
        if self.execution_scope == ExecutionScope.PROJECT_WIDE:
            return TestScope.PROJECT_WIDE
        elif self.execution_scope == ExecutionScope.BACKEND_ONLY:
            return TestScope.BACKEND_ONLY
        elif self.execution_scope == ExecutionScope.FRONTEND_ONLY:
            return TestScope.FRONTEND_ONLY
        elif self.execution_scope == ExecutionScope.SPECIFIC_MODULE:
            return TestScope.SPECIFIC_MODULE
        elif self.execution_scope == ExecutionScope.SPECIFIC_TEST:
            return TestScope.SPECIFIC_TEST
        else:
            return TestScope.PROJECT_WIDE
    
    def check_environment(self) -> bool:
        """检查环境 - 使用新架构"""
        print(f"\n=== 检查环境 ({self.operation_mode.value}) ===")
        
        try:
            # 检查所有环境组件
            env_results = self.environment_checker.check_environment(EnvironmentComponent.ALL)
            
            # 记录环境检查结果
            self.report["environment_results"] = {
                "summary": self.environment_checker.get_environment_summary(),
                "details": {
                    component: {
                        "status": result.status,
                        "details": result.details,
                        "version": result.version,
                        "errors": result.errors,
                        "warnings": result.warnings
                    }
                    for component, result in env_results.items()
                },
                "success": env_results.get("summary", {}).get("overall_status") == "healthy"
            }
            
            # 输出环境摘要
            summary = self.report["environment_results"]["summary"]
            print(f"环境检查: {summary['healthy_components']}/{summary['total_components']} 健康")
            
            return self.report["environment_results"]["success"]
                
        except Exception as e:
            error_msg = f"检查环境时出错: {str(e)}"
            print(f"✗ {error_msg}")
            self.report["errors"].append(error_msg)
            return False
        
    def _generate_summary(self, success: bool):
        """生成执行总结"""
        summary = {
            "overall_success": success,
            "operation_mode": self.operation_mode.value,
            "execution_scope": self.execution_scope.value,
            "specific_target": self.specific_target,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if self.report["test_results"]:
            summary["test_success"] = self.report["test_results"]["success"]
            
        if self.report["fix_results"]:
            summary["fix_success"] = self.report["fix_results"]["success"]
            
        self.report["summary"] = summary
        
        print(f"\n=== 执行总结 ===")
        print(f"操作模式: {summary['operation_mode']}")
        print(f"执行范围: {summary['execution_scope']}")
        if summary['specific_target']:
            print(f"特定目标: {summary['specific_target']}")
        print(f"总体结果: {'✓ 成功' if success else '✗ 失败'}")
        
        if "test_success" in summary:
            print(f"测试结果: {'✓ 通过' if summary['test_success'] else '✗ 失败'}")
            
        if "fix_success" in summary:
            print(f"修复结果: {'✓ 成功' if summary['fix_success'] else '✗ 失败'}")
            
    def save_report(self, report_path: Optional[Path] = None):
        """保存执行报告"""
        if report_path is None:
            report_path = self.project_root / f"unified_auto_fix_report_{int(time.time())}.json"
            
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.report, f, ensure_ascii=False, indent=2)
            print(f"✓ 执行报告已保存到 {report_path}")
        except Exception as e:
            print(f"✗ 保存执行报告时出错: {e}")
    
    def _save_detailed_reports(self):
        """保存详细报告 - 使用新架构"""
        try:
            # 保存测试报告
            if self.report.get("test_results"):
                test_results_data = [{
                    "test_type": "unit",
                    "test_scope": self.execution_scope.value,
                    "command": self.report["test_results"]["command"],
                    "return_code": self.report["test_results"]["return_code"],
                    "duration": self.report["test_results"]["duration"],
                    "tests_collected": self.report["test_results"]["tests_collected"],
                    "tests_passed": self.report["test_results"]["tests_passed"],
                    "tests_failed": self.report["test_results"]["tests_failed"],
                    "tests_skipped": self.report["test_results"]["tests_skipped"],
                    "success": self.report["test_results"]["success"]
                }]
                self.report_generator.generate_test_report(test_results_data)
            
            # 保存修复报告
            if self.report.get("fix_results"):
                fix_results_data = {
                    "fixes_made": self.report["fix_results"]["fixes_details"],
                    "files_processed": self.report["fix_results"]["total_fixes"],
                    "files_fixed": self.report["fix_results"]["successful_fixes"],
                    "overall_success": self.report["fix_results"]["success"]
                }
                self.report_generator.generate_fix_report(fix_results_data)
            
            # 保存环境检查报告
            if self.report.get("environment_results"):
                env_results_data = {
                    "results": self.report["environment_results"]["details"],
                    "summary": self.report["environment_results"]["summary"]
                }
                self.report_generator.generate_environment_report(env_results_data)
            
            # 生成HTML和Markdown报告
            if self.report.get("test_results") or self.report.get("fix_results"):
                summary_data = {
                    "title": "Unified AI Project 执行报告",
                    "generated_at": self.report["timestamp"],
                    "project_root": str(self.project_root),
                    "summary": self.report.get("summary", {}),
                    "test_results": self.report.get("test_results", {}),
                    "fix_results": self.report.get("fix_results", {}),
                    "environment_results": self.report.get("environment_results", {})
                }
                
                self.report_generator.generate_html_report(summary_data)
                self.report_generator.generate_markdown_report(summary_data)
                
        except Exception as e:
            print(f"✗ 保存详细报告时出错: {e}")
            self.report["errors"].append(f"保存详细报告失败: {e}")

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="统一自动修复工具 - 支持四种操作模式和范围执行",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
操作模式说明:
  pure_test          單純測試 - 仅运行测试，不执行修复
  test_then_fix      測試後自動修復 - 先运行测试，如果失败则执行修复
  pure_fix           單純自動修復 - 仅执行修复，不运行测试
  fix_then_test      自動修復後自動測試 - 先执行修复，然后运行测试

执行范围说明:
  project_wide       整个项目 - 对整个项目执行操作
  backend_only       仅后端 - 仅对后端代码执行操作
  frontend_only      仅前端 - 仅对前端代码执行操作
  specific_module    特定模块 - 对指定模块执行操作
  specific_test      特定测试 - 对指定测试文件执行操作

示例:
  python unified_auto_fix.py pure_test project_wide
  python unified_auto_fix.py test_then_fix backend_only
  python unified_auto_fix.py pure_fix project_wide
  python unified_auto_fix.py fix_then_test specific_module --target agents
  python unified_auto_fix.py pure_test specific_test --target tests/test_example.py
        """
    )
    
    parser.add_argument(
        "mode",
        choices=["pure_test", "test_then_fix", "pure_fix", "fix_then_test"],
        help="操作模式"
    )
    
    parser.add_argument(
        "scope",
        choices=["project_wide", "backend_only", "frontend_only", "specific_module", "specific_test"],
        help="执行范围"
    )
    
    parser.add_argument(
        "--target",
        type=str,
        help="特定目标（模块名称或测试文件路径）"
    )
    
    parser.add_argument(
        "--report",
        type=str,
        help="报告文件路径"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细输出"
    )
    
    return parser.parse_args()

def main():
    """主函数 - 使用新架构"""
    args = parse_arguments()
    
    print("=== Unified AI Project 统一自动修复工具 (新架构) ===")
    print(f"项目根目录: {PROJECT_ROOT}")
    
    try:
        # 创建统一自动修复实例
        auto_fix = UnifiedAutoFix(PROJECT_ROOT)
        
        # 设置操作模式
        mode = OperationMode(args.mode)
        auto_fix.set_operation_mode(mode)
        
        # 设置执行范围
        scope = ExecutionScope(args.scope)
        auto_fix.set_execution_scope(scope, args.target)
        
        # 加载配置
        config = auto_fix.config_manager.load_config(ConfigType.FIX)
        if config.get("fix_settings", {}).get("verbose", False):
            print("详细模式已启用")
        
        # 执行操作
        success = auto_fix.execute()
        
        # 保存报告
        report_path = Path(args.report) if args.report else None
        auto_fix.save_report(report_path)
        
        # 清理资源
        auto_fix.process_utils.cleanup_processes()
        
        # 返回适当的退出码
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
        return 1
    except Exception as e:
        print(f"执行过程中出现错误: {e}")
        if hasattr(args, 'verbose') and args.verbose:
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())