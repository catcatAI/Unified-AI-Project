"""
性能基准测试实现
基于SYSTEM_INTEGRATION_TEST_ENHANCEMENT_PLAN.md设计文档
"""

import logging
import time
import psutil
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import json
import os

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """性能指标"""
    
    def __init__(self) -> None:
        self.timestamp: datetime = datetime.now()  # 时间戳
        self.response_time: float = 0.0  # 响应时间(秒)
        self.throughput: float = 0.0  # 吞吐量(请求/秒)
        self.concurrency: int = 0  # 并发用户数
        self.cpu_usage: float = 0.0  # CPU使用率(%)
        self.memory_usage: float = 0.0  # 内存使用率(MB)
        self.error_rate: float = 0.0  # 错误率(%)
        self.test_name: str = ""  # 测试名称
        self.test_description: str = ""  # 测试描述


class PerformanceBenchmark:
    """性能基准测试器"""
    
    def __init__(self, project_root: str = ".") -> None:
        self.project_root = project_root
        self.benchmark_history: List[PerformanceMetrics] = []
        self.thresholds: Dict[str, float] = {
            "response_time": 5.0,  # 响应时间阈值(秒)
            "throughput": 10.0,  # 吞吐量阈值(请求/秒)
            "error_rate": 1.0  # 错误率阈值(%)
        }
        
    def run_api_benchmark(self, api_endpoint: str, num_requests: int = 100, concurrency: int = 10) -> Optional[PerformanceMetrics]:
        """运行API性能基准测试"""
        try:
            logger.info(f"Running API benchmark for {api_endpoint} with {num_requests} requests and {concurrency} concurrency")
            
            # 使用locust进行API基准测试
            cmd = [
                "locust",
                "--headless",
                "--users", str(concurrency),
                "--spawn-rate", str(concurrency),
                "--run-time", "1m",
                "--host", api_endpoint,
                "--only-summary"
            ]
            
            # 运行测试
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                _ = logger.error(f"API benchmark failed: {result.stderr}")
                return None
                
            # 解析测试结果
            metrics = self._parse_api_benchmark_results(result.stdout, api_endpoint, concurrency)
            
            if metrics:
                _ = self.benchmark_history.append(metrics)
                logger.info(f"API benchmark completed: response_time={metrics.response_time:.3f}s, "
                           f"throughput={metrics.throughput:.2f} req/s, error_rate={metrics.error_rate:.2f}%")
                           
            return metrics
        except Exception as e:
            _ = logger.error(f"Failed to run API benchmark: {e}")
            return None
            
    def run_component_benchmark(self, component_name: str, test_function: Callable, iterations: int = 1000) -> Optional[PerformanceMetrics]:
        """运行组件性能基准测试"""
        try:
            logger.info(f"Running component benchmark for {component_name} with {iterations} iterations")
            
            # 记录初始系统资源
            initial_cpu = psutil.cpu_percent(interval=1)
            initial_memory = psutil.virtual_memory().used / (1024 * 1024)  # MB
            
            # 运行测试函数
            start_time = time.time()
            errors = 0
            
            for i in range(iterations):
                try:
                    _ = test_function()
                except Exception as e:
                    _ = logger.warning(f"Error in iteration {i}: {e}")
                    errors += 1
                    
            end_time = time.time()
            
            # 记录最终系统资源
            final_cpu = psutil.cpu_percent(interval=1)
            final_memory = psutil.virtual_memory().used / (1024 * 1024)  # MB
            
            # 计算性能指标
            total_time = end_time - start_time
            avg_response_time = total_time / iterations
            throughput = iterations / total_time
            error_rate = (errors / iterations) * 100
            
            # 创建性能指标对象
            metrics = PerformanceMetrics()
            metrics.timestamp = datetime.now()
            metrics.response_time = avg_response_time
            metrics.throughput = throughput
            metrics.concurrency = 1  # 单线程测试
            metrics.cpu_usage = (final_cpu + initial_cpu) / 2
            metrics.memory_usage = final_memory - initial_memory
            metrics.error_rate = error_rate
            metrics.test_name = f"Component Benchmark: {component_name}"
            metrics.test_description = f"Component benchmark for {component_name} with {iterations} iterations"
            
            _ = self.benchmark_history.append(metrics)
            
            logger.info(f"Component benchmark completed: response_time={metrics.response_time:.6f}s, "
                       f"throughput={metrics.throughput:.2f} ops/s, error_rate={metrics.error_rate:.2f}%")
                       
            return metrics
        except Exception as e:
            _ = logger.error(f"Failed to run component benchmark: {e}")
            return None
            
    def _parse_api_benchmark_results(self, output: str, api_endpoint: str, concurrency: int) -> Optional[PerformanceMetrics]:
        """解析API基准测试结果"""
        try:
            metrics = PerformanceMetrics()
            metrics.timestamp = datetime.now()
            metrics.concurrency = concurrency
            metrics.test_name = f"API Benchmark: {api_endpoint}"
            metrics.test_description = f"API benchmark for {api_endpoint} with {concurrency} concurrent users"
            
            # 简化的解析逻辑（实际应用中需要根据locust输出格式进行解析）
            lines = output.split('\n')
            for line in lines:
                if 'Response time' in line:
                    # 提取响应时间
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'ms' in part:
                            metrics.response_time = float(part.replace('ms', '')) / 1000  # 转换为秒
                            break
                elif 'Requests' in line and '/s' in line:
                    # 提取吞吐量
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if '/s' in part:
                            metrics.throughput = float(part.replace('/s', ''))
                            break
                elif 'Failures' in line:
                    # 提取错误率
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if '%' in part:
                            metrics.error_rate = float(part.replace('%', ''))
                            break
                            
            # 获取系统资源使用情况
            metrics.cpu_usage = psutil.cpu_percent(interval=1)
            metrics.memory_usage = psutil.virtual_memory().used / (1024 * 1024)  # MB
            
            return metrics
        except Exception as e:
            _ = logger.error(f"Failed to parse API benchmark results: {e}")
            return None
            
    def run_regression_detection(self, current_metrics: PerformanceMetrics, baseline_metrics: PerformanceMetrics, 
                               threshold: float = 5.0) -> Dict[str, Any]:
        """运行性能回归检测"""
        try:
            regression_results = {
                "has_regression": False,
                "regressions": [],
                "improvements": []
            }
            
            # 检查响应时间回归
            response_time_change = ((current_metrics.response_time - baseline_metrics.response_time) / 
                                  baseline_metrics.response_time) * 100
            if response_time_change > threshold:
                regression_results["has_regression"] = True
                regression_results["regressions"].append({
                    "metric": "response_time",
                    "change": response_time_change,
                    "current": current_metrics.response_time,
                    "baseline": baseline_metrics.response_time
                })
            elif response_time_change < -threshold:
                regression_results["improvements"].append({
                    "metric": "response_time",
                    "change": response_time_change,
                    "current": current_metrics.response_time,
                    "baseline": baseline_metrics.response_time
                })
                
            # 检查吞吐量回归
            throughput_change = ((baseline_metrics.throughput - current_metrics.throughput) / 
                               baseline_metrics.throughput) * 100
            if throughput_change > threshold:
                regression_results["has_regression"] = True
                regression_results["regressions"].append({
                    "metric": "throughput",
                    "change": throughput_change,
                    "current": current_metrics.throughput,
                    "baseline": baseline_metrics.throughput
                })
            elif throughput_change < -threshold:
                regression_results["improvements"].append({
                    "metric": "throughput",
                    "change": throughput_change,
                    "current": current_metrics.throughput,
                    "baseline": baseline_metrics.throughput
                })
                
            # 检查错误率回归
            error_rate_change = ((current_metrics.error_rate - baseline_metrics.error_rate) / 
                               max(baseline_metrics.error_rate, 0.01)) * 100
            if error_rate_change > threshold:
                regression_results["has_regression"] = True
                regression_results["regressions"].append({
                    "metric": "error_rate",
                    "change": error_rate_change,
                    "current": current_metrics.error_rate,
                    "baseline": baseline_metrics.error_rate
                })
            elif error_rate_change < -threshold:
                regression_results["improvements"].append({
                    "metric": "error_rate",
                    "change": error_rate_change,
                    "current": current_metrics.error_rate,
                    "baseline": baseline_metrics.error_rate
                })
                
            logger.info(f"Regression detection completed: has_regression={regression_results['has_regression']}")
            return regression_results
        except Exception as e:
            _ = logger.error(f"Failed to run regression detection: {e}")
            return {"has_regression": False, "regressions": [], "improvements": []}
            
    def get_benchmark_trend(self, limit: int = 10) -> List[PerformanceMetrics]:
        """获取性能基准测试趋势"""
        return self.benchmark_history[-limit:] if len(self.benchmark_history) > limit else self.benchmark_history
        
    def check_performance_thresholds(self, metrics: PerformanceMetrics) -> Dict[str, bool]:
        """检查性能阈值"""
        results = {}
        results["response_time_ok"] = metrics.response_time <= self.thresholds["response_time"]
        results["throughput_ok"] = metrics.throughput >= self.thresholds["throughput"]
        results["error_rate_ok"] = metrics.error_rate <= self.thresholds["error_rate"]
        return results
        
    def generate_benchmark_report(self, metrics: PerformanceMetrics) -> str:
        """生成性能基准测试报告文本"""
        report = f"""
性能基准测试报告
================
_ = 生成时间: {metrics.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
测试名称: {metrics.test_name}

性能指标:
  响应时间: {metrics.response_time:.6f} 秒
  吞吐量: {metrics.throughput:.2f} 请求/秒
  并发用户数: {metrics.concurrency}
  CPU使用率: {metrics.cpu_usage:.2f}%
  内存使用: {metrics.memory_usage:.2f} MB
  错误率: {metrics.error_rate:.2f}%

阈值检查:
  响应时间阈值 ({self.thresholds['response_time']}s): {'通过' if metrics.response_time <= self.thresholds['response_time'] else '未通过'}
  吞吐量阈值 ({self.thresholds['throughput']} req/s): {'通过' if metrics.throughput >= self.thresholds['throughput'] else '未通过'}
  错误率阈值 ({self.thresholds['error_rate']}%): {'通过' if metrics.error_rate <= self.thresholds['error_rate'] else '未通过'}
"""
        return report.strip()
        
    def save_benchmark_results(self, metrics: PerformanceMetrics, filename: str = None) -> bool:
        """保存基准测试结果"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"benchmark_results_{timestamp}.json"
                
            # 转换为可序列化的格式
            result_data = {
                "timestamp": metrics.timestamp.isoformat(),
                "response_time": metrics.response_time,
                "throughput": metrics.throughput,
                "concurrency": metrics.concurrency,
                "cpu_usage": metrics.cpu_usage,
                "memory_usage": metrics.memory_usage,
                "error_rate": metrics.error_rate,
                "test_name": metrics.test_name,
                "test_description": metrics.test_description
            }
            
            filepath = os.path.join(self.project_root, filename)
            with open(filepath, 'w') as f:
                json.dump(result_data, f, indent=2)
                
            _ = logger.info(f"Saved benchmark results to {filepath}")
            return True
        except Exception as e:
            _ = logger.error(f"Failed to save benchmark results: {e}")
            return False
            
    def set_performance_thresholds(self, response_time_threshold: float = None, 
                                 throughput_threshold: float = None, error_rate_threshold: float = None):
        """设置性能阈值"""
        if response_time_threshold is not None:
            self.thresholds["response_time"] = response_time_threshold
        if throughput_threshold is not None:
            self.thresholds["throughput"] = throughput_threshold
        if error_rate_threshold is not None:
            self.thresholds["error_rate"] = error_rate_threshold
        _ = logger.info(f"Updated performance thresholds: {self.thresholds}")