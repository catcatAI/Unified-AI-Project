#!/usr/bin/env python3
"""
转义序列修复器
修复正则表达式中的无效转义序列
"""

import re
import sys
from pathlib import Path

def fix_escape_sequences_in_file(file_path: Path) -> bool:
    """修复文件中的转义序列"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修复常见的无效转义序列
        # 使用原始字符串或双反斜杠
        escape_fixes = [
            # 正则表达式相关的转义序列
            (r'([^\\])\s', r'\1\\s'),      # \s -> \\s
            (r'([^\\])\d', r'\1\\d'),      # \d -> \\d  
            (r'([^\\])\w', r'\1\\w'),      # \w -> \\w
            (r'([^\\])\b', r'\1\\b'),      # \b -> \\b
            (r'([^\\])\(', r'\1\\\('),     # \( -> \\(
            (r'([^\\])\)', r'\1\\\)'),     # \) -> \\)
            (r'([^\\])\[', r'\1\\\['),     # \[ -> \\[
            (r'([^\\])\]', r'\1\\\]'),     # \] -> \\]
            (r'([^\\])\{', r'\1\\\{'),     # \{ -> \\{
            (r'([^\\])\}', r'\1\\\}'),     # \} -> \\}
        ]
        
        for pattern, replacement in escape_fixes:
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 修复 {file_path.name} 中的转义序列")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ 修复 {file_path.name} 失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 启动转义序列修复器...")
    
    # 需要修复的文件列表
    files_to_fix = [
        "comprehensive_discovery_system.py"
    ]
    
    total_fixed = 0
    
    for file_name in files_to_fix:
        file_path = Path(file_name)
        
        if not file_path.exists():
            print(f"⚠️ 文件不存在: {file_name}")
            continue
        
        if fix_escape_sequences_in_file(file_path):
            total_fixed += 1
    
    print(f"\n📊 修复统计:")
    print(f"修复成功: {total_fixed}/{len(files_to_fix)}")
    
    if total_fixed > 0:
        print("✅ 转义序列修复完成")
    else:
        print("⚠️ 无需修复或修复失败")
    
    return 0 if total_fixed == len(files_to_fix) else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)