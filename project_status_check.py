#!/usr/bin/env python3
"""
项目状态检查脚本 - 检查项目的当前状态和剩余错误
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def count_python_files():
    """统计项目中的Python文件数量"""
    print("统计Python文件数量...")
    
    python_files = list(project_root.rglob("*.py"))
    print(f"✓ 项目中共有 {len(python_files)} 个Python文件")
    return len(python_files)

def check_syntax_errors():
    """检查项目中的语法错误"""
    print("\n检查语法错误...")
    
    python_files = list(project_root.rglob("*.py"))
    error_files = []
    
    # 只检查前100个文件以避免性能问题
    files_to_check = python_files[:100]
    
    for py_file in files_to_check:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(py_file)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                error_files.append((py_file, result.stderr))
        except subprocess.TimeoutExpired:
            error_files.append((py_file, "检查超时"))
        except Exception as e:
            error_files.append((py_file, str(e)))
    
    print(f"✓ 检查了 {len(files_to_check)} 个文件")
    print(f"✓ 发现 {len(error_files)} 个存在语法错误的文件")
    
    # 显示前10个错误文件
    if error_files:
        print("\n前10个存在语法错误的文件:")
        for i, (file_path, error_msg) in enumerate(error_files[:10]):
            print(f"  {i+1}. {file_path.relative_to(project_root)}")
            print(f"     错误: {error_msg[:50]}...")
    
    return len(error_files)

def validate_auto_fix_system():
    """验证自动修复系统状态"""
    print("\n验证自动修复系统...")
    
    try:
        # 验证核心组件
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus
        from unified_auto_fix_system.core.fix_result import FixResult
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        
        print("✓ 核心组件导入成功")
        
        # 验证基本功能
        result = FixResult(
            fix_type=FixType.SYNTAX_FIX,
            status=FixStatus.SUCCESS,
            issues_found=1,
            issues_fixed=1
        )
        assert result.is_successful()
        print("✓ 数据类功能正常")
        
        # 验证修复器功能
        fixer = EnhancedSyntaxFixer(project_root)
        bad_code = "def test_func()\n    return True"
        fixed_code = fixer._fix_missing_colons(bad_code)
        assert "def test_func():" in fixed_code
        print("✓ 修复器功能正常")
        
        print("✓ 自动修复系统验证通过")
        return True
        
    except Exception as e:
        print(f"✗ 自动修复系统验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_core_system_files():
    """检查核心系统文件状态"""
    print("\n检查核心系统文件...")
    
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
    
    error_count = 0
    for file_path in core_files:
        full_path = project_root / file_path
        if full_path.exists():
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(full_path)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    print(f"✓ {file_path} 无语法错误")
                else:
                    print(f"✗ {file_path} 存在语法错误")
                    error_count += 1
            except Exception as e:
                print(f"✗ 检查 {file_path} 时出错: {e}")
                error_count += 1
        else:
            print(f"⚠️  {file_path} 不存在")
            error_count += 1
    
    return error_count == 0

def main():
    """主函数"""
    print("开始项目状态检查...")
    print("=" * 30)
    
    # 1. 统计Python文件
    total_files = count_python_files()
    
    # 2. 检查语法错误
    error_count = check_syntax_errors()
    
    # 3. 验证自动修复系统
    system_ok = validate_auto_fix_system()
    
    # 4. 检查核心系统文件
    core_files_ok = check_core_system_files()
    
    print("\n" + "=" * 30)
    print("项目状态检查结果:")
    print(f"  总Python文件数: {total_files}")
    print(f"  检查中发现错误文件数: {error_count} (检查了100个文件)")
    print(f"  自动修复系统状态: {'正常' if system_ok else '异常'}")
    print(f"  核心系统文件状态: {'正常' if core_files_ok else '异常'}")
    
    if system_ok and core_files_ok:
        print("\n🎉 项目状态检查完成，自动修复系统准备就绪！")
        return 0
    else:
        print("\n❌ 项目状态检查发现问题，请检查上述错误。")
        return 1

if __name__ == "__main__":
    sys.exit(main())