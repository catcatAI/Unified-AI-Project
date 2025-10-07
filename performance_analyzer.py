#!/usr/bin/env python3
"""
性能分析器
分析系统性能和瓶颈
"""

import time
import sys
import psutil
import cProfile
import pstats
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.benchmarks = {}
        self.performance_data = []
    
    def analyze_system_performance(self) -> Dict[str, Any]:
        """分析系统性能"""
        print("🔍 分析系统性能...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "cpu_performance": self.analyze_cpu_performance(),
            "memory_performance": self.analyze_memory_performance(),
            "disk_performance": self.analyze_disk_performance(),
            "bottlenecks": self.identify_bottlenecks()
        }
        
        return results
    
    def analyze_cpu_performance(self) -> Dict[str, Any]:
        """分析CPU性能"""
        print("💻 分析CPU性能...")
        
        # 获取CPU信息
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # 测试CPU性能
        start_time = time.time()
        cpu_percent = psutil.cpu_percent(interval=3)
        end_time = time.time()
        
        cpu_analysis = {
            "cpu_count": cpu_count,
            "cpu_frequency_mhz": cpu_freq.current if cpu_freq else "unknown",
            "cpu_usage_percent": cpu_percent,
            "measurement_time_seconds": end_time - start_time,
            "performance_status": "good" if cpu_percent < 80 else "warning" if cpu_percent < 95 else "critical"
        }
        
        return cpu_analysis
    
    def analyze_memory_performance(self) -> Dict[str, Any]:
        """分析内存性能"""
        print("💾 分析内存性能...")
        
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        memory_analysis = {
            "total_memory_gb": round(memory.total / (1024**3), 2),
            "available_memory_gb": round(memory.available / (1024**3), 2),
            "memory_usage_percent": memory.percent,
            "swap_total_gb": round(swap.total / (1024**3), 2),
            "swap_usage_percent": swap.percent,
            "performance_status": "good" if memory.percent < 80 else "warning" if memory.percent < 95 else "critical"
        }
        
        return memory_analysis
    
    def analyze_disk_performance(self) -> Dict[str, Any]:
        """分析磁盘性能"""
        print("💽 分析磁盘性能...")
        
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        disk_analysis = {
            "total_disk_gb": round(disk.total / (1024**3), 2),
            "free_disk_gb": round(disk.free / (1024**3), 2),
            "disk_usage_percent": disk.percent,
            "disk_read_mb": round(disk_io.read_bytes / (1024**2), 2) if disk_io else 0,
            "disk_write_mb": round(disk_io.write_bytes / (1024**2), 2) if disk_io else 0,
            "performance_status": "good" if disk.percent < 80 else "warning" if disk.percent < 95 else "critical"
        }
        
        return disk_analysis
    
    def identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """识别性能瓶颈"""
        print("🔍 识别性能瓶颈...")
        
        bottlenecks = []
        
        # 检查CPU瓶颈
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 90:
            bottlenecks.append({
                "type": "cpu",
                "severity": "high",
                "message": f"CPU使用率过高: {cpu_percent}%",
                "suggestion": "考虑优化算法或减少并发处理"
            })
        elif cpu_percent > 70:
            bottlenecks.append({
                "type": "cpu",
                "severity": "medium",
                "message": f"CPU使用率较高: {cpu_percent}%",
                "suggestion": "监控CPU使用趋势"
            })
        
        # 检查内存瓶颈
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            bottlenecks.append({
                "type": "memory",
                "severity": "high",
                "message": f"内存使用率过高: {memory.percent}%",
                "suggestion": "检查内存泄漏或优化数据结构"
            })
        elif memory.percent > 70:
            bottlenecks.append({
                "type": "memory",
                "severity": "medium",
                "message": f"内存使用率较高: {memory.percent}%",
                "suggestion": "监控内存使用趋势"
            })
        
        # 检查磁盘瓶颈
        disk = psutil.disk_usage('/')
        if disk.percent > 90:
            bottlenecks.append({
                "type": "disk",
                "severity": "high",
                "message": f"磁盘使用率过高: {disk.percent}%",
                "suggestion": "清理磁盘空间或扩展存储"
            })
        
        return bottlenecks
    
    def benchmark_function(self, func, *args, **kwargs) -> Dict[str, Any]:
        """基准测试函数性能"""
        print(f"⏱️ 基准测试函数: {func.__name__}")
        
        # 使用cProfile进行性能分析
        profiler = cProfile.Profile()
        
        start_time = time.time()
        profiler.enable()
        
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        profiler.disable()
        end_time = time.time()
        
        # 获取性能统计
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        
        benchmark_result = {
            "function_name": func.__name__,
            "execution_time_seconds": end_time - start_time,
            "success": success,
            "total_calls": stats.total_calls,
            "primitive_calls": stats.prim_calls,
            "cumulative_time": stats.total_tt
        }
        
        if not success:
            benchmark_result["error"] = error
        
        return benchmark_result
    
    def generate_performance_report(self, analysis_results: Dict[str, Any]) -> str:
        """生成性能分析报告"""
        report = []
        
        report.append("# 📊 系统性能分析报告")
        report.append(f"\n**分析时间**: {analysis_results['timestamp']}")
        
        # CPU性能
        cpu_perf = analysis_results['cpu_performance']
        report.append(f"\n## 💻 CPU性能")
        report.append(f"- CPU核心数: {cpu_perf['cpu_count']}")
        report.append(f"- CPU频率: {cpu_perf['cpu_frequency_mhz']} MHz")
        report.append(f"- CPU使用率: {cpu_perf['cpu_usage_percent']}%")
        report.append(f"- 性能状态: {cpu_perf['performance_status']}")
        
        # 内存性能
        memory_perf = analysis_results['memory_performance']
        report.append(f"\n## 💾 内存性能")
        report.append(f"- 总内存: {memory_perf['total_memory_gb']} GB")
        report.append(f"- 可用内存: {memory_perf['available_memory_gb']} GB")
        report.append(f"- 内存使用率: {memory_perf['memory_usage_percent']}%")
        report.append(f"- 交换空间使用率: {memory_perf['swap_usage_percent']}%")
        report.append(f"- 性能状态: {memory_perf['performance_status']}")
        
        # 磁盘性能
        disk_perf = analysis_results['disk_performance']
        report.append(f"\n## 💽 磁盘性能")
        report.append(f"- 总磁盘空间: {disk_perf['total_disk_gb']} GB")
        report.append(f"- 可用磁盘空间: {disk_perf['free_disk_gb']} GB")
        report.append(f"- 磁盘使用率: {disk_perf['disk_usage_percent']}%")
        report.append(f"- 磁盘读取: {disk_perf['disk_read_mb']} MB")
        report.append(f"- 磁盘写入: {disk_perf['disk_write_mb']} MB")
        report.append(f"- 性能状态: {disk_perf['performance_status']}")
        
        # 性能瓶颈
        bottlenecks = analysis_results['bottlenecks']
        if bottlenecks:
            report.append(f"\n## ⚠️ 性能瓶颈")
            for bottleneck in bottlenecks:
                report.append(f"\n### {bottleneck['type'].upper()}瓶颈")
                report.append(f"- 严重程度: {bottleneck['severity']}")
                report.append(f"- 问题: {bottleneck['message']}")
                report.append(f"- 建议: {bottleneck['suggestion']}")
        else:
            report.append(f"\n## ✅ 性能状态")
            report.append("未发现明显的性能瓶颈")
        
        return "\n".join(report)

def main():
    """主函数"""
    print("🚀 启动系统性能分析器...")
    
    analyzer = PerformanceAnalyzer()
    
    try:
        # 分析系统性能
        results = analyzer.analyze_system_performance()
        
        # 生成报告
        report = analyzer.generate_performance_report(results)
        
        # 保存报告
        report_file = "performance_analysis_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📊 性能分析报告已保存到: {report_file}")
        
        # 显示关键结果
        print("\n📈 关键性能指标:")
        print(f"💻 CPU使用率: {results['cpu_performance']['cpu_usage_percent']}%")
        print(f"💾 内存使用率: {results['memory_performance']['memory_usage_percent']}%")
        print(f"💽 磁盘使用率: {results['disk_performance']['disk_usage_percent']}%")
        print(f"⚠️  性能瓶颈: {len(results['bottlenecks'])} 个")
        
    except Exception as e:
        print(f"❌ 性能分析失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)