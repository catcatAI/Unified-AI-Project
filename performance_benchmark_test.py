#!/usr/bin/env python3
"""
性能基准测试
评估AGI系统的性能指标和基准
"""

import asyncio
import time
import json
import psutil
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# 添加项目路径
import sys
sys.path.append('apps/backend/src')
sys.path.append('.')

from unified_scheduler_framework import (
    create_unified_scheduler, create_parallel_scheduler, 
    create_pipeline_scheduler, TaskConfig
)
from enhanced_input_validator import create_smart_validator
from enhanced_output_validator import create_enhanced_output_validator


class PerformanceBenchmarkTester:
    """性能基准测试器"""
    
    def __init__(self):
        self.benchmark_results = []
        self.system_metrics = []
        self.monitoring_active = False
        self.monitoring_thread = None
        
    def start_system_monitoring(self):
        """启动系统监控"""
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_system_resources)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
    
    def stop_system_monitoring(self):
        """停止系统监控"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
    
    def _monitor_system_resources(self):
        """监控系统资源"""
        while self.monitoring_active:
            try:
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                # 内存使用
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_used_mb = memory.used / 1024 / 1024
                
                # 磁盘IO
                disk_io = psutil.disk_io_counters()
                disk_read_mb = disk_io.read_bytes / 1024 / 1024 if disk_io else 0
                disk_write_mb = disk_io.write_bytes / 1024 / 1024 if disk_io else 0
                
                # 网络IO
                net_io = psutil.net_io_counters()
                net_sent_mb = net_io.bytes_sent / 1024 / 1024 if net_io else 0
                net_recv_mb = net_io.bytes_recv / 1024 / 1024 if net_io else 0
                
                self.system_metrics.append({
                    "timestamp": time.time(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "memory_used_mb": memory_used_mb,
                    "disk_read_mb": disk_read_mb,
                    "disk_write_mb": disk_write_mb,
                    "net_sent_mb": net_sent_mb,
                    "net_recv_mb": net_recv_mb
                })
                
                time.sleep(0.5)  # 每0.5秒采样一次
                
            except Exception as e:
                print(f"监控线程错误: {e}")
                time.sleep(1)
    
    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """运行综合性能基准测试"""
        print("🚀 开始AGI系统性能基准测试")
        
        benchmark_start = time.time()
        results = {
            "test_name": "AGI系统性能基准测试",
            "start_time": datetime.now().isoformat(),
            "benchmarks": {},
            "system_metrics": {},
            "overall_score": 0.0
        }
        
        try:
            # 1. 响应时间基准测试
            print("\n📊 1. 响应时间基准测试")
            results["benchmarks"]["response_time"] = await self._benchmark_response_time()
            
            # 2. 吞吐量基准测试
            print("\n📈 2. 吞吐量基准测试")
            results["benchmarks"]["throughput"] = await self._benchmark_throughput()
            
            # 3. 并发性能基准测试
            print("\n⚡ 3. 并发性能基准测试")
            results["benchmarks"]["concurrency"] = await self._benchmark_concurrency()
            
            # 4. 内存使用基准测试
            print("\n💾 4. 内存使用基准测试")
            results["benchmarks"]["memory_usage"] = await self._benchmark_memory_usage()
            
            # 5. 处理延迟基准测试
            print("\n⏱️ 5. 处理延迟基准测试")
            results["benchmarks"]["processing_latency"] = await self._benchmark_processing_latency()
            
            # 6. 系统稳定性基准测试
            print("\n🛡️ 6. 系统稳定性基准测试")
            results["benchmarks"]["stability"] = await self._benchmark_stability()
            
            # 计算总体评分
            benchmark_end = time.time()
            results["total_execution_time"] = benchmark_end - benchmark_start
            results["overall_score"] = self._calculate_overall_score(results["benchmarks"])
            
            # 分析系统指标
            results["system_metrics"] = self._analyze_system_metrics()
            
            print(f"\n✅ 性能基准测试完成")
            print(f"总执行时间: {results['total_execution_time']:.2f}秒")
            print(f"总体性能评分: {results['overall_score']:.1f}/10.0")
            
            return results
            
        except Exception as e:
            print(f"\n❌ 性能基准测试失败: {e}")
            results["error"] = str(e)
            return results
    
    async def _benchmark_response_time(self) -> Dict[str, Any]:
        """响应时间基准测试"""
        print("  测试不同复杂度任务的响应时间...")
        
        test_cases = [
            {
                "name": "简单任务",
                "command": "python -c \"print('简单任务完成')\"",
                "timeout": 5
            },
            {
                "name": "中等复杂度任务",
                "command": "python -c \"import time; time.sleep(0.1); print('中等任务完成')\"",
                "timeout": 10
            },
            {
                "name": "复杂任务",
                "command": "python -c \"import time; [time.sleep(0.05) for _ in range(3)]; print('复杂任务完成')\"",
                "timeout": 15
            }
        ]
        
        response_times = []
        scheduler = create_unified_scheduler()
        
        for test_case in test_cases:
            times = []
            
            # 运行多次取平均值
            for i in range(5):
                task_config = TaskConfig(
                    name=f"response_test_{test_case['name']}_{i}",
                    command=test_case["command"],
                    timeout=test_case["timeout"]
                )
                scheduler.register_task(task_config)
                
                start_time = time.time()
                result = await scheduler.execute_task(task_config.name)
                end_time = time.time()
                
                if result.status.value == "completed":
                    response_time = end_time - start_time
                    times.append(response_time)
            
            if times:
                avg_time = sum(times) / len(times)
                max_time = max(times)
                min_time = min(times)
                
                response_times.append({
                    "task_complexity": test_case["name"],
                    "average_response_time": avg_time,
                    "max_response_time": max_time,
                    "min_response_time": min_time,
                    "test_count": len(times)
                })
        
        # 计算总体统计
        if response_times:
            overall_avg = sum(rt["average_response_time"] for rt in response_times) / len(response_times)
            performance_score = max(0, 10 - overall_avg)  # 响应时间越短，分数越高
        else:
            overall_avg = 0
            performance_score = 0
        
        return {
            "success": len(response_times) > 0,
            "response_times": response_times,
            "overall_average_response_time": overall_avg,
            "performance_score": performance_score,
            "grade": self._get_performance_grade(performance_score)
        }
    
    async def _benchmark_throughput(self) -> Dict[str, Any]:
        """吞吐量基准测试"""
        print("  测试系统处理并发请求的能力...")
        
        # 创建并行调度器
        parallel_scheduler = create_parallel_scheduler(max_concurrent_tasks=5)
        
        # 创建多个简单任务
        task_configs = []
        for i in range(10):
            task_config = TaskConfig(
                name=f"throughput_task_{i}",
                command=f"python -c \"print('Task {i}'); import time; time.sleep(0.1)\"",
                timeout=10
            )
            parallel_scheduler.register_task(task_config)
            task_configs.append(task_config)
        
        # 启动系统监控
        self.start_system_monitoring()
        self.system_metrics = []  # 重置监控数据
        
        start_time = time.time()
        
        # 执行所有任务
        task_names = [tc.name for tc in task_configs]
        results = await parallel_scheduler.execute_tasks(task_names)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 停止监控
        self.stop_system_monitoring()
        
        # 分析结果
        successful_tasks = sum(1 for r in results if r.status.value == "completed")
        total_tasks = len(results)
        throughput = successful_tasks / total_time if total_time > 0 else 0
        
        # 计算并发效率
        theoretical_max = len(task_configs) / 0.1  # 每个任务理论耗时0.1秒
        efficiency = (throughput / theoretical_max) * 100 if theoretical_max > 0 else 0
        
        # 评分
        performance_score = min(10, throughput * 2)  # 每任务/秒得2分，最高10分
        
        return {
            "success": successful_tasks > 0,
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "total_execution_time": total_time,
            "throughput_per_second": throughput,
            "concurrent_efficiency": efficiency,
            "performance_score": performance_score,
            "grade": self._get_performance_grade(performance_score)
        }
    
    async def _benchmark_concurrency(self) -> Dict[str, Any]:
        """并发性能基准测试"""
        print("  测试不同并发级别下的系统表现...")
        
        concurrency_levels = [1, 2, 4, 8]
        concurrency_results = []
        
        for level in concurrency_levels:
            print(f"    测试并发级别: {level}")
            
            scheduler = create_parallel_scheduler(max_concurrent_tasks=level)
            
            # 创建任务
            task_configs = []
            for i in range(level * 2):  # 每个并发级别创建2倍任务
                task_config = TaskConfig(
                    name=f"concurrency_task_{level}_{i}",
                    command=f"python -c \"print('Task {level}_{i}'); import time; time.sleep(0.2)\"",
                    timeout=15
                )
                scheduler.register_task(task_config)
                task_configs.append(task_config)
            
            start_time = time.time()
            task_names = [tc.name for tc in task_configs]
            results = await scheduler.execute_tasks(task_names)
            end_time = time.time()
            
            successful_tasks = sum(1 for r in results if r.status.value == "completed")
            total_time = end_time - start_time
            
            concurrency_results.append({
                "concurrency_level": level,
                "total_tasks": len(task_configs),
                "successful_tasks": successful_tasks,
                "total_time": total_time,
                "tasks_per_second": successful_tasks / total_time if total_time > 0 else 0,
                "efficiency": (successful_tasks / len(task_configs)) * 100
            })
        
        # 分析并发扩展性
        if len(concurrency_results) > 1:
            scalability_score = self._calculate_scalability_score(concurrency_results)
        else:
            scalability_score = 0
        
        return {
            "success": len(concurrency_results) > 0,
            "concurrency_results": concurrency_results,
            "scalability_score": scalability_score,
            "optimal_concurrency_level": self._find_optimal_concurrency(concurrency_results)
        }
    
    async def _benchmark_memory_usage(self) -> Dict[str, Any]:
        """内存使用基准测试"""
        print("  测试系统内存使用情况和内存效率...")
        
        # 获取初始内存状态
        initial_memory = psutil.virtual_memory()
        initial_memory_mb = initial_memory.used / 1024 / 1024
        
        # 创建不同规模的测试
        memory_tests = []
        
        for i in range(5):
            # 创建包含大量数据的任务
            large_data = "x" * (1000 * (i + 1))  # 递增的数据量
            
            task_config = TaskConfig(
                name=f"memory_test_{i}",
                command=f"python -c \"data='{large_data}'; print(f'Memory test {i}: {{len(data)}} bytes')\"",
                timeout=10
            )
            memory_tests.append(task_config)
        
        scheduler = create_unified_scheduler()
        
        memory_snapshots = []
        
        for i, task_config in enumerate(memory_tests):
            # 记录执行前的内存状态
            before_memory = psutil.virtual_memory()
            before_memory_mb = before_memory.used / 1024 / 1024
            
            scheduler.register_task(task_config)
            result = await scheduler.execute_task(task_config.name)
            
            # 记录执行后的内存状态
            after_memory = psutil.virtual_memory()
            after_memory_mb = after_memory.used / 1024 / 1024
            
            memory_snapshots.append({
                "test_index": i,
                "data_size_kb": len(task_config.command) / 1024,
                "memory_before_mb": before_memory_mb,
                "memory_after_mb": after_memory_mb,
                "memory_increase_mb": after_memory_mb - before_memory_mb,
                "execution_success": result.status.value == "completed"
            })
        
        # 分析内存使用趋势
        final_memory = psutil.virtual_memory()
        final_memory_mb = final_memory.used / 1024 / 1024
        
        memory_efficiency = self._calculate_memory_efficiency(memory_snapshots)
        
        return {
            "success": len(memory_snapshots) > 0,
            "memory_snapshots": memory_snapshots,
            "initial_memory_mb": initial_memory_mb,
            "final_memory_mb": final_memory_mb,
            "memory_increase_mb": final_memory_mb - initial_memory_mb,
            "memory_efficiency_score": memory_efficiency,
            "memory_leak_detected": final_memory_mb > initial_memory_mb + 50  # 50MB阈值
        }
    
    async def _benchmark_processing_latency(self) -> Dict[str, Any]:
        """处理延迟基准测试"""
        print("  测试不同处理阶段的延迟...")
        
        latency_tests = [
            {
                "stage": "input_validation",
                "description": "输入验证延迟",
                "test_function": self._test_input_validation_latency
            },
            {
                "stage": "task_scheduling",
                "description": "任务调度延迟",
                "test_function": self._test_task_scheduling_latency
            },
            {
                "stage": "output_generation",
                "description": "输出生成延迟",
                "test_function": self._test_output_generation_latency
            }
        ]
        
        latency_results = []
        
        for test in latency_tests:
            print(f"    测试: {test['description']}")
            result = await test["test_function"]()
            latency_results.append(result)
        
        # 计算总体延迟评分
        avg_latency = sum(r["average_latency_ms"] for r in latency_results) / len(latency_results)
        latency_score = max(0, 10 - avg_latency / 100)  # 每100ms延迟扣1分
        
        return {
            "success": len(latency_results) > 0,
            "latency_results": latency_results,
            "overall_average_latency_ms": avg_latency,
            "latency_score": latency_score,
            "grade": self._get_performance_grade(latency_score)
        }
    
    async def _test_input_validation_latency(self) -> Dict[str, Any]:
        """测试输入验证延迟"""
        from enhanced_input_validator import create_smart_validator
        
        validator = create_smart_validator()
        test_inputs = [
            {"type": "text", "content": "简单的文本输入", "metadata": {}},
            {"type": "code", "content": "print('hello')", "metadata": {"language": "python"}},
            {"type": "structured", "content": {"key": "value"}, "metadata": {}}
        ]
        
        latencies = []
        
        for test_input in test_inputs:
            start_time = time.time()
            result = validator.validate_input(test_input, test_input["type"])
            end_time = time.time()
            
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
        
        avg_latency = sum(latencies) / len(latencies)
        
        return {
            "stage": "input_validation",
            "test_count": len(latencies),
            "average_latency_ms": avg_latency,
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "meets_requirement": avg_latency < 100  # 100ms要求
        }
    
    async def _test_task_scheduling_latency(self) -> Dict[str, Any]:
        """测试任务调度延迟"""
        scheduler = create_unified_scheduler()
        
        # 创建简单任务
        task_config = TaskConfig(
            name="scheduling_latency_test",
            command="python -c 'print(\"test\")'",
            timeout=5
        )
        scheduler.register_task(task_config)
        
        latencies = []
        
        for i in range(5):
            start_time = time.time()
            result = await scheduler.execute_task(task_config.name)
            end_time = time.time()
            
            if result.status.value == "completed":
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)
        
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        return {
            "stage": "task_scheduling",
            "test_count": len(latencies),
            "average_latency_ms": avg_latency,
            "min_latency_ms": min(latencies) if latencies else 0,
            "max_latency_ms": max(latencies) if latencies else 0,
            "meets_requirement": avg_latency < 500  # 500ms要求
        }
    
    async def _test_output_generation_latency(self) -> Dict[str, Any]:
        """测试输出生成延迟"""
        from enhanced_output_validator import create_enhanced_output_validator
        
        validator = create_enhanced_output_validator()
        
        test_outputs = [
            {
                "content": "这是一个测试输出",
                "quality_score": 0.8
            },
            {
                "content": "```python\nprint('hello')\n```",
                "format": "python",
                "quality_score": 0.9
            },
            {
                "content": {
                    "overview": "测试总结",
                    "details": "详细内容",
                    "recommendations": ["建议1", "建议2"]
                },
                "completeness": 0.95,
                "quality_score": 0.85
            }
        ]
        
        latencies = []
        
        for i, test_output in enumerate(test_outputs):
            output_type = ["text_analysis", "code_suggestion", "summary_report"][i]
            requirements = {}
            
            start_time = time.time()
            result = validator.validate_output(test_output, output_type, requirements)
            end_time = time.time()
            
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
        
        avg_latency = sum(latencies) / len(latencies)
        
        return {
            "stage": "output_generation",
            "test_count": len(latencies),
            "average_latency_ms": avg_latency,
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "meets_requirement": avg_latency < 200  # 200ms要求
        }
    
    async def _benchmark_stability(self) -> Dict[str, Any]:
        """系统稳定性基准测试"""
        print("  测试系统在压力下的稳定性...")
        
        # 创建压力测试场景
        stress_scheduler = create_parallel_scheduler(max_concurrent_tasks=8)
        
        # 创建大量任务
        stress_tasks = []
        for i in range(20):
            task_config = TaskConfig(
                name=f"stress_task_{i}",
                command=f"python -c \"import time; time.sleep(0.1); print('Stress {i}')\"",
                timeout=30
            )
            stress_scheduler.register_task(task_config)
            stress_tasks.append(task_config)
        
        # 启动监控
        self.start_system_monitoring()
        self.system_metrics = []
        
        start_time = time.time()
        
        try:
            # 执行压力测试
            task_names = [tc.name for tc in stress_tasks]
            results = await stress_scheduler.execute_tasks(task_names)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # 分析结果
            successful_tasks = sum(1 for r in results if r.status.value == "completed")
            failed_tasks = sum(1 for r in results if r.status.value == "failed")
            
            # 检查错误模式
            error_types = {}
            for result in results:
                if result.error_message:
                    error_type = result.error_message.split(":")[0] if ":" in result.error_message else "unknown"
                    error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # 计算稳定性指标
            success_rate = successful_tasks / len(results) if results else 0
            stability_score = success_rate * 10  # 转换为10分制
            
            # 分析系统资源使用稳定性
            resource_stability = self._analyze_resource_stability()
            
            return {
                "success": True,
                "total_tasks": len(results),
                "successful_tasks": successful_tasks,
                "failed_tasks": failed_tasks,
                "success_rate": success_rate,
                "error_distribution": error_types,
                "total_execution_time": total_time,
                "stability_score": stability_score,
                "resource_stability": resource_stability,
                "grade": self._get_performance_grade(stability_score)
            }
            
        finally:
            self.stop_system_monitoring()
    
    def _calculate_overall_score(self, benchmarks: Dict[str, Any]) -> float:
        """计算总体性能评分"""
        scores = []
        
        for benchmark_name, benchmark_result in benchmarks.items():
            if "performance_score" in benchmark_result:
                scores.append(benchmark_result["performance_score"])
            elif "stability_score" in benchmark_result:
                scores.append(benchmark_result["stability_score"])
            elif "scalability_score" in benchmark_result:
                scores.append(benchmark_result["scalability_score"])
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _get_performance_grade(self, score: float) -> str:
        """获取性能等级"""
        if score >= 9.0:
            return "A+ (优秀)"
        elif score >= 8.0:
            return "A (良好)"
        elif score >= 7.0:
            return "B (中等)"
        elif score >= 6.0:
            return "C (及格)"
        elif score >= 5.0:
            return "D (较差)"
        else:
            return "F (失败)"
    
    def _calculate_scalability_score(self, concurrency_results: List[Dict]) -> float:
        """计算可扩展性评分"""
        if len(concurrency_results) < 2:
            return 0.0
        
        # 分析并发效率随并发级别增加的变化
        efficiencies = [r["efficiency"] for r in concurrency_results]
        
        # 理想情况下，效率应该保持稳定或略有下降
        efficiency_trend = 0
        for i in range(1, len(efficiencies)):
            if efficiencies[i] >= efficiencies[i-1] * 0.8:  # 允许20%的效率下降
                efficiency_trend += 1
        
        return (efficiency_trend / (len(efficiencies) - 1)) * 10
    
    def _find_optimal_concurrency(self, concurrency_results: List[Dict]) -> int:
        """找到最优并发级别"""
        if not concurrency_results:
            return 1
        
        # 找到效率最高的并发级别
        best_result = max(concurrency_results, key=lambda x: x["tasks_per_second"])
        return best_result["concurrency_level"]
    
    def _calculate_memory_efficiency(self, memory_snapshots: List[Dict]) -> float:
        """计算内存效率评分"""
        if not memory_snapshots:
            return 0.0
        
        # 分析内存增长与数据大小的关系
        memory_efficiencies = []
        for snapshot in memory_snapshots:
            if snapshot["data_size_kb"] > 0:
                efficiency = 1.0 / (snapshot["memory_increase_mb"] / (snapshot["data_size_kb"] / 1024))
                memory_efficiencies.append(min(efficiency, 10.0))  # 限制最大分数
        
        return sum(memory_efficiencies) / len(memory_efficiencies) if memory_efficiencies else 0.0
    
    def _analyze_resource_stability(self) -> Dict[str, Any]:
        """分析资源使用稳定性"""
        if not self.system_metrics:
            return {"stability_score": 0.0, "analysis": "无监控数据"}
        
        # 计算CPU和内存使用的标准差
        cpu_values = [m["cpu_percent"] for m in self.system_metrics]
        memory_values = [m["memory_percent"] for m in self.system_metrics]
        
        cpu_std = self._calculate_std_dev(cpu_values)
        memory_std = self._calculate_std_dev(memory_values)
        
        # 稳定性分数：标准差越小越稳定
        cpu_stability = max(0, 10 - cpu_std)
        memory_stability = max(0, 10 - memory_std)
        
        overall_stability = (cpu_stability + memory_stability) / 2
        
        return {
            "stability_score": overall_stability,
            "cpu_stability": cpu_stability,
            "memory_stability": memory_stability,
            "cpu_std": cpu_std,
            "memory_std": memory_std
        }
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """计算标准差"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _analyze_system_metrics(self) -> Dict[str, Any]:
        """分析系统指标"""
        if not self.system_metrics:
            return {"analysis": "无系统监控数据"}
        
        cpu_values = [m["cpu_percent"] for m in self.system_metrics]
        memory_values = [m["memory_percent"] for m in self.system_metrics]
        
        return {
            "peak_cpu_percent": max(cpu_values) if cpu_values else 0,
            "average_cpu_percent": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
            "peak_memory_percent": max(memory_values) if memory_values else 0,
            "average_memory_percent": sum(memory_values) / len(memory_values) if memory_values else 0,
            "total_samples": len(self.system_metrics),
            "monitoring_duration": self.system_metrics[-1]["timestamp"] - self.system_metrics[0]["timestamp"] if len(self.system_metrics) > 1 else 0
        }


def create_performance_benchmark() -> PerformanceBenchmarkTester:
    """创建性能基准测试器"""
    return PerformanceBenchmarkTester()


async def run_performance_benchmark():
    """运行性能基准测试"""
    tester = create_performance_benchmark()
    
    try:
        results = await tester.run_comprehensive_benchmark()
        
        # 生成详细报告
        report = generate_performance_report(results)
        print("\n" + "="*60)
        print(report)
        print("="*60)
        
        # 保存结果
        results_file = "performance_benchmark_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📊 详细性能数据已保存到: {results_file}")
        
        return results["overall_score"] >= 7.0  # 7分以上认为性能良好
        
    except Exception as e:
        print(f"\n❌ 性能基准测试执行失败: {e}")
        return False


def generate_performance_report(results: Dict[str, Any]) -> str:
    """生成性能报告"""
    report = []
    report.append("AGI系统性能基准测试报告")
    report.append("=" * 50)
    report.append(f"测试时间: {results.get('start_time', 'Unknown')}")
    report.append(f"总执行时间: {results.get('total_execution_time', 0):.2f}秒")
    report.append(f"总体性能评分: {results.get('overall_score', 0):.1f}/10.0")
    report.append("")
    
    # 详细基准测试结果
    benchmarks = results.get("benchmarks", {})
    
    for benchmark_name, benchmark_result in benchmarks.items():
        report.append(f"📊 {benchmark_name.upper()}:")
        
        if benchmark_name == "response_time":
            report.append(f"  总体平均响应时间: {benchmark_result.get('overall_average_response_time', 0):.3f}秒")
            report.append(f"  性能评分: {benchmark_result.get('performance_score', 0):.1f}/10.0")
            report.append(f"  等级: {benchmark_result.get('grade', 'Unknown')}")
            
            for rt in benchmark_result.get('response_times', []):
                report.append(f"    {rt['task_complexity']}: {rt['average_response_time']:.3f}s (max: {rt['max_response_time']:.3f}s)")
        
        elif benchmark_name == "throughput":
            report.append(f"  吞吐量: {benchmark_result.get('throughput_per_second', 0):.2f} 任务/秒")
            report.append(f"  并发效率: {benchmark_result.get('concurrent_efficiency', 0):.1f}%")
            report.append(f"  性能评分: {benchmark_result.get('performance_score', 0):.1f}/10.0")
            report.append(f"  等级: {benchmark_result.get('grade', 'Unknown')}")
        
        elif benchmark_name == "concurrency":
            report.append(f"  可扩展性评分: {benchmark_result.get('scalability_score', 0):.1f}/10.0")
            report.append(f"  最优并发级别: {benchmark_result.get('optimal_concurrency_level', 1)}")
            
            for cr in benchmark_result.get('concurrency_results', []):
                report.append(f"    并发{cr['concurrency_level']}: {cr['tasks_per_second']:.2f}任务/秒, 效率{cr['efficiency']:.1f}%")
        
        elif benchmark_name == "stability":
            report.append(f"  稳定性评分: {benchmark_result.get('stability_score', 0):.1f}/10.0")
            report.append(f"  成功率: {benchmark_result.get('success_rate', 0):.1%}")
            report.append(f"  等级: {benchmark_result.get('grade', 'Unknown')}")
        
        report.append("")
    
    # 系统指标
    system_metrics = results.get("system_metrics", {})
    if system_metrics:
        report.append("💻 系统资源使用情况:")
        report.append(f"  峰值CPU使用率: {system_metrics.get('peak_cpu_percent', 0):.1f}%")
        report.append(f"  平均CPU使用率: {system_metrics.get('average_cpu_percent', 0):.1f}%")
        report.append(f"  峰值内存使用率: {system_metrics.get('peak_memory_percent', 0):.1f}%")
        report.append(f"  平均内存使用率: {system_metrics.get('average_memory_percent', 0):.1f}%")
        report.append("")
    
    # 性能建议
    overall_score = results.get("overall_score", 0)
    if overall_score >= 9.0:
        report.append("🎯 性能评价: 优秀 - 系统性能表现出色")
    elif overall_score >= 8.0:
        report.append("🎯 性能评价: 良好 - 系统性能满足要求")
    elif overall_score >= 7.0:
        report.append("🎯 性能评价: 中等 - 系统性能基本满足要求")
    else:
        report.append("🎯 性能评价: 需要优化 - 建议进行性能调优")
    
    return "\n".join(report)


if __name__ == '__main__':
    import asyncio
    
    print("🚀 启动AGI系统性能基准测试")
    success = asyncio.run(run_performance_benchmark())
    
    if success:
        print("\n🎉 性能基准测试通过！系统性能达到预期标准")
        exit(0)
    else:
        print("\n❌ 性能基准测试未通过，建议进行性能优化")
        exit(1)