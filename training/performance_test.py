#!/usr/bin/env python3
"""
增量学习系统性能测试
"""

import sys
import time
from pathlib import Path

# 添加项目路径
project_root: str = Path(__file__).parent.parent
_ = sys.path.insert(0, str(project_root))

from training.incremental_learning_manager import (
    DataTracker, 
    TrainingScheduler,
    IncrementalLearningManager
)

def test_data_scanning_performance() -> None:
    """测试数据扫描性能"""
    _ = print("⏱️  测试数据扫描性能...")
    
    # 创建数据跟踪器
    tracker = DataTracker()
    
    # 记录开始时间
    start_time = time.time()
    
    # 扫描数据
    new_data = tracker.scan_for_new_data()
    
    # 记录结束时间
    end_time = time.time()
    
    # 计算耗时
    elapsed_time = end_time - start_time
    
    _ = print(f"  ✅ 扫描完成，发现 {len(new_data)} 个新增/修改文件")
    _ = print(f"  ⏱️  扫描耗时: {elapsed_time:.2f} 秒")
    
    # 性能评估
    if elapsed_time < 5:
        _ = print(f"  🚀 扫描性能优秀")
    elif elapsed_time < 15:
        _ = print(f"  ✅ 扫描性能良好")
    elif elapsed_time < 30:
        _ = print(f"  ⚠️  扫描性能一般")
    else:
        _ = print(f"  ❌ 扫描性能较差，需要优化")
    
    return elapsed_time

def test_resource_monitoring() -> None:
    """测试资源监控功能"""
    _ = print("🖥️  测试资源监控功能...")
    
    # 创建训练调度器
    scheduler = TrainingScheduler()
    
    # 获取系统资源
    resources = scheduler._get_available_resources()
    
    _ = print(f"  ✅ 系统资源信息:")
    for key, value in resources.items():
        if key in ['memory_available', 'memory_total', 'disk_space_available']:
            _ = print(f"     {key}: {value / (1024*1024*1024):.2f} GB")
        elif key == 'cpu_percent':
            _ = print(f"     {key}: {value}%")
        else:
            _ = print(f"     {key}: {value}")
    
    # 测试资源检查功能
    test_task = {'model_name': 'concept_models'}
    try:
        can_execute = scheduler._can_execute_task(test_task)
        print(f"  ✅ 任务执行检查: {'可以执行' if can_execute else '资源不足'}")
    except Exception as e:
        _ = print(f"  ❌ 任务执行检查失败: {e}")
        return False
    
    return True

def test_incremental_learning_performance() -> None:
    """测试增量学习整体性能"""
    _ = print("📊 测试增量学习整体性能...")
    
    # 记录开始时间
    start_time = time.time()
    
    # 创建增量学习管理器
    learner = IncrementalLearningManager()
    
    # 获取状态
    status = learner.get_status()
    
    # 记录结束时间
    end_time = time.time()
    
    # 记录耗时
    elapsed_time = end_time - start_time
    
    _ = print(f"  ✅ 系统初始化耗时: {elapsed_time:.2f} 秒")
    _ = print(f"  ✅ 待处理任务数: {status.get('pending_tasks', 0)}")
    _ = print(f"  ✅ 缓冲区数据数: {status.get('buffered_data', 0)}")
    _ = print(f"  ✅ 已处理文件数: {status.get('processed_files', 0)}")
    
    return elapsed_time

def main() -> None:
    """主函数"""
    _ = print("🚀 增量学习系统性能测试")
    print("=" * 40)
    
    # 测试数据扫描性能
    try:
        scan_time = test_data_scanning_performance()
    except Exception as e:
        _ = print(f"❌ 数据扫描测试失败: {e}")
        scan_time = float('inf')
    _ = print()
    
    # 测试资源监控功能
    try:
        _ = test_resource_monitoring()
    except Exception as e:
        _ = print(f"❌ 资源监控测试失败: {e}")
    _ = print()
    
    # 测试增量学习整体性能
    try:
        init_time = test_incremental_learning_performance()
    except Exception as e:
        _ = print(f"❌ 增量学习性能测试失败: {e}")
        init_time = float('inf')
    _ = print()
    
    print("=" * 40)
    _ = print("性能测试总结:")
    _ = print(f"  数据扫描耗时: {scan_time:.2f} 秒")
    _ = print(f"  系统初始化耗时: {init_time:.2f} 秒")
    
    if scan_time < 5 and init_time < 2:
        _ = print("  🎉 性能测试通过，系统响应迅速")
        return 0
    elif scan_time < 15 and init_time < 5:
        _ = print("  ✅ 性能测试通过，系统响应良好")
        return 0
    elif scan_time < 30 and init_time < 10:
        _ = print("  ⚠️  性能测试警告，系统响应较慢")
        return 1
    else:
        _ = print("  ❌ 性能测试失败，系统响应过慢")
        return 1

if __name__ == "__main__":
    _ = sys.exit(main())