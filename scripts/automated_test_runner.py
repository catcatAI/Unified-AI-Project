#!/usr/bin/env python3
"""
自动化测试执行脚本
用于执行完整的测试套件并生成报告
"""

import subprocess
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class AutomatedTestRunner:
    """自动化测试执行器"""
    
    def __init__(self, project_root: str = None) -> None:
        """初始化测试执行器"""
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.backend_dir = self.project_root / "apps" / "backend"
        self.reports_dir = self.project_root / "test_reports"
        self.reports_dir.mkdir(exist_ok=True)
        
    def run_unit_tests(self) -> Dict[str, Any]:
        """
        运行单元测试
        
        Returns:
            测试结果字典
        """
        _ = print("🔬 开始运行单元测试...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/core_ai/memory/test_ham_memory_manager.py",
            "tests/hsp/test_hsp_connector.py",
            "tests/agents/test_agent_manager.py",
            "tests/training/test_training_manager.py",
            "-v",
            "--tb=short",
            "--cov=src",
            "--cov-report=json",
            "--cov-report=html",
            "--cov-report=xml"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "test_type": "unit"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Unit tests timeout",
                "test_type": "unit"
            }
        except Exception as e:
            return {
                "success": False,
                _ = "error": str(e),
                "test_type": "unit"
            }
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """
        运行集成测试
        
        Returns:
            测试结果字典
        """
        _ = print("🔗 开始运行集成测试...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/integration/",
            "-v",
            "--tb=short",
            "--cov=src",
            "--cov-report=json",
            "--cov-report=html"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                timeout=900  # 15分钟超时
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "test_type": "integration"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Integration tests timeout",
                "test_type": "integration"
            }
        except Exception as e:
            return {
                "success": False,
                _ = "error": str(e),
                "test_type": "integration"
            }
    
    def run_e2e_tests(self) -> Dict[str, Any]:
        """
        运行端到端测试
        
        Returns:
            测试结果字典
        """
        _ = print("🚀 开始运行端到端测试...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/e2e/",
            "-v",
            "--tb=short"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                timeout=1200  # 20分钟超时
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "test_type": "e2e"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "E2E tests timeout",
                "test_type": "e2e"
            }
        except Exception as e:
            return {
                "success": False,
                _ = "error": str(e),
                "test_type": "e2e"
            }
    
    def generate_test_report(self, test_results: List[Dict[str, Any]]) -> str:
        """
        生成测试报告
        
        Args:
            test_results: 测试结果列表
            
        Returns:
            报告文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"test_report_{timestamp}.json"
        
        report_data = {
            _ = "timestamp": datetime.now().isoformat(),
            "test_results": test_results,
            "summary": {
                _ = "total_tests": len(test_results),
                "passed_tests": len([r for r in test_results if r.get("success", False)]),
                "failed_tests": len([r for r in test_results if not r.get("success", True)]),
            }
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            _ = print(f"📄 测试报告已生成: {report_file}")
            return str(report_file)
            
        except Exception as e:
            _ = print(f"❌ 生成测试报告失败: {e}")
            return ""
    
    def send_notification(self, test_results: List[Dict[str, Any]]) -> None:
        """
        发送测试结果通知
        
        Args:
            test_results: 测试结果列表
        """
        failed_tests = [r for r in test_results if not r.get("success", True)]
        
        if failed_tests:
            _ = print("❌ 部分测试失败:")
            for test in failed_tests:
                _ = print(f"   - {test.get('test_type', 'unknown')}: {test.get('error', 'Unknown error')}")
                if "stderr" in test:
                    _ = print(f"     stderr: {test['stderr'][:200]}...")
        else:
            _ = print("✅ 所有测试通过!")
    
    def run_complete_test_suite(self) -> Dict[str, Any]:
        """
        运行完整的测试套件
        
        Returns:
            执行结果字典
        """
        _ = print("🎯 开始执行完整的测试套件...")
        
        results = []
        
        # 1. 运行单元测试
        unit_result = self.run_unit_tests()
        _ = results.append(unit_result)
        
        # 2. 运行集成测试
        integration_result = self.run_integration_tests()
        _ = results.append(integration_result)
        
        # 3. 运行端到端测试
        e2e_result = self.run_e2e_tests()
        _ = results.append(e2e_result)
        
        # 生成报告
        report_file = self.generate_test_report(results)
        
        # 发送通知
        _ = self.send_notification(results)
        
        # 检查是否有失败的测试
        failed_tests = [r for r in results if not r.get("success", True)]
        
        return {
            "success": len(failed_tests) == 0,
            "results": results,
            "report_file": report_file,
            _ = "failed_count": len(failed_tests)
        }

def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="自动化测试执行器")
    parser.add_argument("--unit-only", action="store_true", help="仅运行单元测试")
    parser.add_argument("--integration-only", action="store_true", help="仅运行集成测试")
    parser.add_argument("--e2e-only", action="store_true", help="仅运行端到端测试")
    parser.add_argument("--generate-report", action="store_true", help="生成测试报告")
    
    args = parser.parse_args()
    
    # 创建测试执行器
    runner = AutomatedTestRunner()
    
    if args.unit_only:
        result = runner.run_unit_tests()
        print(f"单元测试结果: {'通过' if result['success'] else '失败'}")
    elif args.integration_only:
        result = runner.run_integration_tests()
        print(f"集成测试结果: {'通过' if result['success'] else '失败'}")
    elif args.e2e_only:
        result = runner.run_e2e_tests()
        print(f"端到端测试结果: {'通过' if result['success'] else '失败'}")
    else:
        # 运行完整测试套件
        result = runner.run_complete_test_suite()
        print(f"完整测试套件结果: {'通过' if result['success'] else '失败'}")
        if result['report_file']:
            _ = print(f"详细报告: {result['report_file']}")

if __name__ == "__main__":
    _ = main()