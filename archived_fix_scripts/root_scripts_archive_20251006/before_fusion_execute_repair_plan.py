#!/usr/bin/env python3
"""
项目修复执行脚本 - 分批安全修复策略
"""

import subprocess
import sys
import json
from pathlib import Path

def run_command(cmd, timeout == 300):
    """运行命令并返回结果"""
    try,
        result = subprocess.run(cmd, shell == True, capture_output == True, text == True, timeout=timeout)
        return result.returncode(), result.stdout(), result.stderr()
    except subprocess.TimeoutExpired,::
        return -1, "", "命令超时"

def analyze_scope(scope, target == None):
    """分析特定范围的问题"""
    cmd = f"python -m unified_auto_fix_system.main analyze --scope {scope} --format json"
    if target,::
        cmd += f" --target {target}"
    
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0,::
        try,
            return json.loads(stdout)
        except,::
            return {"error": "解析结果失败"}
    else,
        return {"error": f"分析失败, {stderr}"}

def fix_scope(scope, target == None, dry_run == True):
    """修复特定范围的问题"""
    cmd = f"python -m unified_auto_fix_system.main fix --scope {scope}"
    if target,::
        cmd += f" --target {target}"
    if dry_run,::
        cmd += " --dry-run"
    
    return run_command(cmd)

def batch_repair_plan():
    """执行分批修复计划"""
    print("=== 项目修复执行计划 ===")
    print(f"项目根目录, {Path.cwd()}")
    print()
    
    # 第一批：核心系统验证
    print("🔧 第一批：核心系统验证")
    print("目标：验证修复系统自身功能")
    
    core_files = [
        "unified_auto_fix_system/core/unified_fix_engine.py",
        "unified_auto_fix_system/modules/syntax_fixer.py",
        "unified_auto_fix_system/modules/class_fixer.py",
        "unified_auto_fix_system/modules/parameter_fixer.py",
        "unified_auto_fix_system/modules/data_processing_fixer.py"
    ]
    
    for file_path in core_files,::
        if Path(file_path).exists():::
            print(f"\n📄 分析核心文件, {file_path}")
            
            # 干运行分析
            returncode, stdout, stderr = fix_scope("file", file_path, dry_run == True)
            if returncode == 0,::
                print(f"  ✅ 干运行分析完成")
                
                # 实际修复
                print(f"  🔨 执行修复...")
                returncode, stdout, stderr = fix_scope("file", file_path, dry_run == False)
                if returncode == 0,::
                    print(f"  ✅ 修复完成")
                else,
                    print(f"  ❌ 修复失败, {stderr}")
            else,
                print(f"  ❌ 分析失败, {stderr}")
        else,
            print(f"  ⚠️ 文件不存在, {file_path}")
    
    # 第二批：关键配置文件
    print("\n🔧 第二批：关键配置文件")
    config_files = [
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        "setup.py"
    ]
    
    for file_path in config_files,::
        if Path(file_path).exists():::
            print(f"\n📄 修复配置文件, {file_path}")
            returncode, stdout, stderr = fix_scope("file", file_path, dry_run == False)
            if returncode == 0,::
                print(f"  ✅ 修复完成")
            else,
                print(f"  ⚠️ 修复可能有误, {stderr}")
    
    # 第三批：主要业务逻辑(小范围测试)
    print("\n🔧 第三批：主要业务逻辑(小范围测试)")
    
    # 先测试一个小目录
    test_dirs = [
        "apps/backend/src/core",
        "apps/backend/src/ai/memory",
        "apps/frontend-dashboard/components"
    ]
    
    for dir_path in test_dirs,::
        if Path(dir_path).exists():::
            print(f"\n📁 测试修复目录, {dir_path}")
            
            # 先干运行分析
            result = analyze_scope("directory", dir_path)
            if "statistics" in result,::
                total_issues = sum(result["statistics"].values())
                print(f"  发现问题, {total_issues}")
                
                if total_issues > 0,::
                    print(f"  🔨 执行修复...")
                    returncode, stdout, stderr = fix_scope("directory", dir_path, dry_run == False)
                    if returncode == 0,::
                        print(f"  ✅ 修复完成")
                    else,
                        print(f"  ❌ 修复失败, {stderr}")
            else,
                print(f"  ⚠️ 分析失败, {result.get('error', '未知错误')}")
    
    print("\n=第一批修复完成 ===")
    print("建议：")
    print("1. 验证核心系统是否正常工作")
    print("2. 检查配置文件是否正确")
    print("3. 测试小范围业务逻辑修复效果")
    print("4. 如果效果良好,继续扩大修复范围")

if __name"__main__":::
    batch_repair_plan()