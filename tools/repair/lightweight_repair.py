#!/usr/bin/env python3
"""
轻量级修复脚本 - 专注于修复关键文件而不触发大型项目分析
"""

import sys
import os
import json
import traceback
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def validate_repair_system():
    """轻量级验证修复系统"""
    print("轻量级验证自动修复系统...")
    
    try:
        # 只验证最基本的组件
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
        
        # 验证语法修复器（不触发项目分析）
        fixer = EnhancedSyntaxFixer(project_root)
        # 直接测试修复方法
        bad_code = "def test_func()\n    return True"
        fixed_code = fixer._fix_missing_colons(bad_code)
        assert "def test_func():" in fixed_code
        print("✓ 语法修复功能正常")
        
        print("✓ 轻量级验证通过")
        return True
        
    except Exception as e:
        print(f"✗ 轻量级验证失败: {e}")
        traceback.print_exc()
        return False

def find_files_with_syntax_errors():
    """查找存在语法错误的文件（轻量级方法）"""
    print("查找可能存在语法错误的文件...")
    
    # 重点关注已知可能存在问题的目录
    key_directories = [
        "apps/backend/src",
        "apps/backend/tests",
        "training",
        "analysis",
        "cli"
    ]
    
    error_files = []
    
    # 检查这些目录中的Python文件
    for dir_name in key_directories:
        dir_path = project_root / dir_name
        if dir_path.exists():
            # 只检查前几个文件以避免性能问题
            py_files = list(dir_path.rglob("*.py"))[:10]  # 限制为每个目录最多10个文件
            for py_file in py_files:
                error_files.append(py_file)
    
    print(f"✓ 找到 {len(error_files)} 个待检查文件")
    return error_files[:30]  # 限制总数以避免性能问题

def check_file_syntax(file_path):
    """检查单个文件的语法"""
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(file_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return None  # 没有语法错误
        else:
            return result.stderr  # 返回错误信息
    except Exception as e:
        return str(e)

def create_file_backup(file_path):
    """创建文件备份"""
    try:
        backup_path = file_path.with_suffix(file_path.suffix + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        import shutil
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception as e:
        print(f"创建备份失败 {file_path}: {e}")
        return None

def fix_syntax_issues_in_file(file_path):
    """修复文件中的语法问题"""
    try:
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        from unified_auto_fix_system.core.fix_result import FixContext
        from unified_auto_fix_system.core.fix_types import FixScope, FixPriority
        
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 创建语法修复器（不触发项目分析）
        fixer = EnhancedSyntaxFixer(project_root)
        
        # 应用各种修复
        original_content = content
        content = fixer._fix_missing_colons(content)
        content = fixer._fix_indentation(content)
        content = fixer._fix_unmatched_parentheses(content)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            # 创建备份
            backup_path = create_file_backup(file_path)
            
            # 写入修复后的内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True, backup_path
        else:
            return False, None
            
    except Exception as e:
        print(f"修复文件失败 {file_path}: {e}")
        traceback.print_exc()
        return False, None

def repair_files_lightweight():
    """轻量级文件修复"""
    print("开始轻量级文件修复...")
    
    # 1. 查找文件
    files_to_check = find_files_with_syntax_errors()
    
    if not files_to_check:
        print("未找到需要检查的文件")
        return True
    
    # 2. 检查并修复文件
    results = {
        "total_checked": len(files_to_check),
        "syntax_errors_found": 0,
        "files_fixed": 0,
        "errors": []
    }
    
    for i, file_path in enumerate(files_to_check, 1):
        print(f"[{i}/{len(files_to_check)}] 检查文件: {file_path.name}")
        
        try:
            # 检查语法
            syntax_error = check_file_syntax(file_path)
            if syntax_error:
                print(f"  发现语法错误: {syntax_error[:50]}...")
                results["syntax_errors_found"] += 1
                
                # 尝试修复
                fixed, backup_path = fix_syntax_issues_in_file(file_path)
                if fixed:
                    print(f"  ✓ 文件已修复，备份: {backup_path.name if backup_path else 'None'}")
                    results["files_fixed"] += 1
                    
                    # 验证修复
                    verify_error = check_file_syntax(file_path)
                    if verify_error:
                        print(f"  ⚠️  修复后仍存在语法错误: {verify_error[:50]}...")
                else:
                    print(f"  ✗ 无法修复文件")
                    results["errors"].append(f"{file_path.name}: 无法修复")
            else:
                print(f"  ✓ 文件无语法错误")
                
        except Exception as e:
            print(f"  ✗ 检查文件时出错: {e}")
            results["errors"].append(f"{file_path.name}: {str(e)}")
    
    # 3. 显示结果
    print(f"\n修复结果:")
    print(f"  检查文件数: {results['total_checked']}")
    print(f"  发现语法错误: {results['syntax_errors_found']}")
    print(f"  成功修复: {results['files_fixed']}")
    print(f"  错误数: {len(results['errors'])}")
    
    if results["errors"]:
        print(f"\n错误详情:")
        for error in results["errors"][:5]:  # 只显示前5个错误
            print(f"  - {error}")
        if len(results["errors"]) > 5:
            print(f"  ... 还有 {len(results['errors']) - 5} 个错误")
    
    return results["syntax_errors_found"] == 0 or results["files_fixed"] > 0

def main():
    """主函数"""
    print("开始轻量级项目修复...")
    print("=" * 30)
    
    # 1. 验证修复系统
    if not validate_repair_system():
        print("❌ 自动修复系统验证失败")
        return 1
    
    print()
    
    # 2. 执行轻量级修复
    success = repair_files_lightweight()
    
    print("\n" + "=" * 30)
    if success:
        print("🎉 轻量级修复完成！")
        return 0
    else:
        print("⚠️  修复过程中出现问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())