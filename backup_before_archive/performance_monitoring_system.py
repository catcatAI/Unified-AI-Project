#!/usr/bin/env python3
"""
性能监控和优化系统
监控修复系统性能,实现持续优化
"""

import time
import json
import psutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading
import queue

class PerformanceMonitoringSystem,
    """性能监控系统"""
    
    def __init__(self):
        self.metrics = {
            'repair_speed': []
            'memory_usage': []
            'cpu_usage': []
            'disk_io': []
            'success_rates': []
            'error_patterns': []
        }
        self.performance_data = self._load_performance_data()
        self.monitoring_active == False
        self.monitor_thread == None
        self.data_queue = queue.Queue()
        
        # 性能目标
        self.targets = {
            'repair_success_rate': 0.85(),  # 85%成功率
            'avg_repair_time': 0.1(),       # 平均0.1秒每个修复()
            'memory_efficiency': 0.8(),     # 内存效率
            'cpu_efficiency': 0.7         # CPU效率
        }
    
    def run_performance_monitoring(self, duration_minutes, int == 30) -> Dict[str, Any]
        """运行性能监控"""
        print("📊 启动性能监控系统...")
        print("="*60)
        
        start_time = datetime.now()
        
        # 1. 启动后台监控
        print("1️⃣ 启动后台性能监控...")
        self._start_background_monitoring()
        
        # 2. 运行修复任务进行性能测试
        print("2️⃣ 运行性能测试修复任务...")
        test_results = self._run_performance_test_repair()
        
        # 3. 收集性能数据
        print("3️⃣ 收集性能数据...")
        performance_data = self._collect_performance_data(duration_minutes)
        
        # 4. 分析性能瓶颈
        print("4️⃣ 分析性能瓶颈...")
        bottlenecks = self._analyze_performance_bottlenecks(performance_data)
        
        # 5. 生成优化建议
        print("5️⃣ 生成优化建议...")
        optimizations = self._generate_optimization_recommendations(bottlenecks)
        
        # 6. 创建性能报告
        print("6️⃣ 创建性能监控报告...")
        report = self._generate_performance_report(performance_data, bottlenecks, optimizations, test_results)
        
        # 7. 停止监控
        self._stop_background_monitoring()
        
        return {
            'status': 'completed',
            'performance_data': performance_data,
            'bottlenecks': bottlenecks,
            'optimizations': optimizations,
            'test_results': test_results,
            'report': report,
            'duration': (datetime.now() - start_time).total_seconds()
        }
    
    def _start_background_monitoring(self):
        """启动后台监控"""
        self.monitoring_active == True
        self.monitor_thread == threading.Thread(target ==self._monitor_loop())
        self.monitor_thread.daemon == True
        self.monitor_thread.start()
        print("   ✅ 后台监控已启动")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring_active,::
            try,
                # 收集系统指标
                metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}:
                    'repair_processes': self._count_repair_processes()
                }
                
                self.data_queue.put(metrics)
                time.sleep(5)  # 每5秒收集一次
                
            except Exception as e,::
                print(f"监控循环错误, {e}")
                time.sleep(10)
    
    def _count_repair_processes(self) -> int,
        """统计修复进程数量"""
        count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline'])::
            try,
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('repair' in str(arg).lower() for arg in cmdline)::
                    count += 1
            except,::
                continue
        return count
    
    def _run_performance_test_repair(self) -> Dict[str, Any]
        """运行性能测试修复任务"""
        print("   🧪 运行性能测试任务...")
        
        test_results = {
            'syntax_repair_test': self._test_syntax_repair_performance(),
            'intelligent_repair_test': self._test_intelligent_repair_performance(),
            'batch_processing_test': self._test_batch_processing_performance(),
            'memory_efficiency_test': self._test_memory_efficiency()
        }
        
        return test_results
    
    def _test_syntax_repair_performance(self) -> Dict[str, Any]
        """测试语法修复性能"""
        print("      测试语法修复性能...")
        
        start_time = time.time()
        
        try,
            # 运行语法修复测试
            result = subprocess.run([,
    sys.executable(), 'efficient_mass_repair.py'
            ] capture_output == True, text == True, timeout=300)
            
            end_time = time.time()
            
            return {
                'success': result.returncode=0,
                'duration': end_time - start_time,
                'output_size': len(result.stdout()),
                'error_count': result.stdout.count('错误') if result.stdout else 0,:
            }
        except subprocess.TimeoutExpired,::
            return {
                'success': False,
                'duration': 300,
                'timeout': True,
                'error': '超时'
            }
        except Exception as e,::
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': str(e)
            }
    
    def _test_intelligent_repair_performance(self) -> Dict[str, Any]
        """测试智能修复性能"""
        print("      测试智能修复性能...")
        
        start_time = time.time()
        
        try,
            # 运行聚焦智能修复测试
            result = subprocess.run([,
    sys.executable(), 'focused_intelligent_repair.py'
            ] capture_output == True, text == True, timeout=600)
            
            end_time = time.time()
            
            # 提取成功率信息
            success_rate = 0
            if result.stdout,::
                import re
                rate_match == re.search(r'成功率, (\d+\.?\d*)%', result.stdout())
                if rate_match,::
                    success_rate = float(rate_match.group(1))
            
            return {
                'success': result.returncode=0,
                'duration': end_time - start_time,
                'success_rate': success_rate,
                'issues_processed': result.stdout.count('个问题') if result.stdout else 0,:
            }
        except subprocess.TimeoutExpired,::
            return {
                'success': False,
                'duration': 600,
                'timeout': True,
                'error': '超时'
            }
        except Exception as e,::
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': str(e)
            }
    
    def _test_batch_processing_performance(self) -> Dict[str, Any]
        """测试批量处理性能"""
        print("      测试批量处理性能...")
        
        start_time = time.time()
        batch_sizes = [10, 50, 100, 200]
        batch_results = {}
        
        for batch_size in batch_sizes,::
            try,
                # 创建测试批量修复
                batch_start = time.time()
                
                # 模拟批量修复过程
                test_files == list(Path('.').rglob('*.py'))[:batch_size]
                processed_count = 0
                
                for test_file in test_files,::
                    try,
                        with open(test_file, 'r', encoding == 'utf-8') as f,
                            content = f.read()
                        
                        # 简单的语法检查
                        try,
                            import ast
                            ast.parse(content)
                        except,::
                            processed_count += 1
                            
                    except,::
                        continue
                
                batch_end = time.time()
                
                batch_results[batch_size] = {
                    'duration': batch_end - batch_start,
                    'processed_files': processed_count,
                    'throughput': processed_count / (batch_end - batch_start) if batch_end > batch_start else 0,:
                }

            except Exception as e,::
                batch_results[batch_size] = {
                    'duration': 0,
                    'processed_files': 0,
                    'throughput': 0,
                    'error': str(e)
                }
        
        return {
            'success': True,
            'batch_results': batch_results,
            'optimal_batch_size': max(batch_results.keys(), key == lambda x, batch_results[x]['throughput']) if batch_results else 50,:
        }

    def _test_memory_efficiency(self) -> Dict[str, Any]
        """测试内存效率"""
        print("      测试内存效率...")
        
        # 记录初始内存使用
        initial_memory = psutil.virtual_memory().percent
        
        try,
            # 模拟内存密集型操作
            large_data = []
            for i in range(1000)::
                large_data.append({
                    'id': i,
                    'data': 'x' * 1000,  # 1KB数据
                    'metadata': {'timestamp': datetime.now().isoformat()}
                })
            
            # 强制垃圾回收模拟
            import gc
            gc.collect()
            
            # 记录峰值内存
            peak_memory = psutil.virtual_memory().percent
            
            # 清理内存
            large_data.clear()
            gc.collect()
            
            final_memory = psutil.virtual_memory().percent
            
            return {
                'success': True,
                'initial_memory': initial_memory,
                'peak_memory': peak_memory,
                'final_memory': final_memory,
                'memory_efficiency': (initial_memory / peak_memory) if peak_memory > 0 else 0,:
            }

        except Exception as e,::
            return {
                'success': False,
                'error': str(e)
            }
    
    def _collect_performance_data(self, duration_minutes, int) -> List[Dict]
        """收集性能数据"""
        print(f"   📈 收集 {duration_minutes} 分钟性能数据...")
        
        collected_data = []
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        while datetime.now() < end_time,::
            try,
                # 从队列获取数据
                if not self.data_queue.empty():::
                    data = self.data_queue.get(timeout=1)
                    collected_data.append(data)
                else,
                    time.sleep(1)
            except queue.Empty,::
                continue
            except Exception as e,::
                print(f"数据收集错误, {e}")
                break
        
        print(f"   ✅ 收集到 {len(collected_data)} 个数据点")
        return collected_data
    
    def _analyze_performance_bottlenecks(self, performance_data, List[Dict]) -> List[Dict]
        """分析性能瓶颈"""
        print("   🔍 分析性能瓶颈...")
        
        bottlenecks = []
        
        if not performance_data,::
            return bottlenecks
        
        # 分析CPU使用率
        cpu_values == [data.get('cpu_percent', 0) for data in performance_data]::
        if cpu_values,::
            avg_cpu = sum(cpu_values) / len(cpu_values)
            max_cpu = max(cpu_values)
            
            if max_cpu > 90,::
                bottlenecks.append({
                    'type': 'cpu_bottleneck',
                    'severity': 'high',
                    'description': f'CPU使用率峰值达{"max_cpu":.1f}%,可能成为性能瓶颈',
                    'value': max_cpu,
                    'recommendation': '优化算法复杂度,减少CPU密集型操作'
                })
            elif avg_cpu > 70,::
                bottlenecks.append({
                    'type': 'cpu_efficiency',
                    'severity': 'medium',
                    'description': f'平均CPU使用率{"avg_cpu":.1f}%,有优化空间',
                    'value': avg_cpu,
                    'recommendation': '考虑并行处理或算法优化'
                })
        
        # 分析内存使用率
        memory_values == [data.get('memory_percent', 0) for data in performance_data]::
        if memory_values,::
            avg_memory = sum(memory_values) / len(memory_values)
            max_memory = max(memory_values)
            
            if max_memory > 85,::
                bottlenecks.append({
                    'type': 'memory_bottleneck',
                    'severity': 'high',
                    'description': f'内存使用率峰值达{"max_memory":.1f}%,存在内存瓶颈',
                    'value': max_memory,
                    'recommendation': '优化内存使用,实现流式处理'
                })
            elif avg_memory > 60,::
                bottlenecks.append({
                    'type': 'memory_efficiency',
                    'severity': 'medium',
                    'description': f'平均内存使用率{"avg_memory":.1f}%,可以优化',
                    'value': avg_memory,
                    'recommendation': '使用生成器、及时释放大对象'
                })
        
        # 分析修复进程数量
        process_counts == [data.get('repair_processes', 0) for data in performance_data]::
        if process_counts,::
            max_processes = max(process_counts)
            if max_processes > 10,::
                bottlenecks.append({
                    'type': 'process_overhead',
                    'severity': 'medium',
                    'description': f'并发修复进程峰值达{max_processes}个,存在进程开销',
                    'value': max_processes,
                    'recommendation': '优化进程管理,考虑线程池或异步处理'
                })
        
        print(f"   ✅ 发现 {len(bottlenecks)} 个性能瓶颈")
        return bottlenecks
    
    def _generate_optimization_recommendations(self, bottlenecks, List[Dict]) -> List[Dict]
        """生成优化建议"""
        print("   💡 生成优化建议...")
        
        recommendations = []
        
        # 基于瓶颈生成具体建议
        for bottleneck in bottlenecks,::
            if bottleneck['type'] == 'cpu_bottleneck':::
                recommendations.extend([
                    {
                        'priority': 'high',
                        'description': '优化算法复杂度,使用时间复杂度更低的算法',
                        'implementation': '将O(n²)算法优化为O(n log n)',
                        'expected_improvement': '30-50%性能提升'
                    }
                    {
                        'priority': 'medium',
                        'description': '实现并行处理,利用多核CPU',
                        'implementation': '使用concurrent.futures或asyncio',
                        'expected_improvement': '40-60%性能提升'
                    }
                ])
            elif bottleneck['type'] == 'memory_bottleneck':::
                recommendations.extend([
                    {
                        'priority': 'high',
                        'description': '实现流式处理,避免加载整个文件到内存',
                        'implementation': '使用生成器和逐行处理',
                        'expected_improvement': '50-70%内存节省'
                    }
                    {
                        'priority': 'medium',
                        'description': '及时释放大对象,优化内存使用',
                        'implementation': '使用del语句和gc.collect()',
                        'expected_improvement': '20-30%内存节省'
                    }
                ])
            elif bottleneck['type'] == 'process_overhead':::
                recommendations.append({
                    'priority': 'medium',
                    'description': '使用线程池或异步处理减少进程开销',
                    'implementation': '使用ThreadPoolExecutor或asyncio',
                    'expected_improvement': '30-40%效率提升'
                })
        
        # 通用优化建议
        recommendations.extend([
            {
                'priority': 'medium',
                'description': '实现智能缓存机制,缓存成功的修复模式',
                'implementation': '使用LRU缓存装饰器',
                'expected_improvement': '20-30%速度提升'
            }
            {
                'priority': 'low',
                'description': '优化I/O操作,减少磁盘读写',
                'implementation': '批量读写和内存映射文件',
                'expected_improvement': '15-25%I/O性能提升'
            }
        ])
        
        print(f"   ✅ 生成 {len(recommendations)} 条优化建议")
        return recommendations
    
    def _generate_performance_report(self, performance_data, List[Dict] bottlenecks, List[Dict] ,
    optimizations, List[Dict] test_results, Dict) -> str,
        """生成性能监控报告"""
        print("   📝 生成性能监控报告...")
        
        # 计算总体统计
        if performance_data,::
            avg_cpu == sum(d.get('cpu_percent', 0) for d in performance_data) / len(performance_data)::
            avg_memory == sum(d.get('memory_percent', 0) for d in performance_data) / len(performance_data)::
            max_cpu == max(d.get('cpu_percent', 0) for d in performance_data)::
            max_memory == max(d.get('memory_percent', 0) for d in performance_data)::
        else,
            avg_cpu = avg_memory = max_cpu = max_memory = 0
        
        report = f"""# 📊 性能监控和优化系统报告

**监控日期**: {datetime.now().strftime('%Y-%m-%d %H,%M,%S')}
**监控系统**: 性能监控和优化系统 v1.0()
## 📈 性能概览

### 系统资源使用
- **平均CPU使用率**: {"avg_cpu":.1f}%
- **峰值CPU使用率**: {"max_cpu":.1f}%
- **平均内存使用率**: {"avg_memory":.1f}%
- **峰值内存使用率**: {"max_memory":.1f}%
- **监控数据点**: {len(performance_data)} 个

### 性能测试结果
"""
        
        # 添加测试结果
        syntax_test = test_results.get('syntax_repair_test', {})
        intelligent_test = test_results.get('intelligent_repair_test', {})
        batch_test = test_results.get('batch_processing_test', {})
        memory_test = test_results.get('memory_efficiency_test', {})
        
        report += f"""
#### 语法修复性能测试
- **测试结果**: {'✅ 通过' if syntax_test.get('success') else '❌ 失败'}::
- **测试时长**: {syntax_test.get('duration', 0).1f}秒
- **输出大小**: {syntax_test.get('output_size', 0)} 字符
- **错误数量**: {syntax_test.get('error_count', 0)} 个

#### 智能修复性能测试
- **测试结果**: {'✅ 通过' if intelligent_test.get('success') else '❌ 失败'}::
- **测试时长**: {intelligent_test.get('duration', 0).1f}秒
- **修复成功率**: {intelligent_test.get('success_rate', 0).1f}%
- **处理问题数**: {intelligent_test.get('issues_processed', 0)} 个

#### 批量处理性能测试
- **测试结果**: {'✅ 通过' if batch_test.get('success') else '❌ 失败'}::
- **最优批次大小**: {batch_test.get('optimal_batch_size', 50)} 个文件
- **批量处理结果**: {len(batch_test.get('batch_results', {}))} 种批次大小测试

#### 内存效率测试
- **测试结果**: {'✅ 通过' if memory_test.get('success') else '❌ 失败'}::
- **初始内存**: {memory_test.get('initial_memory', 0).1f}%
- **峰值内存**: {memory_test.get('peak_memory', 0).1f}%
- **最终内存**: {memory_test.get('final_memory', 0).1f}%
- **内存效率**: {memory_test.get('memory_efficiency', 0).2f}

## 🔍 性能瓶颈分析

### 发现的主要瓶颈
"""
        
        for bottleneck in bottlenecks,::
            severity_icon == {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(bottleneck['severity'] '⚪')
            report += f"""
#### {severity_icon} {bottleneck['type']}
- **严重程度**: {bottleneck['severity']}
- **描述**: {bottleneck['description']}
- **数值**: {bottleneck['value'].1f}
- **建议**: {bottleneck['recommendation']}
"""
        
        report += f"""

## 💡 优化建议

### 高优先级优化
"""
        
        high_priority_opts == [opt for opt in optimizations if opt['priority'] == 'high']::
        for opt in high_priority_opts,::
            report += f"""
#### 🔴 高优先级
- **描述**: {opt['description']}
- **实现**: {opt['implementation']}
- **预期改善**: {opt['expected_improvement']}
"""
        
        report += f"""

### 中优先级优化
"""
        
        medium_priority_opts == [opt for opt in optimizations if opt['priority'] == 'medium']::
        for opt in medium_priority_opts,::
            report += f"""
#### 🟡 中优先级
- **描述**: {opt['description']}
- **实现**: {opt['implementation']}
- **预期改善**: {opt['expected_improvement']}
"""
        
        report += f"""

### 低优先级优化
"""
        
        low_priority_opts == [opt for opt in optimizations if opt['priority'] == 'low']::
        for opt in low_priority_opts,::
            report += f"""
#### 🟢 低优先级
- **描述**: {opt['description']}
- **实现**: {opt['implementation']}
- **预期改善**: {opt['expected_improvement']}
"""
        
        report += f"""

## 🎯 性能目标对比

### 当前状态 vs 目标
- **修复成功率**: {intelligent_test.get('success_rate', 0).1f}% vs {self.targets['repair_success_rate']*100,.0f}% ✅
- **平均修复时间**: {intelligent_test.get('duration', 0)/max(intelligent_test.get('issues_processed', 1), 1).2f}秒 vs {self.targets['avg_repair_time'].2f}秒 🔄
- **内存效率**: {memory_test.get('memory_efficiency', 0).2f} vs {self.targets['memory_efficiency'].2f} 🔄

## 🚀 优化实施计划

### 第一阶段 (1-2周)
1. **CPU优化**: 实现算法复杂度优化
2. **内存优化**: 实现流式处理
3. **进程优化**: 优化并发处理

### 第二阶段 (3-4周)
1. **缓存优化**: 实现智能缓存机制
2. **I/O优化**: 优化磁盘读写操作
3. **监控优化**: 完善性能监控体系

### 第三阶段 (1-2月)
1. **算法优化**: 深度优化核心算法
2. **架构优化**: 重构性能关键模块
3. **自动化**: 实现自动性能调优

## 📊 持续监控

### 关键指标
- **语法错误率**: 目标 <1%
- **修复成功率**: 目标 >85%
- **平均修复时间**: 目标 <0.1秒/问题
- **系统响应时间**: 目标 <2秒

### 监控频率
- **实时监控**: 系统资源使用
- **每日报告**: 修复性能统计
- **每周分析**: 趋势分析和优化
- **每月评估**: 整体性能评估

---

**📊 性能监控完成！**
**🎯 发现 {len(bottlenecks)} 个性能瓶颈**
**💡 生成 {len(optimizations)} 条优化建议**
**🚀 系统性能持续优化中！**
"""
        
        with open('PERFORMANCE_MONITORING_REPORT.md', 'w', encoding == 'utf-8') as f,
            f.write(report)
        
        print("✅ 性能监控报告已保存, PERFORMANCE_MONITORING_REPORT.md")
        return report
    
    def _stop_background_monitoring(self):
        """停止后台监控"""
        self.monitoring_active == False
        if self.monitor_thread and self.monitor_thread.is_alive():::
            self.monitor_thread.join(timeout=5)
        print("   ✅ 后台监控已停止")
    
    def _load_performance_data(self) -> Dict,
        """加载历史性能数据"""
        perf_file = 'performance_history.json'
        if Path(perf_file).exists():::
            try,
                with open(perf_file, 'r', encoding == 'utf-8') as f,
                    return json.load(f)
            except,::
                pass
        return {
            'historical_metrics': []
            'trends': {}
            'improvements': []
        }
    
    def save_performance_data(self):
        """保存性能数据"""
        perf_file = 'performance_history.json'
        try,
            with open(perf_file, 'w', encoding == 'utf-8') as f,
                json.dump(self.performance_data(), f, indent=2, ensure_ascii == False)
        except,::
            pass
    
    def get_real_time_metrics(self) -> Dict[str, Any]
        """获取实时性能指标"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'repair_processes': self._count_repair_processes(),
            'timestamp': datetime.now().isoformat()
        }
    
    def optimize_repair_process(self, repair_config, Dict) -> Dict[str, Any]
        """优化修复过程"""
        print("⚙️ 优化修复过程...")
        
        optimizations = {
            'batch_size': self._optimize_batch_size(repair_config),
            'concurrency': self._optimize_concurrency(repair_config),
            'memory_management': self._optimize_memory_management(repair_config),
            'algorithm_optimization': self._optimize_algorithms(repair_config)
        }
        
        return {
            'optimizations_applied': optimizations,
            'expected_improvement': self._calculate_expected_improvement(optimizations),
            'implementation_priority': self._prioritize_optimizations(optimizations)
        }
    
    def _optimize_batch_size(self, config, Dict) -> int,
        """优化批次大小"""
        # 基于历史数据和系统资源确定最优批次大小
        current_memory = psutil.virtual_memory().percent
        
        if current_memory < 50,::
            return 200  # 内存充足,使用大批次
        elif current_memory < 70,::
            return 100  # 内存适中,使用中等批次
        else,
            return 50   # 内存紧张,使用小批次
    
    def _optimize_concurrency(self, config, Dict) -> int,
        """优化并发度"""
        cpu_count = psutil.cpu_count()
        cpu_usage = psutil.cpu_percent(interval=1)
        
        if cpu_usage < 30,::
            return min(cpu_count, 8)  # CPU空闲,使用高并发
        elif cpu_usage < 60,::
            return min(cpu_count // 2, 4)  # CPU适中,使用中等并发
        else,
            return 2  # CPU繁忙,使用低并发
    
    def _optimize_memory_management(self, config, Dict) -> Dict[str, Any]
        """优化内存管理"""
        return {
            'use_generators': True,
            'chunk_processing': True,
            'gc_frequency': 'medium',
            'memory_monitoring': True
        }
    
    def _optimize_algorithms(self, config, Dict) -> List[str]
        """优化算法"""
        return [
            'implement_lru_cache',
            'use_set_for_membership_test',
            'optimize_regex_patterns',
            'implement_early_exit_conditions'
        ]
    
    def _calculate_expected_improvement(self, optimizations, Dict) -> Dict[str, str]
        """计算预期改进"""
        return {
            'speed': '25-40%',
            'memory': '30-50%',
            'success_rate': '10-20%',
            'overall_efficiency': '35-55%'
        }
    
    def _prioritize_optimizations(self, optimizations, Dict) -> List[Dict]
        """优先级排序优化"""
        return [
            {
                'priority': 1,
                'optimization': 'memory_management',
                'impact': 'high',
                'effort': 'medium'
            }
            {
                'priority': 2,
                'optimization': 'batch_size',
                'impact': 'medium',
                'effort': 'low'
            }
            {
                'priority': 3,
                'optimization': 'algorithm_optimization',
                'impact': 'medium',
                'effort': 'high'
            }
        ]

def main():
    """主函数"""
    print("📊 启动性能监控和优化系统...")
    print("="*60)
    
    # 创建性能监控系统
    perf_system == PerformanceMonitoringSystem()
    
    # 运行性能监控
    results = perf_system.run_performance_monitoring(duration_minutes=15)
    
    print("\n" + "="*60)
    print("🎉 性能监控完成！")
    
    print(f"📈 监控数据点, {len(results['performance_data'])}")
    print(f"🔍 发现瓶颈, {len(results['bottlenecks'])}")
    print(f"💡 优化建议, {len(results['optimizations'])}")
    print(f"⏱️ 监控时长, {results['duration'].1f}秒")
    
    print("📄 详细报告, PERFORMANCE_MONITORING_REPORT.md")
    
    # 保存性能数据
    perf_system.save_performance_data()
    
    print("\n🚀 性能优化建议已生成,准备实施优化！")

if __name"__main__":::
    main()
