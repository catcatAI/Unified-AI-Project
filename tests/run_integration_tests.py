#!/usr/bin/env python3
"""
集成测试运行脚本
用于执行系统集成测试并生成报告
"""

import os
import sys
import argparse
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path


def run_command(command, cwd=None, capture_output=True):
    """
    运行命令并返回结果
    
    Args:
        command: 要执行的命令
        cwd: 工作目录
        capture_output: 是否捕获输出
        
    Returns:
        subprocess.CompletedProcess: 命令执行结果
    """
    print(f"Executing: {' '.join(command) if isinstance(command, list) else command}")
    
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            check=False
        )
        
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
            
        return result
    except Exception as e:
        print(f"Error executing command: {e}")
        return None


def setup_test_environment() -> None:
    """
    设置测试环境
    
    Returns:
        bool: 环境设置是否成功
    """
    print("Setting up test environment...")
    
    # 确保在正确的目录中
    project_root: str = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    # 安装测试依赖
    print("Installing test dependencies...")
    result = run_command([sys.executable, "-m", "pip", "install", "-e", ".[test]"])
    if result and result.returncode != 0:
        print("Warning: Failed to install test dependencies")
    
    # 检查pytest是否可用
    result = run_command([sys.executable, "-m", "pytest", "--version"])
    if not result or result.returncode != 0:
        print("Installing pytest...")
        run_command([sys.executable, "-m", "pip", "install", "pytest"])
    
    return True


def run_integration_tests(test_type="all", markers=None, parallel=False) -> None:
    """
    运行集成测试
    
    Args:
        test_type: 测试类型 (all, system, performance, specific_module)
        markers: pytest标记
        parallel: 是否并行执行
        
    Returns:
        dict: 测试结果
    """
    print(f"Running integration tests (type: {test_type})...")
    
    # 构建pytest命令
    cmd = [sys.executable, "-m", "pytest"]
    
    # 设置测试路径
    if test_type == "all":
        cmd.extend(["tests/integration/", "-v"])
    elif test_type == "system":
        cmd.extend(["tests/integration/test_system_level_integration.py", "-v"])
    elif test_type == "performance":
        cmd.extend(["tests/integration/test_performance_benchmark.py", "-v"])
    else:
        # 特定模块测试
        cmd.extend([f"tests/integration/test_{test_type}_integration.py", "-v"])
    
    # 添加标记
    if markers:
        cmd.extend(["-m", markers])
    
    # 添加并行执行选项
    if parallel:
        cmd.extend(["-n", "auto"])
    
    # 添加覆盖率选项
    cmd.extend(["--cov=src", "--cov-report=html:coverage_html", "--cov-report=xml:coverage.xml"])
    
    # 添加JUnit XML报告
    cmd.extend(["--junitxml=test_results.xml"])
    
    # 执行测试
    start_time = time.time()
    result = run_command(cmd)
    end_time = time.time()
    
    # 解析结果
    test_result = {
        "success": result is not None and result.returncode == 0,
        "return_code": result.returncode if result else -1,
        "execution_time": end_time - start_time,
        "stdout": result.stdout if result else "",
        "stderr": result.stderr if result else ""
    }
    
    return test_result


def generate_test_report(test_results, output_dir="test_reports") -> None:
    """
    生成测试报告
    
    Args:
        test_results: 测试结果
        output_dir: 输出目录
    """
    print("Generating test report...")
    
    # 创建输出目录
    Path(output_dir).mkdir(exist_ok=True)
    
    # 生成JSON报告
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "test_results": test_results,
        "summary": {
            "total_tests": "N/A",
            "passed": "N/A",
            "failed": "N/A",
            "execution_time": test_results.get("execution_time", 0)
        }
    }
    
    report_file = Path(output_dir) / f"integration_test_report_{int(time.time())}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"Test report saved to: {report_file}")
    
    # 打印摘要
    print("\n" + "="*50)
    print("INTEGRATION TEST SUMMARY")
    print("="*50)
    print(f"Execution Time: {test_results.get('execution_time', 0):.2f} seconds")
    print(f"Status: {'PASSED' if test_results.get('success', False) else 'FAILED'}")
    print(f"Return Code: {test_results.get('return_code', 'N/A')}")
    print("="*50)


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="Run integration tests for Unified AI Project")
    parser.add_argument(
        "--type",
        choices=["all", "system", "performance", "agent", "hsp", "memory", "training", "core"],
        default="all",
        help="Type of integration tests to run"
    )
    parser.add_argument(
        "--markers",
        help="pytest markers to filter tests"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    parser.add_argument(
        "--no-setup",
        action="store_true",
        help="Skip environment setup"
    )
    
    args = parser.parse_args()
    
    print("Unified AI Project Integration Test Runner")
    print("="*50)
    
    # 设置测试环境
    if not args.no_setup:
        if not setup_test_environment():
            print("Failed to setup test environment")
            return 1
    
    # 运行集成测试
    test_results = run_integration_tests(
        test_type=args.type,
        markers=args.markers,
        parallel=args.parallel
    )
    
    # 生成测试报告
    generate_test_report(test_results)
    
    # 返回执行结果
    return 0 if test_results.get("success", False) else 1


if __name__ == "__main__":
    sys.exit(main())