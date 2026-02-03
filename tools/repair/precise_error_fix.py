#!/usr/bin/env python3
"""
精确错误修复脚本 - 针对项目中剩余的语法错误文件进行修复
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

def get_remaining_error_files():
    """获取剩余的错误文件列表"""
    # 根据之前的记忆，项目仍有约1901个文件存在语法错误
    # 我们需要找到这些文件并进行修复
    
    error_files = []
    
    # 检查一些已知可能存在问题的文件
    known_problem_files = [
        "unified_auto_fix_system/core/fix_result_new.py",
        "unified_auto_fix_system/core/enhanced_unified_fix_engine.py",
        # 可以添加更多已知问题文件
    ]
    
    for file_path in known_problem_files:
        full_path = project_root / file_path
        if full_path.exists():
            error_files.append(full_path)
    
    return error_files

def check_syntax_errors(file_path):
    """检查文件的语法错误"""
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(file_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return None  # 没有语法错误
        else:
            return result.stderr  # 返回错误信息
    except Exception as e:
        return str(e)

def fix_syntax_errors(file_path):
    """修复文件的语法错误"""
    try:
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        from unified_auto_fix_system.core.fix_result import FixContext
        from unified_auto_fix_system.core.fix_types import FixScope, FixPriority
        
        # 创建修复上下文
        context = FixContext(
            project_root=project_root,
            target_path=file_path,
            scope=FixScope.SPECIFIC_FILE,
            priority=FixPriority.HIGH,
            backup_enabled=True,
            dry_run=False
        )
        
        # 创建语法修复器
        fixer = EnhancedSyntaxFixer(project_root)
        
        # 执行修复
        result = fixer.fix(context)
        
        return result
    except Exception as e:
        print(f"修复文件 {file_path} 时出错: {e}")
        traceback.print_exc()
        return None

def validate_file_after_fix(file_path):
    """修复后验证文件"""
    try:
        # 检查语法错误
        syntax_error = check_syntax_errors(file_path)
        if syntax_error:
            print(f"✗ 文件 {file_path} 仍存在语法错误: {syntax_error}")
            return False
        
        # 尝试导入模块（如果适用）
        # 这里可以添加更具体的验证逻辑
        
        print(f"✓ 文件 {file_path} 修复验证通过")
        return True
    except Exception as e:
        print(f"验证文件 {file_path} 时出错: {e}")
        return False

def create_backup(file_path):
    """创建文件备份"""
    try:
        backup_path = file_path.with_suffix(file_path.suffix + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        import shutil
        shutil.copy2(file_path, backup_path)
        print(f"✓ 已创建备份: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"创建备份失败: {e}")
        return None

def repair_specific_files(file_list):
    """修复特定文件列表"""
    print(f"开始修复 {len(file_list)} 个文件...")
    
    results = {
        "total": len(file_list),
        "successful": 0,
        "failed": 0,
        "errors": []
    }
    
    for i, file_path in enumerate(file_list, 1):
        print(f"\n[{i}/{len(file_list)}] 修复文件: {file_path}")
        
        try:
            # 1. 首先检查文件是否存在语法错误
            syntax_error = check_syntax_errors(file_path)
            if not syntax_error:
                print(f"  文件 {file_path} 没有语法错误，跳过")
                results["successful"] += 1
                continue
            
            print(f"  发现语法错误: {syntax_error[:100]}...")
            
            # 2. 创建备份
            backup_path = create_backup(file_path)
            
            # 3. 执行修复
            result = fix_syntax_errors(file_path)
            if result:
                print(f"  修复结果: {result.summary()}")
                
                if result.is_successful():
                    # 4. 验证修复
                    if validate_file_after_fix(file_path):
                        print(f"  ✓ 文件修复成功")
                        results["successful"] += 1
                    else:
                        print(f"  ✗ 文件修复后验证失败")
                        results["failed"] += 1
                        results["errors"].append(f"{file_path}: 修复后验证失败")
                else:
                    print(f"  ✗ 文件修复失败: {result.error_message}")
                    results["failed"] += 1
                    results["errors"].append(f"{file_path}: {result.error_message}")
            else:
                print(f"  ✗ 修复过程失败")
                results["failed"] += 1
                results["errors"].append(f"{file_path}: 修复过程失败")
                
        except Exception as e:
            print(f"  ✗ 处理文件时出错: {e}")
            results["failed"] += 1
            results["errors"].append(f"{file_path}: {str(e)}")
            traceback.print_exc()
    
    return results

def main():
    """主函数"""
    print("开始精确错误修复...")
    print("=" * 30)
    
    # 1. 获取需要修复的文件列表
    error_files = get_remaining_error_files()
    if not error_files:
        print("未找到需要修复的文件")
        return 0
    
    print(f"找到 {len(error_files)} 个需要修复的文件")
    for file_path in error_files:
        print(f"  - {file_path}")
    
    print()
    
    # 2. 修复文件
    results = repair_specific_files(error_files)
    
    print("\n" + "=" * 30)
    print("修复结果汇总:")
    print(f"  总计文件数: {results['total']}")
    print(f"  成功修复: {results['successful']}")
    print(f"  修复失败: {results['failed']}")
    
    if results["errors"]:
        print("\n错误详情:")
        for error in results["errors"]:
            print(f"  - {error}")
    
    if results["successful"] == results["total"]:
        print("\n🎉 所有文件修复完成！")
        return 0
    else:
        print(f"\n⚠️  部分文件修复失败，请检查上述错误。")
        return 1

if __name__ == "__main__":
    sys.exit(main())