#!/usr/bin/env python3
"""
流程控制模块
协调测试执行器、错误分析器和修复执行器,管理完整的测试-修复流程
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 使用相对导入
# 修复导入路径,这些模块在不同的目录下
from tests.test_runner import TestRunner
from apps.backend.scripts.error_analyzer import ErrorAnalyzer
from apps.backend.scripts.fix_executor import FixExecutor


class WorkflowController:
    def __init__(self) -> None:
        self.test_runner = TestRunner()
        self.error_analyzer = ErrorAnalyzer("test_results/latest_test_results.json")
        self.fix_executor = FixExecutor()
        self.max_iterations = 3  # 最大迭代次数,防止无限循环
    
    def run_workflow(self, pytest_args: Optional[str] = None) -> bool:
        """
        运行完整的测试-修复工作流程
        返回True表示所有测试通过,False表示仍有失败
        """
        print("[WORKFLOW] 启动测试-修复工作流程")
        print("=" * 60)
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n[WORKFLOW] 第 {iteration} 轮迭代")
            print("-" * 40)
            
            # 1. 运行测试
            if not self._run_tests(pytest_args):
                return False
            
            # 2. 分析错误
            errors = self._analyze_errors()
            if not errors:
                print("[WORKFLOW] ✓ 所有测试通过,工作流程完成")
                return True
            
            # 3. 执行修复
            if not self._execute_fixes():
                print("[WORKFLOW] ✗ 修复执行失败")
                return False
            
            # 等待一段时间再继续下一轮
            print("[WORKFLOW] 等待修复生效...")
            time.sleep(2)
        
        print(f"[WORKFLOW] ✗ 达到最大迭代次数 ({self.max_iterations}),仍有测试失败")
        return False
    
    def _run_tests(self, pytest_args: Optional[str] = None) -> bool:
        """运行测试"""
        print("[WORKFLOW] 步骤 1, 运行测试")
        # 将字符串参数转换为列表
        test_paths: List[str] = [pytest_args] if pytest_args else []
        test_results = self.test_runner.run_tests(test_paths if test_paths else [])
        # 如果测试通过,直接返回,
        if test_results.get("exit_code", -1) == 0:
            print("[WORKFLOW] ✓ 测试通过,无需进一步处理")
            return False  # 返回False表示不需要继续流程
        
        print("[WORKFLOW] ✗ 测试失败,继续错误分析")
        return True
    
    def _analyze_errors(self) -> List[Dict[str, Any]]:
        """分析错误"""
        print("[WORKFLOW] 步骤 2, 分析测试错误")
        report = self.error_analyzer.generate_error_report()
        
        print(f"[WORKFLOW] 发现 {report.get('total_errors', 0)} 个错误")
        for error_type, count in report.get('errors_by_type', {}).items():
            print(f"  {error_type}: {count}")
        
        # 保存错误报告
        self.error_analyzer.save_error_report()
        print("[WORKFLOW] 错误分析完成")
        
        return report.get('error_details', [])
    
    def _execute_fixes(self) -> bool:
        """执行修复"""
        print("[WORKFLOW] 步骤 3, 执行自动修复")
        success = self.fix_executor.execute_fixes()
        
        if success:
            print("[WORKFLOW] ✓ 自动修复执行完成")
        else:
            print("[WORKFLOW] ✗ 自动修复执行失败")
        
        return success
    
    def run_in_separate_terminals(self, pytest_args: Optional[str] = None) -> bool:
        """
        在不同终端中运行测试和修复
        使用PowerShell启动并行任务
        """
        print("[WORKFLOW] 在不同终端中运行测试和修复流程")
        
        # 创建PowerShell脚本来启动并行任务
        ps_script = f"""
# 测试-修复工作流程启动脚本
$projectRoot = "{Path(__file__).parent.parent.parent.parent}"

# 启动测试终端
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$projectRoot'; Write-Host '[TERMINAL 1] 测试执行终端' -ForegroundColor Green; python scripts/test_runner.py {pytest_args or ''}"
)

# 等待测试启动
Start-Sleep -Seconds 2

# 启动分析和修复终端
Start-Process powershell -ArgumentList @(
    "-NoExit", 
    "-Command",
    "Set-Location '$projectRoot'; Write-Host '[TERMINAL 2] 错误分析和修复终端' -ForegroundColor Yellow; Write-Host '等待测试结果...' -ForegroundColor Cyan; while($true) {{ if(Test-Path 'test_results.json') {{ python scripts/error_analyzer.py; if((Get-Content 'error_report.json' | ConvertFrom-Json).total_errors -gt 0) {{ python scripts/fix_executor.py }} }}; Start-Sleep -Seconds 5 }}"
)
"""
        
        # 保存脚本到临时文件
        script_path = Path(__file__).parent / "start_workflow.ps1"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(ps_script)
        
        # 执行脚本
        try:
            subprocess.run([
                "powershell", 
                "-ExecutionPolicy", "Bypass", 
                "-File", str(script_path)
            ], check=True)
            
            print("[WORKFLOW] 并行终端已启动")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[WORKFLOW] 启动并行终端时出错: {e}")
            return False


def main() -> None:
    controller = WorkflowController()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--separate-terminals":
            # 在不同终端中运行
            pytest_args = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
            controller.run_in_separate_terminals(pytest_args)
        else:
            # 正常运行工作流程
            pytest_args = " ".join(sys.argv[1:]) if sys.argv[1:] else None
            success = controller.run_workflow(pytest_args)
            sys.exit(0 if success else 1)
    else:
        # 默认运行工作流程
        success = controller.run_workflow()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()