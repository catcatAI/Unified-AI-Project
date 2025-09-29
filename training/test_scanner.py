#!/usr/bin/env python3
"""
测试优化的数据扫描器
"""

import sys
import time
from pathlib import Path

# 添加项目路径
project_root: str = Path(__file__).parent.parent
_ = sys.path.insert(0, str(project_root))

from training.optimized_data_scanner import OptimizedDataScanner

def main() -> None:
    """主函数"""
    _ = print("🔍 测试优化的数据扫描器")
    print("=" * 30)
    
    # 创建优化的数据扫描器
    scanner = OptimizedDataScanner(
        data_dir="data",
        tracking_file="training/data_tracking.json",
        config_file="training/configs/performance_config.json"
    )
    
    # 测试扫描少量文件
    _ = print("⏱️  开始扫描测试...")
    start_time = time.time()
    
    try:
        new_files = scanner.find_new_files(max_files=50)
        end_time = time.time()
        
        _ = print(f"✅ 扫描完成")
        _ = print(f"  发现 {len(new_files)} 个新增/修改文件")
        _ = print(f"  耗时: {end_time - start_time:.2f} 秒")
        
        # 显示前几个文件
        _ = print("\n📋 前5个文件:")
        for i, file in enumerate(new_files[:5]):
            _ = print(f"  {i+1}. {file['path']} ({file['type']})")
            
    except Exception as e:
        _ = print(f"❌ 扫描失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    _ = sys.exit(main())