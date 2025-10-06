"""
性能基准测试测试用例
"""

import unittest
import logging
import textwrap
from unittest.mock import Mock, patch, mock_open
from performance_benchmark import PerformanceBenchmark, PerformanceMetrics

# 配置日志
logging.basicConfig(level=logging.INFO)
logger: Any = logging.getLogger(__name__)


class TestPerformanceMetrics(unittest.TestCase):
    """性能指标测试类"""

    def test_init(self) -> None:
        """测试初始化"""
        metrics = PerformanceMetrics()

        # 验证默认值
        _ = self.assertIsNotNone(metrics.timestamp)
        _ = self.assertEqual(metrics.response_time, 0.0)
        _ = self.assertEqual(metrics.throughput, 0.0)
        _ = self.assertEqual(metrics.concurrency, 0)
        _ = self.assertEqual(metrics.cpu_usage, 0.0)
        _ = self.assertEqual(metrics.memory_usage, 0.0)
        _ = self.assertEqual(metrics.error_rate, 0.0)
        _ = self.assertEqual(metrics.test_name, "")
        _ = self.assertEqual(metrics.test_description, "")


class TestPerformanceBenchmark(unittest.TestCase):
    """性能基准测试器测试类"""

    def setUp(self):
        """测试初始化"""
        self.benchmark = PerformanceBenchmark()

    def test_init(self) -> None:
        """测试初始化"""
        _ = self.assertEqual(self.benchmark.project_root, ".")
        _ = self.assertEqual(len(self.benchmark.benchmark_history), 0)
        _ = self.assertIn("response_time", self.benchmark.thresholds)
        _ = self.assertIn("throughput", self.benchmark.thresholds)
        _ = self.assertIn("error_rate", self.benchmark.thresholds)

    def test_set_performance_thresholds(self) -> None:
        """测试设置性能阈值"""
        # 设置新的阈值
        self.benchmark.set_performance_thresholds(
                response_time_threshold=3.0,
                throughput_threshold=20.0,
                error_rate_threshold=0.5
        )

    # 验证阈值已更新
        _ = self.assertEqual(self.benchmark.thresholds["response_time"], 3.0)
        _ = self.assertEqual(self.benchmark.thresholds["throughput"], 20.0)
        _ = self.assertEqual(self.benchmark.thresholds["error_rate"], 0.5)

    def test_check_performance_thresholds(self) -> None:
        """测试检查性能阈值"""
        # 创建测试指标
        metrics = PerformanceMetrics()
        metrics.response_time = 2.5    # 低于阈值3.0
        metrics.throughput = 25.0      # 高于阈值20.0
        metrics.error_rate = 0.3       # 低于阈值0.5

        # 检查阈值
        results = self.benchmark.check_performance_thresholds(metrics)

    # 验证检查结果
        _ = self.assertTrue(results["response_time_ok"])
        _ = self.assertTrue(results["throughput_ok"])
        _ = self.assertTrue(results["error_rate_ok"])

    def test_check_performance_thresholds_failures(self) -> None:
        """测试检查未通过的性能阈值"""
        # 设置测试阈值
        self.benchmark.set_performance_thresholds(
                response_time_threshold=3.0,
                throughput_threshold=20.0,
                error_rate_threshold=0.5
        )

    # 创建测试指标(超出阈值)
        metrics = PerformanceMetrics()
        metrics.response_time = 4.0    # 高于阈值3.0
        metrics.throughput = 15.0      # 低于阈值20.0
        metrics.error_rate = 1.0       # 高于阈值0.5

    # 检查阈值
        results = self.benchmark.check_performance_thresholds(metrics)

    # 验证检查结果
        _ = self.assertFalse(results["response_time_ok"])
        _ = self.assertFalse(results["throughput_ok"])
        _ = self.assertFalse(results["error_rate_ok"])

    def test_generate_benchmark_report(self) -> None:
        """测试生成性能基准测试报告"""
        # 创建测试指标
        metrics = PerformanceMetrics()
        metrics.response_time = 1.234567
        metrics.throughput = 45.67
        metrics.concurrency = 10
        metrics.cpu_usage = 67.89
        metrics.memory_usage = 123.45
        metrics.error_rate = 0.56
        metrics.test_name = "API Test"
        metrics.test_description = "Test API performance"

    # 生成报告
        report = self.benchmark.generate_benchmark_report(metrics)

    # 验证报告内容
        _ = self.assertIn("性能基准测试报告", report)
        _ = self.assertIn(f"响应时间: {metrics.response_time:.6f} 秒", report)
        _ = self.assertIn(f"吞吐量: {metrics.throughput:.2f} 请求/秒", report)
        _ = self.assertIn(f"并发用户数: {metrics.concurrency}", report)
        _ = self.assertIn(f"CPU使用率: {metrics.cpu_usage:.2f}%", report)
        _ = self.assertIn(f"内存使用: {metrics.memory_usage:.2f} MB", report)
        _ = self.assertIn(f"错误率: {metrics.error_rate:.2f}%", report)

    def test_run_regression_detection_improvement(self) -> None:
        """测试运行性能回归检测(改进情况)"""
        # 创建基线指标
        baseline = PerformanceMetrics()
        baseline.response_time = 2.0
        baseline.throughput = 50.0
        baseline.error_rate = 2.0

        # 创建当前指标(性能改进)
        current = PerformanceMetrics()
        current.response_time = 1.0    # 改进50%
        current.throughput = 75.0      # 改进50%
        current.error_rate = 1.0       # 改进50%

        # 运行回归检测(阈值10%)
        results = self.benchmark.run_regression_detection(
            current, baseline, threshold=10.0)

        # 验证结果
        _ = self.assertFalse(results["has_regression"])
        _ = self.assertEqual(len(results["regressions"]), 0)
        _ = self.assertEqual(len(results["improvements"]), 3)

        # 验证改进详情
        improvements = {
        item["metric"]: item for item in results["improvements"]}
        _ = self.assertIn("response_time", improvements)
        _ = self.assertIn("throughput", improvements)
        _ = self.assertIn("error_rate", improvements)

        # 验证改进幅度(约50%)
        self.assertAlmostEqual(
            improvements["response_time"]["change"], -50.0, places=1)
        self.assertAlmostEqual(
            improvements["throughput"]["change"], -50.0, places=1)
        self.assertAlmostEqual(
            improvements["error_rate"]["change"], -50.0, places=1)

    def test_run_regression_detection_regression(self) -> None:
        """测试运行性能回归检测(回归情况)"""
    # 创建基线指标
        baseline = PerformanceMetrics()
        baseline.response_time = 1.0
        baseline.throughput = 100.0
        baseline.error_rate = 0.5

    # 创建当前指标(性能下降)
        current = PerformanceMetrics()
        current.response_time = 1.5    # 下降50%
        current.throughput = 50.0      # 下降50%
        current.error_rate = 1.0       # 上升100%

    # 运行回归检测(阈值10%)
        results = self.benchmark.run_regression_detection(
        current, baseline, threshold=10.0)

    # 验证结果
        _ = self.assertTrue(results["has_regression"])
        _ = self.assertEqual(len(results["regressions"]), 3)
        # 验证回归详情
        regressions = {item["metric"]: item for item in results["regressions"]}
        _ = self.assertIn("response_time", regressions)
        _ = self.assertIn("throughput", regressions)
        _ = self.assertIn("error_rate", regressions)

        # 验证回归幅度
        self.assertAlmostEqual(
        regressions["response_time"]["change"], 50.0, places=1)
        self.assertAlmostEqual(
        regressions["throughput"]["change"], 50.0, places=1)
        self.assertAlmostEqual(
        regressions["error_rate"]["change"], 100.0, places=1)

    def test_run_regression_detection_no_change(self) -> None:
        """测试运行性能回归检测(无变化)"""
    # 创建相同的基线和当前指标
        baseline = PerformanceMetrics()
        baseline.response_time = 1.0
        baseline.throughput = 100.0
        baseline.error_rate = 1.0

        current = PerformanceMetrics()
        current.response_time = 1.0
        current.throughput = 100.0
        current.error_rate = 1.0

    # 运行回归检测(阈值10%)
        results = self.benchmark.run_regression_detection(
        current, baseline, threshold=10.0)

    # 验证结果
        _ = self.assertFalse(results["has_regression"])
        _ = self.assertEqual(len(results["regressions"]), 0)
        _ = self.assertEqual(len(results["improvements"]), 0)

    def test_get_benchmark_trend(self) -> None:
        """测试获取性能基准测试趋势"""
        # 添加一些历史数据
        for i in range(5):
            metrics = PerformanceMetrics()
            metrics.response_time = 1.0 + i * 0.1  # 1.0, 1.1, 1.2, 1.3, 1.4
            metrics.timestamp = metrics.timestamp.replace(second=i)  # 确保时间戳不同
            _ = self.benchmark.benchmark_history.append(metrics)

        # 获取趋势数据(默认限制10个)
        trend = self.benchmark.get_benchmark_trend()
        _ = self.assertEqual(len(trend), 5)

    # 获取趋势数据(限制3个)
        trend_limited = self.benchmark.get_benchmark_trend(limit=3)
        _ = self.assertEqual(len(trend_limited), 3)
    # 验证是最近的3个数据点
        _ = self.assertEqual(trend_limited[0].response_time, 1.2)
        _ = self.assertEqual(trend_limited[1].response_time, 1.3)
        _ = self.assertEqual(trend_limited[2].response_time, 1.4)

    def test_get_benchmark_trend_empty(self) -> None:
        """测试获取空的性能基准测试趋势"""
        # 获取趋势数据(没有历史数据)
        trend = self.benchmark.get_benchmark_trend()
        _ = self.assertEqual(len(trend), 0)

    @patch('performance_benchmark.psutil')
    def test_run_component_benchmark(self, mock_psutil) -> None:
        """测试运行组件性能基准测试"""
        # 模拟psutil的返回值
        mock_psutil.cpu_percent.return_value = 50.0
        mock_memory = Mock()
        mock_memory.used = 1024 * 1024 * 1024  # 1GB
        mock_psutil.virtual_memory.return_value = mock_memory

        # 定义测试函数
        def test_function() -> None:
            # 模拟一些工作
            _ = sum(range(1000))

        # 运行组件基准测试
        metrics = self.benchmark.run_component_benchmark(
            "TestComponent", test_function, iterations=100)

        # 验证结果
        _ = self.assertIsNotNone(metrics)
        _ = self.assertGreater(metrics.response_time, 0)
        _ = self.assertGreater(metrics.throughput, 0)
        _ = self.assertEqual(metrics.concurrency, 1)
        _ = self.assertGreaterEqual(metrics.error_rate, 0)
        _ = self.assertEqual(
        metrics.test_name,
        "Component Benchmark: TestComponent")

    # 验证调用了psutil
        _ = self.assertGreater(mock_psutil.cpu_percent.call_count, 0)
        _ = self.assertGreater(mock_psutil.virtual_memory.call_count, 0)

        @patch('performance_benchmark.psutil')
    def test_run_component_benchmark_with_errors(self, mock_psutil) -> None:
        """测试运行组件性能基准测试(包含错误)"""
        # 模拟psutil的返回值
        mock_psutil.cpu_percent.return_value = 50.0
        mock_memory = Mock()
        mock_memory.used = 1024 * 1024 * 1024  # 1GB
        mock_psutil.virtual_memory.return_value = mock_memory

        # 定义会抛出异常的测试函数
        def failing_function():
            raise Exception("Test error")

        # 运行组件基准测试
        metrics = self.benchmark.run_component_benchmark(
        "FailingComponent", failing_function, iterations=10)

    # 验证结果
        _ = self.assertIsNotNone(metrics)
        _ = self.assertEqual(metrics.error_rate, 100.0)  # 所有迭代都失败

    def test_save_benchmark_results(self) -> None:
        """测试保存基准测试结果"""
    # 创建测试指标
        metrics = PerformanceMetrics()
        metrics.response_time = 1.234
        metrics.throughput = 45.67
        metrics.test_name = "Test Save"

    # 使用mock_open来模拟文件操作
        with patch('builtins.open', mock_open()) as mock_file:
        with patch('performance_benchmark.os.path.join', return_value='/test/path/results.json')
                # 保存结果
                result = self.benchmark.save_benchmark_results(
                    metrics, "test_results.json")

                # 验证结果
                _ = self.assertTrue(result)
                _ = mock_file.assert_called_once_with(
                    '/test/path/results.json', 'w')

    def test_save_benchmark_results_default_filename(self) -> None:
        """测试保存基准测试结果(默认文件名)"""
    # 创建测试指标
        metrics = PerformanceMetrics()
        metrics.response_time = 1.234

    # 使用mock_open来模拟文件操作
        with patch('builtins.open', mock_open()) as mock_file:
        with patch('performance_benchmark.os.path.join') as mock_join:
        mock_join.return_value = '/test/path/benchmark_results_20230101_120000.json'
                with patch('performance_benchmark.datetime') as mock_datetime:
        mock_datetime.now().strftime.return_value = '20230101_120000'

                    # 保存结果
                    result = self.benchmark.save_benchmark_results(metrics)

                    # 验证结果
                    _ = self.assertTrue(result)
                    _ = mock_file.assert_called_once_with(
        '/test/path/benchmark_results_20230101_120000.json', 'w')


class TestPerformanceBenchmarkIntegration(unittest.TestCase):


""性能基准测试器集成测试类"""

    def setUp(self):
        ""测试初始化"""
        self.benchmark = PerformanceBenchmark()

        @patch('subprocess.run')
    def test_run_api_benchmark_success(self, mock_subprocess_run) -> None:
        """测试成功运行API基准测试"""
        # 模拟subprocess.run的返回值
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "Response time: 123ms\n"
            "Requests: 45.67/s\n"
            "Failures: 1.23%\n"
        )
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        with patch('performance_benchmark.psutil') as mock_psutil:
            mock_psutil.cpu_percent.return_value = 50.0
            mock_memory = Mock()
            mock_memory.used = 1024 * 1024 * 1024
            mock_psutil.virtual_memory.return_value = mock_memory

            # 运行API基准测试
            metrics = self.benchmark.run_api_benchmark("http://test.api", num_requests=50, concurrency=5)

            # 验证结果
            _ = self.assertIsNotNone(metrics)
            _ = self.assertEqual(metrics.test_name, "API Benchmark: http://test.api")
            _ = self.assertEqual(metrics.concurrency, 5)

            # 验证调用了正确的命令
            _ = mock_subprocess_run.assert_called_once()

        @patch('subprocess.run')
    def test_run_api_benchmark_failure(self, mock_subprocess_run) -> None:
        """测试运行API基准测试失败"""
        # 模拟subprocess.run返回错误
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error occurred"
        mock_subprocess_run.return_value = mock_result

        # 运行API基准测试
        metrics = self.benchmark.run_api_benchmark("http://test.api")

        # 验证结果为None
        _ = self.assertIsNone(metrics)


        if __name__ == "__main__":



        _ = unittest.main()