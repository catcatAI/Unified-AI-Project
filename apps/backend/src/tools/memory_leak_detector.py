"""
Angela AI Memory Leak Detector
內存泄漏檢測工具
"""

import gc
import psutil
import time
import tracemalloc
from typing import Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class MemorySnapshot:
    """內存快照"""
    timestamp: float
    rss_mb: float  # 物理內存
    vms_mb: float  # 虛擬內存
    percent: float  # 內存使用百分比
    python_objects: int  # Python對象數量
    gc_objects: List[int]  # GC世代對象數量

@dataclass
class MemoryLeak:
    """內存泄漏報告"""
    detected: bool
    rate_mb_per_min: float
    growth_percent: float
    duration_minutes: float
    snapshots: List[MemorySnapshot]

class MemoryLeakDetector:
    def __init__(self, sampling_interval: int = 30):
        """
        初始化內存泄漏檢測器
        
        Args:
            sampling_interval: 採樣間隔（秒）
        """
        self.sampling_interval = sampling_interval
        self.snapshots: List[MemorySnapshot] = []
        self.process = psutil.Process()
        self.is_monitoring = False
        self.start_time = None
        
        # 閾值設置
        self.leak_threshold_mb_per_min = 2.0  # MB/分鐘
        self.growth_threshold_percent = 10.0  # 百分比增長
        
    def start_monitoring(self) -> None:
        """開始監控"""
        if self.is_monitoring:
            print("內存監控已在運行中")
            return
            
        print("開始內存泄漏檢測...")
        self.is_monitoring = True
        self.start_time = time.time()
        
        # 啟用tracemalloc
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        # 執行垃圾回收
        gc.collect()
        
        # 採集初始快照
        self._take_snapshot()
        
    def stop_monitoring(self) -> MemoryLeak:
        """停止監控並返回檢測結果"""
        if not self.is_monitoring:
            raise RuntimeError("監控未開始")
            
        print("停止內存泄漏檢測...")
        self.is_monitoring = False
        
        # 最終快照
        self._take_snapshot()
        
        # 分析結果
        leak_result = self._analyze_leak()
        
        # 停止tracemalloc
        if tracemalloc.is_tracing():
            tracemalloc.stop()
            
        return leak_result
        
    def _take_snapshot(self) -> None:
        """採集內存快照"""
        try:
            # 獲取進程內存信息
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # 獲取Python對象信息
            python_objects = len(gc.get_objects())
            gc_counts = [len(gc.get_objects(generation)) for generation in range(3)]
            
            snapshot = MemorySnapshot(
                timestamp=time.time(),
                rss_mb=memory_info.rss / 1024 / 1024,
                vms_mb=memory_info.vms / 1024 / 1024,
                percent=memory_percent,
                python_objects=python_objects,
                gc_objects=gc_counts
            )
            
            self.snapshots.append(snapshot)
            print(f"內存快照: {snapshot.rss_mb:.1f}MB ({snapshot.percent:.1f}%)")
            
        except Exception as e:
            print(f"採集內存快照失敗: {e}")
            
    def _analyze_leak(self) -> MemoryLeak:
        """分析內存泄漏"""
        if len(self.snapshots) < 2:
            return MemoryLeak(
                detected=False,
                rate_mb_per_min=0.0,
                growth_percent=0.0,
                duration_minutes=0.0,
                snapshots=self.snapshots
            )
            
        # 計算時間範圍
        start_time = self.snapshots[0].timestamp
        end_time = self.snapshots[-1].timestamp
        duration_minutes = (end_time - start_time) / 60
        
        # 計算內存增長率
        start_memory = self.snapshots[0].rss_mb
        end_memory = self.snapshots[-1].rss_mb
        memory_growth = end_memory - start_memory
        
        rate_mb_per_min = memory_growth / duration_minutes if duration_minutes > 0 else 0
        growth_percent = (memory_growth / start_memory) * 100 if start_memory > 0 else 0
        
        # 判斷是否為內存泄漏
        detected = (
            rate_mb_per_min > self.leak_threshold_mb_per_min and
            growth_percent > self.growth_threshold_percent
        )
        
        return MemoryLeak(
            detected=detected,
            rate_mb_per_min=rate_mb_per_min,
            growth_percent=growth_percent,
            duration_minutes=duration_minutes,
            snapshots=self.snapshots
        )
        
    def get_memory_usage_by_type(self) -> Dict[str, int]:
        """獲取按類型分組的內存使用"""
        try:
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                snapshot = tracemalloc.take_snapshot()
                
                # 統計各類型的內存使用
                stats = snapshot.statistics('lineno')
                type_stats = {}
                
                for stat in stats[:10]:  # 取前10個最大的
                    filename = stat.traceback[0].filename
                    lineno = stat.traceback[0].lineno
                    size_mb = stat.size / 1024 / 1024
                    
                    key = f"{Path(filename).name}:{lineno}"
                    type_stats[key] = size_mb
                    
                return type_stats
            else:
                return {}
        except Exception as e:
            print(f"獲取內存使用統計失敗: {e}")
            return {}
            
    def force_garbage_collection(self) -> Dict[str, int]:
        """強制垃圾回收並返回結果"""
        print("執行垃圾回收...")
        
        # 記錄回收前的對象數量
        before_objects = len(gc.get_objects())
        
        # 執行垃圾回收
        collected = [gc.collect() for _ in range(3)]
        
        # 記錄回收後的對象數量
        after_objects = len(gc.get_objects())
        
        result = {
            'before_objects': before_objects,
            'after_objects': after_objects,
            'collected_objects': before_objects - after_objects,
            'gc_cycles': collected
        }
        
        print(f"垃圾回收完成: 回收了 {result['collected_objects']} 個對象")
        return result
        
    def generate_report(self, leak_result: MemoryLeak) -> str:
        """生成詳細報告"""
        report = []
        report.append("=" * 60)
        report.append("Angela AI 內存泄漏檢測報告")
        report.append("=" * 60)
        report.append("")
        
        # 基本信息
        report.append(f"檢測持續時間: {leak_result.duration_minutes:.1f} 分鐘")
        report.append(f"採樣間隔: {self.sampling_interval} 秒")
        report.append(f"快照數量: {len(leak_result.snapshots)}")
        report.append("")
        
        # 內存統計
        if leak_result.snapshots:
            start_memory = leak_result.snapshots[0].rss_mb
            end_memory = leak_result.snapshots[-1].rss_mb
            max_memory = max(s.rss_mb for s in leak_result.snapshots)
            
            report.append("內存使用統計:")
            report.append(f"  起始內存: {start_memory:.1f} MB")
            report.append(f"  結束內存: {end_memory:.1f} MB")
            report.append(f"  峰值內存: {max_memory:.1f} MB")
            report.append(f"  內存增長: {end_memory - start_memory:.1f} MB")
            report.append("")
        
        # 泄漏檢測結果
        report.append("泄漏檢測結果:")
        report.append(f"  檢測到泄漏: {'是' if leak_result.detected else '否'}")
        report.append(f"  增長率: {leak_result.rate_mb_per_min:.2f} MB/分鐘")
        report.append(f"  增長百分比: {leak_result.growth_percent:.1f}%")
        report.append("")
        
        # 閾值信息
        report.append("檢測閾值:")
        report.append(f"  泄漏閾值: {self.leak_threshold_mb_per_min} MB/分鐘")
        report.append(f"  增長閾值: {self.growth_threshold_percent}%")
        report.append("")
        
        # 類型統計
        type_stats = self.get_memory_usage_by_type()
        if type_stats:
            report.append("內存使用排行 (按文件:行號):")
            for location, size in sorted(type_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
                report.append(f"  {location}: {size:.2f} MB")
            report.append("")
        
        # Python對象統計
        if leak_result.snapshots:
            start_objects = leak_result.snapshots[0].python_objects
            end_objects = leak_result.snapshots[-1].python_objects
            object_growth = end_objects - start_objects
            
            report.append("Python對象統計:")
            report.append(f"  起始對象: {start_objects:,}")
            report.append(f"  結束對象: {end_objects:,}")
            report.append(f"  對象增長: {object_growth:,}")
            report.append("")
        
        # 建議
        report.append("建議:")
        if leak_result.detected:
            report.append("  ⚠️  檢測到潛在的內存泄漏")
            report.append("  - 檢查事件監聽器是否正確移除")
            report.append("  - 檢查定時器是否正確清理")
            report.append("  - 檢查大對象是否及時釋放")
            report.append("  - 考慮使用弱引用避免循環引用")
        else:
            report.append("  ✅ 未檢測到明顯的內存泄漏")
            report.append("  - 繼續監控長期運行情況")
            report.append("  - 定期執行垃圾回收")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)

def main():
    """主函數 - 演示內存泄漏檢測"""
    print("Angela AI 內存泄漏檢測器")
    print("按 Ctrl+C 停止檢測")
    print()
    
    detector = MemoryLeakDetector(sampling_interval=10)
    detector.start_monitoring()
    
    try:
        while True:
            time.sleep(detector.sampling_interval)
            if detector.is_monitoring:
                detector._take_snapshot()
    except KeyboardInterrupt:
        print("\n停止檢測...")
        leak_result = detector.stop_monitoring()
        
        # 生成報告
        report = detector.generate_report(leak_result)
        print(report)
        
        # 保存報告到文件
        with open("memory_leak_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        print("報告已保存到 memory_leak_report.txt")

if __name__ == "__main__":
    main()