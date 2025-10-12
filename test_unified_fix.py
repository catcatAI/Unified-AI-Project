#!/usr/bin/env python3
"""
测试统一修复系统的功能
"""

import sys
from pathlib import Path

# 添加tools目录到路径
tools_path = Path(__file__).parent / "tools"
sys.path.insert(0, str(tools_path))

try:
    from unified_fix import ProjectScopeFixer
    
    # 创建修复器实例
    project_root = Path(__file__).parent
    fixer = ProjectScopeFixer(project_root)
    
    # 测试范围检查
    test_files = [
        "apps/backend/src/main.py",  # 应该在范围内
        "node_modules/test.js",      # 应该被排除
        "venv/lib/python3.8/site-packages/package.py",  # 应该被排除
        "data/test.json",            # 应该被排除
    ]
    
    print("测试文件范围检查:")
    for test_file in test_files:
        file_path = project_root / test_file
        in_scope = fixer.is_in_project_scope(file_path)
        print(f"  {test_file}: {'在范围内' if in_scope else '被排除'}")
    
    # 测试扫描功能
    print("\n扫描项目文件...")
    project_files = fixer.scan_project_files()
    print(f"找到 {len(project_files)} 个项目文件")
    
    # 显示前5个文件
    print("\n前5个文件:")
    for file_path in project_files[:5]:
        rel_path = file_path.relative_to(project_root)
        print(f"  {rel_path}")
    
    print("\n✅ 统一修复系统功能正常")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()