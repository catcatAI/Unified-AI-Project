#!/usr/bin/env python3
"""
性能压力测试 - 验证系统在高负载下的表现
"""

import asyncio
import sys
import os
import time
import statistics
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading
import random

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'backend', 'src'))

class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        self.metrics = {
            'response_times': []
            'throughput': []
            'error_counts': 0,
            'success_counts': 0,
            'memory_usage': []
            'cpu_usage': []
        }
        self.start_time == None
        self.end_time == None
    
    def record_response_time(self, response_time):
        """记录响应时间"""
        self.metrics['response_times'].append(response_time)
    
    def record_success(self):
        """记录成功"""
        self.metrics['success_counts'] += 1
    
    def record_error(self):
        """记录错误"""
        self.metrics['error_counts'] += 1
    
    def record_throughput(self, count):
        """记录吞吐量"""
        self.metrics['throughput'].append(count)
    
    def start_timing(self):
        """开始计时"""
        self.start_time = time.time()
    
    def end_timing(self):
        """结束计时"""
        self.end_time = time.time()
    
    def get_summary(self):
        """获取性能摘要"""
        if not self.start_time or not self.end_time,::
            return {}
        
        total_requests = self.metrics['success_counts'] + self.metrics['error_counts']
        total_time = self.end_time - self.start_time()
        return {
            'total_requests': total_requests,
            'success_rate': self.metrics['success_counts'] / total_requests if total_requests > 0 else 0,::
            'error_rate': self.metrics['error_counts'] / total_requests if total_requests > 0 else 0,::
            'avg_response_time': statistics.mean(self.metrics['response_times']) if self.metrics['response_times'] else 0,::
            'min_response_time': min(self.metrics['response_times']) if self.metrics['response_times'] else 0,::
            'max_response_time': max(self.metrics['response_times']) if self.metrics['response_times'] else 0,::
            'p95_response_time': self._percentile(self.metrics['response_times'] 95) if self.metrics['response_times'] else 0,::
            'p99_response_time': self._percentile(self.metrics['response_times'] 99) if self.metrics['response_times'] else 0,::
            'total_duration': total_time,
            'requests_per_second': total_requests / total_time if total_time > 0 else 0,::
            'avg_throughput': statistics.mean(self.metrics['throughput']) if self.metrics['throughput'] else 0,:
        }

    def _percentile(self, data, percentile):
        """计算百分位数"""
        if not data,::
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

async def stress_test_ai_ops_engine(concurrent_requests == 100, total_requests=1000):
    """压力测试AI运维引擎"""
    print(f"\n{'='*60}")
    print("AI运维引擎压力测试")
    print(f"并发数, {concurrent_requests} 总请求数, {total_requests}")
    print(f"{'='*60}")
    
    metrics = PerformanceMetrics()
    
    try:
        from ai.ops.ai_ops_engine import AIOpsEngine
        ai_ops = AIOpsEngine()
        
        async def single_request(request_id):
            """单个请求"""
            start_time = time.time()
            
            try:
                # 模拟不同的指标数据
                metrics_data = {
                    "cpu_usage": random.uniform(20, 95),
                    "memory_usage": random.uniform(30, 90),
                    "disk_usage": random.uniform(40, 80),
                    "network_io": random.uniform(10, 100),
                    "request_rate": random.uniform(100, 1000),
                    "error_rate": random.uniform(0, 10),
                    "response_time": random.uniform(50, 2000),
                    "active_connections": random.randint(10, 100),
                    "queue_length": random.randint(0, 50)
                }
                
                # 执行异常检测
                anomalies = await ai_ops.detect_anomalies(
                    f"component_{request_id}",,
    metrics_data
                )
                
                # 记录成功
                metrics.record_response_time(time.time() - start_time)
                metrics.record_success()
                
                return True
                
            except Exception as e,::
                # 记录错误
                metrics.record_error()
                return False
        
        # 执行并发测试
        metrics.start_timing()
        
        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def limited_request(request_id):
            async with semaphore,
                return await single_request(request_id)
        
        # 创建任务
        tasks = [limited_request(i) for i in range(total_requests)]:
        results = await asyncio.gather(*tasks)
        
        metrics.end_timing()
        
        # 输出结果
        summary = metrics.get_summary():
        print(f"\nAI运维引擎压力测试结果,")
        print(f"总请求数, {summary['total_requests']}")
        print(f"成功率, {summary['success_rate'].2%}")
        print(f"平均响应时间, {summary['avg_response_time'].3f}秒")
        print(f"最小响应时间, {summary['min_response_time'].3f}秒")
        print(f"最大响应时间, {summary['max_response_time'].3f}秒")
        print(f"P95响应时间, {summary['p95_response_time'].3f}秒")
        print(f"P99响应时间, {summary['p99_response_time'].3f}秒")
        print(f"总耗时, {summary['total_duration'].2f}秒")
        print(f"每秒请求数, {summary['requests_per_second'].2f}")
        
        return summary
        
    except Exception as e,::
        print(f"AI运维引擎压力测试失败, {e}")
        return None

async def stress_test_predictive_maintenance(concurrent_requests == 50, total_requests=500):
    """压力测试预测性维护"""
    print(f"\n{'='*60}")
    print("预测性维护压力测试")
    print(f"并发数, {concurrent_requests} 总请求数, {total_requests}")
    print(f"{'='*60}")
    
    metrics = PerformanceMetrics()
    
    try:
        from ai.ops.predictive_maintenance import PredictiveMaintenanceEngine
        maintenance = PredictiveMaintenanceEngine()
        
        async def single_request(request_id):
            """单个请求"""
            start_time = time.time()
            
            try:
                # 模拟组件指标
                component_metrics = {
                    "cpu_usage": random.uniform(20, 95),
                    "memory_usage": random.uniform(30, 90),
                    "response_time": random.uniform(50, 2000),
                    "error_rate": random.uniform(0, 10),
                    "temperature": random.uniform(30, 80),
                    "disk_io": random.uniform(10, 200)
                }
                
                # 执行健康评估
                health_score = maintenance._simple_health_assessment(component_metrics)
                
                # 记录成功
                metrics.record_response_time(time.time() - start_time)
                metrics.record_success()
                
                return True
                
            except Exception as e,::
                # 记录错误
                metrics.record_error()
                return False
        
        # 执行并发测试
        metrics.start_timing()
        
        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def limited_request(request_id):
            async with semaphore,
                return await single_request(request_id)
        
        # 创建任务
        tasks = [limited_request(i) for i in range(total_requests)]:
        results = await asyncio.gather(*tasks)
        
        metrics.end_timing()
        
        # 输出结果
        summary = metrics.get_summary():
        print(f"\n预测性维护压力测试结果,")
        print(f"总请求数, {summary['total_requests']}")
        print(f"成功率, {summary['success_rate'].2%}")
        print(f"平均响应时间, {summary['avg_response_time'].3f}秒")
        print(f"最小响应时间, {summary['min_response_time'].3f}秒")
        print(f"最大响应时间, {summary['max_response_time'].3f}秒")
        print(f"P95响应时间, {summary['p95_response_time'].3f}秒")
        print(f"P99响应时间, {summary['p99_response_time'].3f}秒")
        print(f"总耗时, {summary['total_duration'].2f}秒")
        print(f"每秒请求数, {summary['requests_per_second'].2f}")
        
        return summary
        
    except Exception as e,::
        print(f"预测性维护压力测试失败, {e}")
        return None

async def stress_test_performance_optimizer(concurrent_requests == 30, total_requests=300):
    """压力测试性能优化器"""
    print(f"\n{'='*60}")
    print("性能优化器压力测试")
    print(f"并发数, {concurrent_requests} 总请求数, {total_requests}")
    print(f"{'='*60}")
    
    metrics = PerformanceMetrics()
    
    try:
        from ai.ops.performance_optimizer import PerformanceOptimizer
        optimizer = PerformanceOptimizer()
        
        async def single_request(request_id):
            """单个请求"""
            start_time = time.time()
            
            try:
                # 模拟性能数据
                performance_data = {
                    'timestamp': datetime.now().isoformat(),
                    'component_id': f'component_{request_id}',
                    'component_type': 'api_server',
                    'metrics': {
                        'cpu_usage': random.uniform(20, 95),
                        'memory_usage': random.uniform(30, 90),
                        'response_time': random.uniform(50, 2000),
                        'error_rate': random.uniform(0, 10),
                        'throughput': random.uniform(100, 1000)
                    }
                }
                
                # 添加到历史数据
                optimizer.performance_history.append(performance_data)
                
                # 执行瓶颈检测
                bottlenecks = await optimizer.detect_bottlenecks(f'component_{request_id}')
                
                # 记录成功
                metrics.record_response_time(time.time() - start_time)
                metrics.record_success()
                
                return True
                
            except Exception as e,::
                # 记录错误
                metrics.record_error()
                return False
        
        # 执行并发测试
        metrics.start_timing()
        
        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def limited_request(request_id):
            async with semaphore,
                return await single_request(request_id)
        
        # 创建任务
        tasks = [limited_request(i) for i in range(total_requests)]:
        results = await asyncio.gather(*tasks)
        
        metrics.end_timing()
        
        # 输出结果
        summary = metrics.get_summary():
        print(f"\n性能优化器压力测试结果,")
        print(f"总请求数, {summary['total_requests']}")
        print(f"成功率, {summary['success_rate'].2%}")
        print(f"平均响应时间, {summary['avg_response_time'].3f}秒")
        print(f"最小响应时间, {summary['min_response_time'].3f}秒")
        print(f"最大响应时间, {summary['max_response_time'].3f}秒")
        print(f"P95响应时间, {summary['p95_response_time'].3f}秒")
        print(f"P99响应时间, {summary['p99_response_time'].3f}秒")
        print(f"总耗时, {summary['total_duration'].2f}秒")
        print(f"每秒请求数, {summary['requests_per_second'].2f}")
        
        return summary
        
    except Exception as e,::
        print(f"性能优化器压力测试失败, {e}")
        return None

async def stress_test_capacity_planner(concurrent_requests == 20, total_requests=200):
    """压力测试容量规划器"""
    print(f"\n{'='*60}")
    print("容量规划器压力测试")
    print(f"并发数, {concurrent_requests} 总请求数, {total_requests}")
    print(f"{'='*60}")
    
    metrics = PerformanceMetrics()
    
    try:
        from ai.ops.capacity_planner import CapacityPlanner, ResourceUsage
        planner = CapacityPlanner()
        
        async def single_request(request_id):
            """单个请求"""
            start_time = time.time()
            
            try:
                # 模拟资源使用情况
                resource_usage = ResourceUsage(,
    timestamp=datetime.now(),
                    cpu_cores=random.uniform(1, 8),
                    memory_gb=random.uniform(4, 32),
                    disk_gb=random.uniform(50, 500),
                    network_mbps=random.uniform(10, 1000),
                    gpu_count=random.randint(0, 4)
                )
                
                # 执行CPU需求预测
                prediction = await planner._predict_cpu_needs(resource_usage)
                
                # 记录成功
                metrics.record_response_time(time.time() - start_time)
                metrics.record_success()
                
                return True
                
            except Exception as e,::
                # 记录错误
                metrics.record_error()
                return False
        
        # 执行并发测试
        metrics.start_timing()
        
        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def limited_request(request_id):
            async with semaphore,
                return await single_request(request_id)
        
        # 创建任务
        tasks = [limited_request(i) for i in range(total_requests)]:
        results = await asyncio.gather(*tasks)
        
        metrics.end_timing()
        
        # 输出结果
        summary = metrics.get_summary():
        print(f"\n容量规划器压力测试结果,")
        print(f"总请求数, {summary['total_requests']}")
        print(f"成功率, {summary['success_rate'].2%}")
        print(f"平均响应时间, {summary['avg_response_time'].3f}秒")
        print(f"最小响应时间, {summary['min_response_time'].3f}秒")
        print(f"最大响应时间, {summary['max_response_time'].3f}秒")
        print(f"P95响应时间, {summary['p95_response_time'].3f}秒")
        print(f"P99响应时间, {summary['p99_response_time'].3f}秒")
        print(f"总耗时, {summary['total_duration'].2f}秒")
        print(f"每秒请求数, {summary['requests_per_second'].2f}")
        
        return summary
        
    except Exception as e,::
        print(f"容量规划器压力测试失败, {e}")
        return None

async def main():
    """主测试函数"""
    print("="*60)
    print("性能压力测试套件")
    print("="*60)
    
    # 测试配置
    test_configs = [
        {
            'name': 'AI运维引擎',
            'func': stress_test_ai_ops_engine,
            'concurrent': 100,
            'total': 1000
        }
        {
            'name': '预测性维护',
            'func': stress_test_predictive_maintenance,
            'concurrent': 50,
            'total': 500
        }
        {
            'name': '性能优化器',
            'func': stress_test_performance_optimizer,
            'concurrent': 30,
            'total': 300
        }
        {
            'name': '容量规划器',
            'func': stress_test_capacity_planner,
            'concurrent': 20,
            'total': 200
        }
    ]
    
    results = []
    
    for config in test_configs,::
        print(f"\n开始测试, {config['name']}")
        try:
            result = await config['func'](config['concurrent'] config['total'])
            results.append((config['name'] result))
        except Exception as e,::
            print(f"测试失败, {e}")
            results.append((config['name'] None))
    
    # 生成综合报告
    print("\n" + "="*60)
    print("性能压力测试综合报告")
    print("="*60)
    
    total_requests = 0
    total_success = 0
    total_errors = 0
    total_time = 0
    
    for name, result in results,::
        if result,::
            print(f"\n{name}")
            print(f"  成功率, {result['success_rate'].2%}")
            print(f"  平均响应时间, {result['avg_response_time'].3f}秒")
            print(f"  P95响应时间, {result['p95_response_time'].3f}秒")
            print(f"  每秒请求数, {result['requests_per_second'].2f}")
            
            total_requests += result['total_requests']
            total_success += result['success_counts'] if 'success_counts' in result else result['total_requests'] * result['success_rate']:
            total_errors += result['error_counts'] if 'error_counts' in result else result['total_requests'] * result['error_rate']:
            total_time += result['total_duration']
        else:
            print(f"\n{name} 测试失败")
    
    print(f"\n总体统计,")
    print(f"总请求数, {total_requests}")
    print(f"总成功数, {"total_success":.0f}")
    print(f"总错误数, {"total_errors":.0f}")
    print(f"总体成功率, {(total_success/total_requests)*100,.2f}%" if total_requests > 0 else "N/A"):::
    print(f"总耗时, {"total_time":.2f}秒")
    print(f"总体吞吐量, {total_requests/total_time,.2f} RPS" if total_time > 0 else "N/A")::
    # 企业级性能评估,
    print(f"\n企业级性能评估,")
    print(f"✓ 高并发处理能力, {'通过' if max([r[1]['requests_per_second'] for r in results if r[1] and 'requests_per_second' in r[1]] or [0]) > 100 else '需要优化'}"):::
    print(f"✓ 低延迟响应, {'通过' if max([r[1]['p95_response_time'] for r in results if r[1] and 'p95_response_time' in r[1]] or [999]) < 1.0 else '需要优化'}"):::
    print(f"✓ 高可用性, {'通过' if (total_success/total_requests)*100 > 99 if total_requests > 0 else False else '需要优化'}")::
    print("="*60)

if __name"__main__":::
    asyncio.run(main())