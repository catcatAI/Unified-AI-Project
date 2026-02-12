#!/usr/bin/env python3
"""
Angela AI - Memory Profiler and Leak Detector
内存分析器和泄漏检测器

监控内存使用情况，检测内存泄漏，提供内存优化建议。
"""

import gc
import sys
import time
import tracemalloc
import psutil
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import weakref
import logging
logger = logging.getLogger(__name__)


@dataclass
class MemorySnapshot:
    """内存快照"""
    timestamp: datetime
    current_memory: int  # 当前内存使用量 (MB)
    peak_memory: int  # 峰值内存使用量 (MB)
    rss_memory: int  # RSS 内存 (MB)
    available_memory: int  # 可用内存 (MB)
    gc_objects: int  # GC 对象数量
    gc_collections: Dict[str, int]  # GC 回收次数


@dataclass
class MemoryLeakInfo:
    """内存泄漏信息"""
    object_type: str
    count: int
    size: int  # 字节
    traceback: Optional[str] = None


@dataclass
class MemoryProfile:
    """内存分析结果"""
    snapshots: List[MemorySnapshot] = field(default_factory=list)
    leaks: List[MemoryLeakInfo] = field(default_factory=list)
    total_objects: int = 0
    recommendations: List[str] = field(default_factory=list)


class MemoryProfiler:
    """内存分析器"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.snapshots: List[MemorySnapshot] = []
        self.tracking_started = False
        self.object_refs: Dict[str, List[weakref.ref]] = defaultdict(list)
        self._start_memory: Optional[int] = None
    
    def start_tracking(self) -> None:
        """开始内存跟踪"""
        if not self.enabled:
            return
        
        if self.tracking_started:
            print("⚠️  内存跟踪已在运行中")
            return
        
        tracemalloc.start()
        self._start_memory = self._get_current_memory()
        self.tracking_started = True
        print("✓ 内存跟踪已启动")
    
    def stop_tracking(self) -> None:
        """停止内存跟踪"""
        if not self.enabled or not self.tracking_started:
            return
        
        tracemalloc.stop()
        self.tracking_started = False
        print("✓ 内存跟踪已停止")
    
    def take_snapshot(self, label: str = "") -> MemorySnapshot:
        """获取内存快照"""
        if not self.enabled or not self.tracking_started:
            return MemorySnapshot(
                timestamp=datetime.now(),
                current_memory=0,
                peak_memory=0,
                rss_memory=0,
                available_memory=0,
                gc_objects=0,
                gc_collections={}
            )
        
        # 获取 tracemalloc 快照
        snapshot = tracemalloc.take_snapshot()
        
        # 获取当前内存使用
        current_memory = self._get_current_memory()
        peak_memory = self._get_peak_memory()
        
        # 获取 RSS 内存
        rss_memory = self._get_rss_memory()
        
        # 获取 GC 信息
        gc.collect()
        gc_objects = len(gc.get_objects())
        gc_collections = {
            "gen0": gc.get_count()[0],
            "gen1": gc.get_count()[1],
            "gen2": gc.get_count()[2],
        }
        
        # 获取可用内存
        available_memory = self._get_available_memory()
        
        mem_snapshot = MemorySnapshot(
            timestamp=datetime.now(),
            current_memory=current_memory,
            peak_memory=peak_memory,
            rss_memory=rss_memory,
            available_memory=available_memory,
            gc_objects=gc_objects,
            gc_collections=gc_collections
        )
        
        self.snapshots.append(mem_snapshot)
        
        if label:
            print(f"✓ 快照已创建: {label} ({current_memory:.2f} MB)")
        
        return mem_snapshot
    
    def detect_leaks(self, threshold: int = 100) -> List[MemoryLeakInfo]:
        """检测内存泄漏"""
        if not self.enabled or len(self.snapshots) < 2:
            return []
        
        leaks = []
        
        # 比较第一个和最后一个快照
        first_snapshot = self.snapshots[0]
        last_snapshot = self.snapshots[-1]
        
        # 获取对象统计
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        # 统计对象类型增长
        for stat in top_stats:
            if stat.size > threshold * 1024:  # 阈值 (字节)
                leaks.append(MemoryLeakInfo(
                    object_type=str(stat.traceback),
                    count=stat.count,
                    size=stat.size
                ))
        
        return leaks[:10]  # 返回前 10 个可能的泄漏
    
    def profile_function(self, func: Callable) -> Callable:
        """函数装饰器：分析函数内存使用"""
        if not self.enabled:
            return func
        
        def wrapper(*args, **kwargs):
            if not self.tracking_started:
                self.start_tracking()
            
            self.take_snapshot(f"调用前: {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                self.take_snapshot(f"调用后: {func.__name__}")
                return result
            finally:
                pass
        
        return wrapper
    
    def analyze_growth(self) -> Dict[str, Any]:
        """分析内存增长"""
        if len(self.snapshots) < 2:
            return {"status": "insufficient_data"}
        
        first = self.snapshots[0]
        last = self.snapshots[-1]
        
        memory_growth = last.current_memory - first.current_memory
        gc_object_growth = last.gc_objects - first.gc_objects
        
        duration = (last.timestamp - first.timestamp).total_seconds()
        growth_rate = memory_growth / duration if duration > 0 else 0
        
        return {
            "memory_growth_mb": memory_growth,
            "memory_growth_rate_mb_per_sec": growth_rate,
            "gc_object_growth": gc_object_growth,
            "duration_seconds": duration,
            "start_memory_mb": first.current_memory,
            "end_memory_mb": last.current_memory,
            "peak_memory_mb": last.peak_memory,
        }
    
    def get_recommendations(self) -> List[str]:
        """获取内存优化建议"""
        recommendations = []
        
        analysis = self.analyze_growth()
        
        if "memory_growth_rate_mb_per_sec" in analysis:
            growth_rate = analysis["memory_growth_rate_mb_per_sec"]
            
            if growth_rate > 10:  # 每秒增长超过 10 MB
                recommendations.append(
                    f"⚠️  检测到高内存增长率 ({growth_rate:.2f} MB/s)，可能存在内存泄漏"
                )
        
        if len(self.snapshots) > 1:
            leaks = self.detect_leaks()
            if leaks:
                recommendations.append(f"⚠️  检测到 {len(leaks)} 个潜在的内存泄漏")
                for leak in leaks[:3]:
                    recommendations.append(f"   - {leak.object_type}: {leak.size / 1024:.2f} KB")
        
        # GC 建议
        if self.snapshots:
            last_snapshot = self.snapshots[-1]
            if last_snapshot.gc_objects > 100000:
                recommendations.append(
                    f"⚠️  GC 对象数量较多 ({last_snapshot.gc_objects})，考虑手动调用 gc.collect()"
                )
        
        # 系统内存建议
        available_memory = self._get_available_memory()
        if available_memory < 500:  # 可用内存少于 500 MB
            recommendations.append(
                f"⚠️  系统可用内存较低 ({available_memory:.2f} MB)，考虑优化内存使用"
            )
        
        if not recommendations:
            recommendations.append("✓ 未检测到明显的内存问题")
        
        return recommendations
    
    def generate_report(self) -> str:
        """生成内存分析报告"""
        report = []
        report.append("=" * 60)
        report.append("Angela AI - 内存分析报告")
        report.append("=" * 60)
        report.append("")
        
        # 快照信息
        report.append(f"快照数量: {len(self.snapshots)}")
        if self.snapshots:
            first = self.snapshots[0]
            last = self.snapshots[-1]
            report.append(f"开始时间: {first.timestamp}")
            report.append(f"结束时间: {last.timestamp}")
            report.append(f"持续时间: {(last.timestamp - first.timestamp).total_seconds():.2f} 秒")
            report.append("")
            
            # 内存使用
            report.append("内存使用:")
            report.append(f"  初始内存: {first.current_memory:.2f} MB")
            report.append(f"  当前内存: {last.current_memory:.2f} MB")
            report.append(f"  峰值内存: {last.peak_memory:.2f} MB")
            report.append(f"  RSS 内存: {last.rss_memory:.2f} MB")
            report.append(f"  可用内存: {last.available_memory:.2f} MB")
            report.append("")
            
            # GC 信息
            report.append("垃圾回收:")
            report.append(f"  GC 对象数量: {last.gc_objects}")
            report.append(f"  Gen0 对象: {last.gc_collections['gen0']}")
            report.append(f"  Gen1 对象: {last.gc_collections['gen1']}")
            report.append(f"  Gen2 对象: {last.gc_collections['gen2']}")
            report.append("")
            
            # 增长分析
            analysis = self.analyze_growth()
            if "memory_growth_mb" in analysis:
                report.append("内存增长分析:")
                report.append(f"  内存增长: {analysis['memory_growth_mb']:.2f} MB")
                report.append(f"  增长率: {analysis['memory_growth_rate_mb_per_sec']:.2f} MB/s")
                report.append(f"  GC 对象增长: {analysis['gc_object_growth']}")
                report.append("")
        
        # 泄漏检测
        leaks = self.detect_leaks()
        if leaks:
            report.append(f"检测到 {len(leaks)} 个潜在泄漏:")
            for i, leak in enumerate(leaks[:5], 1):
                report.append(f"  {i}. {leak.object_type}: {leak.size / 1024:.2f} KB ({leak.count} 对象)")
            report.append("")
        
        # 优化建议
        recommendations = self.get_recommendations()
        report.append("优化建议:")
        for rec in recommendations:
            report.append(f"  {rec}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    # 辅助方法
    def _get_current_memory(self) -> float:
        """获取当前内存使用量 (MB)"""
        current, peak = tracemalloc.get_traced_memory()
        return current / 1024 / 1024
    
    def _get_peak_memory(self) -> float:
        """获取峰值内存使用量 (MB)"""
        current, peak = tracemalloc.get_traced_memory()
        return peak / 1024 / 1024
    
    def _get_rss_memory(self) -> float:
        """获取 RSS 内存 (MB)"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def _get_available_memory(self) -> float:
        """获取可用内存 (MB)"""
        return psutil.virtual_memory().available / 1024 / 1024


# 全局内存分析器实例
_profiler: Optional[MemoryProfiler] = None


def get_profiler() -> MemoryProfiler:
    """获取全局内存分析器"""
    global _profiler
    if _profiler is None:
        _profiler = MemoryProfiler()
    return _profiler


def profile_memory(func: Callable) -> Callable:
    """内存分析装饰器"""
    profiler = get_profiler()
    return profiler.profile_function(func)


def print_memory_report() -> None:
    """打印内存分析报告"""
    profiler = get_profiler()
    print(profiler.generate_report())


def start_memory_tracking() -> None:
    """启动内存跟踪"""
    profiler = get_profiler()
    profiler.start_tracking()


def stop_memory_tracking() -> None:
    """停止内存跟踪"""
    profiler = get_profiler()
    profiler.stop_tracking()


def take_memory_snapshot(label: str = "") -> None:
    """获取内存快照"""
    profiler = get_profiler()
    profiler.take_snapshot(label)


if __name__ == "__main__":
    # 测试内存分析器
    profiler = MemoryProfiler()
    profiler.start_tracking()
    
    # 模拟内存使用
    data = []
    for i in range(10000):
        data.append([j for j in range(100)])
    
    profiler.take_snapshot("分配后")
    
    # 释放内存
    del data
    gc.collect()
    
    profiler.take_snapshot("释放后")
    
    print(profiler.generate_report())
