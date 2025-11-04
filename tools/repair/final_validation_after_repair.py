#!/usr/bin/env python3
"""
修复后最终验证 - 确认自动修复系统在修复后仍然正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def validate_system_after_repair():
    """修复后验证系统"""
    print("修复后验证自动修复系统...")
    
    try:
        # 1. 验证核心组件仍然可以导入
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus
        from unified_auto_fix_system.core.fix_result import FixResult
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        
        print("✓ 核心组件仍然可以导入")
        
        # 2. 验证数据结构功能
        result = FixResult(
            fix_type=FixType.SYNTAX_FIX,
            status=FixStatus.SUCCESS,
            issues_found=5,
            issues_fixed=5
        )
        
        if result.is_successful() and "成功修复 5 个问题" in result.summary():
            print("✓ 数据结构功能正常")
        else:
            print("✗ 数据结构功能异常")
            return False
        
        # 3. 验证修复器功能（不触发项目分析）
        fixer = EnhancedSyntaxFixer(project_root)
        
        # 测试修复方法
        bad_code = "def test_func()\n    return True"
        fixed_code = fixer._fix_missing_colons(bad_code)
        if "def test_func():" in fixed_code:
            print("✓ 修复器功能正常")
        else:
            print("✗ 修复器功能异常")
            return False
        
        # 4. 验证枚举值
        assert FixType.SYNTAX_FIX.value == "syntax_fix"
        assert FixStatus.SUCCESS.value == "success"
        print("✓ 枚举值正确")
        
        print("✓ 修复后系统验证通过")
        return True
        
    except Exception as e:
        print(f"✗ 修复后系统验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_system_files():
    """检查系统文件状态"""
    print("\n检查系统文件状态...")
    
    # 检查统一自动修复系统的核心文件
    core_files = [
        "unified_auto_fix_system/__init__.py",
        "unified_auto_fix_system/core/fix_types.py",
        "unified_auto_fix_system/core/fix_result.py",
        "unified_auto_fix_system/core/unified_fix_engine.py",
        "unified_auto_fix_system/modules/base_fixer.py",
        "unified_auto_fix_system/modules/syntax_fixer.py",
        "unified_auto_fix_system/modules/import_fixer.py"
    ]
    
    all_good = True
    for file_path in core_files:
        full_path = project_root / file_path
        if full_path.exists():
            # 检查语法
            try:
                import subprocess
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(full_path)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    print(f"✓ {file_path} 无语法错误")
                else:
                    print(f"✗ {file_path} 存在语法错误: {result.stderr[:50]}...")
                    all_good = False
            except Exception as e:
                print(f"✗ 检查 {file_path} 时出错: {e}")
                all_good = False
        else:
            print(f"⚠️  {file_path} 不存在")
            all_good = False
    
    return all_good

def main():
    """主函数"""
    print("开始修复后最终验证...")
    print("=" * 25)
    
    # 1. 验证系统功能
    system_ok = validate_system_after_repair()
    
    # 2. 检查系统文件
    files_ok = check_system_files()
    
    print("\n" + "=" * 25)
    if system_ok and files_ok:
        print("🎉 修复后最终验证通过！")
        print("自动修复系统功能正常，核心文件无语法错误。")
        return 0
    else:
        print("❌ 修复后最终验证失败！")
        if not system_ok:
            print("  - 系统功能存在问题")
        if not files_ok:
            print("  - 系统文件存在语法错误")
        return 1

if __name__ == "__main__":
    sys.exit(main())