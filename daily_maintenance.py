#!/usr/bin/env python3
"""
日常维护脚本 - 每日自动运行
"""

import subprocess
import sys
from datetime import datetime

def daily_maintenance():
    """日常维护流程"""
    print(f"🌅 开始日常维护 - {datetime.now()}")
    
    # 1. 快速系统检查
    print("1️⃣ 快速系统检查...")
    try:
        subprocess.run([sys.executable, 'quick_system_check.py'], check=True, timeout=60)
        print("   ✅ 系统检查完成")
    except:
        print("   ⚠️ 系统检查失败")
    
    # 2. 语法错误扫描
    print("2️⃣ 语法错误扫描...")
    try:
        result = subprocess.run([sys.executable, 'scan_project_syntax_errors.py'], 
                              capture_output=True, text=True, timeout=120)
        error_count = result.stdout.count('发现语法错误')
        print(f"   📊 发现 {error_count} 个语法错误")
        
        if error_count > 10:  # 如果错误较多，运行修复
            print("3️⃣ 自动修复语法错误...")
            subprocess.run([sys.executable, 'efficient_mass_repair.py'], timeout=300)
            print("   ✅ 语法修复完成")
    except:
        print("   ⚠️ 语法扫描失败")
    
    # 3. 更新文档
    print("4️⃣ 更新维护日志...")
    try:
        with open('maintenance_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now()}: 日常维护完成\n")
        print("   ✅ 维护日志已更新")
    except:
        print("   ⚠️ 日志更新失败")
    
    print("✅ 日常维护完成！")

if __name__ == "__main__":
    daily_maintenance()
