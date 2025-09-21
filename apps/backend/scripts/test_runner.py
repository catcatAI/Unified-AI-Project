#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行器
用于执行测试套件并生成结果报告
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestRunner:
    """测试运行器"""
    
    def __init__(self, results_dir: str = "test_results"):
        """
        初始化测试运行器
        
        Args:
            results_dir: 测试结果目录
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
    
    def run_tests(self, test_paths: List[str] = None, extra_args: List[str] = None) -> Dict[str, Any]:
        """
        运行测试套件
        
        Args:
            test_paths: 测试路径列表
            extra_args: 额外的pytest参数
            
        Returns:
            测试结果
        """
        # 构建命令
        cmd = [sys.executable, "-m", "pytest"]
        
        if test_paths:
            cmd.extend(test_paths)
        else:
            cmd.append(".")
        
        if extra_args:
            cmd.extend(extra_args)
        
        # 添加默认参数
        cmd.extend([
            "--tb=short",
            "--json-report",
            "--json-report-file=latest_test_results.json",
            "-v"
        ])
        
        logger.info(f"运行测试命令: {' '.join(cmd)}")
        
        try:
            # 运行测试
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
            
            # 解析结果
            test_results = {
                "command": " ".join(cmd),
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
            
            # 保存结果
            self._save_test_results(test_results)
            
            return test_results
        except Exception as e:
            logger.error(f"运行测试失败: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _save_test_results(self, results: Dict[str, Any]):
        """
        保存测试结果
        
        Args:
            results: 测试结果
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{timestamp}.json"
            
            with open(self.results_dir / filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 同时保存为最新结果
            with open(self.results_dir / "latest_test_results.json", 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"测试结果已保存到: {self.results_dir / filename}")
        except Exception as e:
            logger.error(f"保存测试结果失败: {e}")
    
    def get_test_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        从测试结果中提取摘要信息
        
        Args:
            results: 测试结果
            
        Returns:
            测试摘要
        """
        # 这里应该解析stdout来提取测试统计信息
        # 简化实现，实际应该更复杂
        stdout = results.get('stdout', '')
        
        # 简单的统计提取
        lines = stdout.split('\n')
        summary_line = None
        for line in lines:
            if 'passed' in line and 'failed' in line:
                summary_line = line
                break
        
        return {
            "raw_summary": summary_line,
            "exit_code": results.get('exit_code', -1),
            "timestamp": results.get('timestamp')
        }


# 添加pytest标记，防止被误认为测试类
TestRunner.__test__ = False


def main():
    """主函数"""
    runner = TestRunner()
    
    # 示例使用方式
    # 运行所有测试
    # results = runner.run_tests()
    
    # 运行特定测试
    # results = runner.run_tests(["tests/unit"], ["-x", "--tb=short"])
    
    # 获取测试摘要
    # summary = runner.get_test_summary(results)
    
    logger.info("测试运行器已准备就绪")

if __name__ == "__main__":
    main()