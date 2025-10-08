#!/usr/bin/env python3
"""
快速项目复杂度检查
判断项目是否适合使用简单修复方法
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def quick_complexity_assessment():
    """快速评估项目复杂度"""
    print("🔍 快速项目复杂度评估")
    print("=" * 50)
    
    project_root = Path('.')
    
    # 基础统计（限制范围以提高速度）
    total_files = 0
    python_files = 0
    total_lines = 0
    syntax_errors = 0
    max_file_lines = 0
    
    # 只分析关键目录，避免超时
    key_dirs = ['apps', 'packages', 'tools', 'tests']
    
    for check_dir in key_dirs:
        dir_path = project_root / check_dir
        if not dir_path.exists():
            continue
            
        for root, dirs, files in os.walk(dir_path):
            if '__pycache__' in root or '.git' in root:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    python_files += 1
                    file_path = Path(root) / file
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        lines = len(content.split('\n'))
                        total_lines += lines
                        max_file_lines = max(max_file_lines, lines)
                        
                        # 简单语法检查
                        try:
                            compile(content, str(file_path), 'exec')
                        except SyntaxError:
                            syntax_errors += 1
                            
                    except Exception:
                        pass
                        
                    total_files += 1
                    
                    # 限制分析数量，避免超时
                    if python_files > 100:  # 限制分析100个文件
                        break
            if python_files > 100:
                break
    
    # 估算总数（基于抽样）
    estimated_total_files = sum(1 for _ in project_root.rglob('*.py'))
    
    print(f"📊 快速评估结果:")
    print(f"  📁 Python文件总数: {estimated_total_files}")
    print(f"  📊 抽样分析文件: {python_files}")
    print(f"  📏 总行数(抽样): {total_lines:,}")
    print(f"  ❌ 语法错误(抽样): {syntax_errors}")
    print(f"  📐 最大文件: {max_file_lines} 行")
    
    # 复杂度判断
    if estimated_total_files > 500 or total_lines > 50000 or syntax_errors > 50:
        complexity = "complex"
        print(f"\n🚨 复杂度等级: {complexity.upper()}")
        print(f"🚨 结论: 项目复杂度过高，禁止使用简单修复脚本")
        print(f"🚨 要求: 必须使用统一自动修复系统的分批模式")
        return False
        
    elif estimated_total_files > 100 or total_lines > 10000 or syntax_errors > 10:
        complexity = "medium"  
        print(f"\n⚠️ 复杂度等级: {complexity.upper()}")
        print(f"⚠️ 结论: 项目复杂度中等，建议分批处理")
        print(f"⚠️ 要求: 使用统一修复系统，按目录分批处理")
        return True
        
    else:
        complexity = "simple"
        print(f"\n✅ 复杂度等级: {complexity.upper()}")
        print(f"✅ 结论: 项目复杂度较低，可以使用统一修复系统")
        print(f"✅ 要求: 仍需使用统一修复系统，避免简单脚本")
        return True

def main():
    """主函数"""
    print(f"⏰ 检查时间: {datetime.now()}")
    
    success = quick_complexity_assessment()
    
    if success:
        print(f"\n🎯 建议: 可以继续使用统一自动修复系统")
        sys.exit(0)
    else:
        print(f"\n🚨 警告: 项目过于复杂，必须极其谨慎")
        print(f"🚨 禁止: 任何简单修复脚本的使用")
        sys.exit(1)

if __name__ == "__main__":
    main()