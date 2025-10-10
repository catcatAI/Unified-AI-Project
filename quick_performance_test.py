#!/usr/bin/env python3
"""
快速性能测试
运行核心性能指标的简化测试
"""

import asyncio
import time
import json
from datetime import datetime
from typing import Dict, List, Any

# 添加项目路径
import sys
sys.path.append('apps/backend/src')
sys.path.append('.')

from unified_scheduler_framework import (
    create_unified_scheduler, create_parallel_scheduler, TaskConfig
)


class QuickPerformanceTester:
    """快速性能测试器"""
    
    async def run_quick_benchmark(self) -> Dict[str, Any]:
        """运行快速性能基准测试"""
        print("🚀 开始AGI系统快速性能基准测试")
        
        benchmark_start = time.time()
        results = {
            "test_name": "AGI系统快速性能基准测试",
            "start_time": datetime.now().isoformat(),
            "benchmarks": {},
            "overall_score": 0.0
        }
        
        try:
            # 1. 响应时间测试
            print("\n📊 1. 响应时间测试")
            results["benchmarks"]["response_time"] = await self._quick_response_time_test()
            
            # 2. 吞吐量测试
            print("\n📈 2. 吞吐量测试")
            results["benchmarks"]["throughput"] = await self._quick_throughput_test()
            
            # 3. 并发测试
            print("\n⚡ 3. 并发测试")
            results["benchmarks"]["concurrency"] = await self._quick_concurrency_test()
            
            # 计算总体评分
            benchmark_end = time.time()
            results["total_execution_time"] = benchmark_end - benchmark_start
            results["overall_score"] = self._calculate_overall_score(results["benchmarks"])
            
            print(f"\n✅ 快速性能测试完成")
            print(f"总执行时间: {results['total_execution_time']:.2f}秒")
            print(f"总体性能评分: {results['overall_score']:.1f}/10.0")
            
            return results
            
        except Exception as e:
            print(f"\n❌ 快速性能测试失败: {e}")
            results["error"] = str(e)
            return results
    
    async def _quick_response_time_test(self) -> Dict[str, Any]:
        """快速响应时间测试"""
        print("  测试基本响应时间...")
        
        scheduler = create_unified_scheduler()
        
        # 简单任务测试
        task_config = TaskConfig(
            name="quick_response_test",
            command="python -c \"print('Quick test')\"",
            timeout=10
        )
        scheduler.register_task(task_config)
        
        # 测试3次取平均
        response_times = []
        for i in range(3):
            start_time = time.time()
            result = await scheduler.execute_task(task_config.name)
            end_time = time.time()
            
            if result.status.value == "completed":
                response_time = end_time - start_time
                response_times.append(response_time)
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            performance_score = max(0, 10 - avg_response_time * 10)  # 响应时间越短分数越高
            
            return {
                "success": True,
                "average_response_time": avg_response_time,
                "max_response_time": max(response_times),
                "min_response_time": min(response_times),
                "performance_score": performance_score,
                "meets_requirement": avg_response_time < 2.0  # 2秒要求
            }
        else:
            return {
                "success": False,
                "error": "所有响应时间测试失败"
            }
    
    async def _quick_throughput_test(self) -> Dict[str, Any]:
        """快速吞吐量测试"""
        print("  测试基本吞吐量...")
        
        scheduler = create_parallel_scheduler(max_concurrent_tasks=3)
        
        # 创建5个简单并发任务
        task_configs = []
        for i in range(5):
            task_config = TaskConfig(
                name=f"quick_throughput_{i}",
                command=f"python -c \"print('Task {i}')\"",
                timeout=10
            )
            scheduler.register_task(task_config)
            task_configs.append(task_config)
        
        start_time = time.time()
        task_names = [tc.name for tc in task_configs]
        results = await scheduler.execute_tasks(task_names)
        end_time = time.time()
        
        total_time = end_time - start_time
        successful_tasks = sum(1 for r in results if r.status.value == "completed")
        throughput = successful_tasks / total_time if total_time > 0 else 0
        
        performance_score = min(10, throughput * 5)  # 基础吞吐量评分
        
        return {
            "success": successful_tasks > 0,
            "total_tasks": len(results),
            "successful_tasks": successful_tasks,
            "total_execution_time": total_time,
            "throughput_per_second": throughput,
            "performance_score": performance_score,
            "meets_requirement": throughput > 1.0  # 每秒至少1个任务
        }
    
    async def _quick_concurrency_test(self) -> Dict[str, Any]:
        """快速并发测试"""
        print("  测试基本并发能力...")
        
        # 测试并发级别2
        scheduler = create_parallel_scheduler(max_concurrent_tasks=2)
        
        task_configs = []
        for i in range(4):
            task_config = TaskConfig(
                name=f"quick_concurrent_{i}",
                command=f"python -c \"import time; time.sleep(0.05); print('Task {i}')\"",
                timeout=10
            )
            scheduler.register_task(task_config)
            task_configs.append(task_config)
        
        start_time = time.time()
        task_names = [tc.name for tc in task_configs]
        results = await scheduler.execute_tasks(task_names)
        end_time = time.time()
        
        successful_tasks = sum(1 for r in results if r.status.value == "completed")
        total_time = end_time - start_time
        
        # 并发效率计算
        sequential_time_estimate = 4 * 0.05  # 4个任务，每个0.05秒
        actual_time = total_time
        efficiency = (sequential_time_estimate / actual_time) * 100 if actual_time > 0 else 0
        
        performance_score = min(10, efficiency / 10)  # 效率转换为分数
        
        return {
            "success": successful_tasks > 0,
            "total_tasks": len(results),
            "successful_tasks": successful_tasks,
            "total_execution_time": total_time,
            "concurrent_efficiency": efficiency,
            "performance_score": performance_score,
            "meets_requirement": efficiency > 50  # 50%效率要求
        }
    
    def _calculate_overall_score(self, benchmarks: Dict[str, Any]) -> float:
        """计算总体性能评分"""
        scores = []
        
        for benchmark_result in benchmarks.values():
            if benchmark_result.get("success", False):
                if "performance_score" in benchmark_result:
                    scores.append(benchmark_result["performance_score"])
                elif "concurrent_efficiency" in benchmark_result:
                    scores.append(benchmark_result["concurrent_efficiency"] / 10)  # 转换为10分制
        
        return sum(scores) / len(scores) if scores else 0.0


def create_quick_performance_tester() -> QuickPerformanceTester:
    """创建快速性能测试器"""
    return QuickPerformanceTester()


async def run_quick_performance_benchmark():
    """运行快速性能基准测试"""
    tester = create_quick_performance_tester()
    
    try:
        results = await tester.run_quick_benchmark()
        
        # 生成简化报告
        report = generate_quick_performance_report(results)
        print("\n" + "="*50)
        print(report)
        print("="*50)
        
        # 保存结果
        results_file = "quick_performance_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📊 快速性能数据已保存到: {results_file}")
        
        return results["overall_score"] >= 6.0  # 6分以上认为性能基本合格
        
    except Exception as e:
        print(f"\n❌ 快速性能测试执行失败: {e}")
        return False


def generate_quick_performance_report(results: Dict[str, Any]) -> str:
    """生成快速性能报告"""
    report = []
    report.append("AGI系统快速性能测试报告")
    report.append("=" * 40)
    report.append(f"测试时间: {results.get('start_time', 'Unknown')}")
    report.append(f"总执行时间: {results.get('total_execution_time', 0):.2f}秒")
    report.append(f"总体性能评分: {results.get('overall_score', 0):.1f}/10.0")
    report.append("")
    
    benchmarks = results.get("benchmarks", {})
    
    for benchmark_name, benchmark_result in benchmarks.items():
        if benchmark_result.get("success", False):
            if benchmark_name == "response_time":
                report.append(f"📊 响应时间: {benchmark_result.get('average_response_time', 0):.3f}秒")
                report.append(f"   评分: {benchmark_result.get('performance_score', 0):.1f}/10.0")
            
            elif benchmark_name == "throughput":
                report.append(f"📈 吞吐量: {benchmark_result.get('throughput_per_second', 0):.2f} 任务/秒")
                report.append(f"   评分: {benchmark_result.get('performance_score', 0):.1f}/10.0")
            
            elif benchmark_name == "concurrency":
                report.append(f"⚡ 并发效率: {benchmark_result.get('concurrent_efficiency', 0):.1f}%")
                report.append(f"   评分: {benchmark_result.get('performance_score', 0):.1f}/10.0")
        else:
            report.append(f"❌ {benchmark_name}: 测试失败")
    
    overall_score = results.get("overall_score", 0)
    if overall_score >= 8.0:
        report.append(f"\n🎯 性能评价: 优秀 ({overall_score:.1f}/10.0)")
    elif overall_score >= 6.0:
        report.append(f"\n🎯 性能评价: 良好 ({overall_score:.1f}/10.0)")
    elif overall_score >= 4.0:
        report.append(f"\n🎯 性能评价: 一般 ({overall_score:.1f}/10.0)")
    else:
        report.append(f"\n🎯 性能评价: 需要优化 ({overall_score:.1f}/10.0)")
    
    return "\n".join(report)


if __name__ == '__main__':
    import asyncio
    
    print("🚀 启动AGI系统快速性能基准测试")
    success = asyncio.run(run_quick_performance_benchmark())
    
    if success:
        print("\n🎉 快速性能测试通过！系统性能基本达标")
        exit(0)
    else:
        print("\n❌ 快速性能测试未通过，建议检查系统配置")
        exit(1)
