#!/usr/bin/env python3
"""
文件移动脚本 - 用于项目重构
"""

import shutil
import os
from pathlib import Path

def move_file(src, dst_dir):
    """移动文件到目标目录"""
    src_path = Path(src)
    dst_path = Path(dst_dir)
    
    if not src_path.exists():
        print(f"⚠️  源文件不存在: {src}")
        return False
    
    dst_path.mkdir(parents=True, exist_ok=True)
    
    try:
        dst_file = dst_path / src_path.name
        shutil.move(str(src_path), str(dst_file))
        print(f"✅ 已移动: {src} -> {dst_dir}/")
        return True
    except Exception as e:
        print(f"❌ 移动失败 {src}: {e}")
        return False

# 定义要移动的文件
files_to_move = [
    # check_*.py -> scripts/audit/
    ("check_system_completeness.py", "scripts/audit/"),
    ("check_real_status.py", "scripts/audit/"),
    
    # comprehensive_*.py -> scripts/audit/
    ("comprehensive_issue_scanner.py", "scripts/audit/"),
    ("comprehensive_quality_check.py", "scripts/audit/"),
    ("comprehensive_component_audit.py", "scripts/audit/"),
    ("comprehensive_system_check.py", "scripts/audit/"),
    ("comprehensive_audit.py", "scripts/audit/"),
    ("comprehensive_system_validation.py", "scripts/audit/"),
    ("comprehensive_auto_fix.py", "scripts/fixes/"),
    
    # fix_*.py -> scripts/fixes/
    ("fix_exceptions.py", "scripts/fixes/"),
    ("fix_action_executor.py", "scripts/fixes/"),
    
    # debug_*.py -> scripts/debug/
    ("debug_syntax.py", "scripts/debug/"),
    ("debug_real_training.py", "scripts/debug/"),
    ("debug_ethics.py", "scripts/debug/"),
    ("debug_main.py", "scripts/debug/"),
]

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 开始移动文件...")
    print("=" * 70)
    
    success_count = 0
    fail_count = 0
    
    for filename, dst_dir in files_to_move:
        if move_file(filename, dst_dir):
            success_count += 1
        else:
            fail_count += 1
    
    print("\n" + "=" * 70)
    print(f"✅ 成功: {success_count} 个文件")
    print(f"❌ 失败: {fail_count} 个文件")
    print("=" * 70)
