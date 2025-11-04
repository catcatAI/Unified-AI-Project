#!/usr/bin/env python3
"""
运行项目修复的脚本
使用项目现有的统一修复系统
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))

from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
from unified_auto_fix_system.core.fix_result import FixContext, FixReport

def main():
    """主函数"""
    print("开始使用统一修复系统修复项目...")
    
    # 初始化修复引擎
    engine = UnifiedFixEngine(project_root)
    
    # 创建修复上下文
    context = FixContext(
        project_root=project_root,
        target_path=None,  # 修复整个项目
        backup_enabled=True,
        dry_run=False
    )
    
    # 执行修复
    print("正在分析项目并修复问题...")
    report = engine.fix_issues(context)
    
    # 输出结果摘要
    print("\n" + "="*50)
    print("修复完成!")
    print("="*50)
    print(report.get_summary())
    
    # 输出各模块修复结果
    print("\n各模块修复结果:")
    for fix_type, result in report.fix_results.items():
        print(f"  {fix_type}: {result.summary()}")
    
    # 检查是否有错误
    if report.errors:
        print(f"\n修复过程中遇到 {len(report.errors)} 个错误:")
        for error in report.errors:
            print(f"  - {error}")

if __name__ == "__main__":
    main()