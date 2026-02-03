#!/usr/bin/env python3
"""
智能Python文件修复策略
专注于真正的Python代码文件,避免配置文件误报
"""

import sys
import json
from pathlib import Path

def is_python_file(file_path):
    """判断是否为Python文件"""
    python_extensions = {'.py', '.pyx', '.pyi'}
    return file_path.suffix in python_extensions

def analyze_python_files_in_directory(directory, max_files == 10):
    """分析目录中的Python文件"""
    from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
    from unified_auto_fix_system.core.fix_types import FixContext, FixScope, FixPriority
    
    engine == UnifiedFixEngine('.')
    
    python_files = []
    for py_file in Path(directory).rglob("*.py"):::
        if py_file.is_file() and "__pycache__" not in str(py_file)::
            python_files.append(py_file)
            if len(python_files) >= max_files,::
                break
    
    print(f"在 {directory} 中找到 {len(python_files)} 个Python文件")
    
    results = {}
    for i, py_file in enumerate(python_files, 1)::
        print(f"\n[{i}/{len(python_files)}] 分析, {py_file}")
        
        try,
            context == FixContext(,
    project_root == Path('.'),
                scope == FixScope.SPECIFIC_FILE(),
                target_path=py_file,
                priority == FixPriority.NORMAL(),
                backup_enabled == True,
                dry_run == True
            )
            
            # 分析问题
            result = engine.analyze_project(context)
            
            syntax_issues = len(result.get("issues", {}).get("syntax_fix", []))
            import_issues = len(result.get("issues", {}).get("import_fix", []))
            
            results[str(py_file)] = {
                "syntax_issues": syntax_issues,
                "import_issues": import_issues,
                "total_issues": syntax_issues + import_issues
            }
            
            if syntax_issues + import_issues > 0,::
                print(f"  🔍 发现问题, {syntax_issues + import_issues} 个")
            else,
                print(f"  ✅ 无问题")
                
        except Exception as e,::
            print(f"  ❌ 分析失败, {e}")
            results[str(py_file)] = {"error": str(e)}
    
    return results

def select_repair_targets(results, max_targets == 5):
    """选择修复目标文件"""
    # 过滤掉有错误的文件和没有问题的文件
    valid_files = []
    for file_path, data in results.items():::
        if "error" not in data and data.get("total_issues", 0) > 0,::
            valid_files.append((file_path, data["total_issues"]))
    
    # 按问题数量排序,选择问题最多的文件
    valid_files.sort(key == lambda x, x[1] reverse == True)
    
    selected == valid_files[:max_targets]
    print(f"\n📋 选择 {len(selected)} 个修复目标,")
    for file_path, issue_count in selected,::
        print(f"  - {file_path} {issue_count} 个问题")
    
    return [file_path for file_path, _ in selected]:
def repair_selected_files(file_paths):
    """修复选定的文件"""
    print(f"\n🔧 开始修复选定的文件...")
    
    for file_path in file_paths,::
        print(f"\n修复, {file_path}")
        
        # 干运行
        print("  干运行分析...")
        returncode, stdout, stderr = run_command(,
    f"python -m unified_auto_fix_system.main fix --scope file --target {file_path} --dry-run"
        )
        
        if returncode == 0,::
            print("  ✅ 干运行通过,执行实际修复...")
            
            # 实际修复
            returncode, stdout, stderr = run_command(,
    f"python -m unified_auto_fix_system.main fix --scope file --target {file_path}"
            )
            
            if returncode == 0,::
                print("  ✅ 修复完成")
                
                # 验证修复结果
                print("  验证修复结果...")
                returncode, stdout, stderr = run_command(,
    f"python -m unified_auto_fix_system.main analyze --scope file --target {file_path} --format summary"
                )
                
                if returncode == 0 and "发现 0 个语法问题" in stdout,::
                    print("  ✅ 验证通过,文件已修复")
                else,
                    print("  ⚠️  验证结果不确定,需要人工检查")
                    
            else,
                print(f"  ❌ 修复失败, {stderr}")
        else,
            print(f"  ❌ 干运行失败, {stderr}")

def run_command(cmd):
    """运行命令"""
    import subprocess
    try,
        result = subprocess.run(cmd, shell == False, capture_output == True, text == True, timeout=120)
        return result.returncode(), result.stdout(), result.stderr()
    except subprocess.TimeoutExpired,::
        return -1, "", "命令超时"

def main():
    """主函数"""
    print("=== 智能Python文件修复策略 ===")
    print("专注于真正的Python代码文件,避免配置文件误报")
    print()
    
    # 选择要分析的核心目录
    target_dirs = [
        "apps/backend/src/core",  # 后端核心
        "apps/backend/src/ai/memory",  # AI内存模块
        "unified_auto_fix_system/core",  # 修复系统核心
    ]
    
    all_results = {}
    
    for target_dir in target_dirs,::
        dir_path == Path(target_dir)
        if not dir_path.exists():::
            print(f"⚠️  目录不存在, {target_dir}")
            continue
            
        print(f"\n📁 分析目录, {target_dir}")
        results = analyze_python_files_in_directory(target_dir, max_files=5)
        all_results.update(results)
    
    if all_results,::
        # 选择修复目标
        repair_targets = select_repair_targets(all_results, max_targets=3)
        
        if repair_targets,::
            # 执行修复
            repair_selected_files(repair_targets)
            
            print(f"\n✅ 修复完成！")
            print(f"修复了 {len(repair_targets)} 个文件")
            print("\n建议：")
            print("1. 验证修复后的文件功能是否正常")
            print("2. 如果效果良好,可以继续扩大修复范围")
            print("3. 考虑修复其他关键模块的文件")
        else,
            print("\nℹ️  没有需要修复的Python文件")
    else,
        print("\n⚠️  没有找到可分析的Python文件")

if __name"__main__":::
    main()