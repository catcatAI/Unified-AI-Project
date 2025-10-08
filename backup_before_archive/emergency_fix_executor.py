#!/usr/bin/env python3
"""
第6阶段：紧急修复执行器
修复代码质量检查中发现的关键问题
"""

import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

def fix_unterminated_string(file_path: Path) -> bool:
    """修复未终止的字符串字面量"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修复未终止的f-string
        content = re.sub(r'f"[^"]*$', 'f"""', content, flags=re.MULTILINE)
        content = re.sub(r"f'[^']*$", "f'''", content, flags=re.MULTILINE)
        
        # 修复未终止的普通字符串
        content = re.sub(r'"[^"]*$', '""', content, flags=re.MULTILINE)
        content = re.sub(r"'[^']*$", "''", content, flags=re.MULTILINE)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 修复 {file_path.name} 中的未终止字符串")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ 修复 {file_path.name} 失败: {e}")
        return False

def fix_unmatched_parenthesis(file_path: Path) -> bool:
    """修复不匹配的括号"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 简单的不匹配括号修复
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # 检查行末的括号
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                # 如果行末有不匹配的右括号，尝试移除
                if stripped.endswith(')') and stripped.count('(') < stripped.count(')'):
                    line = line.rstrip()[:-1]
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 修复 {file_path.name} 中的不匹配括号")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ 修复 {file_path.name} 失败: {e}")
        return False

def fix_escape_sequences(file_path: Path) -> bool:
    """修复无效的转义序列"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修复无效的转义序列
        content = re.sub(r'([^\\])\\s', r'\1\\s', content)  # \s -> \\s
        content = re.sub(r'([^\\])\\d', r'\1\\d', content)  # \d -> \\d
        content = re.sub(r'([^\\])\\(', r'\1\\(', content)  # \( -> \\(
        content = re.sub(r'([^\\])\\[', r'\1\\\[', content)  # \[ -> \\[
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 修复 {file_path.name} 中的无效转义序列")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ 修复 {file_path.name} 失败: {e}")
        return False

def fix_line_length(file_path: Path) -> bool:
    """修复行长度过长的问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            if len(line) > 120:
                # 尝试在合适的位置断行
                # 首先尝试在逗号后断行
                if ',' in line:
                    parts = line.split(',')
                    if len(parts) > 1:
                        # 将最后一部分移到下一行，保持缩进
                        indent = len(line) - len(line.lstrip())
                        new_line = ','.join(parts[:-1]) + ',\n' + ' ' * indent + parts[-1].lstrip()
                        fixed_lines.extend(new_line.split('\n'))
                        continue
                
                # 如果无法智能断行，添加警告注释
                if len(line) > 120:
                    fixed_lines.append(line[:117] + '...  # FIXME: 行过长')
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 修复 {file_path.name} 中的行长度问题")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ 修复 {file_path.name} 失败: {e}")
        return False

def fix_indentation(file_path: Path) -> bool:
    """修复缩进问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            if line.strip() and not line.startswith('#'):
                leading_spaces = len(line) - len(line.lstrip())
                # 如果缩进不是4的倍数，调整为4的倍数
                if leading_spaces % 4 != 0 and leading_spaces > 0:
                    new_indent = (leading_spaces // 4) * 4
                    line = ' ' * new_indent + line.lstrip()
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 修复 {file_path.name} 中的缩进问题")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ 修复 {file_path.name} 失败: {e}")
        return False

def main():
    """主函数：执行紧急修复"""
    print("🚨 启动紧急修复执行器 - 第6阶段")
    print(f"修复时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 需要修复的问题文件列表
    problematic_files = [
        ("documentation_detector.py", ["unterminated_string", "unmatched_parenthesis"]),
        ("logic_error_detector.py", ["unterminated_string"]),
        ("monitoring_dashboard.py", ["unterminated_string"]),
        ("performance_analyzer.py", ["unterminated_string"]),
        ("security_detector.py", ["unterminated_string"]),
        ("weekly_comprehensive_check.py", ["unterminated_string"]),
        ("comprehensive_discovery_system.py", ["escape_sequences"]),
        ("architecture_validator.py", ["line_length", "indentation"])
    ]
    
    total_fixed = 0
    total_files = len(problematic_files)
    
    for file_name, issues in problematic_files:
        file_path = Path(file_name)
        
        if not file_path.exists():
            print(f"⚠️  文件不存在: {file_name}")
            continue
        
        print(f"\n🔧 修复文件: {file_name}")
        file_fixed = False
        
        for issue in issues:
            if issue == "unterminated_string":
                if fix_unterminated_string(file_path):
                    file_fixed = True
            elif issue == "unmatched_parenthesis":
                if fix_unmatched_parenthesis(file_path):
                    file_fixed = True
            elif issue == "escape_sequences":
                if fix_escape_sequences(file_path):
                    file_fixed = True
            elif issue == "line_length":
                if fix_line_length(file_path):
                    file_fixed = True
            elif issue == "indentation":
                if fix_indentation(file_path):
                    file_fixed = True
        
        if file_fixed:
            total_fixed += 1
            print(f"✅ {file_name} 修复完成")
        else:
            print(f"⚠️  {file_name} 无需修复或修复失败")
    
    print(f"\n📊 修复统计:")
    print(f"总文件数: {total_files}")
    print(f"修复成功: {total_fixed}")
    print(f"修复率: {(total_fixed/total_files)*100:.1f}%")
    
    if total_fixed == total_files:
        print("\n🎉 所有关键问题修复完成！")
        return 0
    elif total_fixed > 0:
        print("\n✅ 部分问题已修复")
        return 0
    else:
        print("\n❌ 修复效果不佳，需要手动干预")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)