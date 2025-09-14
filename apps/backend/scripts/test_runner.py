#!/usr/bin/env python3
"""
独立的测试执行模块
负责运行测试并收集结果，将结果保存到文件中供后续分析
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class TestRunner:
    def __init__(self, output_file: str = "test_results.json"):
        self.output_file = output_file
        self.project_root = Path(__file__).parent.parent
    
    def run_tests(self, pytest_args: Optional[str] = None) -> Dict[str, Any]:
        """运行测试并生成结果文件"""
        print("[TEST] 开始运行测试套件")
        print("=" * 50)
        
        # 构建命令
        cmd = [sys.executable, "-m", "pytest", "--tb=short", "-v"]
        if pytest_args:
            cmd.extend(pytest_args.split())
        
        # 执行测试
        try:
            process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            # 分析结果
            test_results = {
                "exit_code": process.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "timestamp": str(datetime.now())
            }
            
            # 保存结果到文件
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(test_results, f, ensure_ascii=False, indent=2)
            
            # 输出测试结果到终端
            print(stdout)
            if stderr:
                print(stderr, file=sys.stderr)
            
            print("=" * 50)
            print(f"[TEST] 测试完成，退出码: {process.returncode}")
            
            return test_results
            
        except Exception as e:
            error_result = {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "timestamp": str(datetime.now())
            }
            
            # 保存错误结果到文件
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(error_result, f, ensure_ascii=False, indent=2)
            
            print(f"[TEST] 运行测试时发生错误: {e}", file=sys.stderr)
            return error_result


if __name__ == "__main__":
    # 可以直接运行测试
    runner = TestRunner()
    
    # 获取命令行参数（如果有）
    args = sys.argv[1] if len(sys.argv) > 1 else None
    
    runner.run_tests(args)