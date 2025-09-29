"""
测试覆盖率分析器测试用例
"""

import unittest
import logging
import json
from unittest.mock import Mock, patch, mock_open
from coverage_analyzer import CoverageAnalyzer, CoverageMetrics

# 配置日志
logging.basicConfig(level=logging.INFO)
logger: Any = logging.getLogger(__name__)


class TestCoverageAnalyzer(unittest.TestCase):
    """覆盖率分析器测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.analyzer = CoverageAnalyzer()
        
    def test_init(self) -> None:
        """测试初始化"""
        _ = self.assertEqual(self.analyzer.project_root, ".")
        _ = self.assertEqual(len(self.analyzer.coverage_history), 0)
        _ = self.assertIn("line_coverage", self.analyzer.thresholds)
        _ = self.assertIn("branch_coverage", self.analyzer.thresholds)
        _ = self.assertIn("function_coverage", self.analyzer.thresholds)
        
    def test_set_coverage_thresholds(self) -> None:
        """测试设置覆盖率阈值"""
        # 设置新的阈值
        self.analyzer.set_coverage_thresholds(
            line_threshold=95.0,
            branch_threshold=90.0,
            function_threshold=92.0
        )
        
        # 验证阈值已更新
        _ = self.assertEqual(self.analyzer.thresholds["line_coverage"], 95.0)
        _ = self.assertEqual(self.analyzer.thresholds["branch_coverage"], 90.0)
        _ = self.assertEqual(self.analyzer.thresholds["function_coverage"], 92.0)
        
    def test_parse_coverage_data(self) -> None:
        """测试解析覆盖率数据"""
        # 模拟覆盖率数据
        coverage_data = {
            "totals": {
                "percent_covered": 85.5,
                "num_statements": 1000,
                "covered_lines": 855,
                "num_branches": 200,
                "missing_branches": [1, 2, 3]
            },
            "files": {
                "test_file.py": {
                    "functions": {
                        "func1": {"executed": True},
                        "func2": {"executed": False},
                        "func3": {"executed": True}
                    }
                }
            }
        }
        
        # 解析数据
        metrics = self.analyzer._parse_coverage_data(coverage_data)
        
        # 验证解析结果
        _ = self.assertIsInstance(metrics, CoverageMetrics)
        _ = self.assertEqual(metrics.line_coverage, 85.5)
        _ = self.assertEqual(metrics.total_lines, 1000)
        _ = self.assertEqual(metrics.covered_lines, 855)
        _ = self.assertEqual(metrics.total_branches, 200)
        _ = self.assertEqual(metrics.covered_branches, 197)  # 200 - 3
        _ = self.assertEqual(metrics.branch_coverage, 98.5)  # (197/200)*100
        self.assertAlmostEqual(metrics.function_coverage, 66.67, places=2)  # (2/3)*100，四舍五入到小数点后两位
        _ = self.assertIsNotNone(metrics.timestamp)
        
    def test_estimate_function_coverage(self) -> None:
        """测试估算函数覆盖率"""
        # 模拟文件覆盖率数据
        coverage_data = {
            "files": {
                "file1.py": {
                    "functions": {
                        "func1": {"executed": True},
                        "func2": {"executed": True},
                        "func3": {"executed": False}
                    }
                },
                "file2.py": {
                    "functions": {
                        "func4": {"executed": True},
                        "func5": {"executed": False}
                    }
                }
            }
        }
        
        # 估算函数覆盖率
        function_coverage = self.analyzer._estimate_function_coverage(coverage_data)
        
        # 验证估算结果：5个函数中有3个被覆盖，覆盖率应该是60%
        _ = self.assertEqual(function_coverage, 60.0)
        
    def test_estimate_function_coverage_empty_data(self) -> None:
        """测试估算空数据的函数覆盖率"""
        # 空数据
        coverage_data = {}
        
        # 估算函数覆盖率
        function_coverage = self.analyzer._estimate_function_coverage(coverage_data)
        
        # 验证估算结果：没有函数，覆盖率应该是0%
        _ = self.assertEqual(function_coverage, 0.0)
        
    def test_check_coverage_thresholds(self) -> None:
        """测试检查覆盖率阈值"""
        # 创建测试指标
        metrics = CoverageMetrics()
        metrics.line_coverage = 92.0
        metrics.branch_coverage = 88.0
        metrics.function_coverage = 91.0
        
        # 检查阈值（默认阈值：行覆盖率90%，分支覆盖率85%，函数覆盖率90%）
        results = self.analyzer.check_coverage_thresholds(metrics)
        
        # 验证检查结果
        self.assertTrue(results["line_coverage_ok"])      # 92.0 >= 90.0
        self.assertTrue(results["branch_coverage_ok"])    # 88.0 >= 85.0
        self.assertTrue(results["function_coverage_ok"])  # 91.0 >= 90.0
        
    def test_check_coverage_thresholds_failures(self) -> None:
        """测试检查未通过的覆盖率阈值"""
        # 创建测试指标（低于阈值）
        metrics = CoverageMetrics()
        metrics.line_coverage = 85.0      # 低于默认阈值90.0
        metrics.branch_coverage = 80.0    # 低于默认阈值85.0
        metrics.function_coverage = 88.0  # 低于默认阈值90.0
        
        # 检查阈值
        results = self.analyzer.check_coverage_thresholds(metrics)
        
        # 验证检查结果
        _ = self.assertFalse(results["line_coverage_ok"])
        _ = self.assertFalse(results["branch_coverage_ok"])
        _ = self.assertFalse(results["function_coverage_ok"])
        
    def test_generate_coverage_report(self) -> None:
        """测试生成覆盖率报告"""
        # 创建测试指标
        metrics = CoverageMetrics()
        metrics.line_coverage = 92.5
        metrics.total_lines = 1000
        metrics.covered_lines = 925
        metrics.branch_coverage = 88.0
        metrics.total_branches = 200
        metrics.covered_branches = 176
        metrics.function_coverage = 91.0
        metrics.total_functions = 50
        metrics.covered_functions = 45
        
        # 生成报告
        report = self.analyzer.generate_coverage_report(metrics)
        
        # 验证报告内容
        _ = self.assertIn("覆盖率分析报告", report)
        _ = self.assertIn(f"行覆盖率: {metrics.line_coverage:.2f}%", report)
        _ = self.assertIn(f"分支覆盖率: {metrics.branch_coverage:.2f}%", report)
        _ = self.assertIn(f"函数覆盖率: {metrics.function_coverage:.2f}%", report)
        _ = self.assertIn("通过", report)  # 所有指标都应通过默认阈值
        
    def test_get_coverage_trend(self) -> None:
        """测试获取覆盖率趋势"""
        # 添加一些历史数据
        for i in range(5):
            metrics = CoverageMetrics()
            metrics.line_coverage = 80.0 + i * 2  # 80, 82, 84, 86, 88
            metrics.timestamp = metrics.timestamp.replace(second=i)  # 确保时间戳不同
            _ = self.analyzer.coverage_history.append(metrics)
            
        # 获取趋势数据（默认限制10个）
        trend = self.analyzer.get_coverage_trend()
        _ = self.assertEqual(len(trend), 5)
        
        # 获取趋势数据（限制3个）
        trend_limited = self.analyzer.get_coverage_trend(limit=3)
        _ = self.assertEqual(len(trend_limited), 3)
        # 验证是最近的3个数据点
        _ = self.assertEqual(trend_limited[0].line_coverage, 84.0)
        _ = self.assertEqual(trend_limited[1].line_coverage, 86.0)
        _ = self.assertEqual(trend_limited[2].line_coverage, 88.0)
        
    def test_get_coverage_trend_empty(self) -> None:
        """测试获取空的覆盖率趋势"""
        # 获取趋势数据（没有历史数据）
        trend = self.analyzer.get_coverage_trend()
        _ = self.assertEqual(len(trend), 0)


class TestCoverageAnalyzerIntegration(unittest.TestCase):
    """覆盖率分析器集成测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.analyzer = CoverageAnalyzer()
        
    _ = @patch('subprocess.run')
    def test_run_coverage_analysis_success(self, mock_subprocess_run) -> None:
        """测试成功运行覆盖率分析"""
        # 模拟subprocess.run的返回值
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Coverage analysis completed"
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result
        
        # 模拟_coverage_data文件
        mock_coverage_data = {
            "totals": {
                "percent_covered": 90.0,
                "num_statements": 100,
                "covered_lines": 90
            }
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_coverage_data))) as mock_file:
            with patch('os.path.exists', return_value=True):
                with patch('os.remove'):
                    # 运行覆盖率分析
                    metrics = self.analyzer.run_coverage_analysis()
                    
                    # 验证结果
                    _ = self.assertIsNotNone(metrics)
                    _ = self.assertEqual(metrics.line_coverage, 90.0)
                    
                    # 验证调用了正确的命令
                    _ = self.assertEqual(mock_subprocess_run.call_count, 2)  # run和json两个命令
                    
    _ = @patch('subprocess.run')
    def test_run_coverage_analysis_failure(self, mock_subprocess_run) -> None:
        """测试运行覆盖率分析失败"""
        # 模拟subprocess.run返回错误
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error occurred"
        mock_subprocess_run.return_value = mock_result
        
        # 运行覆盖率分析
        metrics = self.analyzer.run_coverage_analysis()
        
        # 验证结果为None
        _ = self.assertIsNone(metrics)
        
    _ = @patch('subprocess.run')
    def test_generate_coverage_report_failure(self, mock_subprocess_run) -> None:
        """测试生成覆盖率报告失败"""
        # 模拟第一个命令成功，第二个命令失败
        def side_effect(*args, **kwargs):
            if 'json' in args[0]:
                # json命令失败
                mock_result = Mock()
                mock_result.returncode = 1
                mock_result.stdout = ""
                mock_result.stderr = "JSON generation failed"
                return mock_result
            else:
                # run命令成功
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = "Coverage analysis completed"
                mock_result.stderr = ""
                return mock_result
                
        mock_subprocess_run.side_effect = side_effect
        
        # 运行覆盖率分析
        metrics = self.analyzer.run_coverage_analysis()
        
        # 验证结果为None
        _ = self.assertIsNone(metrics)


if __name__ == "__main__":
    _ = unittest.main()