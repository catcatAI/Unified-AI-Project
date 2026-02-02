"""
Angela AI v6.0 - Integration Test Runner
整合测试运行器

运行所有整合测试并生成综合报告。

Usage:
    python run_integration_tests.py [--full] [--quick] [--report]

Options:
    --full    运行完整的测试套件（包括慢测试）
    --quick   只运行快速测试
    --report  生成详细的HTML报告

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

import subprocess
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.backend_dir = self.test_dir.parent.parent
        self.results = {}
        
    def discover_tests(self):
        """发现所有测试文件"""
        test_files = [
            'test_full_system_integration.py',
            'test_end_to_end_scenarios.py',
            'test_performance_benchmarks.py',
            'test_error_recovery.py',
            'test_digital_life_compliance.py',
        ]
        return [self.test_dir / f for f in test_files]
    
    def run_test_file(self, test_file: Path, markers: str = None):
        """运行单个测试文件"""
        print(f"\n{'='*70}")
        print(f"Running: {test_file.name}")
        print(f"{'='*70}")
        
        cmd = [
            sys.executable, '-m', 'pytest',
            str(test_file),
            '-v',
            '--tb=short',
        ]
        
        if markers:
            cmd.extend(['-m', markers])
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.backend_dir,
                capture_output=False,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error running {test_file.name}: {e}")
            return False
    
    def run_all_tests(self, full: bool = False, quick: bool = False):
        """运行所有测试"""
        print(f"\n{'='*70}")
        print(f"ANGELA AI v6.0 - COMPREHENSIVE INTEGRATION TEST SUITE")
        print(f"{'='*70}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test Directory: {self.test_dir}")
        print(f"{'='*70}\n")
        
        test_files = self.discover_tests()
        
        markers = None
        if quick:
            markers = 'not slow'
        elif not full:
            markers = 'not slow'
        
        passed = 0
        failed = 0
        
        for test_file in test_files:
            if test_file.exists():
                success = self.run_test_file(test_file, markers)
                self.results[test_file.name] = 'PASSED' if success else 'FAILED'
                if success:
                    passed += 1
                else:
                    failed += 1
            else:
                print(f"Warning: {test_file.name} not found")
                self.results[test_file.name] = 'NOT_FOUND'
                failed += 1
        
        return passed, failed
    
    def generate_report(self):
        """生成测试报告"""
        print(f"\n{'='*70}")
        print(f"TEST EXECUTION SUMMARY")
        print(f"{'='*70}")
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nResults:")
        
        for test_name, result in self.results.items():
            status_icon = '✓' if result == 'PASSED' else '✗' if result == 'FAILED' else '?'
            print(f"  {status_icon} {test_name:45s} : {result}")
        
        passed = sum(1 for r in self.results.values() if r == 'PASSED')
        failed = sum(1 for r in self.results.values() if r == 'FAILED')
        total = len(self.results)
        
        print(f"\n{'='*70}")
        print(f"SUMMARY:")
        print(f"  Total Tests: {total}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Success Rate: {passed/total*100:.1f}%" if total > 0 else "  N/A")
        print(f"{'='*70}")
        
        return passed, failed
    
    def generate_html_report(self, output_file: str = 'integration_test_report.html'):
        """生成HTML报告"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Angela AI v6.0 - Integration Test Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .summary {{
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .test-result {{
            background-color: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .passed {{
            border-left: 5px solid #27ae60;
        }}
        .failed {{
            border-left: 5px solid #e74c3c;
        }}
        .not-found {{
            border-left: 5px solid #f39c12;
        }}
        .metric {{
            display: inline-block;
            margin: 10px 20px 10px 0;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 3px;
        }}
        .status-passed {{ color: #27ae60; font-weight: bold; }}
        .status-failed {{ color: #e74c3c; font-weight: bold; }}
        .status-not-found {{ color: #f39c12; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Angela AI v6.0 - Integration Test Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>Executive Summary</h2>
        <div class="metric">
            <strong>Total Tests:</strong> {len(self.results)}
        </div>
        <div class="metric">
            <strong>Passed:</strong> <span class="status-passed">{sum(1 for r in self.results.values() if r == 'PASSED')}</span>
        </div>
        <div class="metric">
            <strong>Failed:</strong> <span class="status-failed">{sum(1 for r in self.results.values() if r == 'FAILED')}</span>
        </div>
        <div class="metric">
            <strong>Success Rate:</strong> {sum(1 for r in self.results.values() if r == 'PASSED')/len(self.results)*100:.1f}%
        </div>
    </div>
    
    <h2>Test Details</h2>
"""
        
        for test_name, result in self.results.items():
            css_class = 'passed' if result == 'PASSED' else 'failed' if result == 'FAILED' else 'not-found'
            status_class = f"status-{result.lower().replace('_', '-')}"
            
            html_content += f"""
    <div class="test-result {css_class}">
        <h3>{test_name}</h3>
        <p>Status: <span class="{status_class}">{result}</span></p>
    </div>
"""
        
        html_content += """
    <div class="summary" style="margin-top: 40px;">
        <h2>Test Suite Description</h2>
        <ul>
            <li><strong>test_full_system_integration.py</strong> - Complete cognitive cycle, biological system coordination, execution pipeline, memory-learning integration, real-time feedback loop</li>
            <li><strong>test_end_to_end_scenarios.py</strong> - End-to-end user scenarios including touch interaction, conversation, autonomous behavior, and file organization</li>
            <li><strong>test_performance_benchmarks.py</strong> - Performance benchmarks for response time, concurrency, memory usage, CPU usage, and long-running stability</li>
            <li><strong>test_error_recovery.py</strong> - Error recovery tests for component failures, network interruptions, data corruption, and degraded mode operation</li>
            <li><strong>test_digital_life_compliance.py</strong> - Digital life compliance verification including self-awareness, physiological simulation, autonomous decision-making, learning capability, emotional expression, real-time feedback, and life intensity formula</li>
        </ul>
    </div>
</body>
</html>
"""
        
        output_path = self.test_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\nHTML report generated: {output_path}")
        return output_path


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Run Angela AI v6.0 Integration Tests')
    parser.add_argument('--full', action='store_true', help='Run full test suite including slow tests')
    parser.add_argument('--quick', action='store_true', help='Run only quick tests')
    parser.add_argument('--report', action='store_true', help='Generate HTML report')
    parser.add_argument('--list', action='store_true', help='List all test files')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.list:
        print("Test Files:")
        for test_file in runner.discover_tests():
            exists = "✓" if test_file.exists() else "✗"
            print(f"  {exists} {test_file.name}")
        return
    
    # 运行测试
    passed, failed = runner.run_all_tests(full=args.full, quick=args.quick)
    
    # 生成报告
    runner.generate_report()
    
    # 生成HTML报告
    if args.report:
        runner.generate_html_report()
    
    # 返回退出码
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
