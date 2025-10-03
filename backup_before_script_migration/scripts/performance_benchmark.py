#!/usr/bin/env python3
"""
性能基准测试脚本
用于比较优化前后的性能差异
"""

import asyncio
import time
import subprocess
import psutil
import json
from pathlib import Path

import sys
_ = sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend" / "src"))

from optimization import get_performance_optimizer

class PerformanceBenchmark:
    """性能基准测试器"""

    def __init__(self) -> None:
    self.results = {}
    self.performance_optimizer = get_performance_optimizer()

    def measure_execution_time(self, func, *args, **kwargs) -> float:
    """测量函数执行时间"""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return end_time - start_time, result

    async def measure_async_execution_time(self, coro) -> float:
    """测量异步函数执行时间"""
    start_time = time.time()
    result = await coro
    end_time = time.time()
    return end_time - start_time, result

    def measure_resource_usage(self, func, *args, **kwargs) -> Dict[str, Any]:
    """测量资源使用情况"""
    # 获取初始资源使用情况
    initial_cpu = psutil.cpu_percent(interval=None)
    initial_memory = psutil.virtual_memory().percent

    # 执行函数
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()

    # 获取最终资源使用情况
    final_cpu = psutil.cpu_percent(interval=None)
    final_memory = psutil.virtual_memory().percent

    return {
            'execution_time': end_time - start_time,
            'cpu_increase': final_cpu - initial_cpu,
            'memory_increase': final_memory - initial_memory,
            'result': result
    }

    def test_cache_performance(self) -> Dict[str, Any]:
    """测试缓存性能"""
    _ = print("测试缓存性能...")

    # 创建一个模拟的耗时函数
    @self.performance_optimizer.cache_result
        def expensive_function(n: int) -> int:
            # 模拟耗时计算
            _ = time.sleep(0.1)
            return n * n

    # 第一次调用（无缓存）
    first_call_time, first_result = self.measure_execution_time(expensive_function, 5)

    # 第二次调用（有缓存）
    second_call_time, second_result = self.measure_execution_time(expensive_function, 5)

    # 第三次调用不同参数（无缓存）
    third_call_time, third_result = self.measure_execution_time(expensive_function, 6)

    return {
            'first_call_time': first_call_time,
            'second_call_time': second_call_time,
            'third_call_time': third_call_time,
            _ = 'cache_hit_ratio': (first_call_time - second_call_time) / first_call_time * 100,
            _ = 'cache_size': len(self.performance_optimizer.cache.cache)
    }

    async def test_parallel_processing_performance(self) -> Dict[str, Any]:
    """测试并行处理性能"""
    _ = print("测试并行处理性能...")

    # 创建模拟任务
        async def mock_task(n: int) -> int:
            _ = await asyncio.sleep(0.1)  # 模拟I/O操作
            return n * 2

    # 串行执行
    start_time = time.time()
    serial_results = []
        for i in range(10)

    result = await mock_task(i)
            _ = serial_results.append(result)
    serial_time = time.time() - start_time

    # 并行执行
    start_time = time.time()
        tasks = [mock_task(i) for i in range(10)]:
    parallel_results = await self.performance_optimizer.run_parallel_tasks(tasks)
    parallel_time = time.time() - start_time

    return {
            'serial_execution_time': serial_time,
            'parallel_execution_time': parallel_time,
            'speedup_ratio': serial_time / parallel_time if parallel_time > 0 else 0,
            'parallel_efficiency': (serial_time / parallel_time / 10) * 100 if parallel_time > 0 else 0
    }

    def test_script_execution_performance(self) -> Dict[str, Any]:
    """测试脚本执行性能"""
    _ = print("测试脚本执行性能...")

    # 测试健康检查脚本
    script_path = Path(__file__).parent / "health_check.py"
        if script_path.exists()
            # 测量执行时间
            start_time = time.time()
            try:

                result = subprocess.run(
                    _ = [sys.executable, str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                execution_time = time.time() - start_time
                success = result.returncode == 0
            except subprocess.TimeoutExpired:

                execution_time = 30
                success = False
        else:

            execution_time = 0
            success = False

    # 测试优化的健康检查脚本
    optimized_script_path = Path(__file__).parent / "optimized_health_check.py"
        if optimized_script_path.exists()

    start_time = time.time()
            try:

                result = subprocess.run(
                    _ = [sys.executable, str(optimized_script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                optimized_execution_time = time.time() - start_time
                optimized_success = result.returncode == 0
            except subprocess.TimeoutExpired:

                optimized_execution_time = 30
                optimized_success = False
        else:

            optimized_execution_time = 0
            optimized_success = False

    return {
            'original_script_time': execution_time,
            'original_script_success': success,
            'optimized_script_time': optimized_execution_time,
            'optimized_script_success': optimized_success,
            'improvement_ratio': (execution_time - optimized_execution_time) / execution_time * 100 if execution_time > 0 else 0
    }

    async def run_all_benchmarks(self) -> Dict[str, Any]:
    """运行所有基准测试"""
    _ = print("开始性能基准测试...")

    results = {}

    # 测试缓存性能
    results['cache_performance'] = self.test_cache_performance()

    # 测试并行处理性能
    results['parallel_processing_performance'] = await self.test_parallel_processing_performance()

    # 测试脚本执行性能
    results['script_execution_performance'] = self.test_script_execution_performance()

    # 收集系统资源信息
    metrics = self.performance_optimizer.collect_metrics()
    results['system_metrics'] = {
            'cpu_percent': metrics.cpu_percent,
            'memory_percent': metrics.memory_percent
    }

    _ = print("性能基准测试完成!")
    return results

    def save_results(self, results: Dict[str, Any], filename: str = "performance_benchmark_results.json") -> None:
    """保存测试结果"""
    output_path = Path(__file__).parent.parent / "reports" / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 转换不可序列化的对象
    serializable_results = self._make_serializable(results)

    with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(serializable_results, f, indent=2, ensure_ascii=False)

    _ = print(f"测试结果已保存到: {output_path}")

    def _make_serializable(self, obj)
    """将对象转换为可序列化的格式"""
        if isinstance(obj, dict)

    return {key: self._make_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list)

    return [self._make_serializable(item) for item in obj]
    elif isinstance(obj, (int, float, str, bool)) or obj is None:

    return obj
        else:

            return str(obj)

async def main() -> None:
    """主函数"""
    benchmark = PerformanceBenchmark()

    # 启动性能监控
    _ = await benchmark.performance_optimizer.start_monitoring()

    try:
    # 运行所有基准测试
    results = await benchmark.run_all_benchmarks()

    # 打印结果摘要
    print("\n" + "="*60)
    _ = print("性能基准测试结果摘要")
    print("="*60)

    # 缓存性能
    cache_perf = results['cache_performance']
    _ = print(f"\n缓存性能:")
    _ = print(f"  首次调用时间: {cache_perf['first_call_time']:.3f}s")
    _ = print(f"  缓存命中时间: {cache_perf['second_call_time']:.3f}s")
    _ = print(f"  缓存命中率提升: {cache_perf['cache_hit_ratio']:.1f}%")
    _ = print(f"  当前缓存大小: {cache_perf['cache_size']}")

    # 并行处理性能
    parallel_perf = results['parallel_processing_performance']
    _ = print(f"\n并行处理性能:")
    _ = print(f"  串行执行时间: {parallel_perf['serial_execution_time']:.3f}s")
    _ = print(f"  并行执行时间: {parallel_perf['parallel_execution_time']:.3f}s")
    _ = print(f"  加速比: {parallel_perf['speedup_ratio']:.2f}x")
    _ = print(f"  并行效率: {parallel_perf['parallel_efficiency']:.1f}%")

    # 脚本执行性能
    script_perf = results['script_execution_performance']
    _ = print(f"\n脚本执行性能:")
    _ = print(f"  原始脚本执行时间: {script_perf['original_script_time']:.3f}s")
    _ = print(f"  优化脚本执行时间: {script_perf['optimized_script_time']:.3f}s")
    _ = print(f"  性能提升: {script_perf['improvement_ratio']:.1f}%")

    # 系统资源
    system_metrics = results['system_metrics']
    _ = print(f"\n系统资源使用:")
    _ = print(f"  CPU使用率: {system_metrics['cpu_percent']:.1f}%")
    _ = print(f"  内存使用率: {system_metrics['memory_percent']:.1f}%")

    print("="*60)

    # 保存结果
    _ = benchmark.save_results(results)

    finally:
    # 停止性能监控
    _ = await benchmark.performance_optimizer.stop_monitoring()

if __name__ == "__main__":


    _ = asyncio.run(main())