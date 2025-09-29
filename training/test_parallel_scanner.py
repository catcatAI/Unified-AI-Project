#!/usr/bin/env python3
"""
测试并行优化的数据扫描器性能
"""

import sys
import time
from pathlib import Path

# 添加项目路径
project_root: str = Path(__file__).parent.parent
_ = sys.path.insert(0, str(project_root))

from training.optimized_data_scanner import OptimizedDataScanner
from training.parallel_optimized_data_scanner import ParallelOptimizedDataScanner

def test_serial_scanner() -> None:
    """测试串行扫描器性能"""
    _ = print("⏱️  测试串行扫描器性能...")
    
    # 创建串行扫描器
    scanner = OptimizedDataScanner(
        data_dir="data",
        tracking_file="training/data_tracking.json",
        config_file="training/configs/performance_config.json"
    )
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        new_files = scanner.find_new_files(max_files=100)
        end_time = time.time()
        
        _ = print(f"✅ 串行扫描完成")
        _ = print(f"  发现 {len(new_files)} 个新增/修改文件")
        _ = print(f"  耗时: {end_time - start_time:.2f} 秒")
        
        return end_time - start_time
    except Exception as e:
        _ = print(f"❌ 串行扫描失败: {e}")
        return float('inf')

def test_parallel_scanner() -> None:
    """测试并行扫描器性能"""
    _ = print("⏱️  测试并行扫描器性能...")
    
    # 创建并行扫描器
    scanner = ParallelOptimizedDataScanner(
        data_dir="data",
        tracking_file="training/data_tracking.json",
        config_file="training/configs/performance_config.json"
    )
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        new_files = scanner.find_new_files(max_files=100)
        end_time = time.time()
        
        _ = print(f"✅ 并行扫描完成")
        _ = print(f"  发现 {len(new_files)} 个新增/修改文件")
        _ = print(f"  耗时: {end_time - start_time:.2f} 秒")
        
        return end_time - start_time
    except Exception as e:
        _ = print(f"❌ 并行扫描失败: {e}")
        return float('inf')

def main() -> None:
    """主函数"""
    _ = print("🔍 测试并行优化的数据扫描器性能")
    print("=" * 40)
    
    # 测试串行扫描器
    serial_time = test_serial_scanner()
    _ = print()
    
    # 测试并行扫描器
    parallel_time = test_parallel_scanner()
    _ = print()
    
    # 性能对比
    print("=" * 40)
    _ = print("性能对比:")
    _ = print(f"  串行扫描耗时: {serial_time:.2f} 秒")
    _ = print(f"  并行扫描耗时: {parallel_time:.2f} 秒")
    
    if serial_time != float('inf') and parallel_time != float('inf'):
        if parallel_time < serial_time:
            improvement = (serial_time - parallel_time) / serial_time * 100
            _ = print(f"  🚀 性能提升: {improvement:.1f}%")
        else:
            _ = print("  ⚠️  并行扫描未提升性能")
    else:
        _ = print("  ❌ 测试失败，无法进行性能对比")
    
    return 0

if __name__ == "__main__":
    _ = sys.exit(main())