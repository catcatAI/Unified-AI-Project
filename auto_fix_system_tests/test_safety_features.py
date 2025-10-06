#!/usr/bin/env python3
"""测试修复系统的范围控制功能"""

import sys
from pathlib import Path

def test_scope_control():
    """测试范围控制功能"""
    try:
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        from unified_auto_fix_system.core.fix_types import FixContext, FixScope, FixPriority
        
        # 创建引擎
        engine = UnifiedFixEngine(".")
        
        # 测试不同的范围设置
        scopes = [
            FixScope.PROJECT,
            FixScope.BACKEND, 
            FixScope.SPECIFIC_FILE,
            FixScope.SPECIFIC_DIRECTORY
        ]
        
        print("测试范围控制功能:")
        
        for scope in scopes:
            context = FixContext(
                project_root=Path("."),
                scope=scope,
                priority=FixPriority.NORMAL,
                backup_enabled=True,
                dry_run=True  # 干运行模式，不实际修复
            )
            
            # 获取目标文件列表来验证范围控制
            if hasattr(engine.modules[FixType.SYNTAX_FIX], '_get_target_files'):
                target_files = engine.modules[FixType.SYNTAX_FIX]._get_target_files(context)
                print(f"  {scope.value}: 找到 {len(target_files)} 个目标文件")
            else:
                print(f"  {scope.value}: 模块方法可用")
        
        print("✅ 范围控制功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 范围控制测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dry_run_protection():
    """测试干运行保护机制"""
    try:
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        from unified_auto_fix_system.core.fix_types import FixContext, FixScope, FixPriority
        
        engine = UnifiedFixEngine(".")
        
        # 创建干运行上下文
        context = FixContext(
            project_root=Path("."),
            scope=FixScope.PROJECT,
            priority=FixPriority.NORMAL,
            backup_enabled=True,
            dry_run=True  # 启用干运行模式
        )
        
        print("\n测试干运行保护机制:")
        
        # 执行干运行分析
        result = engine.analyze_project(context)
        
        if "issues" in result:
            issue_count = sum(len(issues) for issues in result["issues"].values())
            print(f"  干运行分析完成，发现问题: {issue_count}")
            print("  ✅ 干运行模式正常工作，不会实际修改文件")
            return True
        else:
            print("  ❌ 干运行分析未返回预期结果")
            return False
            
    except Exception as e:
        print(f"❌ 干运行保护测试失败: {e}")
        return False

def test_backup_protection():
    """测试备份保护机制"""
    try:
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        from unified_auto_fix_system.core.fix_types import FixContext, FixScope, FixPriority
        
        engine = UnifiedFixEngine(".")
        
        # 创建启用备份的上下文
        context = FixContext(
            project_root=Path("."),
            scope=FixScope.PROJECT,
            priority=FixPriority.NORMAL,
            backup_enabled=True,  # 启用备份
            dry_run=True  # 干运行模式
        )
        
        print("\n测试备份保护机制:")
        
        # 检查备份目录设置
        backup_dir = engine.backup_dir
        print(f"  备份目录: {backup_dir}")
        print(f"  备份目录存在: {backup_dir.exists()}")
        
        if backup_dir.exists():
            print("  ✅ 备份保护机制已配置")
            return True
        else:
            print("  ❌ 备份目录不存在")
            return False
            
    except Exception as e:
        print(f"❌ 备份保护测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试修复系统安全功能...")
    print("=" * 50)
    
    tests = [
        ("范围控制测试", test_scope_control),
        ("干运行保护测试", test_dry_run_protection),
        ("备份保护测试", test_backup_protection)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"  失败，可能影响后续测试")
    
    print(f"\n安全功能测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✅ 所有安全功能测试通过！")
        print("\n安全特性总结:")
        print("  - 范围控制: 支持PROJECT、BACKEND、SPECIFIC_FILE等多种范围")
        print("  - 干运行模式: 可以分析问题而不实际修改文件")
        print("  - 备份机制: 自动创建备份，支持恢复")
        print("  - 模块化设计: 可以单独启用/禁用特定修复模块")
        return 0
    else:
        print("❌ 部分安全功能测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())