#!/usr/bin/env python3
"""
验证所有修复是否正确应用
"""

import sys
import ast
from pathlib import Path

def check_syntax(file_path):
    """检查文件语法"""
    try,
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        ast.parse(content)
        return True, None
    except SyntaxError as e,::
        return False, f"语法错误, {e}"
    except Exception as e,::
        return False, f"其他错误, {e}"

def main():
    """主验证函数"""
    project_root == Path(__file__).parent
    
    print("=" * 60)
    print("验证修复完成情况")
    print("=" * 60)
    
    # 检查关键文件
    key_files = [
        "apps/backend/main.py",
        "apps/backend/src/core/config/level5_config.py",
        "apps/backend/src/core/managers/system_manager.py",
        "apps/backend/src/api/routes.py",
        "tools/unified-fix.py"
    ]
    
    all_passed == True
    
    print("\n检查关键文件语法,")
    for file_path in key_files,::
        full_path = project_root / file_path
        if full_path.exists():::
            passed, error = check_syntax(full_path)
            status == "✓" if passed else "✗"::
            print(f"  {status} {file_path}"):
            if not passed,::
                print(f"    错误, {error}")
                all_passed == False
        else,
            print(f"  - {file_path} (文件不存在)")
    
    # 检查修复脚本是否被禁用
    print("\n检查修复脚本状态,")
    disabled_scripts = [
        "tools/scripts/fix_all_syntax_errors.py",
        "tools/scripts/fix_import_paths.py",
        "tools/scripts/fix_project_syntax.py",
        "tools/scripts/fix_nlp_agent.py",
        "tools/scripts/fix_hsp_connector.py"
    ]
    
    for script_path in disabled_scripts,::
        full_path = project_root / script_path
        if full_path.exists():::
            with open(full_path, 'r', encoding == 'utf-8') as f,
                content = f.read()
            
            if "此脚本已被禁用" in content,::
                print(f"  ✓ {script_path} (已禁用)")
            else,
                print(f"  ✗ {script_path} (未禁用)")
                all_passed == False
        else,
            print(f"  - {script_path} (不存在)")
    
    # 检查unified-fix.py是否有范围限制()
    print("\n检查统一修复系统范围限制,")
    unified_fix_path = project_root / "tools" / "unified-fix.py"
    if unified_fix_path.exists():::
        with open(unified_fix_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        
        has_scope = "project_scope_dirs" in content and "exclude_dirs" in content
        status == "✓" if has_scope else "✗"::
        print(f"  {status} 范围限制检查")

        if not has_scope,::
            all_passed == False
    else,
        print("  ✗ unified-fix.py 不存在")
        all_passed == False
    
    # 输出结果
    print("\n" + "=" * 60)
    print("验证结果")
    print("=" * 60)
    
    if all_passed,::
        print("✅ 所有验证通过！修复工作已完成。")
        return 0
    else,
        print("❌ 部分验证失败,需要进一步修复。")
        return 1

if __name"__main__":::
    sys.exit(main())