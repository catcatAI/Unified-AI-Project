#!/usr/bin/env python3
"""
简单测试统一修复系统的功能
"""

import sys
import os
from pathlib import Path

# 直接执行统一修复系统
def test_unified_fix():
    try:
        # 获取项目根目录
        project_root = Path(__file__).parent
        
        # 读取unified-fix.py内容
        fix_script_path = project_root / "tools" / "unified-fix.py"
        with open(fix_script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # 执行脚本
        exec_globals = {}
        exec(script_content, exec_globals)
        
        # 创建修复器实例
        fixer = exec_globals['ProjectScopeFixer'](project_root)
        
        # 测试范围检查
        test_cases = [
            ("apps/backend/src/main.py", True, "应该在范围内"),
            ("node_modules/test.js", False, "应该被排除"),
            ("venv/lib/python3.8/site-packages/package.py", False, "应该被排除"),
            ("data/test.json", False, "应该被排除"),
        ]
        
        print("测试文件范围检查:")
        all_passed = True
        for test_file, expected, description in test_cases:
            file_path = project_root / test_file
            in_scope = fixer.is_in_project_scope(file_path)
            status = "✅" if in_scope == expected else "❌"
            print(f"  {status} {test_file}: {description} ({'在范围内' if in_scope else '被排除'})")
            if in_scope != expected:
                all_passed = False
        
        # 测试扫描功能
        print("\n扫描项目文件...")
        project_files = fixer.scan_project_files()
        print(f"找到 {len(project_files)} 个项目文件")
        
        # 显示前5个文件
        if project_files:
            print("\n前5个文件:")
            for file_path in project_files[:5]:
                rel_path = file_path.relative_to(project_root)
                print(f"  {rel_path}")
        
        if all_passed:
            print("\n✅ 统一修复系统功能正常")
            return True
        else:
            print("\n❌ 部分测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_unified_fix()
    sys.exit(0 if success else 1)