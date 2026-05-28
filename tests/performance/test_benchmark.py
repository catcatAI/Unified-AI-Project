#!/usr/bin/env python3
"""
性能基准测试 - 与企业级标准对比
"""

import asyncio
import time
import statistics
from datetime import datetime

class EnterpriseBenchmark:
    """企业级性能基准"""
    
    # 企业级性能标准
    ENTERPRISE_STANDARDS = {
        'response_time': {
            'p50': 0.1,  # 50%请求响应时间 < 100ms
            'p95': 0.5,  # 95%请求响应时间 < 500ms
            'p99': 1.0,  # 99%请求响应时间 < 1000ms
        },
        'throughput': {
            'min_rps': 1000,  # 最小每秒请求数
            'target_rps': 5000,  # 目标每秒请求数
        },
        'availability': {
            'min': 99.9,  # 最小可用性 99.9%
            'target': 99.99,  # 目标可用性 99.99%
        },
        'resource_usage': {
            'cpu_max': 80,  # CPU使用率不超过80%
            'memory_max': 85,  # 内存使用率不超过85%
        },
        'concurrency': {
            'min_concurrent': 100,  # 最小并发数
            'target_concurrent': 1000,  # 目标并发数
        }
    }
    
    def __init__(self):
        self.test_results = {}
    
    def evaluate_performance(self, component_name, metrics):
        """评估性能是否符合企业标准"""
        results = {
            'component': component_name,
            'metrics': metrics,
            'passed': [],
            'failed': [],
            'score': 0
        }
        
        # 评估响应时间
        if 'p95_response_time' in metrics:
            if metrics['p95_response_time'] <= self.ENTERPRISE_STANDARDS['response_time']['p95']:
                results['passed'].append(f"P95响应时间 {metrics['p95_response_time']:.3f}s < {self.ENTERPRISE_STANDARDS['response_time']['p95']}s")
            else:
                results['failed'].append(f"P95响应时间 {metrics['p95_response_time']:.3f}s > {self.ENTERPRISE_STANDARDS['response_time']['p95']}s")
        
        if 'p99_response_time' in metrics:
            if metrics['p99_response_time'] <= self.ENTERPRISE_STANDARDS['response_time']['p99']:
                results['passed'].append(f"P99响应时间 {metrics['p99_response_time']:.3f}s < {self.ENTERPRISE_STANDARDS['response_time']['p99']}s")
            else:
                results['failed'].append(f"P99响应时间 {metrics['p99_response_time']:.3f}s > {self.ENTERPRISE_STANDARDS['response_time']['p99']}s")
        
        # 评估吞吐量
        if 'requests_per_second' in metrics:
            if metrics['requests_per_second'] >= self.ENTERPRISE_STANDARDS['throughput']['min_rps']:
                results['passed'].append(f"吞吐量 {metrics['requests_per_second']:.2f} RPS >= {self.ENTERPRISE_STANDARDS['throughput']['min_rps']} RPS")
            else:
                results['failed'].append(f"吞吐量 {metrics['requests_per_second']:.2f} RPS < {self.ENTERPRISE_STANDARDS['throughput']['min_rps']} RPS")
        
        # 评估可用性
        if 'success_rate' in metrics:
            availability = metrics['success_rate'] * 100
            if availability >= self.ENTERPRISE_STANDARDS['availability']['min']:
                results['passed'].append(f"可用性 {availability:.2f}% >= {self.ENTERPRISE_STANDARDS['availability']['min']}%")
            else:
                results['failed'].append(f"可用性 {availability:.2f}% < {self.ENTERPRISE_STANDARDS['availability']['min']}%")
        
        # 计算得分
        total_checks = len(results['passed']) + len(results['failed'])
        if total_checks > 0:
            results['score'] = (len(results['passed']) / total_checks) * 100
        
        return results

async def benchmark_ai_ops_engine():
    """AI运维引擎基准测试"""
    print("\n" + "="*60)
    print("AI运维引擎基准测试")
    print("="*60)
    
    try:
        from ai.ops.ai_ops_engine import AIOpsEngine
        ai_ops = AIOpsEngine()
        
        # 测试参数
        test_cases = [
            {'concurrent': 100, 'total': 1000, 'name': '标准负载'},
            {'concurrent': 500, 'total': 5000, 'name': '高负载'},
            {'concurrent': 1000, 'total': 10000, 'name': '极限负载'},
        ]
        
        results = []
        
        for test_case in test_cases:
            print(f"\n测试场景, {test_case['name']} (并发, {test_case['concurrent']} 总数, {test_case['total']})")
            
            # 执行测试
            response_times = []
            success_count = 0
            error_count = 0
            
            start_time = time.time()
            
            # 使用信号量控制并发
            semaphore = asyncio.Semaphore(test_case['concurrent'])
            
            async def single_request():
                nonlocal success_count, error_count
                async with semaphore:
                    req_start = time.time()
                    try:
                        anomalies = await ai_ops.detect_anomalies(
                            "test_component",
                            {
                                "cpu_usage": 85.0,
                                "memory_usage": 75.0,
                                "error_rate": 2.5,
                                "response_time": 450
                            }
                        )
                        response_times.append(time.time() - req_start)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
            
            # 创建任务
            tasks = [single_request() for _ in range(test_case['total'])]
            await asyncio.gather(*tasks)
            
            end_time = time.time()
            
            # 计算指标
            total_requests = success_count + error_count
            duration = end_time - start_time
            
            metrics = {
                'total_requests': total_requests,
                'success_rate': success_count / total_requests if total_requests > 0 else 0,
                'error_rate': error_count / total_requests if total_requests > 0 else 0,
                'avg_response_time': statistics.mean(response_times) if response_times else 0,
                'min_response_time': min(response_times) if response_times else 0,
                'max_response_time': max(response_times) if response_times else 0,
                'p95_response_time': sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0,
                'p99_response_time': sorted(response_times)[int(len(response_times) * 0.99)] if response_times else 0,
                'total_duration': duration,
                'requests_per_second': total_requests / duration if duration > 0 else 0,
            }
            
            results.append((test_case['name'], metrics))
            
            # 输出结果
            print(f"  成功率, {metrics['success_rate']:.2%}")
            print(f"  平均响应时间, {metrics['avg_response_time']:.3f}s")
            print(f"  P95响应时间, {metrics['p95_response_time']:.3f}s")
            print(f"  P99响应时间, {metrics['p99_response_time']:.3f}s")
            print(f"  每秒请求数, {metrics['requests_per_second']:.2f}")
        
        return results
        
    except Exception as e:
        print(f"AI运维引擎基准测试失败, {e}")
        return []

async def benchmark_predictive_maintenance():
    """预测性维护基准测试"""
    print("\n" + "="*60)
    print("预测性维护基准测试")
    print("="*60)
    
    try:
        from ai.ops.predictive_maintenance import PredictiveMaintenanceEngine
        maintenance = PredictiveMaintenanceEngine()
        
        # 测试参数
        test_cases = [
            {'concurrent': 50, 'total': 500, 'name': '标准负载'},
            {'concurrent': 200, 'total': 2000, 'name': '高负载'},
            {'concurrent': 500, 'total': 5000, 'name': '极限负载'},
        ]
        
        results = []
        
        for test_case in test_cases:
            print(f"\n测试场景, {test_case['name']} (并发, {test_case['concurrent']} 总数, {test_case['total']})")
            
            # 执行测试
            response_times = []
            success_count = 0
            error_count = 0
            
            start_time = time.time()
            
            # 使用信号量控制并发
            semaphore = asyncio.Semaphore(test_case['concurrent'])
            
            async def single_request():
                nonlocal success_count, error_count
                async with semaphore:
                    req_start = time.time()
                    try:
                        health_score = maintenance._simple_health_assessment({
                            "cpu_usage": 75.0,
                            "memory_usage": 60.0,
                            "response_time": 300,
                            "error_rate": 1.0
                        })
                        response_times.append(time.time() - req_start)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
            
            # 创建任务
            tasks = [single_request() for _ in range(test_case['total'])]
            await asyncio.gather(*tasks)
            
            end_time = time.time()
            
            # 计算指标
            total_requests = success_count + error_count
            duration = end_time - start_time
            
            metrics = {
                'total_requests': total_requests,
                'success_rate': success_count / total_requests if total_requests > 0 else 0,
                'error_rate': error_count / total_requests if total_requests > 0 else 0,
                'avg_response_time': statistics.mean(response_times) if response_times else 0,
                'min_response_time': min(response_times) if response_times else 0,
                'max_response_time': max(response_times) if response_times else 0,
                'p95_response_time': sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0,
                'p99_response_time': sorted(response_times)[int(len(response_times) * 0.99)] if response_times else 0,
                'total_duration': duration,
                'requests_per_second': total_requests / duration if duration > 0 else 0,
            }
            
            results.append((test_case['name'], metrics))
            
            # 输出结果
            print(f"  成功率, {metrics['success_rate']:.2%}")
            print(f"  平均响应时间, {metrics['avg_response_time']:.3f}s")
            print(f"  P95响应时间, {metrics['p95_response_time']:.3f}s")
            print(f"  P99响应时间, {metrics['p99_response_time']:.3f}s")
            print(f"  每秒请求数, {metrics['requests_per_second']:.2f}")
        
        return results
        
    except Exception as e:
        print(f"预测性维护基准测试失败, {e}")
        return []

async def main():
    """主测试函数"""
    print("="*60)
    print("企业级性能基准测试")
    print("="*60)
    
    benchmark = EnterpriseBenchmark()
    
    # 执行基准测试
    ai_ops_results = await benchmark_ai_ops_engine()
    maintenance_results = await benchmark_predictive_maintenance()
    
    # 评估结果
    print("\n" + "="*60)
    print("企业级性能评估报告")
    print("="*60)
    
    all_results = []
    
    # 评估AI运维引擎
    for test_name, metrics in ai_ops_results:
        evaluation = benchmark.evaluate_performance(f"AI运维引擎-{test_name}", metrics)
        all_results.append(evaluation)
        
        print(f"\n{evaluation['component']}")
        print(f"  总体得分, {evaluation['score']:.1f}/100")
        if evaluation['passed']:
            print("  ✅ 通过项,")
            for item in evaluation['passed']:
                print(f"    - {item}")
        if evaluation['failed']:
            print("  ❌ 失败项,")
            for item in evaluation['failed']:
                print(f"    - {item}")
    
    # 评估预测性维护
    for test_name, metrics in maintenance_results:
        evaluation = benchmark.evaluate_performance(f"预测性维护-{test_name}", metrics)
        all_results.append(evaluation)
        
        print(f"\n{evaluation['component']}")
        print(f"  总体得分, {evaluation['score']:.1f}/100")
        if evaluation['passed']:
            print("  ✅ 通过项,")
            for item in evaluation['passed']:
                print(f"    - {item}")
        if evaluation['failed']:
            print("  ❌ 失败项,")
            for item in evaluation['failed']:
                print(f"    - {item}")
    
    # 总体评估
    if all_results:
        avg_score = statistics.mean([r['score'] for r in all_results])
        print(f"\n{'='*60}")
        print(f"总体企业级性能得分, {avg_score:.1f}/100")
        
        if avg_score >= 90:
            print("🏆 优秀 - 达到企业级高性能标准")
        elif avg_score >= 80:
            print("✅ 良好 - 基本达到企业级标准")
        elif avg_score >= 70:
            print("⚠️  一般 - 需要优化以满足企业级要求")
        else:
            print("❌ 不达标 - 需要重大改进")
        
        # 建议
        print("\n优化建议,")
        all_failed = [item for r in all_results for item in r['failed']]
        if all_failed:
            print("- 需要关注的性能问题,")
            for item in set(all_failed):
                print(f"  • {item}")
        else:
            print("- 系统性能已达到企业级标准")
    
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
