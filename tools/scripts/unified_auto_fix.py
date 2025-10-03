#!/usr/bin/env python3
"""
统一自动修复工具 - 支持四种操作模式和范围执行
支持: 單純測試、測試後自動修復、單純自動修復、自動修復後自動測試
"""

import sys
import json
import traceback
import argparse
import time
from pathlib import Path
from enum import Enum
from typing import Optional, Dict, List, Any

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 从正确路径导入组件
from scripts.core.fix_engine import FixEngine, FixType, FixStatus
from tests.test_runner import TestRunner
from scripts.core.environment_checker import EnvironmentChecker, EnvironmentComponent
# 修复模块导入路径
from scripts.modules.import_fixer import ImportFixer
from scripts.modules.dependency_fixer import DependencyFixer
from scripts.modules.syntax_fixer import SyntaxFixer
from scripts.modules.enhanced_syntax_fixer import EnhancedSyntaxFixer
from scripts.modules.cleanup_module import CleanupModule

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

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.backend_root = project_root / "apps" / "backend"
        self.src_dir = self.backend_root / "src"
        self.frontend_root = project_root / "apps" / "frontend-dashboard"
        self.desktop_root = project_root / "apps" / "desktop-app"

        # 初始化新架构组件
        self.fix_engine = FixEngine(project_root)
        self.test_runner = TestRunner()
        self.environment_checker = EnvironmentChecker(project_root)

        # 初始化修复模块
        self.import_fixer = ImportFixer(project_root)
        self.dependency_fixer = DependencyFixer(project_root)
        # 优先使用增强版语法修复器
        try:
            self.syntax_fixer = EnhancedSyntaxFixer(project_root)
        except Exception as e:
            print(f"警告: 无法初始化增强版语法修复器，使用基础版本: {e}")
            self.syntax_fixer = SyntaxFixer(project_root)
        self.cleanup_module = CleanupModule(project_root)

        # 启用修复类型
        self.fix_engine.enable_fix_type(FixType.IMPORT_FIX)
        self.fix_engine.enable_fix_type(FixType.DEPENDENCY_FIX)
        self.fix_engine.enable_fix_type(FixType.SYNTAX_FIX)
        self.fix_engine.enable_fix_type(FixType.CLEANUP_FIX)

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

    def set_operation_mode(self, mode: OperationMode) -> None:
        """设置操作模式"""
        self.operation_mode = mode
        self.report["operation_mode"] = mode.value

    def set_execution_scope(self, scope: ExecutionScope, target: Optional[str] = None) -> None:
        """设置执行范围"""
        self.execution_scope = scope
        self.specific_target = target
        self.report["execution_scope"] = scope.value
        self.report["specific_target"] = target

    def run_tests(self) -> bool:
        """运行测试 - 使用新架构"""
        print(f"\n=== 运行测试 ({self.operation_mode.value}) ===")

        try:
            # 直接运行测试

            # 运行测试 - 调整为正确的测试运行器方法
            test_result = self.test_runner.run_tests(
                test_paths=[self.specific_target] if self.specific_target else None,
                extra_args=["--tb=short", "-v"]
            )

            # 记录测试结果 - 调整为测试运行器返回的格式
            self.report["test_results"] = {
                "command": test_result.get("command", ""),
                "return_code": test_result.get("exit_code", -1),
                "stdout": test_result.get("stdout", ""),
                "stderr": test_result.get("stderr", ""),
                "success": test_result.get("exit_code", -1) == 0,
                # 从stdout中提取测试统计信息
                "tests_collected": 0,  # 需要从stdout解析
                "tests_passed": 0,     # 需要从stdout解析
                "tests_failed": 0,     # 需要从stdout解析
                "tests_skipped": 0,    # 需要从stdout解析
                "duration": 0          # 需要计算或从结果中提取
            }

            return test_result.get("exit_code", -1) == 0

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
            fix_results = self.fix_engine.run_all_fixes()

            # 记录修复结果
            self.report["fix_results"] = {
                "total_fixes": len(fix_results),
                "successful_fixes": sum(1 for r in fix_results.values() if r.status == FixStatus.COMPLETED),
                "failed_fixes": sum(1 for r in fix_results.values() if r.status == FixStatus.FAILED),
                "fixes_details": [
                    {
                        "type": r.fix_type.value,
                        "target": r.target,
                        "status": r.status.value,
                        "message": r.message,
                        "duration": r.get_duration()
                    }
                    for r in fix_results.values()
                ],
                "success": all(r.status == FixStatus.COMPLETED for r in fix_results.values())
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
                print("环境检查失败，但继续执行测试")
                success = self.run_tests()

        elif self.operation_mode == OperationMode.TEST_THEN_FIX:
            # 測試後自動修復
            test_success = self.run_tests()
            if not test_success:
                print("测试失败，开始自动修复...")
                success = self.run_auto_fix()
            else:
                print("测试通过，跳过修复")
                success = True

        elif self.operation_mode == OperationMode.PURE_FIX:
            # 單純自動修復
            success = self.run_auto_fix()

        elif self.operation_mode == OperationMode.FIX_THEN_TEST:
            # 自動修復後自動測試
            fix_success = self.run_auto_fix()
            if fix_success:
                print("修复完成，开始测试...")
                success = self.run_tests()
            else:
                print("修复失败，跳过测试")
                success = False

        # 生成总结报告
        self._generate_summary(success)

        # 保存详细报告
        self._save_detailed_reports()

        return success

    def _map_to_test_scope(self) -> None:
        """映射执行范围到测试范围 - 简化实现"""
        return None

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

    def _generate_summary(self, success: bool) -> None:
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

        print(f"=== 执行总结 ===")
        print(f"操作模式: {summary['operation_mode']}")
        print(f"执行范围: {summary['execution_scope']}")
        if summary['specific_target']:
            print(f"特定目标: {summary['specific_target']}")
        print(f"总体结果: {'✓ 成功' if success else '✗ 失败'}")

        if "test_success" in summary:
            print(f"测试结果: {'✓ 通过' if summary['test_success'] else '✗ 失败'}")

        if "fix_success" in summary:
            print(f"修复结果: {'✓ 成功' if summary['fix_success'] else '✗ 失败'}")

    def save_report(self, report_path: Optional[Path] = None) -> None:
        """保存执行报告"""
        if report_path is None:
            report_path = self.project_root / f"unified_auto_fix_report_{int(time.time())}.json"

        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.report, f, ensure_ascii=False, indent=2)
            print(f"✓ 执行报告已保存到 {report_path}")
        except Exception as e:
            print(f"✗ 保存执行报告时出错: {e}")

    def _save_detailed_reports(self) -> None:
        """保存详细报告 - 使用新架构"""
        try:
            # 由于移除了不存在的组件，跳过生成详细报告的步骤
            pass

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

def main() -> None:
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

        # 执行操作
        success = auto_fix.execute()

        # 保存报告
        report_path = Path(args.report) if args.report else None
        auto_fix.save_report(report_path)

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