#!/usr/bin/env python3
"""
测试自动修复系统的实际修复功能
"""

import sys
import os
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_actual_syntax_fix():
    """测试实际语法修复功能"""
    print("测试实际语法修复功能...")
    
    try:
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        from unified_auto_fix_system.core.fix_result import FixContext
        from unified_auto_fix_system.core.fix_types import FixScope, FixPriority
        
        # 创建临时目录和测试文件
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test_syntax.py"
            
            # 创建一个有语法错误的文件
            bad_content = """def test_function()
    return True

if True
    print("Hello")
"""
            test_file.write_text(bad_content, encoding='utf-8')
            print("✓ 创建了带语法错误的测试文件")
            
            # 创建语法修复器
            fixer = EnhancedSyntaxFixer(temp_path)
            
            # 创建修复上下文
            context = FixContext(
                project_root=temp_path,
                target_path=test_file,
                scope=FixScope.SPECIFIC_FILE,
                priority=FixPriority.NORMAL,
                dry_run=False  # 实际修复
            )
            
            # 执行修复
            result = fixer.fix(context)
            print(f"✓ 修复完成: {result.summary()}")
            
            # 检查修复结果
            if result.is_successful():
                # 读取修复后的文件
                fixed_content = test_file.read_text(encoding='utf-8')
                print("✓ 文件已成功修复")
                print("修复后的内容:")
                print(fixed_content)
                
                # 验证修复是否正确
                assert "def test_function():" in fixed_content
                assert "if True:" in fixed_content
                print("✓ 修复内容正确")
            else:
                print(f"✗ 修复失败: {result.error_message}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ 实际语法修复测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dry_run_mode():
    """测试干运行模式"""
    print("\n测试干运行模式...")
    
    try:
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        from unified_auto_fix_system.core.fix_result import FixContext
        from unified_auto_fix_system.core.fix_types import FixScope, FixPriority
        
        # 创建临时目录和测试文件
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test_dry_run.py"
            
            # 创建一个有语法错误的文件
            bad_content = """def another_function()
    return False"""
            test_file.write_text(bad_content, encoding='utf-8')
            print("✓ 创建了带语法错误的测试文件")
            
            # 创建语法修复器
            fixer = EnhancedSyntaxFixer(temp_path)
            
            # 创建修复上下文（干运行模式）
            context = FixContext(
                project_root=temp_path,
                target_path=test_file,
                scope=FixScope.SPECIFIC_FILE,
                priority=FixPriority.NORMAL,
                dry_run=True  # 干运行模式
            )
            
            # 执行分析
            issues = fixer.analyze(context)
            print(f"✓ 分析完成，发现 {len(issues)} 个问题")
            
            # 执行干运行修复
            result = fixer.fix(context)
            print(f"✓ 干运行修复完成: {result.summary()}")
            
            # 检查文件是否未被修改
            unchanged_content = test_file.read_text(encoding='utf-8')
            assert unchanged_content == bad_content
            print("✓ 干运行模式下文件未被修改")
        
        return True
    except Exception as e:
        print(f"✗ 干运行模式测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backup_functionality():
    """测试备份功能"""
    print("\n测试备份功能...")
    
    try:
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        
        # 创建临时目录和测试文件
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test_backup.py"
            
            # 创建测试文件
            original_content = "print('original content')"
            test_file.write_text(original_content, encoding='utf-8')
            print("✓ 创建了测试文件")
            
            # 创建语法修复器（具体实现类）
            fixer = EnhancedSyntaxFixer(temp_path)
            
            # 创建备份
            backup_path = fixer._create_backup(test_file)
            print(f"✓ 创建了备份文件: {backup_path}")
            
            # 检查备份文件是否存在且内容正确
            assert backup_path.exists()
            backup_content = backup_path.read_text(encoding='utf-8')
            assert backup_content == original_content
            print("✓ 备份文件内容正确")
        
        return True
    except Exception as e:
        print(f"✗ 备份功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试统一自动修复系统的实际修复功能...")
    print("=" * 50)
    
    # 运行各项测试
    tests = [
        test_actual_syntax_fix,
        test_dry_run_mode,
        test_backup_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"测试完成: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有实际修复功能测试通过！")
        return 0
    else:
        print("❌ 部分实际修复功能测试失败，请检查上述错误。")
        return 1

if __name__ == "__main__":
    sys.exit(main())