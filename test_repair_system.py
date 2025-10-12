#!/usr/bin/env python3
"""
测试修复系统的实际功能
"""

import sys
import os
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "tools"))

def test_unified_fix():
    """测试统一修复系统"""
    try:
        # 导入修复系统
        from unified_fix import ProjectScopeFixer
        
        # 创建修复器
        project_root = Path(__file__).parent
        fixer = ProjectScopeFixer(project_root)
        
        # 测试范围检查
        test_cases = [
            ("apps/backend/src/main.py", True),
            ("node_modules/test.js", False),
            ("venv/lib/test.py", False),
            ("data/test.json", False),
        ]
        
        print("测试文件范围检查:")
        all_passed = True
        for file_path, expected in test_cases:
            full_path = project_root / file_path
            in_scope = fixer.is_in_project_scope(full_path)
            status = "✓" if in_scope == expected else "✗"
            print(f"  {status} {file_path}: {'范围内' if in_scope else '范围外'}")
            if in_scope != expected:
                all_passed = False
        
        # 测试扫描功能
        print("\n扫描项目文件...")
        project_files = fixer.scan_project_files()
        print(f"找到 {len(project_files)} 个项目文件")
        
        # 测试修复功能
        if project_files:
            print(f"\n测试修复功能（前3个文件）:")
            for file_path in project_files[:3]:
                rel_path = file_path.relative_to(project_root)
                success = fixer.fix_syntax_errors(file_path)
                status = "✓" if success else "✗"
                print(f"  {status} {rel_path}")
        
        return all_passed
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backend_imports():
    """测试后端导入"""
    try:
        print("\n测试后端模块导入...")
        
        # 添加路径
        backend_path = Path(__file__).parent / "apps" / "backend"
        sys.path.insert(0, str(backend_path))
        
        # 测试导入
        import src.api.routes
        import src.core.managers.system_manager
        import src.core.config.system_config
        
        print("  ✓ 所有后端模块导入成功")
        return True
        
    except ImportError as e:
        print(f"  ✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"  ✗ 其他错误: {e}")
        return False

def main():
    print("=" * 60)
    print("测试修复系统功能")
    print("=" * 60)
    
    # 测试修复系统
    fix_test_passed = test_unified_fix()
    
    # 测试后端导入
    import_test_passed = test_backend_imports()
    
    # 输出结果
    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)
    print(f"修复系统测试: {'通过' if fix_test_passed else '失败'}")
    print(f"后端导入测试: {'通过' if import_test_passed else '失败'}")
    
    if fix_test_passed and import_test_passed:
        print("\n✅ 所有测试通过！")
        return 0
    else:
        print("\n❌ 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
